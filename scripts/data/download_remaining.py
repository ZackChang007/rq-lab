"""
数据补充下载脚本 - 完成剩余待下载数据

待下载任务：
1. 缺失的 3 个 TTM1 因子
2. 期权主力月份
3. 新闻舆情（需先安装 rqdatac[news]）
4. 期权指标
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import rqdatac
from utils.common import setup_license

setup_license()
rqdatac.init()

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"
LOG_PATH = DATA_ROOT / "download_log.json"
DAILY_QUOTA_MB = 1024
QUOTA_MARGIN_MB = 10

_session_used_mb = 0.0


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


def check_quota(need_mb=50):
    """检查流量是否充足"""
    info = get_quota_info()
    rem = info["remaining_mb"]
    if rem < QUOTA_MARGIN_MB:
        print(f"[流量不足] 剩余 {rem:.1f} MB，低于安全余量")
        return False
    if rem < need_mb:
        print(f"[流量紧张] 剩余 {rem:.1f} MB，需要 {need_mb} MB")
        return False
    return True


def track_usage(before_mb):
    """追踪实际流量消耗"""
    global _session_used_mb
    info = get_quota_info()
    actual = info["used_mb"] - before_mb
    if actual > 0:
        _session_used_mb += actual
    return actual


def download_missing_ttm1():
    """下载缺失的 3 个 TTM1 因子"""
    print("\n=== 1. 下载缺失 TTM1 因子 ===")

    # 读取因子名称
    factor_names_path = DATA_ROOT / "stock" / "factor_names.json"
    if not factor_names_path.exists():
        print("[错误] factor_names.json 不存在")
        return

    factor_names = json.loads(factor_names_path.read_text(encoding="utf-8"))
    ttm1_factors = [f for f in factor_names if "_ttm1_0" in f]

    # 检查已下载
    factor_dir = DATA_ROOT / "factor"
    downloaded_ttm1 = {f.stem for f in factor_dir.glob("*_ttm1_0.parquet")}
    missing = [f for f in ttm1_factors if f not in downloaded_ttm1]

    if not missing:
        print("[完成] TTM1 因子已全部下载")
        return

    print(f"[待下载] 缺失 TTM1 因子: {missing}")

    # 获取股票列表
    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()

    start_date = "2010-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    for factor_name in missing:
        if not check_quota(5):
            print("[停止] 流量不足")
            return

        try:
            info_before = get_quota_info()
            before_mb = info_before["used_mb"]

            print(f"  [下载] {factor_name} ...", end=" ", flush=True)
            df = rqdatac.get_factor(stock_ids, factor_name, start_date, end_date, expect_df=True)

            actual_used = track_usage(before_mb)

            if df is not None and not df.empty:
                out_path = DATA_ROOT / f"factor/{factor_name}.parquet"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
                print(f"完成 ({len(df)} 行, 消耗 {actual_used:.2f} MB)")
            else:
                print(f"数据为空 (消耗 {actual_used:.2f} MB)")
        except Exception as e:
            print(f"失败: {e}")


def download_options_dominant_month():
    """下载商品期权主力月份（仅支持商品期权）"""
    print("\n=== 2. 下载商品期权主力月份 ===")

    if not check_quota(10):
        return

    # 商品期权品种（仅商品期权支持此 API）
    # 格式: 品种代码，如 'CU', 'AU', 'RB' 等
    commodity_options = ['CU', 'AU', 'RB', 'I', 'MA', 'TA', 'CF', 'SR', 'OI', 'C', 'M', 'Y', 'P', 'PP']

    all_data = []
    for sym in commodity_options:
        try:
            info_before = get_quota_info()
            before_mb = info_before["used_mb"]

            print(f"  [下载] 商品期权主力月份 {sym} ...", end=" ", flush=True)
            df = rqdatac.options.get_dominant_month(
                sym,
                start_date="2017-01-01",  # 商品期权上市日
                end_date=datetime.now().strftime("%Y-%m-%d")
            )

            actual_used = track_usage(before_mb)

            if df is not None and not df.empty:
                all_data.append(df)
                print(f"完成 ({len(df)} 行, 消耗 {actual_used:.2f} MB)")
            else:
                print(f"数据为空 (消耗 {actual_used:.2f} MB)")
        except Exception as e:
            print(f"失败: {e}")

    # 合并保存
    if all_data:
        # 将 Series 列表转换为 DataFrame
        merged = pd.concat(all_data) if len(all_data) > 1 else all_data[0]
        if isinstance(merged, pd.Series):
            merged = merged.to_frame(name="dominant_contract")
        out_path = DATA_ROOT / "options/commodity_dominant_month.parquet"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
        print(f"  [合并] 商品期权主力月份 -> {out_path} ({len(merged)} 行)")


def download_news():
    """下载新闻舆情"""
    print("\n=== 3. 下载新闻舆情 ===")

    # 检查 news 模块是否可用
    if not hasattr(rqdatac, 'news'):
        print("[跳过] news 模块未安装，请运行: pip install rqdatac[news]")
        return

    if not check_quota(50):
        return

    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()[:100]  # 限制数量

    try:
        info_before = get_quota_info()
        before_mb = info_before["used_mb"]

        print(f"  [下载] 新闻舆情 ...", end=" ", flush=True)
        df = rqdatac.news.get_stock_news(
            stock_ids,
            start_date="2020-01-01",
            end_date=datetime.now().strftime("%Y-%m-%d")
        )

        actual_used = track_usage(before_mb)

        if df is not None and not df.empty:
            out_path = DATA_ROOT / "alternative/news/stock_news.parquet"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
            print(f"完成 ({len(df)} 行, 消耗 {actual_used:.2f} MB)")
        else:
            print(f"数据为空 (消耗 {actual_used:.2f} MB)")
    except Exception as e:
        print(f"失败: {e}")


def download_options_indicators():
    """下载期权衍生指标 - PCR、IV、Skew 等"""
    print("\n=== 4. 下载期权衍生指标 ===")

    if not check_quota(20):
        return

    # 金融期权标的
    financial_symbols = ["510050.XSHG", "510300.XSHG", "159919.XSHE"]
    # 商品期权品种
    commodity_symbols = ["CU", "AU", "RB", "I", "MA"]

    # 计算当前到期月份（近月和次近月）
    now = datetime.now()
    maturities = [
        f"{now.year % 100}{now.month:02d}",  # 当月
        f"{(now.year if now.month < 12 else now.year + 1) % 100}{(now.month % 12 + 1):02d}",  # 次月
    ]

    all_data = []
    for sym in financial_symbols + commodity_symbols:
        for maturity in maturities:
            try:
                info_before = get_quota_info()
                before_mb = info_before["used_mb"]

                print(f"  [下载] 期权指标 {sym}/{maturity} ...", end=" ", flush=True)
                df = rqdatac.options.get_indicators(
                    sym,
                    maturity=maturity,
                    start_date="2020-01-01",
                    end_date=datetime.now().strftime("%Y-%m-%d")
                )

                actual_used = track_usage(before_mb)

                if df is not None and not df.empty:
                    all_data.append(df)
                    print(f"完成 ({len(df)} 行, 消耗 {actual_used:.2f} MB)")
                else:
                    print(f"数据为空 (消耗 {actual_used:.2f} MB)")
            except Exception as e:
                print(f"失败: {e}")

    # 合并保存
    if all_data:
        merged = pd.concat(all_data) if len(all_data) > 1 else all_data[0]
        out_path = DATA_ROOT / "options/indicators.parquet"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
        print(f"  [合并] 期权指标 -> {out_path} ({len(merged)} 行)")


def session_summary():
    """打印本次会话流量使用摘要"""
    info = get_quota_info()
    print(f"\n=== 流量使用摘要 ===")
    print(f"本次会话消耗: {_session_used_mb:.1f} MB")
    print(f"当前剩余: {info['remaining_mb']:.1f} MB")


def main():
    info = get_quota_info()
    print(f"数据补充下载 | 剩余流量: {info['remaining_mb']:.1f} MB")

    # 1. 下载缺失 TTM1 因子
    download_missing_ttm1()

    # 2. 下载期权主力月份
    download_options_dominant_month()

    # 3. 下载新闻舆情
    download_news()

    # 4. 下载期权指标
    download_options_indicators()

    session_summary()


if __name__ == "__main__":
    main()
