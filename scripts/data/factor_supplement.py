"""
因子数据补充脚本 - 补充 2010-2019 年的因子数据

用法:
    python scripts/data/factor_supplement.py [batch]

    batch: 1-10 (分批下载，每批约 50-100 MB)

策略: 按因子类型分批下载
    1. 技术因子 (2712个) - 优先下载
    2. 估值因子 - 高优先级
    3. 财务因子 (_lyr_, _mrq_, _ttm_) - 按需下载
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
QUOTA_MARGIN_MB = 50  # 保留更多余量

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


def check_quota(need_mb=20):
    info = get_quota_info()
    rem = info["remaining_mb"]
    if rem < QUOTA_MARGIN_MB:
        print(f"  [流量不足] 剩余 {rem:.1f} MB，保留余量 {QUOTA_MARGIN_MB} MB")
        return False
    if rem < need_mb + QUOTA_MARGIN_MB:
        print(f"  [流量紧张] 剩余 {rem:.1f} MB，需要 {need_mb} MB")
        return False
    return True


def track_usage(before_mb):
    global _session_used_mb
    info = get_quota_info()
    actual = info["used_mb"] - before_mb
    if actual > 0:
        _session_used_mb += actual
    return actual


def session_summary():
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


def download_factor_early(factor_name, start_date="2010-01-01", end_date="2019-12-31", need_mb=2):
    """下载单个因子的早期数据"""
    key = f"factor_early/{factor_name}_{start_date}_{end_date}"
    if is_done(key):
        return True, 0

    if not check_quota(need_mb):
        return False, 0

    try:
        info_before = get_quota_info()
        before_mb = info_before["used_mb"]

        # 获取 A 股列表
        cs = rqdatac.all_instruments(type="CS")
        stock_ids = cs["order_book_id"].tolist()

        df = rqdatac.get_factor(stock_ids, factor_name, start_date, end_date, expect_df=True)

        actual_used = track_usage(before_mb)

        if df is not None and not df.empty:
            out_path = DATA_ROOT / f"factor_early/{factor_name}.parquet"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
            mark_done(key, rows=len(df), bytes_est=int(actual_used * 1024 * 1024))
            return True, actual_used
        else:
            mark_done(key, rows=0, bytes_est=int(actual_used * 1024 * 1024))
            return True, actual_used

    except Exception as e:
        err_msg = str(e)
        if "Quota exceeded" in err_msg:
            mark_failed(key, "Quota exceeded")
            return False, 0
        if "No data" in err_msg or "factor not found" in err_msg.lower():
            mark_done(key, rows=0, bytes_est=0)
            return True, 0
        mark_failed(key, err_msg)
        return True, 0  # 继续下一个


def download_batch_technical(batch_num=1, batch_size=100):
    """下载技术因子批次"""
    print(f"\n=== 批次 {batch_num}: 技术因子 (每批 {batch_size} 个) ===")

    # 加载因子列表
    names_file = DATA_ROOT / "stock/factor_names.json"
    if not names_file.exists():
        print("  因子列表文件不存在，跳过")
        return

    all_factors = json.loads(names_file.read_text())
    tech_factors = [f for f in all_factors if not any(x in f for x in ['_lyr_', '_mrq_', '_ttm_'])]
    tech_factors = sorted(tech_factors)

    # 分批
    start_idx = (batch_num - 1) * batch_size
    end_idx = start_idx + batch_size
    batch_factors = tech_factors[start_idx:end_idx]

    if not batch_factors:
        print(f"  批次 {batch_num} 无因子")
        return

    print(f"  本批次因子数: {len(batch_factors)} (索引 {start_idx}-{end_idx-1})")
    print(f"  总技术因子数: {len(tech_factors)}")

    downloaded = 0
    total_used = 0
    for i, factor_name in enumerate(batch_factors):
        ok, used = download_factor_early(factor_name)
        if ok:
            downloaded += 1
            total_used += used
            if i % 10 == 9:
                print(f"  进度: {i+1}/{len(batch_factors)}, 本次消耗: {total_used:.1f} MB")
        else:
            print(f"\n  [停止] 流量不足，已下载 {downloaded} 个")
            break

    print(f"  [完成] 批次 {batch_num}: 下载 {downloaded} 个，消耗 {total_used:.1f} MB")


def download_valuation_factors():
    """下载估值因子（高优先级）"""
    print("\n=== 估值因子早期数据 ===")

    valuation_factors = [
        "pe_ratio", "pe_ratio_ttm", "pe_ratio_lyr",
        "pb_ratio", "pb_ratio_ttm", "pb_ratio_lyr",
        "ps_ratio", "ps_ratio_ttm", "ps_ratio_lyr",
        "pcf_ratio", "pcf_ratio_ttm", "pcf_ratio_lyr",
        "ev", "market_cap",
    ]

    downloaded = 0
    total_used = 0
    for factor_name in valuation_factors:
        ok, used = download_factor_early(factor_name)
        if ok:
            downloaded += 1
            total_used += used
            print(f"  {factor_name}: 完成")
        else:
            print(f"\n  [停止] 流量不足")
            break

    print(f"  [完成] 估值因子: 下载 {downloaded} 个，消耗 {total_used:.1f} MB")


def main():
    batch = sys.argv[1] if len(sys.argv) > 1 else "valuation"

    info = get_quota_info()
    print(f"因子数据补充 | 剩余流量: {info['remaining_mb']:.1f} MB")
    print(f"补充范围: 2010-01-01 ~ 2019-12-31")

    if batch == "valuation":
        download_valuation_factors()
    elif batch.startswith("tech"):
        # tech1, tech2, ... tech27 (2712个因子 / 100 = 27批)
        batch_num = int(batch.replace("tech", ""))
        download_batch_technical(batch_num)
    elif batch == "auto":
        # 自动下载，直到流量不足
        download_valuation_factors()
        for batch_num in range(1, 28):
            if not check_quota(100):
                break
            download_batch_technical(batch_num)
    else:
        print(f"用法: python scripts/data/factor_supplement.py valuation | tech1-27 | auto")
        sys.exit(1)

    session_summary()


if __name__ == "__main__":
    main()