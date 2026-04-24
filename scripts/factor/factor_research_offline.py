"""RQFactor 离线因子研究示例

⚠️ 离线版本说明：
- 数据源：本地 Parquet 文件（data/stock/price_1d.parquet），非 RQData API
- 因子计算：直接从本地价格数据计算，非 execute_factor()
- 检验管道：完全遵循官方推荐（FactorAnalysisEngine + ICAnalysis + Winzorization）
- 其余逻辑均与官方标准一致

官方文档: docs/rqfactor/RQFACTOR_DOCS.md

运行:
    python scripts/factor/factor_research_offline.py
"""
import pandas as pd
from pathlib import Path

# 本地数据路径
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "stock"
PRICE_FILE = DATA_DIR / "price_1d.parquet"

# ── 离线数据加载 ────────────────────────────────────────────────────────────────

def load_local_price_data(start_date: str, end_date: str) -> pd.DataFrame:
    """从本地 Parquet 文件加载价格数据

    ⚠️ 数据源差异：
    - 官方: rqdatac.get_price() → API 调用，消耗配额
    - 离线: pd.read_parquet() → 本地文件，不消耗配额
    """
    if not PRICE_FILE.exists():
        raise FileNotFoundError(f"本地价格数据不存在: {PRICE_FILE}")

    df = pd.read_parquet(PRICE_FILE)

    # 过滤日期范围
    df = df.reset_index()
    df["date"] = pd.to_datetime(df["date"])
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    df = df.set_index(["order_book_id", "date"])

    return df


def get_stock_universe(df: pd.DataFrame, date: str) -> list[str]:
    """从价格数据中提取股票池

    ⚠️ 数据源差异：
    - 官方: rqdatac.index_components() → API 调用，消耗配额
    - 离线: 从价格数据中提取，仅使用本地数据

    注意：此方法获取的是"有数据的股票"，不一定等于官方的指数成分股
    """
    target_date = pd.to_datetime(date)
    # 找到最近的有数据的交易日
    dates = df.index.get_level_values("date").unique().sort_values()
    nearest_date = dates[dates <= target_date].max()

    # 提取该日期有数据的股票
    stocks = df.xs(nearest_date, level="date").index.unique().tolist()
    return stocks


# ── 因子定义（离线计算）────────────────────────────────────────────────────────

def compute_intraday_momentum(df: pd.DataFrame) -> pd.DataFrame:
    """计算日内动量因子

    ⚠️ 因子计算差异：
    - 官方: Factor("close") + execute_factor() → RQFactor 引擎
    - 离线: 直接 pandas 计算

    因子公式：(收盘价 - 开盘价) / (最高价 - 最低价)
    含义：衡量日内趋势强度，值接近1说明收在最高点附近
    """
    factor_df = df[["open", "close", "high", "low"]].copy()
    factor_df["intraday_momentum"] = (factor_df["close"] - factor_df["open"]) / (
        factor_df["high"] - factor_df["low"]
    )
    return factor_df["intraday_momentum"].unstack(level="order_book_id")


def compute_volume_weighted_momentum(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """计算成交量加权动量因子

    公式：rank(动量) × rank(平均成交量)
    """
    # 计算收益率
    close = df["close"].unstack(level="order_book_id")
    returns = close.pct_change(window)

    # 计算平均成交量排名
    volume = df["volume"].unstack(level="order_book_id")
    avg_volume = volume.rolling(window).mean()
    volume_rank = avg_volume.rank(axis=1, pct=True)

    # 动量排名
    momentum_rank = returns.rank(axis=1, pct=True)

    # 综合因子
    factor = momentum_rank * volume_rank
    return factor


# ── 因子检验（官方管道）─────────────────────────────────────────────────────────

def run_factor_test(
    factor_data: pd.DataFrame,
    returns: pd.DataFrame,
    ascending: bool = True,
    periods: int = 1,
) -> dict:
    """构建并运行因子检验管道

    ⚠️ 离线版本限制：
    - ✅ 去极值 (Winzorization) - 无需 API
    - ✅ IC 分析 (ICAnalysis, rank_ic=True) - 无需 API
    - ❌ 行业分类 IC - 需要 rqdatac.instruments()
    - ❌ 分组收益分析 - 需要 rqdatac.instruments() 解析基准

    官方文档: docs/rqfactor/RQFACTOR_DOCS.md 第4章
    """
    from rqfactor.analysis import (
        FactorAnalysisEngine,
        ICAnalysis,
        Winzorization,
    )

    engine = FactorAnalysisEngine()

    # 预处理：去极值
    engine.append(("winzorization", Winzorization(method="mad")))

    # IC 分析（仅 rank_ic，不使用行业分类）
    # 注意：industry_classification 需要 rqdatac API，离线模式不可用
    engine.append(
        ("rank_ic_analysis", ICAnalysis(rank_ic=True))
    )

    # 分组收益分析被跳过 - 需要 rqdatac.instruments() 解析基准
    # 在流量恢复后可启用完整分析

    result = engine.analysis(
        factor_data,
        returns,
        ascending=ascending,
        periods=periods,
        keep_preprocess_result=True,
    )

    return result


def print_ic_summary(result: dict) -> None:
    """打印 IC 分析摘要"""
    ic_result = result.get("rank_ic_analysis")
    if ic_result is None:
        print("无 IC 分析结果")
        return

    summary = ic_result.summary()
    print("\n=== IC 分析摘要 ===")
    print(summary)

    # 关键指标解读
    if hasattr(ic_result, "ic") and ic_result.ic is not None:
        ic_vals = ic_result.ic
        if isinstance(ic_vals, pd.DataFrame):
            ic_vals = ic_vals.iloc[:, 0]
        ic_mean = float(ic_vals.mean())
        ic_std = float(ic_vals.std())
        ir = ic_mean / ic_std if ic_std != 0 else 0
        print(f"\nIC 均值: {ic_mean:.4f}")
        print(f"IC 标准差: {ic_std:.4f}")
        print(f"IR (IC/Std): {ir:.4f}")
        print(f"IC > 0 占比: {(ic_vals > 0).mean():.2%}")


# ── 主流程 ───────────────────────────────────────────────────────────────────────

def main() -> None:
    """运行离线因子研究流程"""
    print("=" * 60)
    print("RQFactor 离线因子研究示例")
    print("=" * 60)
    print("⚠️ 数据源：本地 Parquet（非 RQData API）")
    print("⚠️ 检验管道：完全遵循官方推荐")
    print()

    # 参数设置
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    reference_date = "2023-06-30"  # 用于确定股票池

    # ── 1. 加载本地数据 ──
    print("--- Step 1: 加载本地价格数据 ---")
    price_df = load_local_price_data(start_date, end_date)
    print(f"价格数据形状: {price_df.shape}")
    print(f"日期范围: {price_df.index.get_level_values('date').min().date()} ~ "
          f"{price_df.index.get_level_values('date').max().date()}")

    # 获取股票池
    stock_ids = get_stock_universe(price_df, reference_date)
    print(f"股票池: {len(stock_ids)} 只股票（有数据的股票）")

    # 过滤到目标股票池
    available_stocks = [s for s in stock_ids if s in price_df.index.get_level_values("order_book_id")]
    price_df = price_df.loc[price_df.index.get_level_values("order_book_id").isin(available_stocks)]
    print(f"有效股票: {len(available_stocks)} 只")

    # ── 2. 计算因子值 ──
    print("\n--- Step 2: 计算因子值 ---")
    print("因子: 日内动量 = (收盘 - 开盘) / (最高 - 最低)")
    factor_data = compute_intraday_momentum(price_df)
    print(f"因子值形状: {factor_data.shape}")

    # ── 3. 准备收益率数据 ──
    print("\n--- Step 3: 准备收益率 ---")
    close = price_df["close"].unstack(level="order_book_id")
    returns = close.pct_change()
    print(f"收益率形状: {returns.shape}")

    # ── 4. 因子检验（官方管道）──
    print("\n--- Step 4: 因子检验（官方管道）---")
    result = run_factor_test(factor_data, returns, ascending=True, periods=1)

    # ── 5. 结果解读 ──
    print_ic_summary(result)

    print("\n离线因子研究流程完成！")
    print("\n⚠️ 注意事项:")
    print("- 离线版本使用本地数据，股票池可能与官方 API 不同")
    print("- 检验管道与官方推荐完全一致")
    print("- 流量恢复后建议用官方 API 验证结果")


if __name__ == "__main__":
    main()
