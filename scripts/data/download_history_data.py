"""补充缺失的历史数据（2010-2025）

数据完整性检查发现以下数据仅包含 2026 年数据，需要补充历史：
1. A股-股本结构 (get_shares)
2. A股-融资融券 (get_securities_margin)
3. A股-停牌股票 (is_suspended)
4. A股-ST股票 (is_st_stock)
5. A股-换手率 (get_turnover_rate)
6. 风险因子暴露/收益 (get_factor_exposure/return)
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.common import setup_license
import rqdatac

# 初始化
setup_license()
rqdatac.init()

DATA_DIR = Path("data/stock")
START_DATE = "2010-01-01"
END_DATE = "2025-12-31"


def check_quota():
    """检查剩余流量配额"""
    quota = rqdatac.user.get_quota()
    remaining = (quota['bytes_limit'] - quota['bytes_used']) / 1024 / 1024
    print(f"剩余流量: {remaining:.1f} MB")
    return remaining


def download_shares():
    """下载 A股-股本结构历史数据"""
    print("\n" + "=" * 60)
    print("任务 1: A股-股本结构历史数据 (get_shares)")
    print("=" * 60)

    # 获取所有股票列表
    all_stocks = rqdatac.all_instruments(type='CS')
    stock_list = all_stocks['order_book_id'].tolist()

    print(f"股票数量: {len(stock_list)}")
    print(f"时间范围: {START_DATE} ~ {END_DATE}")

    # 分批下载（每次 500 只股票）
    batch_size = 500
    total_batches = (len(stock_list) + batch_size - 1) // batch_size

    all_data = []

    for i in range(0, len(stock_list), batch_size):
        batch = stock_list[i:i + batch_size]
        batch_num = i // batch_size + 1
        print(f"  批次 {batch_num}/{total_batches}: 下载 {len(batch)} 只股票...")

        try:
            df = rqdatac.get_shares(batch, START_DATE, END_DATE)
            if df is not None and len(df) > 0:
                all_data.append(df)
                print(f"    成功: {len(df)} 行")
            else:
                print(f"    返回空数据")
        except Exception as e:
            print(f"    错误: {str(e)[:50]}")

        # 检查流量
        if i % 1000 == 0 and i > 0:
            remaining = check_quota()
            if remaining < 50:
                print("  流量不足，停止下载")
                break

    if all_data:
        result = pd.concat(all_data)
        output_path = DATA_DIR / "shares_history.parquet"
        result.to_parquet(output_path, engine='pyarrow', compression='snappy')
        print(f"\n保存到: {output_path}")
        print(f"总行数: {len(result)}")
        print(f"时间范围: {result.index.get_level_values('date').min()} ~ {result.index.get_level_values('date').max()}")
        return True
    else:
        print("无数据下载")
        return False


def download_securities_margin():
    """下载 A股-融资融券历史数据"""
    print("\n" + "=" * 60)
    print("任务 2: A股-融资融券历史数据 (get_securities_margin)")
    print("=" * 60)

    # 获取所有股票列表
    all_stocks = rqdatac.all_instruments(type='CS')
    stock_list = all_stocks['order_book_id'].tolist()

    print(f"股票数量: {len(stock_list)}")
    print(f"时间范围: {START_DATE} ~ {END_DATE}")

    # 分批下载
    batch_size = 500
    total_batches = (len(stock_list) + batch_size - 1) // batch_size

    all_data = []

    for i in range(0, len(stock_list), batch_size):
        batch = stock_list[i:i + batch_size]
        batch_num = i // batch_size + 1
        print(f"  批次 {batch_num}/{total_batches}: 下载 {len(batch)} 只股票...")

        try:
            df = rqdatac.get_securities_margin(batch, START_DATE, END_DATE)
            if df is not None and len(df) > 0:
                all_data.append(df)
                print(f"    成功: {len(df)} 行")
            else:
                print(f"    返回空数据")
        except Exception as e:
            print(f"    错误: {str(e)[:50]}")

        # 检查流量
        if i % 1000 == 0 and i > 0:
            remaining = check_quota()
            if remaining < 50:
                print("  流量不足，停止下载")
                break

    if all_data:
        result = pd.concat(all_data)
        output_path = DATA_DIR / "securities_margin_history.parquet"
        result.to_parquet(output_path, engine='pyarrow', compression='snappy')
        print(f"\n保存到: {output_path}")
        print(f"总行数: {len(result)}")
        return True
    else:
        print("无数据下载")
        return False


def download_suspended():
    """下载 A股-停牌股票历史数据"""
    print("\n" + "=" * 60)
    print("任务 3: A股-停牌股票历史数据 (is_suspended)")
    print("=" * 60)

    # 获取所有股票列表
    all_stocks = rqdatac.all_instruments(type='CS')
    stock_list = all_stocks['order_book_id'].tolist()

    print(f"股票数量: {len(stock_list)}")
    print(f"时间范围: {START_DATE} ~ {END_DATE}")

    # 获取交易日历
    trading_dates = rqdatac.get_trading_dates(START_DATE, END_DATE)
    print(f"交易日数: {len(trading_dates)}")

    # 分批下载（按日期范围）
    year_ranges = [(f"{y}-01-01", f"{y}-12-31") for y in range(2010, 2026)]

    all_data = []

    for start, end in year_ranges:
        print(f"  下载 {start[:4]} 年...")
        try:
            df = rqdatac.is_suspended(stock_list, start, end)
            if df is not None and len(df) > 0:
                all_data.append(df)
                print(f"    成功: {df.shape}")
            else:
                print(f"    返回空数据")
        except Exception as e:
            print(f"    错误: {str(e)[:50]}")

        remaining = check_quota()
        if remaining < 50:
            print("  流量不足，停止下载")
            break

    if all_data:
        result = pd.concat(all_data, axis=1)
        output_path = DATA_DIR / "suspended_history.parquet"
        result.to_parquet(output_path, engine='pyarrow', compression='snappy')
        print(f"\n保存到: {output_path}")
        print(f"总行数: {len(result)}, 列数: {len(result.columns)}")
        return True
    else:
        print("无数据下载")
        return False


def download_st_stock():
    """下载 A股-ST股票历史数据"""
    print("\n" + "=" * 60)
    print("任务 4: A股-ST股票历史数据 (is_st_stock)")
    print("=" * 60)

    # 获取所有股票列表
    all_stocks = rqdatac.all_instruments(type='CS')
    stock_list = all_stocks['order_book_id'].tolist()

    print(f"股票数量: {len(stock_list)}")
    print(f"时间范围: {START_DATE} ~ {END_DATE}")

    # 分批下载（按年份）
    year_ranges = [(f"{y}-01-01", f"{y}-12-31") for y in range(2010, 2026)]

    all_data = []

    for start, end in year_ranges:
        print(f"  下载 {start[:4]} 年...")
        try:
            df = rqdatac.is_st_stock(stock_list, start, end)
            if df is not None and len(df) > 0:
                all_data.append(df)
                print(f"    成功: {df.shape}")
            else:
                print(f"    返回空数据")
        except Exception as e:
            print(f"    错误: {str(e)[:50]}")

        remaining = check_quota()
        if remaining < 50:
            print("  流量不足，停止下载")
            break

    if all_data:
        result = pd.concat(all_data, axis=1)
        output_path = DATA_DIR / "st_stock_history.parquet"
        result.to_parquet(output_path, engine='pyarrow', compression='snappy')
        print(f"\n保存到: {output_path}")
        print(f"总行数: {len(result)}, 列数: {len(result.columns)}")
        return True
    else:
        print("无数据下载")
        return False


def download_turnover_rate():
    """下载 A股-换手率历史数据"""
    print("\n" + "=" * 60)
    print("任务 5: A股-换手率历史数据 (get_turnover_rate)")
    print("=" * 60)

    # 获取所有股票列表
    all_stocks = rqdatac.all_instruments(type='CS')
    stock_list = all_stocks['order_book_id'].tolist()

    print(f"股票数量: {len(stock_list)}")
    print(f"时间范围: {START_DATE} ~ {END_DATE}")

    # 分批下载
    batch_size = 500
    total_batches = (len(stock_list) + batch_size - 1) // batch_size

    all_data = []

    for i in range(0, len(stock_list), batch_size):
        batch = stock_list[i:i + batch_size]
        batch_num = i // batch_size + 1
        print(f"  批次 {batch_num}/{total_batches}: 下载 {len(batch)} 只股票...")

        try:
            df = rqdatac.get_turnover_rate(batch, START_DATE, END_DATE)
            if df is not None and len(df) > 0:
                all_data.append(df)
                print(f"    成功: {len(df)} 行")
            else:
                print(f"    返回空数据")
        except Exception as e:
            print(f"    错误: {str(e)[:50]}")

        # 检查流量
        if i % 1000 == 0 and i > 0:
            remaining = check_quota()
            if remaining < 50:
                print("  流量不足，停止下载")
                break

    if all_data:
        result = pd.concat(all_data)
        output_path = DATA_DIR / "turnover_rate_history.parquet"
        result.to_parquet(output_path, engine='pyarrow', compression='snappy')
        print(f"\n保存到: {output_path}")
        print(f"总行数: {len(result)}")
        return True
    else:
        print("无数据下载")
        return False


def main():
    print("=" * 60)
    print("数据历史补充下载")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 检查初始流量
    remaining = check_quota()
    if remaining < 100:
        print("流量不足 100 MB，建议等待重置后再执行")
        return

    # 执行任务
    tasks = [
        ("股本结构历史", download_shares),
        ("融资融券历史", download_securities_margin),
        ("停牌股票历史", download_suspended),
        ("ST股票历史", download_st_stock),
        ("换手率历史", download_turnover_rate),
    ]

    results = {}
    for name, func in tasks:
        try:
            success = func()
            results[name] = "✅ 完成" if success else "❌ 失败"

            # 检查剩余流量
            remaining = check_quota()
            if remaining < 50:
                print("\n流量不足，停止后续任务")
                break
        except Exception as e:
            results[name] = f"❌ 错误: {str(e)[:30]}"

    # 汇总结果
    print("\n" + "=" * 60)
    print("执行结果汇总")
    print("=" * 60)
    for name, status in results.items():
        print(f"  {name}: {status}")

    check_quota()


if __name__ == "__main__":
    main()
