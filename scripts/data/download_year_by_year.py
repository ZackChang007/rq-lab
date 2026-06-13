"""按年份下载大数据量的历史数据

由于风险因子暴露、描述因子暴露、一致预期等 API 一次性调用会消耗全部配额，
需要按年份拆分下载。

用法:
    python scripts/data/download_year_by_year.py --task factor_exposure --year 2010
    python scripts/data/download_year_by_year.py --task descriptor_exposure --year 2020
    python scripts/data/download_year_by_year.py --task consensus --year 2010
    python scripts/data/download_year_by_year.py --task factor_exposure --all
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.common import setup_license
import rqdatac

# 初始化
setup_license()
rqdatac.init()

DATA_DIR = Path("data")
QUOTA_MARGIN = 50  # 保留配额余量 (MB)


def get_quota_info():
    """获取配额信息"""
    quota = rqdatac.user.get_quota()
    return {
        "limit_mb": quota["bytes_limit"] / 1024 / 1024,
        "used_mb": quota["bytes_used"] / 1024 / 1024,
        "remaining_mb": (quota["bytes_limit"] - quota["bytes_used"]) / 1024 / 1024,
    }


def check_quota(need_mb=QUOTA_MARGIN):
    """检查配额是否足够"""
    info = get_quota_info()
    if info["remaining_mb"] < need_mb:
        print(f"⚠️ 配额不足: 剩余 {info['remaining_mb']:.1f} MB, 需要 {need_mb} MB")
        return False
    return True


def download_factor_exposure(year: int, model: str = "v1") -> tuple[bool, float]:
    """下载指定年份的风险因子暴露数据

    Args:
        year: 年份
        model: 模型版本 ('v1' 或 'v2')

    Returns:
        (成功标志, 消耗流量MB)
    """
    print(f"\n[_factor_exposure_{model}_{year}] 开始下载...")

    output_path = DATA_DIR / "risk" / f"factor_exposure_{model}_{year}.parquet"

    if output_path.exists():
        print(f"  已存在，跳过")
        return True, 0.0

    # 获取股票列表
    stock_list = rqdatac.all_instruments(type='CS')['order_book_id'].tolist()
    print(f"  股票数量: {len(stock_list)}")

    info_before = get_quota_info()

    try:
        df = rqdatac.get_factor_exposure(
            order_book_ids=stock_list,
            start_date=f'{year}-01-01',
            end_date=f'{year}-12-31',
            model=model
        )

        if df is not None and len(df) > 0:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, engine='pyarrow', compression='snappy')
            print(f"  成功: {len(df):,} 行 -> {output_path}")
        else:
            print(f"  返回空数据")
            return True, 0.0

    except Exception as e:
        print(f"  错误: {str(e)[:100]}")
        return False, 0.0

    info_after = get_quota_info()
    cost_mb = info_before["remaining_mb"] - info_after["remaining_mb"]
    print(f"  消耗: {cost_mb:.1f} MB, 剩余: {info_after['remaining_mb']:.1f} MB")

    return True, cost_mb


def download_descriptor_exposure(year: int) -> tuple[bool, float]:
    """下载指定年份的描述因子暴露数据

    Args:
        year: 年份

    Returns:
        (成功标志, 消耗流量MB)
    """
    print(f"\n[_descriptor_exposure_{year}] 开始下载...")

    output_path = DATA_DIR / "risk" / f"descriptor_exposure_{year}.parquet"

    if output_path.exists():
        print(f"  已存在，跳过")
        return True, 0.0

    # 获取股票列表
    stock_list = rqdatac.all_instruments(type='CS')['order_book_id'].tolist()
    print(f"  股票数量: {len(stock_list)}")

    info_before = get_quota_info()

    try:
        df = rqdatac.get_descriptor_exposure(
            order_book_ids=stock_list,
            start_date=f'{year}-01-01',
            end_date=f'{year}-12-31'
        )

        if df is not None and len(df) > 0:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, engine='pyarrow', compression='snappy')
            print(f"  成功: {len(df):,} 行 -> {output_path}")
        else:
            print(f"  返回空数据")
            return True, 0.0

    except Exception as e:
        print(f"  错误: {str(e)[:100]}")
        return False, 0.0

    info_after = get_quota_info()
    cost_mb = info_before["remaining_mb"] - info_after["remaining_mb"]
    print(f"  消耗: {cost_mb:.1f} MB, 剩余: {info_after['remaining_mb']:.1f} MB")

    return True, cost_mb


def download_consensus(year: int) -> tuple[bool, float]:
    """下载指定年份的一致预期数据

    Args:
        year: 年份

    Returns:
        (成功标志, 消耗流量MB)
    """
    print(f"\n[_consensus_{year}] 开始下载...")

    output_path = DATA_DIR / "consensus" / f"comp_indicators_{year}.parquet"

    if output_path.exists():
        print(f"  已存在，跳过")
        return True, 0.0

    # 获取股票列表
    stock_list = rqdatac.all_instruments(type='CS')['order_book_id'].tolist()
    print(f"  股票数量: {len(stock_list)}")

    info_before = get_quota_info()

    try:
        df = rqdatac.consensus.get_comp_indicators(
            stock_list,
            start_date=f'{year}-01-01',
            end_date=f'{year}-12-31'
        )

        if df is not None and len(df) > 0:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, engine='pyarrow', compression='snappy')
            print(f"  成功: {len(df):,} 行 -> {output_path}")
        else:
            print(f"  返回空数据")
            return True, 0.0

    except Exception as e:
        print(f"  错误: {str(e)[:100]}")
        return False, 0.0

    info_after = get_quota_info()
    cost_mb = info_before["remaining_mb"] - info_after["remaining_mb"]
    print(f"  消耗: {cost_mb:.1f} MB, 剩余: {info_after['remaining_mb']:.1f} MB")

    return True, cost_mb


def main():
    parser = argparse.ArgumentParser(description="按年份下载历史数据")
    parser.add_argument("--task", required=True,
                        choices=["factor_exposure", "descriptor_exposure", "consensus"],
                        help="任务类型")
    parser.add_argument("--year", type=int, help="下载年份")
    parser.add_argument("--model", default="v1", choices=["v1", "v2"],
                        help="因子模型版本 (仅用于 factor_exposure)")
    parser.add_argument("--all", action="store_true", help="下载所有年份")

    args = parser.parse_args()

    print("=" * 60)
    print(f"按年份下载历史数据 - {args.task}")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    info = get_quota_info()
    print(f"初始配额: {info['remaining_mb']:.1f} MB")

    # 确定年份范围
    if args.all:
        if args.task == "factor_exposure":
            years = range(2010, 2020)  # 2010-2019
        elif args.task == "descriptor_exposure":
            years = range(2020, 2027)  # 2020-2026
        elif args.task == "consensus":
            years = range(2010, 2020)  # 2010-2019
    elif args.year:
        years = [args.year]
    else:
        print("请指定 --year 或 --all")
        return

    total_cost = 0.0
    success_count = 0

    for year in years:
        if not check_quota(QUOTA_MARGIN):
            print(f"\n配额不足，停止下载")
            break

        if args.task == "factor_exposure":
            # 下载 v1 和 v2 两个模型
            for model in ["v1", "v2"]:
                if not check_quota(QUOTA_MARGIN):
                    break
                success, cost = download_factor_exposure(year, model)
                total_cost += cost
                if success:
                    success_count += 1

        elif args.task == "descriptor_exposure":
            success, cost = download_descriptor_exposure(year)
            total_cost += cost
            if success:
                success_count += 1

        elif args.task == "consensus":
            success, cost = download_consensus(year)
            total_cost += cost
            if success:
                success_count += 1

    # 汇总
    info = get_quota_info()
    print("\n" + "=" * 60)
    print("下载汇总")
    print("=" * 60)
    print(f"成功: {success_count}/{len(list(years))}")
    print(f"消耗: {total_cost:.1f} MB")
    print(f"剩余: {info['remaining_mb']:.1f} MB")


if __name__ == "__main__":
    main()
