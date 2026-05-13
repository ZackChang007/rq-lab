"""
RQData 补充数据下载工具

下载建议的补充数据：
1. 期权日线行情 (~50 MB)
2. 期货日线行情 (~100 MB)
3. A股分钟行情样本 (~50 MB)
4. 期权指标 (~15 MB)
5. 期货升贴水数据 (~10 MB)

用法:
    python scripts/data/download_supplement.py
"""
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd
import rqdatac
from utils.common import setup_license

setup_license()

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"
LOG_PATH = DATA_ROOT / "download_log.json"
QUOTA_MARGIN_MB = 10

rqdatac.init()

_session_used_mb = 0.0


def get_quota_info():
    try:
        quota = rqdatac.user.get_quota()
        return {
            "limit_mb": quota["bytes_limit"] / 1024 / 1024,
            "used_mb": quota["bytes_used"] / 1024 / 1024,
            "remaining_mb": (quota["bytes_limit"] - quota["bytes_used"]) / 1024 / 1024,
        }
    except Exception as e:
        print(f"  [警告] 获取配额失败: {e}")
        return {"limit_mb": 1024, "used_mb": 1024, "remaining_mb": 0}


def check_quota(need_mb=50):
    info = get_quota_info()
    rem = info["remaining_mb"]
    if rem < QUOTA_MARGIN_MB:
        print(f"  [流量不足] 剩余 {rem:.1f} MB，停止下载")
        return False
    if rem < need_mb:
        print(f"  [流量紧张] 剩余 {rem:.1f} MB，需要 {need_mb} MB，跳过")
        return False
    return True


def track_usage(before_mb):
    global _session_used_mb
    info = get_quota_info()
    actual = info["used_mb"] - before_mb
    if actual > 0:
        _session_used_mb += actual
    return actual


def load_log():
    if LOG_PATH.exists():
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    return {}


def save_log(log):
    LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


def is_done(key):
    log = load_log()
    for day_data in log.values():
        if key in day_data and day_data[key]["status"] == "done":
            return True
    return False


def mark_done(key, rows=0, bytes_est=0):
    log = load_log()
    today = datetime.now().strftime("%Y-%m-%d")
    log.setdefault(today, {})[key] = {
        "status": "done",
        "rows": rows,
        "bytes_est": bytes_est,
        "ts": datetime.now().isoformat(),
    }
    save_log(log)


def safe_download(key, func, path, need_mb=50):
    if is_done(key):
        print(f"  [跳过] {key} 已下载")
        return True

    if not check_quota(need_mb):
        return False

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(3):
        try:
            info_before = get_quota_info()
            before_mb = info_before["used_mb"]

            print(f"  [下载] {key} ...", end=" ", flush=True)
            df = func()

            actual_used = track_usage(before_mb)

            if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                print(f"数据为空 (消耗 {actual_used:.2f} MB)")
                mark_done(key, rows=0, bytes_est=int(actual_used * 1024 * 1024))
                return True

            if isinstance(df, pd.DataFrame):
                df.to_parquet(str(path), engine="pyarrow", compression="snappy", index=True)
                rows = len(df)
            else:
                # Series 转 DataFrame
                if isinstance(df, pd.Series):
                    df = df.to_frame(name="value")
                    df.to_parquet(str(path), engine="pyarrow", compression="snappy", index=True)
                    rows = len(df)
                else:
                    path = path.with_suffix(".json")
                    path.write_text(json.dumps(df, ensure_ascii=False), encoding="utf-8")
                    rows = 1

            print(f"完成 ({rows} 行, 消耗 {actual_used:.2f} MB)")
            mark_done(key, rows=rows, bytes_est=int(actual_used * 1024 * 1024))
            return True

        except Exception as e:
            err_msg = str(e)
            if "Quota exceeded" in err_msg:
                print(f"流量超限")
                return False
            print(f"失败 (尝试 {attempt+1}/3): {e}")
            traceback.print_exc()
            time.sleep(5)

    return False


def session_summary():
    info = get_quota_info()
    print(f"\n=== 流量使用摘要 ===")
    print(f"  本次会话消耗: {_session_used_mb:.1f} MB")
    print(f"  当前剩余: {info['remaining_mb']:.1f} MB")


def download_options_price():
    """下载期权日线行情"""
    print("\n=== 1. 期权日线行情 ===")

    # 获取期权合约列表
    opt = rqdatac.all_instruments(type="Option")
    if opt is None or opt.empty:
        print("  期权合约列表为空")
        return

    opt_ids = opt["order_book_id"].tolist()
    print(f"  期权合约总数: {len(opt_ids)}")

    # 分批下载（期权数量大，分时段）
    date_ranges = [
        ("2022-01-01", "2023-12-31"),
        ("2024-01-01", "2025-12-31"),
        ("2026-01-01", "2026-12-31"),
    ]

    all_frames = []
    for start, end in date_ranges:
        key = f"options/price_1d_{start}_{end}"
        if is_done(key):
            continue
        if not check_quota(30):
            break

        try:
            info_before = get_quota_info()
            before_mb = info_before["used_mb"]

            print(f"  [下载] {key} ...", end=" ", flush=True)
            df = rqdatac.get_price(
                opt_ids[:500],  # 限制数量避免超时
                start_date=start, end_date=end,
                frequency="1d",
                fields=["open", "close", "high", "low", "total_turnover", "volume", "prev_close", "limit_up", "limit_down"],
                adjust_type="none", expect_df=True,
            )

            actual_used = track_usage(before_mb)

            if df is not None and not df.empty:
                all_frames.append(df)
                rows = len(df)
                print(f"完成 ({rows} 行, 消耗 {actual_used:.2f} MB)")
                mark_done(key, rows=rows, bytes_est=int(actual_used * 1024 * 1024))
            else:
                print(f"数据为空 (消耗 {actual_used:.2f} MB)")
                mark_done(key, rows=0, bytes_est=int(actual_used * 1024 * 1024))

        except Exception as e:
            print(f"失败: {e}")

    if all_frames:
        merged = pd.concat(all_frames)
        out_path = DATA_ROOT / "options/price_1d.parquet"
        merged.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
        print(f"  [合并] 期权日线行情 -> {out_path} ({len(merged)} 行)")


def download_futures_price():
    """下载期货日线行情"""
    print("\n=== 2. 期货日线行情 ===")

    # 获取期货合约列表
    future_types = ['IF', 'IH', 'IC', 'IM', 'TF', 'T', 'TS', 'TL', 'CU', 'AL', 'ZN', 'AU', 'AG']

    all_frames = []
    for ft in future_types:
        key = f"futures/price_1d_{ft}"
        if is_done(key):
            continue
        if not check_quota(10):
            break

        try:
            # 获取该品种的主力合约
            dominant = rqdatac.futures.get_dominant(ft, "2014-01-01", "2026-12-31")
            if dominant is None or dominant.empty:
                continue

            # 获取主力合约ID列表
            contracts = dominant.tolist() if isinstance(dominant, pd.Series) else dominant['dominant_contract'].tolist()
            contracts = list(set(contracts))[:100]  # 唯一值，限制数量

            info_before = get_quota_info()
            before_mb = info_before["used_mb"]

            print(f"  [下载] {ft} 日线行情 ({len(contracts)} 合约) ...", end=" ", flush=True)
            df = rqdatac.get_price(
                contracts,
                start_date="2014-01-01", end_date="2026-12-31",
                frequency="1d",
                fields=["open", "close", "high", "low", "total_turnover", "volume", "open_interest", "prev_close", "limit_up", "limit_down"],
                adjust_type="none", expect_df=True,
            )

            actual_used = track_usage(before_mb)

            if df is not None and not df.empty:
                all_frames.append(df)
                rows = len(df)
                print(f"完成 ({rows} 行, 消耗 {actual_used:.2f} MB)")
                mark_done(key, rows=rows, bytes_est=int(actual_used * 1024 * 1024))
            else:
                print(f"数据为空")
                mark_done(key, rows=0, bytes_est=0)

        except Exception as e:
            print(f"失败: {e}")

    if all_frames:
        merged = pd.concat(all_frames)
        out_path = DATA_ROOT / "futures/price_1d.parquet"
        merged.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
        print(f"  [合并] 期货日线行情 -> {out_path} ({len(merged)} 行)")


def download_stock_minute_sample():
    """下载A股分钟行情样本（2024年）"""
    print("\n=== 3. A股分钟行情样本 ===")

    # 获取部分A股样本
    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()[:50]  # 仅50只样本股票
    print(f"  样本股票数: {len(stock_ids)}")

    # 下载2024年全年分钟数据
    key = "stock/price_1m_2024_sample"
    if not is_done(key) and check_quota(50):
        safe_download(
            key,
            lambda: rqdatac.get_price(
                stock_ids,
                start_date="2024-01-01", end_date="2024-12-31",
                frequency="1m",
                fields=["open", "close", "high", "low", "total_turnover", "volume"],
                adjust_type="pre", expect_df=True,
            ),
            DATA_ROOT / "stock/price_1m_2024_sample.parquet",
            need_mb=50,
        )


def download_options_indicators():
    """下载期权指标"""
    print("\n=== 4. 期权指标 ===")

    # ETF期权标的
    underlying_symbols = ["510050.XSHG", "510300.XSHG", "159919.XSHE"]

    # 下载期权指标数据
    for sym in underlying_symbols:
        key = f"options/indicators_{sym}"
        if is_done(key):
            continue
        if not check_quota(5):
            break

        try:
            info_before = get_quota_info()
            before_mb = info_before["used_mb"]

            print(f"  [下载] 期权指标 {sym} ...", end=" ", flush=True)
            df = rqdatac.options.get_indicators(sym, "2022-01-01", "2026-12-31")

            actual_used = track_usage(before_mb)

            if df is not None and not df.empty:
                out_path = DATA_ROOT / f"options/indicators_{sym}.parquet"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
                rows = len(df)
                print(f"完成 ({rows} 行, 消耗 {actual_used:.2f} MB)")
                mark_done(key, rows=rows, bytes_est=int(actual_used * 1024 * 1024))
            else:
                print(f"数据为空")
                mark_done(key, rows=0, bytes_est=0)

        except Exception as e:
            print(f"失败: {e}")
            if "Quota exceeded" in str(e):
                return


def download_futures_basis():
    """下载期货升贴水数据"""
    print("\n=== 5. 期货升贴水数据 ===")

    future_types = ['IF', 'IH', 'IC', 'IM', 'CU', 'AL', 'ZN', 'AU', 'AG']

    safe_download(
        "futures/basis",
        lambda: rqdatac.futures.get_basis(future_types, "2014-01-01", "2026-12-31"),
        DATA_ROOT / "futures/basis.parquet",
        need_mb=15,
    )


def main():
    info = get_quota_info()
    print(f"RQData 补充数据下载 | 剩余流量: {info['remaining_mb']:.1f} MB")
    print(f"数据目录: {DATA_ROOT}")

    # 按优先级顺序下载
    steps = [
        ("期权日线行情", download_options_price),
        ("期货日线行情", download_futures_price),
        ("A股分钟行情样本", download_stock_minute_sample),
        ("期权指标", download_options_indicators),
        ("期货升贴水", download_futures_basis),
    ]

    for name, func in steps:
        if not check_quota(QUOTA_MARGIN_MB + 10):
            print(f"\n[停止] 流量不足，请稍后继续")
            break
        func()

    session_summary()


if __name__ == "__main__":
    main()