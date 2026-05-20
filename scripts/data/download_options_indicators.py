"""
批量下载历史期权指标数据

包括：
- 金融期权：50ETF、300ETF、500ETF、创业板ETF、沪深300股指
- 商品期权：CU、AU、RB、I、MA、TA、CF、SR、OI、C、M、Y、P、PP 等
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import rqdatac
from utils.common import setup_license

setup_license()
rqdatac.init()

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"
LOG_PATH = DATA_ROOT / "download_log.json"
QUOTA_MARGIN_MB = 50

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
        print(f"[警告] 获取配额失败: {e}")
        return {"limit_mb": 1024, "used_mb": 1024, "remaining_mb": 0}


def check_quota(need_mb=50):
    """检查流量是否充足"""
    info = get_quota_info()
    rem = info["remaining_mb"]
    if rem < QUOTA_MARGIN_MB:
        print(f"[流量不足] 剩余 {rem:.1f} MB，低于安全余量")
        return False
    if rem < need_mb:
        print(f"[流量紧张] 剩余 {rem:.1f} MB，需要 {need_mb} MB")
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


def main():
    info = get_quota_info()
    print(f"期权指标批量下载 | 剩余流量: {info['remaining_mb']:.1f} MB")

    # 金融期权标的
    financial_symbols = [
        "510050.XSHG",  # 50ETF
        "510300.XSHG",  # 300ETF
        "510500.XSHG",  # 500ETF
        "159915.XSHE",  # 创业板ETF
        "159919.XSHE",  # 300ETF深
        "000300.XSHG",  # 沪深300股指
    ]

    # 商品期权品种
    commodity_symbols = [
        "CU", "AU", "RB", "I", "MA", "TA", "CF", "SR", "OI",
        "C", "M", "Y", "P", "PP", "L", "V", "EG", "ZC", "FG",
        "AP", "CJ", "PK", "SP", "SS", "SA", "PF", "UR", "TA"
    ]

    all_symbols = financial_symbols + commodity_symbols

    # 下载参数
    start_year = 2020
    end_year = datetime.now().year

    all_data = []
    total_requests = 0
    skipped = 0

    print(f"\n待下载标的数: {len(all_symbols)}")
    print(f"年份范围: {start_year}-{end_year}")

    for sym in all_symbols:
        if not check_quota(10):
            print(f"\n[停止] 流量不足，已处理 {total_requests} 个请求")
            break

        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                maturity = f"{year % 100}{month:02d}"
                key = f"options/indicators/{sym}/{maturity}"

                if is_done(key):
                    skipped += 1
                    continue

                if not check_quota(1):
                    print(f"\n[停止] 流量不足")
                    break

                try:
                    info_before = get_quota_info()
                    before_mb = info_before["used_mb"]

                    df = rqdatac.options.get_indicators(
                        sym,
                        maturity=maturity,
                        start_date=f"{year}-01-01",
                        end_date=f"{year}-12-31"
                    )

                    actual_used = track_usage(before_mb)

                    if df is not None and not df.empty:
                        all_data.append(df)
                        total_requests += 1
                        # 每个成功请求都打印进度
                        print(f"  [{total_requests}] {sym}/{maturity}: {len(df)} 行, 消耗 {actual_used:.2f} MB", flush=True)
                        mark_done(key, rows=len(df), bytes_est=int(actual_used * 1024 * 1024))
                    else:
                        mark_done(key, rows=0, bytes_est=0)

                except Exception as e:
                    # 静默跳过错误（合约不存在等）
                    pass

    print(f"\n[统计] 总请求: {total_requests}，跳过: {skipped}")

    # 合并保存
    if all_data:
        merged = pd.concat(all_data)
        out_path = DATA_ROOT / "options/indicators_all.parquet"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
        print(f"[保存] 期权指标 -> {out_path} ({len(merged)} 行)")

    # 打印摘要
    info = get_quota_info()
    print(f"\n=== 流量使用摘要 ===")
    print(f"本次会话消耗: {_session_used_mb:.1f} MB")
    print(f"当前剩余: {info['remaining_mb']:.1f} MB")


if __name__ == "__main__":
    main()
