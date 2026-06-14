"""
更新因子数据 - 补充2026年5月7日至6月12日的数据

用法:
    python scripts/data/update_factors.py

说明:
    - 时间范围: 2026-05-07 ~ 2026-06-12
    - 预估流量: ~30 MB
    - 数据格式: 按因子名存储为Parquet
"""
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import rqdatac
from utils.common import setup_license

setup_license()
rqdatac.init()

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"
LOG_FILE = DATA_ROOT / "update_factors.log"


def log(message: str):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


def update_factor(factor_name: str, stock_ids: list, start_date: str, end_date: str):
    """更新单个因子数据"""
    try:
        log(f"  下载因子: {factor_name}")

        df = rqdatac.get_factor(
            stock_ids,
            factor_name,
            start_date=start_date,
            end_date=end_date,
            expect_df=True
        )

        if df is None or df.empty:
            log(f"    ⚠️  {factor_name}: 无数据")
            return False

        # 保存为增量文件
        output_file = DATA_ROOT / "factor" / f"{factor_name}_update.parquet"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(str(output_file), engine="pyarrow", compression="snappy")

        rows = len(df)
        file_size_mb = output_file.stat().st_size / 1024 / 1024
        log(f"    ✅ {factor_name}: {rows:,} 行, {file_size_mb:.2f} MB")

        return True

    except Exception as e:
        log(f"    ❌ {factor_name}: {e}")
        return False


def main():
    log("=" * 80)
    log("开始更新因子数据")
    log("=" * 80)

    start_date = "2026-05-07"
    end_date = "2026-06-12"

    log(f"更新时间范围: {start_date} ~ {end_date}")

    # 获取股票列表
    log("获取A股股票列表...")
    stocks_df = rqdatac.all_instruments(type="CS", date=end_date)
    stock_ids = stocks_df["order_book_id"].tolist()
    log(f"共 {len(stock_ids)} 只股票")

    # 选择重要因子进行更新（优先级高的核心因子）
    priority_factors = [
        "market_cap",
        "circulating_market_cap",
        "pe_ratio",
        "pb_ratio",
        "turnover_ratio",
        "ev",
        "ev_to_ebit",
        "roe",
        "roa",
        "net_profit_margin",
        "gross_profit_margin",
    ]

    log(f"\n计划更新 {len(priority_factors)} 个核心因子:")
    for f in priority_factors:
        log(f"  - {f}")

    log("\n开始下载...")
    success_count = 0
    failed_count = 0

    for i, factor_name in enumerate(priority_factors, 1):
        log(f"\n[{i}/{len(priority_factors)}] {factor_name}")
        success = update_factor(factor_name, stock_ids, start_date, end_date)

        if success:
            success_count += 1
        else:
            failed_count += 1

        # 避免并发连接限制
        if i < len(priority_factors):
            time.sleep(3)

    # 汇总结果
    log("\n" + "=" * 80)
    log("更新完成汇总")
    log("=" * 80)
    log(f"成功: {success_count}/{len(priority_factors)}")
    log(f"失败: {failed_count}/{len(priority_factors)}")

    # 检查配额
    try:
        quota = rqdatac.user.get_quota()
        remaining_mb = (quota["bytes_limit"] - quota["bytes_used"]) / 1024 / 1024
        log(f"\n剩余配额: {remaining_mb:.1f} MB")
    except Exception as e:
        log(f"\n无法获取配额: {e}")

    log("\n" + "=" * 80)


if __name__ == "__main__":
    main()
