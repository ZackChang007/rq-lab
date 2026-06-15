"""
更新股票价格数据 - 补充2026年4月30日至6月12日的数据

用法:
    python scripts/data/update_stock_prices.py

说明:
    - 时间范围: 2026-04-30 ~ 2026-06-12
    - 预估流量: ~50 MB
    - 数据格式: 按股票分批存储为Parquet
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
LOG_FILE = DATA_ROOT / "update_stock_prices.log"


def log(message: str):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


def download_batch(stock_ids: list, start_date: str, end_date: str, batch_num: int):
    """下载一批股票的价格数据"""
    try:
        log(f"  下载批次 {batch_num} ({len(stock_ids)} 只股票)...")

        df = rqdatac.get_price(
            stock_ids,
            start_date=start_date,
            end_date=end_date,
            frequency="1d",
            fields=["open", "close", "high", "low", "volume", "total_turnover"],
            expect_df=True
        )

        if df is None or df.empty:
            log(f"  ⚠️  批次 {batch_num}: 无数据")
            return None

        # 重命名列以匹配现有格式
        df = df.reset_index()
        df = df.rename(columns={
            "total_turnover": "total_turnover"
        })

        log(f"  ✅ 批次 {batch_num}: {len(df):,} 行")
        return df

    except Exception as e:
        log(f"  ❌ 批次 {batch_num}: {e}")
        return None


def main():
    log("=" * 80)
    log("开始更新股票价格数据")
    log("=" * 80)

    start_date = "2026-04-30"
    # 自动获取最新交易日
    latest_trading_date = rqdatac.get_trading_dates('2026-06-01', '2026-06-20')[-1]
    end_date = str(latest_trading_date)

    log(f"更新时间范围: {start_date} ~ {end_date}")

    # 获取股票列表
    log("获取A股股票列表...")
    stocks_df = rqdatac.all_instruments(type="CS", date=end_date)
    stock_ids = stocks_df["order_book_id"].tolist()
    log(f"共 {len(stock_ids)} 只股票")

    # 分批下载（每批500只）
    batch_size = 500
    total_batches = (len(stock_ids) + batch_size - 1) // batch_size
    log(f"分 {total_batches} 批下载（每批 {batch_size} 只）")

    all_data = []
    for i in range(total_batches):
        start_idx = i * batch_size
        end_idx = min(start_idx + batch_size, len(stock_ids))
        batch_stocks = stock_ids[start_idx:end_idx]

        df = download_batch(batch_stocks, start_date, end_date, i + 1)
        if df is not None:
            all_data.append(df)

        # 避免并发连接限制
        if i < total_batches - 1:
            time.sleep(2)

    # 合并所有数据
    if all_data:
        log("\n合并数据...")
        combined_df = pd.concat(all_data, ignore_index=True)
        log(f"总数据量: {len(combined_df):,} 行")

        # 保存为新的批次文件
        output_file = DATA_ROOT / "stock" / f"price_1d_2026_update.parquet"
        combined_df.to_parquet(str(output_file), engine="pyarrow", compression="snappy")

        file_size_mb = output_file.stat().st_size / 1024 / 1024
        log(f"✅ 数据已保存: {output_file.name} ({file_size_mb:.2f} MB)")

        # 显示数据统计
        log("\n数据统计:")
        log(f"  时间范围: {combined_df['date'].min()} ~ {combined_df['date'].max()}")
        log(f"  股票数量: {combined_df['order_book_id'].nunique()}")
        log(f"  数据行数: {len(combined_df):,}")
    else:
        log("❌ 无数据下载成功")

    # 检查配额
    try:
        quota = rqdatac.user.get_quota()
        remaining_mb = (quota["bytes_limit"] - quota["bytes_used"]) / 1024 / 1024
        log(f"\n剩余配额: {remaining_mb:.1f} MB")
    except Exception as e:
        log(f"\n无法获取配额: {e}")

    log("\n" + "=" * 80)
    log("更新完成")
    log("=" * 80)


if __name__ == "__main__":
    main()
