"""
数据补充计划 XII 下载脚本

用法:
    python scripts/data/download_plan_xii.py --task <task_name>

    task_name: style_factor | index_factor | vwap | restricted_shares |
               main_shareholder | private_placement | buy_back | incentive_plan
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import rqdatac
from utils.common import setup_license

# 初始化许可证和 rqdatac
setup_license()
rqdatac.init()

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"
DAILY_QUOTA_MB = 1024
QUOTA_MARGIN_MB = 50  # 安全余量


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


def check_quota(required_mb):
    """检查配额是否充足"""
    info = get_quota_info()
    remaining = info["remaining_mb"]

    if remaining < required_mb + QUOTA_MARGIN_MB:
        print(f"[错误] 配额不足！剩余 {remaining:.1f} MB，需要 {required_mb + QUOTA_MARGIN_MB:.1f} MB")
        return False
    return True


def get_all_stock_codes():
    """获取所有A股股票代码"""
    all_inst = rqdatac.all_instruments(type="CS", date=datetime.now().strftime("%Y-%m-%d"))
    return all_inst["order_book_id"].tolist()


def save_parquet(df, filepath, description):
    """保存为 Parquet 文件"""
    if df is None or df.empty:
        print(f"[警告] {description} 数据为空，跳过保存")
        return

    filepath.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(filepath, compression="snappy", index=True)
    print(f"[成功] {description} -> {filepath} ({len(df)} 行)")


def download_style_factor():
    """下载风格因子暴露数据"""
    print("\n" + "=" * 60)
    print("任务 1: 风格因子暴露")
    print("=" * 60)

    info = get_quota_info()
    print(f"初始配额: {info['limit_mb']:.1f} MB")
    print(f"剩余配额: {info['remaining_mb']:.1f} MB")

    # 获取所有股票代码
    stock_codes = get_all_stock_codes()
    print(f"股票数量: {len(stock_codes)}")

    # 测试小样本：下载最近1个月数据
    print("\n[测试] 下载最近1个月数据估算流量...")
    start_date = "2026-05-01"
    end_date = "2026-05-31"

    try:
        df_sample = rqdatac.get_style_factor_exposure(
            stock_codes[:100],  # 先测试100只股票
            start_date=start_date,
            end_date=end_date,
            model='v1'
        )

        if df_sample is not None and not df_sample.empty:
            sample_size_mb = df_sample.memory_usage(deep=True).sum() / 1024 / 1024
            print(f"样本数据: {len(df_sample)} 行, {sample_size_mb:.2f} MB")

            # 估算全量数据（5500只股票 × 6年）
            # 假设数据量与股票数量和时间长度成正比
            estimated_full_mb = sample_size_mb * (len(stock_codes) / 100) * (6 * 12) / 1  # 6年
            print(f"预估全量流量: {estimated_full_mb:.1f} MB (2019-2026)")

            # 检查配额是否充足
            if not check_quota(estimated_full_mb):
                print("[策略] 采用按年份下载策略")
                return download_style_factor_by_year(stock_codes)

        # 如果配额充足，尝试一次性下载
        print("\n[下载] 尝试一次性下载 2019-2026 数据...")
        start_date = "2019-01-01"
        end_date = "2026-05-31"

        if not check_quota(estimated_full_mb):
            print("[跳过] 配额不足，转为按年份下载")
            return download_style_factor_by_year(stock_codes)

        df = rqdatac.get_style_factor_exposure(
            stock_codes,
            start_date=start_date,
            end_date=end_date,
            model='v1'
        )

        if df is not None:
            filepath = DATA_ROOT / "style_factor" / "style_factor_exposure_v1.parquet"
            save_parquet(df, filepath, "风格因子暴露 v1 (2019-2026)")

            # 检查实际流量消耗
            info_after = get_quota_info()
            used_mb = info['remaining_mb'] - info_after['remaining_mb']
            print(f"实际消耗: {used_mb:.1f} MB")
            return True

    except Exception as e:
        print(f"[错误] {e}")
        if "Quota exceeded" in str(e):
            print("[策略] 配额超限，转为按年份下载")
            return download_style_factor_by_year(stock_codes)

    return False


def download_style_factor_by_year(stock_codes):
    """按年份下载风格因子暴露"""
    print("\n[策略] 按年份下载风格因子暴露")

    years = range(2019, 2026)
    success_count = 0

    for year in years:
        info = get_quota_info()
        if info['remaining_mb'] < QUOTA_MARGIN_MB:
            print(f"[暂停] 剩余配额不足: {info['remaining_mb']:.1f} MB")
            break

        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        print(f"\n[{year}] 开始下载风格因子暴露...")

        try:
            df = rqdatac.get_style_factor_exposure(
                stock_codes,
                start_date=start_date,
                end_date=end_date,
                model='v1'
            )

            if df is not None and not df.empty:
                filepath = DATA_ROOT / "style_factor" / f"style_factor_exposure_v1_{year}.parquet"
                save_parquet(df, filepath, f"风格因子暴露 v1 ({year})")

                info_after = get_quota_info()
                used_mb = info['remaining_mb'] - info_after['remaining_mb']
                print(f"消耗: {used_mb:.1f} MB, 剩余: {info_after['remaining_mb']:.1f} MB")

                success_count += 1
            else:
                print(f"[警告] {year} 年数据为空")

        except Exception as e:
            print(f"[错误] {year} 年下载失败: {e}")
            if "Quota exceeded" in str(e):
                print("[暂停] 配额超限，等待下次执行")
                break

    print(f"\n[汇总] 成功下载 {success_count}/{len(list(years))} 年")
    return success_count > 0


def download_index_factor():
    """下载指数因子暴露数据"""
    print("\n" + "=" * 60)
    print("任务 2: 指数因子暴露")
    print("=" * 60)

    info = get_quota_info()
    print(f"剩余配额: {info['remaining_mb']:.1f} MB")

    # 获取主要指数代码
    index_codes = [
        "000001.XSHG",  # 上证综指
        "000300.XSHG",  # 沪深300
        "000905.XSHG",  # 中证500
        "000852.XSHG",  # 中证1000
        "399006.XSHE",  # 创业板指
    ]

    print(f"指数数量: {len(index_codes)}")

    try:
        # 先测试1个月数据
        print("\n[测试] 下载最近1个月数据估算流量...")
        df_sample = rqdatac.get_index_factor_exposure(
            index_codes[:2],
            start_date="2026-05-01",
            end_date="2026-05-31"
        )

        if df_sample is not None:
            sample_size_mb = df_sample.memory_usage(deep=True).sum() / 1024 / 1024
            print(f"样本数据: {sample_size_mb:.2f} MB")

            # 估算全量流量较小，可以一次性下载
            estimated_full_mb = sample_size_mb * (len(index_codes) / 2) * (6 * 12) / 1
            print(f"预估全量流量: {estimated_full_mb:.1f} MB")

        # 一次性下载 2019-2026
        print("\n[下载] 下载 2019-2026 数据...")
        df = rqdatac.get_index_factor_exposure(
            index_codes,
            start_date="2019-01-01",
            end_date="2026-05-31"
        )

        if df is not None:
            filepath = DATA_ROOT / "index_factor" / "index_factor_exposure.parquet"
            save_parquet(df, filepath, "指数因子暴露 (2019-2026)")

            info_after = get_quota_info()
            used_mb = info['remaining_mb'] - info_after['remaining_mb']
            print(f"实际消耗: {used_mb:.1f} MB")
            return True

    except Exception as e:
        print(f"[错误] {e}")
        return False

    return False


def download_vwap():
    """下载 VWAP 数据"""
    print("\n" + "=" * 60)
    print("任务 3: VWAP 数据")
    print("=" * 60)

    info = get_quota_info()
    print(f"剩余配额: {info['remaining_mb']:.1f} MB")

    stock_codes = get_all_stock_codes()
    print(f"股票数量: {len(stock_codes)}")

    # VWAP 数据量可能较大，采用按年份策略
    print("\n[策略] 按年份下载 VWAP 数据")

    years = range(2019, 2026)
    success_count = 0

    for year in years:
        info = get_quota_info()
        if info['remaining_mb'] < QUOTA_MARGIN_MB:
            print(f"[暂停] 剩余配额不足: {info['remaining_mb']:.1f} MB")
            break

        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        print(f"\n[{year}] 开始下载 VWAP...")

        try:
            df = rqdatac.get_vwap(
                stock_codes,
                start_date=start_date,
                end_date=end_date
            )

            if df is not None and not df.empty:
                filepath = DATA_ROOT / "vwap" / f"vwap_{year}.parquet"
                save_parquet(df, filepath, f"VWAP ({year})")

                info_after = get_quota_info()
                used_mb = info['remaining_mb'] - info_after['remaining_mb']
                print(f"消耗: {used_mb:.1f} MB, 剩余: {info_after['remaining_mb']:.1f} MB")

                success_count += 1
            else:
                print(f"[警告] {year} 年数据为空")

        except Exception as e:
            print(f"[错误] {year} 年下载失败: {e}")
            if "Quota exceeded" in str(e):
                print("[暂停] 配额超限")
                break

    print(f"\n[汇总] 成功下载 {success_count}/{len(list(years))} 年")
    return success_count > 0


def download_restricted_shares():
    """下载限售股解禁数据"""
    print("\n" + "=" * 60)
    print("任务 4: 限售股解禁")
    print("=" * 60)

    info = get_quota_info()
    print(f"剩余配额: {info['remaining_mb']:.1f} MB")

    stock_codes = get_all_stock_codes()
    print(f"股票数量: {len(stock_codes)}")

    # 限售股数据量可能较大，采用按年份策略
    print("\n[策略] 按年份下载限售股数据")

    years = range(2010, 2026)
    success_count = 0

    for year in years:
        info = get_quota_info()
        if info['remaining_mb'] < QUOTA_MARGIN_MB:
            print(f"[暂停] 剩余配额不足: {info['remaining_mb']:.1f} MB")
            break

        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        print(f"\n[{year}] 开始下载限售股数据...")

        try:
            df = rqdatac.get_restricted_shares(
                stock_codes,
                start_date=start_date,
                end_date=end_date
            )

            if df is not None and not df.empty:
                filepath = DATA_ROOT / "stock" / f"restricted_shares_{year}.parquet"
                save_parquet(df, filepath, f"限售股解禁 ({year})")

                info_after = get_quota_info()
                used_mb = info['remaining_mb'] - info_after['remaining_mb']
                print(f"消耗: {used_mb:.1f} MB, 剩余: {info_after['remaining_mb']:.1f} MB")

                success_count += 1
            else:
                print(f"[警告] {year} 年数据为空")

        except Exception as e:
            print(f"[错误] {year} 年下载失败: {e}")
            if "Quota exceeded" in str(e):
                print("[暂停] 配额超限")
                break

    print(f"\n[汇总] 成功下载 {success_count}/{len(list(years))} 年")
    return success_count > 0


def main():
    parser = argparse.ArgumentParser(description="数据补充计划 XII 下载脚本")
    parser.add_argument("--task", required=True, help="任务名称")

    args = parser.parse_args()

    print("=" * 60)
    print(f"数据补充计划 XII")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    task_map = {
        "style_factor": download_style_factor,
        "index_factor": download_index_factor,
        "vwap": download_vwap,
        "restricted_shares": download_restricted_shares,
    }

    if args.task in task_map:
        task_map[args.task]()
    else:
        print(f"[错误] 未知任务: {args.task}")
        print(f"可用任务: {list(task_map.keys())}")
        sys.exit(1)


if __name__ == "__main__":
    main()