"""
串行下载剩余的5个因子数据

用法:
    python scripts/data/download_remaining_factors.py

执行方式: 串行逐个下载，避免并发连接数超限
"""
import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import rqdatac
from utils.common import setup_license

setup_license()

# 初始化 RQData 连接（使用环境变量中的配置）
rqdatac.init()

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"
LOG_FILE = DATA_ROOT / "download_remaining_factors.log"

# 剩余需要下载的因子列表
REMAINING_FACTORS = [
    "deferred_income",
    "disposal_loss_on_asset_ttm1_4",
    "financial_asset_hold_to_maturity_change_ttm1_0",
    "other_effecting_cash_equivalent_items_ttm1_1",
    "seat_costs",
]


def log(message: str):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


def download_factor(factor_name: str, stock_ids: list) -> dict:
    """下载单个因子数据"""
    result = {
        "factor_name": factor_name,
        "success": False,
        "rows": 0,
        "file_size_mb": 0,
        "error": None,
        "start_time": datetime.now().isoformat(),
        "end_time": None,
    }

    try:
        log(f"开始下载因子: {factor_name}")

        # 下载因子数据
        df = rqdatac.get_factor(
            stock_ids,
            factor_name,
            start_date="2010-01-01",
            end_date="2026-06-13",
            expect_df=True
        )

        if df is None or df.empty:
            log(f"  因子 {factor_name} 数据为空")
            result["error"] = "数据为空"
        else:
            # 保存文件
            file_path = DATA_ROOT / "factor" / f"{factor_name}.parquet"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(str(file_path), engine="pyarrow", compression="snappy")

            result["success"] = True
            result["rows"] = len(df)
            result["file_size_mb"] = round(file_path.stat().st_size / 1024 / 1024, 2)

            log(f"  ✅ 成功: {result['rows']:,} 行, {result['file_size_mb']:.2f} MB")

    except Exception as e:
        error_msg = str(e)
        result["error"] = error_msg
        log(f"  ❌ 失败: {error_msg}")

    result["end_time"] = datetime.now().isoformat()
    return result


def main():
    log("=" * 80)
    log("开始串行下载剩余的5个因子数据")
    log(f"待下载因子: {', '.join(REMAINING_FACTORS)}")
    log("=" * 80)

    # 获取股票列表
    log("获取A股股票列表...")
    stocks_df = rqdatac.all_instruments(type="CS")
    stock_ids = stocks_df["order_book_id"].tolist()
    log(f"共 {len(stock_ids)} 只股票")

    # 逐个下载
    results = []
    for i, factor_name in enumerate(REMAINING_FACTORS, 1):
        log(f"\n[{i}/{len(REMAINING_FACTORS)}] 处理因子: {factor_name}")

        result = download_factor(factor_name, stock_ids)
        results.append(result)

        # 如果不是最后一个，等待5秒让连接释放
        if i < len(REMAINING_FACTORS):
            log(f"  等待5秒释放连接...")
            time.sleep(5)

    # 汇总结果
    log("\n" + "=" * 80)
    log("下载完成汇总")
    log("=" * 80)

    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count

    log(f"成功: {success_count}/{len(results)}")
    log(f"失败: {failed_count}/{len(results)}")

    if failed_count > 0:
        log("\n失败的因子:")
        for r in results:
            if not r["success"]:
                log(f"  - {r['factor_name']}: {r['error']}")

    # 保存结果
    result_file = DATA_ROOT / "remaining_factors_download_result.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    log(f"\n详细结果已保存: {result_file}")

    # 检查配额
    try:
        quota = rqdatac.user.get_quota()
        remaining_mb = (quota["bytes_limit"] - quota["bytes_used"]) / 1024 / 1024
        log(f"\n剩余配额: {remaining_mb:.1f} MB")
    except Exception as e:
        log(f"\n无法获取配额信息: {e}")


if __name__ == "__main__":
    main()
