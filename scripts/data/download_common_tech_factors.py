"""
下载常用技术因子
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
FACTOR_DIR = DATA_ROOT / "factor"

def get_quota_mb():
    quota = rqdatac.user.get_quota()
    return quota["bytes_used"] / 1024 / 1024, quota["bytes_limit"] / 1024 / 1024

def download_common_tech_factors():
    """下载常用技术因子"""
    print("=== 下载常用技术因子 ===")

    # 常用技术因子列表
    common_factors = [
        # MA 系列（移动平均线）
        "MA5", "MA10", "MA20", "MA60", "MA120", "MA250",
        # MACD 系列
        "MACD_DEA", "MACD_DIFF", "MACD_HIST",
        # RSI 系列
        "RSI6", "RSI10",
        # KDJ 系列
        "KDJ_D", "KDJ_J", "KDJ_K",
        # BOLL 系列
        "BOLL", "BOLL_DOWN", "BOLL_UP",
        # ATR, CCI
        "ATR", "CCI",
        # VOL 系列
        "VOL5", "VOL10", "VOL20", "VOL60",
    ]

    # 获取全部A股股票
    all_cs = rqdatac.all_instruments('CS')
    stocks = all_cs.order_book_id.unique().tolist()

    # 时间范围
    start_date = "2020-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    print(f"股票数: {len(stocks)}")
    print(f"时间范围: {start_date} ~ {end_date}")
    print(f"待下载因子: {common_factors}")

    success_count = 0
    fail_count = 0

    for factor_name in common_factors:
        # 检查是否已下载
        factor_path = FACTOR_DIR / f"{factor_name}.parquet"
        if factor_path.exists():
            print(f"\n{factor_name}: 已存在，跳过")
            continue

        print(f"\n--- {factor_name} ---")

        # 检查配额
        used, limit = get_quota_mb()
        remaining = limit - used
        if remaining < 30:
            print(f"配额不足 ({remaining:.1f} MB)，停止下载")
            break

        try:
            df = rqdatac.get_factor(
                stocks,
                factor_name,
                start_date,
                end_date
            )

            if df is not None and len(df) > 0:
                # 保存
                df.to_parquet(factor_path, engine='pyarrow', compression='snappy')
                print(f"下载成功: {len(df)} 行")
                success_count += 1
            else:
                print(f"无数据")
                fail_count += 1

        except Exception as e:
            err_msg = str(e)
            if "Quota exceeded" in err_msg:
                print(f"配额超限，停止下载")
                break
            elif "not found" in err_msg.lower() or "does not exist" in err_msg.lower():
                print(f"因子不存在")
                fail_count += 1
            else:
                print(f"下载失败: {e}")
                fail_count += 1

        time.sleep(0.3)

    # 最终状态
    used, limit = get_quota_mb()
    print(f"\n=== 完成 ===")
    print(f"成功: {success_count}, 失败: {fail_count}")
    print(f"配额使用: {used:.1f} MB / {limit:.1f} MB")

if __name__ == "__main__":
    download_common_tech_factors()