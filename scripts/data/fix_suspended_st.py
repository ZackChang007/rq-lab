"""修复停牌和ST股票数据保存问题

问题：is_suspended() 和 is_st_stock() 返回的 DataFrame 列名有重复（股票代码重复）
解决：按年份分别保存为独立文件
"""

import sys
from pathlib import Path
import pandas as pd

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
    """检查剩余流量"""
    quota = rqdatac.user.get_quota()
    remaining = (quota['bytes_limit'] - quota['bytes_used']) / 1024 / 1024
    print(f"剩余流量: {remaining:.1f} MB")
    return remaining


def fix_suspended():
    """修复停牌数据 - 按年份保存"""
    print("\n" + "=" * 60)
    print("修复停牌数据 (is_suspended)")
    print("=" * 60)

    # 获取股票列表
    stock_list = rqdatac.all_instruments(type='CS')['order_book_id'].tolist()
    print(f"股票数量: {len(stock_list)}")

    # 按年份下载并保存
    year_ranges = [(f"{y}-01-01", f"{y}-12-31") for y in range(2010, 2026)]

    for start, end in year_ranges:
        year = start[:4]
        output_path = DATA_DIR / f"suspended_{year}.parquet"

        if output_path.exists():
            print(f"  {year} 年已存在，跳过")
            continue

        print(f"  下载 {year} 年...")
        try:
            df = rqdatac.is_suspended(stock_list, start, end)
            if df is not None and len(df) > 0:
                df.to_parquet(output_path, engine='pyarrow', compression='snappy')
                print(f"    保存成功: {output_path} ({df.shape})")
            else:
                print(f"    返回空数据")
        except Exception as e:
            print(f"    错误: {str(e)[:50]}")

        # 检查流量
        remaining = check_quota()
        if remaining < 50:
            print("  流量不足，停止下载")
            break

    print("\n停牌数据修复完成")
    return True


def fix_st_stock():
    """修复ST股票数据 - 按年份保存"""
    print("\n" + "=" * 60)
    print("修复ST股票数据 (is_st_stock)")
    print("=" * 60)

    # 获取股票列表
    stock_list = rqdatac.all_instruments(type='CS')['order_book_id'].tolist()
    print(f"股票数量: {len(stock_list)}")

    # 按年份下载并保存
    year_ranges = [(f"{y}-01-01", f"{y}-12-31") for y in range(2010, 2026)]

    for start, end in year_ranges:
        year = start[:4]
        output_path = DATA_DIR / f"st_stock_{year}.parquet"

        if output_path.exists():
            print(f"  {year} 年已存在，跳过")
            continue

        print(f"  下载 {year} 年...")
        try:
            df = rqdatac.is_st_stock(stock_list, start, end)
            if df is not None and len(df) > 0:
                df.to_parquet(output_path, engine='pyarrow', compression='snappy')
                print(f"    保存成功: {output_path} ({df.shape})")
            else:
                print(f"    返回空数据")
        except Exception as e:
            print(f"    错误: {str(e)[:50]}")

        # 检查流量
        remaining = check_quota()
        if remaining < 50:
            print("  流量不足，停止下载")
            break

    print("\nST股票数据修复完成")
    return True


def verify_data():
    """验证已下载的历史数据"""
    print("\n" + "=" * 60)
    print("验证历史数据")
    print("=" * 60)

    files_to_check = [
        'shares_history.parquet',
        'securities_margin_history.parquet',
        'turnover_rate_history.parquet',
    ]

    for fname in files_to_check:
        f = DATA_DIR / fname
        if f.exists():
            df = pd.read_parquet(f)
            time_range = ""
            if hasattr(df.index, 'levels') and len(df.index.levels) > 1:
                time_range = f"{df.index.levels[1].min()} ~ {df.index.levels[1].max()}"
            print(f"  {fname}: {len(df):,} 行, {time_range}")
        else:
            print(f"  {fname}: 不存在")

    # 检查按年份保存的文件
    print("\n  停牌数据 (按年份):")
    for y in range(2010, 2026):
        f = DATA_DIR / f"suspended_{y}.parquet"
        if f.exists():
            print(f"    {y}: 存在")

    print("\n  ST股票数据 (按年份):")
    for y in range(2010, 2026):
        f = DATA_DIR / f"st_stock_{y}.parquet"
        if f.exists():
            print(f"    {y}: 存在")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='修复停牌和ST股票数据')
    parser.add_argument('--task', choices=['suspended', 'st_stock', 'verify', 'all'], default='all')
    args = parser.parse_args()

    print("=" * 60)
    print("停牌/ST数据修复脚本")
    print("=" * 60)

    check_quota()

    if args.task in ['suspended', 'all']:
        fix_suspended()

    if args.task in ['st_stock', 'all']:
        fix_st_stock()

    if args.task in ['verify', 'all']:
        verify_data()


if __name__ == "__main__":
    main()
