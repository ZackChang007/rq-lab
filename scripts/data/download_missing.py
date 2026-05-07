"""
按优先级下载缺失数据

优先级：
1. 🔴 高：补充股本/换手率/停牌/ST/融资融券历史数据
2. 🟡 中：下载缺失的风险因子和另类数据
3. 🟢 低：补充技术因子
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import rqdatac

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from utils.common import setup_license

setup_license()
rqdatac.init()

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"
LOG_PATH = DATA_ROOT / "download_log.json"
QUOTA_MARGIN_MB = 10

_session_used_mb = 0.0


def get_quota_info():
    quota = rqdatac.user.get_quota()
    return {
        "limit_mb": quota["bytes_limit"] / 1024 / 1024,
        "used_mb": quota["bytes_used"] / 1024 / 1024,
        "remaining_mb": (quota["bytes_limit"] - quota["bytes_used"]) / 1024 / 1024,
    }


def check_quota(need_mb=10):
    info = get_quota_info()
    if info["remaining_mb"] < QUOTA_MARGIN_MB:
        print(f"  [停止] 剩余 {info['remaining_mb']:.1f} MB，低于安全余量")
        return False
    if info["remaining_mb"] < need_mb:
        print(f"  [跳过] 剩余 {info['remaining_mb']:.1f} MB，需要 {need_mb} MB")
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


def download_and_save(key, func, out_path, need_mb=10):
    """下载并保存数据"""
    if is_done(key):
        print(f"  [跳过] {key} 已下载")
        return True

    if not check_quota(need_mb):
        return False

    try:
        info_before = get_quota_info()
        before_mb = info_before["used_mb"]

        print(f"  [下载] {key} ...", end=" ", flush=True)
        df = func()

        actual_used = track_usage(before_mb)

        if df is not None and not df.empty:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
            rows = len(df)
            print(f"完成 ({rows} 行, 消耗 {actual_used:.2f} MB)")
            mark_done(key, rows=rows, bytes_est=int(actual_used * 1024 * 1024))
            return True
        else:
            print(f"数据为空 (消耗 {actual_used:.2f} MB)")
            mark_done(key, rows=0, bytes_est=int(actual_used * 1024 * 1024))
            return True
    except Exception as e:
        err_msg = str(e)
        if "Quota exceeded" in err_msg:
            print(f"流量超限")
            return False
        print(f"失败: {e}")
        return True  # 继续下一个


def download_high_priority():
    """🔴 高优先级：补充历史数据"""
    print("\n=== 🔴 高优先级：补充历史数据 ===")

    # 获取股票列表
    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()
    print(f"  A股总数: {len(stock_ids)}")

    # 1. 股本数据 - 完整历史
    if not download_and_save(
        "stock/shares_full",
        lambda: rqdatac.get_shares(stock_ids, start_date="2005-01-01", end_date="2026-12-31"),
        DATA_ROOT / "stock/shares.parquet",
        need_mb=100,
    ):
        return False

    # 2. 换手率 - 完整历史
    if not download_and_save(
        "stock/turnover_rate_full",
        lambda: rqdatac.get_turnover_rate(stock_ids, start_date="2005-01-01", end_date="2026-12-31"),
        DATA_ROOT / "stock/turnover_rate.parquet",
        need_mb=100,
    ):
        return False

    # 3. 停牌数据 - 完整历史
    if not download_and_save(
        "stock/suspended_full",
        lambda: rqdatac.is_suspended(stock_ids, start_date="2005-01-01", end_date="2026-12-31"),
        DATA_ROOT / "stock/suspended.parquet",
        need_mb=50,
    ):
        return False

    # 4. ST股票 - 完整历史
    if not download_and_save(
        "stock/st_stock_full",
        lambda: rqdatac.is_st_stock(stock_ids, start_date="2005-01-01", end_date="2026-12-31"),
        DATA_ROOT / "stock/st_stock.parquet",
        need_mb=50,
    ):
        return False

    # 5. 融资融券 - 完整历史（2010-03-31起）
    if not download_and_save(
        "stock/securities_margin_full",
        lambda: rqdatac.get_securities_margin(stock_ids, start_date="2010-03-31", end_date="2026-12-31"),
        DATA_ROOT / "stock/securities_margin.parquet",
        need_mb=100,
    ):
        return False

    return True


def download_medium_priority():
    """🟡 中优先级：风险因子和另类数据"""
    print("\n=== 🟡 中优先级：风险因子和另类数据 ===")

    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()[:500]  # 限制数量

    # 风险因子
    risk_apis = [
        ("risk_factor/descriptor_exposure",
         lambda: rqdatac.get_factor_exposure(stock_ids, "2014-01-01", "2026-12-31", model="v1"),
         30),
        ("risk_factor/factor_covariance_daily",
         lambda: rqdatac.get_factor_covariance("2024-01-01"),  # 单日测试
         5),
        ("risk_factor/specific_risk_daily",
         lambda: rqdatac.get_specific_risk(stock_ids[:200], "2024-01-01", "2026-12-31"),
         30),
    ]

    for key, func, need_mb in risk_apis:
        if not download_and_save(key, func, DATA_ROOT / f"{key}.parquet", need_mb=need_mb):
            return False

    # 另类数据 - 一致预期
    alt_apis = [
        ("alternative/consensus/price",
         lambda: rqdatac.consensus.get_price(stock_ids[:200], "2020-01-01", "2026-12-31"),
         20),
        ("alternative/consensus/market_estimate",
         lambda: rqdatac.consensus.get_market_estimate(stock_ids[:200], "2020-01-01", "2026-12-31"),
         20),
        ("alternative/consensus/security_change",
         lambda: rqdatac.consensus.get_security_change(stock_ids[:200], "2020-01-01", "2026-12-31"),
         10),
        ("alternative/consensus/expect_appr_exceed",
         lambda: rqdatac.consensus.get_expect_appr_exceed(stock_ids[:200], "2020-01-01", "2026-12-31"),
         10),
        ("alternative/consensus/expect_prob",
         lambda: rqdatac.consensus.get_expect_prob(stock_ids[:200], "2020-01-01", "2026-12-31"),
         10),
        ("alternative/consensus/factor",
         lambda: rqdatac.consensus.get_factor(stock_ids[:200], "2020-01-01", "2026-12-31"),
         10),
        ("alternative/consensus/analyst_momentum",
         lambda: rqdatac.consensus.get_analyst_momentum(stock_ids[:200], "2020-01-01", "2026-12-31"),
         10),
    ]

    for key, func, need_mb in alt_apis:
        if not download_and_save(key, func, DATA_ROOT / f"{key}.parquet", need_mb=need_mb):
            return False

    return True


def download_low_priority():
    """🟢 低优先级：技术因子补充"""
    print("\n=== 🟢 低优先级：技术因子补充 ===")

    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()

    # 获取所有因子名
    try:
        all_factors = rqdatac.get_all_factor_names()
    except Exception:
        print("  无法获取因子列表")
        return True

    # 过滤出未下载的技术因子
    existing_factors = set(f.stem for f in (DATA_ROOT / "factor").glob("*.parquet"))

    tech_factors = [f for f in all_factors
                    if not any(x in f for x in ['_lyr_', '_mrq_', '_ttm_'])
                    and not f.startswith(('pe_', 'pb_', 'ps_', 'pcf_'))
                    and f not in existing_factors]

    print(f"  待下载技术因子: {len(tech_factors)} 个")

    start_date = "2020-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    downloaded = 0
    for i, factor_name in enumerate(tech_factors):
        key = f"factor/{factor_name}"
        if is_done(key):
            continue
        if not check_quota(5):
            print(f"  [停止] 流量不足，已下载 {downloaded} 个因子")
            return True

        try:
            info_before = get_quota_info()
            before_mb = info_before["used_mb"]

            print(f"  [下载] {i+1}/{len(tech_factors)} {factor_name} ...", end=" ", flush=True)
            df = rqdatac.get_factor(stock_ids, factor_name, start_date, end_date, expect_df=True)

            actual_used = track_usage(before_mb)

            if df is not None and not df.empty:
                out_path = DATA_ROOT / f"factor/{factor_name}.parquet"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
                print(f"完成 ({len(df)} 行, 消耗 {actual_used:.2f} MB)")
                mark_done(key, rows=len(df), bytes_est=int(actual_used * 1024 * 1024))
                downloaded += 1
            else:
                print(f"数据为空")
                mark_done(key, rows=0, bytes_est=0)
        except Exception as e:
            if "Quota exceeded" in str(e):
                print(f"流量超限")
                return True
            print(f"失败: {e}")

    return True


def main():
    info = get_quota_info()
    print(f"RQData 缺失数据下载 | 剩余流量: {info['remaining_mb']:.1f} MB")
    print(f"数据目录: {DATA_ROOT}")

    # 按优先级顺序执行
    priorities = [
        ("🔴 高优先级", download_high_priority),
        ("🟡 中优先级", download_medium_priority),
        ("🟢 低优先级", download_low_priority),
    ]

    for name, func in priorities:
        if not check_quota(20):
            break
        if not func():
            break

    # 打印摘要
    info = get_quota_info()
    print(f"\n=== 流量使用摘要 ===")
    print(f"  本次会话消耗: {_session_used_mb:.1f} MB")
    print(f"  当前剩余: {info['remaining_mb']:.1f} MB")


if __name__ == "__main__":
    main()
