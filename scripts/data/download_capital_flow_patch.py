"""
补全资金流向数据 - 下载缺失股票的数据
"""
import pandas as pd
import rqdatac
import time
from datetime import datetime
from pathlib import Path
from utils.common import setup_license

setup_license()
rqdatac.init()

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"

def get_quota_mb():
    quota = rqdatac.user.get_quota()
    return quota["bytes_used"] / 1024 / 1024, quota["bytes_limit"] / 1024 / 1024

def download_missing_capital_flow():
    """补全缺失股票的资金流向数据"""
    print("=== 补全资金流向数据 ===")

    # 读取已有数据
    existing_path = DATA_ROOT / "stock" / "capital_flow.parquet"
    existing = pd.read_parquet(existing_path)
    existing_stocks = set(existing.index.get_level_values('order_book_id').unique())

    # 获取全部A股
    all_cs = rqdatac.all_instruments('CS')
    all_stocks = set(all_cs.order_book_id.unique())

    # 计算缺失股票
    missing = sorted(all_stocks - existing_stocks)
    print(f"已有股票: {len(existing_stocks)}")
    print(f"缺失股票: {len(missing)}")

    if not missing:
        print("无需补全，数据已完整")
        return

    # 时间范围
    start_date = "2020-01-02"
    end_date = datetime.now().strftime("%Y-%m-%d")

    # 分批下载（每批 50 只股票）
    batch_size = 50
    batches = [missing[i:i+batch_size] for i in range(0, len(missing), batch_size)]

    new_data_list = []
    total_batches = len(batches)

    for batch_idx, batch in enumerate(batches):
        print(f"\n--- Batch {batch_idx+1}/{total_batches} ({len(batch)} stocks) ---")

        # 检查配额
        used, limit = get_quota_mb()
        remaining = limit - used
        print(f"配额: 已用 {used:.1f} MB / {limit:.1f} MB, 剩余 {remaining:.1f} MB")

        if remaining < 50:  # 预留 50MB
            print(f"配额不足 ({remaining:.1f} MB)，停止下载")
            break

        try:
            # 下载资金流向数据
            df = rqdatac.get_capital_flow(
                batch,
                start_date,
                end_date
            )

            if df is not None and len(df) > 0:
                print(f"获取 {len(df)} 行数据")
                new_data_list.append(df)
            else:
                print(f"无数据返回")

        except Exception as e:
            err_msg = str(e)
            if "Quota exceeded" in err_msg:
                print(f"配额超限，停止下载")
                break
            else:
                print(f"下载失败: {e}")
                continue

        time.sleep(0.5)  # 避免请求过快

    # 合并新数据
    if new_data_list:
        print(f"\n=== 合并数据 ===")
        new_data = pd.concat(new_data_list)
        print(f"新数据: {len(new_data)} 行, {new_data.index.get_level_values('order_book_id').nunique()} 只股票")

        # 与已有数据合并
        combined = pd.concat([existing, new_data])
        combined = combined.sort_index()

        # 保存
        combined.to_parquet(existing_path, engine='pyarrow', compression='snappy')
        print(f"保存至 {existing_path}")
        print(f"总数据: {len(combined)} 行, {combined.index.get_level_values('order_book_id').nunique()} 只股票")
    else:
        print("\n无新数据需要合并")

    # 最终配额状态
    used, limit = get_quota_mb()
    print(f"\n=== 配额使用: {used:.1f} MB / {limit:.1f} MB ===")

if __name__ == "__main__":
    download_missing_capital_flow()