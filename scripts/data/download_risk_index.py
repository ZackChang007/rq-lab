"""补充缺失的风险因子和指数历史数据

任务 6: 风险因子暴露历史 (2010-2019)
任务 7: 风险因子收益历史 (2010-2019)
任务 8: 描述因子暴露 (2020-2026)
任务 9: 一致预期历史 (2010-2019)
任务 10: 指数日线行情 (2010-2026)
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.common import setup_license
import rqdatac

# 初始化
setup_license()
rqdatac.init()

DATA_DIR = Path("data")


def check_quota():
    """检查剩余流量配额"""
    quota = rqdatac.user.get_quota()
    remaining = (quota['bytes_limit'] - quota['bytes_used']) / 1024 / 1024
    print(f"剩余流量: {remaining:.1f} MB")
    return remaining


def download_factor_exposure_early():
    """任务 6: 风险因子暴露历史 (2010-2019)"""
    print("\n" + "=" * 60)
    print("任务 6: 风险因子暴露历史 (get_factor_exposure, 2010-2019)")
    print("=" * 60)

    # 获取股票列表
    stock_list = rqdatac.all_instruments(type='CS')['order_book_id'].tolist()
    print(f"  股票数量: {len(stock_list)}")

    # v1 和 v2 模型
    models = ['v1', 'v2']

    for model in models:
        print(f"\n  模型: {model}")
        output_path = DATA_DIR / "risk" / f"factor_exposure_{model}_2010_2019.parquet"

        if output_path.exists():
            print(f"    已存在，跳过")
            continue

        try:
            df = rqdatac.get_factor_exposure(
                order_book_ids=stock_list,
                start_date='2010-01-01',
                end_date='2019-12-31',
                model=model
            )

            if df is not None and len(df) > 0:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(output_path, engine='pyarrow', compression='snappy')
                print(f"    成功: {len(df)} 行, 保存到 {output_path}")
            else:
                print(f"    返回空数据")

        except Exception as e:
            print(f"    错误: {str(e)[:100]}")

        remaining = check_quota()
        if remaining < 50:
            print("  流量不足，停止下载")
            return False

    return True


def download_factor_return_early():
    """任务 7: 风险因子收益历史 (2010-2019)"""
    print("\n" + "=" * 60)
    print("任务 7: 风险因子收益历史 (get_factor_return, 2010-2019)")
    print("=" * 60)

    output_path = DATA_DIR / "risk" / "factor_return_2010_2019.parquet"

    if output_path.exists():
        print("  已存在，跳过")
        return True

    try:
        df = rqdatac.get_factor_return(
            start_date='2010-01-01',
            end_date='2019-12-31'
        )

        if df is not None and len(df) > 0:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, engine='pyarrow', compression='snappy')
            print(f"  成功: {len(df)} 行, 保存到 {output_path}")
        else:
            print("  返回空数据")

    except Exception as e:
        print(f"  错误: {str(e)[:100]}")

    check_quota()
    return True


def download_descriptor_exposure():
    """任务 8: 描述因子暴露 (2020-2026)"""
    print("\n" + "=" * 60)
    print("任务 8: 描述因子暴露 (get_descriptor_exposure, 2020-2026)")
    print("=" * 60)

    # 获取股票列表
    stock_list = rqdatac.all_instruments(type='CS')['order_book_id'].tolist()
    print(f"  股票数量: {len(stock_list)}")

    output_path = DATA_DIR / "risk" / "descriptor_exposure_2020_2026.parquet"

    if output_path.exists():
        print("  已存在，跳过")
        return True

    try:
        df = rqdatac.get_descriptor_exposure(
            order_book_ids=stock_list,
            start_date='2020-01-01',
            end_date='2026-05-31'
        )

        if df is not None and len(df) > 0:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, engine='pyarrow', compression='snappy')
            print(f"  成功: {len(df)} 行, 保存到 {output_path}")
        else:
            print("  返回空数据")

    except Exception as e:
        print(f"  错误: {str(e)[:100]}")

    check_quota()
    return True


def download_consensus_early():
    """任务 9: 一致预期历史 (2010-2019)"""
    print("\n" + "=" * 60)
    print("任务 9: 一致预期历史 (consensus.get_comp_indicators, 2010-2019)")
    print("=" * 60)

    output_path = DATA_DIR / "consensus" / "comp_indicators_2010_2019.parquet"

    if output_path.exists():
        print("  已存在，跳过")
        return True

    # 获取股票列表
    stock_list = rqdatac.all_instruments(type='CS')['order_book_id'].tolist()
    print(f"  股票数量: {len(stock_list)}")

    try:
        df = rqdatac.consensus.get_comp_indicators(
            stock_list,
            start_date='2010-01-01',
            end_date='2019-12-31'
        )

        if df is not None and len(df) > 0:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, engine='pyarrow', compression='snappy')
            print(f"  成功: {len(df)} 行, 保存到 {output_path}")
        else:
            print("  返回空数据")

    except Exception as e:
        print(f"  错误: {str(e)[:100]}")

    remaining = check_quota()
    if remaining < 50:
        print("  流量不足，停止下载")
        return False

    return True


def download_index_price():
    """任务 10: 指数日线行情 (2010-2026)"""
    print("\n" + "=" * 60)
    print("任务 10: 指数日线行情 (get_price, 2010-2026)")
    print("=" * 60)

    output_path = DATA_DIR / "index" / "price_2010_2026.parquet"

    if output_path.exists():
        # 检查是否需要更新
        df = pd.read_parquet(output_path)
        if hasattr(df.index, 'levels') and len(df.index.levels) > 1:
            max_date = df.index.get_level_values('date').max()
            if max_date >= datetime.now().date():
                print("  已存在且为最新，跳过")
                return True

    # 获取指数列表
    index_list = rqdatac.all_instruments(type='Ind')['order_book_id'].tolist()
    print(f"  指数数量: {len(index_list)}")

    try:
        df = rqdatac.get_price(
            index_list,
            start_date='2010-01-01',
            end_date='2026-05-31',
            frequency='1d',
            fields=['open', 'close', 'high', 'low', 'volume', 'total_turnover']
        )

        if df is not None and len(df) > 0:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, engine='pyarrow', compression='snappy')
            print(f"  成功: {len(df)} 行, 保存到 {output_path}")
        else:
            print("  返回空数据")

    except Exception as e:
        print(f"  错误: {str(e)[:100]}")

    remaining = check_quota()
    if remaining < 50:
        print("  流量不足，停止下载")
        return False

    return True


def verify_downloads():
    """验证已下载的数据"""
    print("\n" + "=" * 60)
    print("验证下载结果")
    print("=" * 60)

    files_to_check = [
        ('risk/factor_exposure_v1_2010_2019.parquet', '风险因子暴露 v1 (2010-2019)'),
        ('risk/factor_exposure_v2_2010_2019.parquet', '风险因子暴露 v2 (2010-2019)'),
        ('risk/factor_return_2010_2019.parquet', '风险因子收益 (2010-2019)'),
        ('risk/descriptor_exposure_2020_2026.parquet', '描述因子暴露 (2020-2026)'),
        ('consensus/comp_indicators_2010_2019.parquet', '一致预期 (2010-2019)'),
        ('index/price_2010_2026.parquet', '指数日线行情 (2010-2026)'),
    ]

    for path, desc in files_to_check:
        f = DATA_DIR / path
        if f.exists():
            df = pd.read_parquet(f)
            print(f"  {desc}: {len(df):,} 行 ✅")
        else:
            print(f"  {desc}: 不存在 ⏳")


def main():
    print("=" * 60)
    print("风险因子和指数历史数据补充")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    check_quota()

    tasks = [
        ("风险因子暴露历史", download_factor_exposure_early),
        ("风险因子收益历史", download_factor_return_early),
        ("描述因子暴露", download_descriptor_exposure),
        ("一致预期历史", download_consensus_early),
        ("指数日线行情", download_index_price),
    ]

    results = {}
    for name, func in tasks:
        try:
            success = func()
            results[name] = "✅ 完成" if success else "❌ 失败"

            remaining = check_quota()
            if remaining < 50:
                print("\n流量不足，停止后续任务")
                break
        except Exception as e:
            results[name] = f"❌ 错误: {str(e)[:30]}"

    # 汇总
    print("\n" + "=" * 60)
    print("执行结果汇总")
    print("=" * 60)
    for name, status in results.items():
        print(f"  {name}: {status}")

    verify_downloads()
    check_quota()


if __name__ == "__main__":
    main()