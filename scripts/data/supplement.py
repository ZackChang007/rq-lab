"""
数据补充脚本 - 补充 progress.md 中待下载的数据

用法:
    python scripts/data/supplement.py [task]

    task: margin | etf | lof | all

优先级（按 progress.md）:
    1. A股融资融券 (补充早期数据)
    2. ETF日线行情
    3. LOF日线行情

注意: 资金流向 API 不存在，无法下载。
"""
import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd
import rqdatac
from utils.common import setup_license

setup_license()
rqdatac.init()

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"
LOG_PATH = DATA_ROOT / "download_log.json"
DAILY_QUOTA_MB = 1024
QUOTA_MARGIN_MB = 10

# 流量追踪
_session_used_mb = 0.0


def get_quota_info():
    """获取配额信息"""
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
    """检查流量是否充足"""
    info = get_quota_info()
    rem = info["remaining_mb"]
    if rem < QUOTA_MARGIN_MB:
        print(f"  [流量不足] 剩余 {rem:.1f} MB，低于安全余量 {QUOTA_MARGIN_MB} MB")
        return False
    if rem < need_mb:
        print(f"  [流量紧张] 剩余 {rem:.1f} MB，需要 {need_mb} MB，跳过")
        return False
    return True


def track_usage(before_mb):
    """追踪实际流量消耗"""
    global _session_used_mb
    info = get_quota_info()
    actual = info["used_mb"] - before_mb
    if actual > 0:
        _session_used_mb += actual
    return actual


def session_summary():
    """打印本次会话流量摘要"""
    info = get_quota_info()
    print(f"\n=== 流量使用摘要 ===")
    print(f"  本次会话消耗: {_session_used_mb:.1f} MB")
    print(f"  当前剩余: {info['remaining_mb']:.1f} MB")


def load_log():
    if LOG_PATH.exists():
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    return {}


def save_log(log):
    LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


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


def is_done(key):
    log = load_log()
    for day_data in log.values():
        if key in day_data and day_data[key]["status"] == "done":
            return True
    return False


def mark_failed(key, err_msg):
    log = load_log()
    today = datetime.now().strftime("%Y-%m-%d")
    log.setdefault(today, {})[key] = {
        "status": "failed",
        "error": err_msg[:200],
        "ts": datetime.now().isoformat(),
    }
    save_log(log)


def safe_download(key, func, path, need_mb=50):
    """安全下载：断点续传 + 流量检查"""
    if is_done(key):
        print(f"  [跳过] {key} 已下载")
        return True

    if not check_quota(need_mb):
        return False

    last_error = None
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

            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(str(path), engine="pyarrow", compression="snappy")
            rows = len(df)
            print(f"完成 ({rows} 行, 消耗 {actual_used:.2f} MB)")
            mark_done(key, rows=rows, bytes_est=int(actual_used * 1024 * 1024))
            return True

        except Exception as e:
            last_error = e
            err_msg = str(e)
            if "Quota exceeded" in err_msg:
                print(f"流量超限")
                mark_failed(key, "Quota exceeded")
                return False
            print(f"失败 (尝试 {attempt+1}/3): {e}")
            traceback.print_exc()
            time.sleep(5)

    mark_failed(key, str(last_error))
    return False


# ── 任务1: A股融资融券（补充早期数据）─────────────────────────────────────
def download_margin():
    """下载融资融券数据（补充早期数据）"""
    print("\n=== Task 1: A股融资融券（补充早期数据）===")

    # 获取全部 A 股
    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()
    print(f"  A股总数: {len(stock_ids)}")

    # 补充 2010-01-01 ~ 2015-12-31 的数据
    date_ranges = [
        ("2010-01-01", "2012-12-31"),
        ("2013-01-01", "2015-12-31"),
    ]

    for start, end in date_ranges:
        key = f"stock/securities_margin_{start}_{end}"
        if is_done(key):
            print(f"  [跳过] {key} 已下载")
            continue

        if not check_quota(30):
            break

        try:
            info_before = get_quota_info()
            before_mb = info_before["used_mb"]

            print(f"  [下载] {key} ...", end=" ", flush=True)
            df = rqdatac.get_securities_margin(stock_ids, start_date=start, end_date=end)

            actual_used = track_usage(before_mb)

            if df is not None and not df.empty:
                out_path = DATA_ROOT / f"stock/securities_margin_{start}_{end}.parquet"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
                print(f"完成 ({len(df)} 行, 消耗 {actual_used:.2f} MB)")
                mark_done(key, rows=len(df), bytes_est=int(actual_used * 1024 * 1024))
            else:
                print(f"数据为空 (消耗 {actual_used:.2f} MB)")
                mark_done(key, rows=0, bytes_est=int(actual_used * 1024 * 1024))

        except Exception as e:
            err_msg = str(e)
            if "Quota exceeded" in err_msg:
                print(f"流量超限")
                mark_failed(key, "Quota exceeded")
                return
            print(f"失败: {e}")
            mark_failed(key, err_msg)


# ── 任务2: ETF日线行情 ─────────────────────────────────────────────────────
def download_etf():
    """下载 ETF 日线行情"""
    print("\n=== Task 2: ETF 日线行情 ===")

    # 获取 ETF 列表
    etf_list = rqdatac.all_instruments(type="ETF")
    etf_ids = etf_list["order_book_id"].tolist()
    print(f"  ETF 总数: {len(etf_ids)}")

    # 下载 2010-01-01 ~ 2014-12-31 的数据（首批 ETF 约在 2010-2014 上市）
    date_ranges = [
        ("2010-01-01", "2012-12-31"),
        ("2013-01-01", "2014-12-31"),
    ]

    all_frames = []
    for start, end in date_ranges:
        key = f"etf/price_1d_{start}_{end}"
        if is_done(key):
            print(f"  [跳过] {key} 已下载")
            continue

        if not check_quota(50):
            break

        try:
            info_before = get_quota_info()
            before_mb = info_before["used_mb"]

            print(f"  [下载] {key} ...", end=" ", flush=True)
            df = rqdatac.get_price(
                etf_ids, start_date=start, end_date=end,
                frequency="1d",
                fields=["open", "close", "high", "low", "total_turnover", "volume"],
                adjust_type="none", expect_df=True
            )

            actual_used = track_usage(before_mb)

            if df is not None and not df.empty:
                all_frames.append(df)
                print(f"完成 ({len(df)} 行, 消耗 {actual_used:.2f} MB)")
                mark_done(key, rows=len(df), bytes_est=int(actual_used * 1024 * 1024))
            else:
                print(f"数据为空 (消耗 {actual_used:.2f} MB)")
                mark_done(key, rows=0, bytes_est=int(actual_used * 1024 * 1024))

        except Exception as e:
            err_msg = str(e)
            if "Quota exceeded" in err_msg:
                print(f"流量超限")
                mark_failed(key, "Quota exceeded")
                return
            print(f"失败: {e}")
            mark_failed(key, err_msg)

    # 合并保存
    if all_frames:
        merged = pd.concat(all_frames)
        out_path = DATA_ROOT / "etf/price_1d.parquet"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
        print(f"  [合并] ETF日线行情 -> {out_path} ({len(merged)} 行)")


# ── 任务3: LOF日线行情 ─────────────────────────────────────────────────────
def download_lof():
    """下载 LOF 日线行情"""
    print("\n=== Task 3: LOF 日线行情 ===")

    # 获取 LOF 列表
    lof_list = rqdatac.all_instruments(type="LOF")
    lof_ids = lof_list["order_book_id"].tolist()
    print(f"  LOF 总数: {len(lof_ids)}")

    # 下载 2010-01-01 ~ 2013-12-31 的数据
    date_ranges = [
        ("2010-01-01", "2012-12-31"),
        ("2013-01-01", "2013-12-31"),
    ]

    all_frames = []
    for start, end in date_ranges:
        key = f"lof/price_1d_{start}_{end}"
        if is_done(key):
            print(f"  [跳过] {key} 已下载")
            continue

        if not check_quota(30):
            break

        try:
            info_before = get_quota_info()
            before_mb = info_before["used_mb"]

            print(f"  [下载] {key} ...", end=" ", flush=True)
            df = rqdatac.get_price(
                lof_ids, start_date=start, end_date=end,
                frequency="1d",
                fields=["open", "close", "high", "low", "total_turnover", "volume"],
                adjust_type="none", expect_df=True
            )

            actual_used = track_usage(before_mb)

            if df is not None and not df.empty:
                all_frames.append(df)
                print(f"完成 ({len(df)} 行, 消耗 {actual_used:.2f} MB)")
                mark_done(key, rows=len(df), bytes_est=int(actual_used * 1024 * 1024))
            else:
                print(f"数据为空 (消耗 {actual_used:.2f} MB)")
                mark_done(key, rows=0, bytes_est=int(actual_used * 1024 * 1024))

        except Exception as e:
            err_msg = str(e)
            if "Quota exceeded" in err_msg:
                print(f"流量超限")
                mark_failed(key, "Quota exceeded")
                return
            print(f"失败: {e}")
            mark_failed(key, err_msg)

    # 合并保存
    if all_frames:
        merged = pd.concat(all_frames)
        out_path = DATA_ROOT / "lof/price_1d.parquet"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
        print(f"  [合并] LOF日线行情 -> {out_path} ({len(merged)} 行)")


# ── 主入口 ────────────────────────────────────────────────────────────────
TASKS = {
    "margin": download_margin,
    "etf": download_etf,
    "lof": download_lof,
}

TASK_ORDER = ["margin", "etf", "lof"]


def main():
    task = sys.argv[1] if len(sys.argv) > 1 else "all"

    info = get_quota_info()
    print(f"数据补充脚本 | 剩余流量: {info['remaining_mb']:.1f} MB")
    print(f"数据目录: {DATA_ROOT}")

    if task == "all":
        for t in TASK_ORDER:
            if not check_quota(QUOTA_MARGIN_MB + 30):
                print(f"\n[停止] 流量不足，请稍后继续")
                break
            TASKS[t]()
    elif task in TASKS:
        TASKS[task]()
    else:
        print(f"未知任务: {task}")
        print(f"可用任务: {', '.join(TASK_ORDER)} | all")
        sys.exit(1)

    session_summary()


if __name__ == "__main__":
    main()
