"""
RQData 宏观因子数据下载脚本

下载所有可用的宏观因子数据（约4007个因子）
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from utils.common import setup_license
import rqdatac as rq

# 初始化
setup_license()
rq.init()

# 输出目录
OUTPUT_DIR = Path("data/macro/factors")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 因子列表文件
FACTORS_FILE = Path("data/macro/factors_list.xlsx")


def get_factor_list():
    """获取所有宏观因子名称列表"""
    df = pd.read_excel(FACTORS_FILE, skiprows=1, names=['factor_name'])
    return df['factor_name'].tolist()


def download_factors(factor_names: list, start_date: str = "20000101", end_date: str = None, batch_size: int = 100):
    """
    批量下载宏观因子数据

    Args:
        factor_names: 因子名称列表
        start_date: 起始日期
        end_date: 截止日期（默认今天）
        batch_size: 每批下载数量
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    total = len(factor_names)
    print(f"开始下载 {total} 个宏观因子...")
    print(f"时间范围: {start_date} ~ {end_date}")
    print(f"批次大小: {batch_size}")
    print("-" * 60)

    downloaded = 0
    failed = []
    total_rows = 0

    for i in range(0, total, batch_size):
        batch = factor_names[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size

        print(f"\n批次 {batch_num}/{total_batches}: 下载因子 {i+1}-{min(i+batch_size, total)}...")

        try:
            df = rq.econ.get_factors(
                factors=batch,
                start_date=start_date,
                end_date=end_date
            )

            if df is not None and len(df) > 0:
                # 重置索引，保存为parquet
                df = df.reset_index()
                output_file = OUTPUT_DIR / f"batch_{batch_num:04d}.parquet"
                df.to_parquet(output_file, index=False)

                rows = len(df)
                total_rows += rows
                downloaded += len(batch)
                print(f"  ✅ 成功: {rows} 行数据 -> {output_file.name}")
            else:
                print(f"  ⚠️ 空数据")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            failed.extend(batch)

        # 检查配额
        try:
            info = rq.user.get_quota()
            used = info.get('used', 0)
            total_quota = info.get('total', 1024)
            remaining = total_quota - used
            print(f"  📊 配额: 已用 {used:.1f}MB / {total_quota:.1f}MB, 剩余 {remaining:.1f}MB")

            # 如果剩余不足50MB，暂停
            if remaining < 50:
                print("\n⚠️ 配额即将用完，停止下载")
                break
        except:
            pass

    print("\n" + "=" * 60)
    print(f"下载完成: {downloaded}/{total} 个因子, 共 {total_rows} 行数据")
    if failed:
        print(f"失败因子数: {len(failed)}")
        # 保存失败列表
        with open("data/macro/failed_factors.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(failed))

    return downloaded, failed, total_rows


def merge_factors():
    """合并所有批次文件为一个文件"""
    import glob

    files = sorted(OUTPUT_DIR.glob("batch_*.parquet"))
    if not files:
        print("没有找到已下载的文件")
        return

    print(f"合并 {len(files)} 个批次文件...")

    dfs = []
    for f in files:
        df = pd.read_parquet(f)
        dfs.append(df)

    merged = pd.concat(dfs, ignore_index=True)
    output_file = OUTPUT_DIR / "all_factors.parquet"
    merged.to_parquet(output_file, index=False)

    print(f"✅ 合并完成: {output_file}")
    print(f"   总行数: {len(merged):,}")
    print(f"   因子数: {merged['factor'].nunique():,}")

    return merged


def main():
    # 获取因子列表
    factors = get_factor_list()
    print(f"因子总数: {len(factors)}")

    # 下载
    downloaded, failed, rows = download_factors(factors, batch_size=50)

    # 合并
    if downloaded > 0:
        merge_factors()


if __name__ == "__main__":
    main()
