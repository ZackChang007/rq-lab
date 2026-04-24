"""RQFactor 因子挖掘与检验示例

完整演示 RQFactor 因子研究流程：
1. 定义因子（内置因子 + 算子组合）
2. 计算因子值
3. 准备收益率数据
4. 构建检验管道
5. 运行 IC 分析和分组收益分析

官方文档: docs/rqfactor/RQFACTOR_DOCS.md
进阶文档: docs/rqfactor/RQFACTOR_ADVANCED.md

运行:
    python scripts/factor/factor_research.py
"""
import rqdatac
from utils.common import setup_license

setup_license()
rqdatac.init()


# ── Step 1: 定义因子 ────────────────────────────────────────────────────────

def define_simple_factor():
    """简单因子：日内振幅比"""
    from rqfactor import Factor

    # (收盘价 - 开盘价) / (最高价 - 最低价)
    # 衡量日内趋势强度，值接近1说明收在最高点附近
    factor = (Factor("close") - Factor("open")) / (Factor("high") - Factor("low"))
    print(f"因子依赖: {factor.dependencies}")
    return factor


def define_composite_factor():
    """复合因子：成交量加权动量"""
    from rqfactor import Factor, MA, RANK, REF, PCT_CHANGE

    # 20日动量 × 20日平均换手率排名
    momentum = PCT_CHANGE(Factor("close"), 20)
    volume_rank = RANK(MA(Factor("volume"), 20))
    factor = RANK(momentum) * volume_rank
    print(f"因子依赖: {factor.dependencies}")
    return factor


def define_financial_factor():
    """财务因子：EP-TTM (市盈率倒数)"""
    from rqfactor import Factor

    factor = 1 / Factor("pe_ratio_ttm")
    print(f"因子依赖: {factor.dependencies}")
    return factor


# ── Step 2: 计算因子值 ──────────────────────────────────────────────────────

def compute_factor(factor, stock_ids, start_date, end_date):
    """执行因子计算"""
    from rqfactor import execute_factor

    print(f"计算因子: {start_date} ~ {end_date}, 股票数: {len(stock_ids)}")
    df = execute_factor(factor, stock_ids, start_date, end_date)
    print(f"因子值形状: {df.shape}")
    print(df.head())
    return df


# ── Step 3: 因子检验 ────────────────────────────────────────────────────────

def run_factor_test(factor_data, returns, ascending=True, periods=1):
    """构建并运行因子检验管道

    官方推荐流程:
    1. 去极值 (Winzorization)
    2. IC 分析 (ICAnalysis)
    3. 分组收益分析 (QuantileReturnAnalysis)
    """
    from rqfactor.analysis import (
        FactorAnalysisEngine,
        ICAnalysis,
        QuantileReturnAnalysis,
        Winzorization,
    )

    engine = FactorAnalysisEngine()

    # 预处理：去极值
    engine.append(("winzorization", Winzorization(method="mad")))

    # IC 分析（使用 rank_ic，申万行业分类）
    engine.append(
        ("rank_ic_analysis", ICAnalysis(rank_ic=True, industry_classification="sws"))
    )

    # 分组收益分析（5分组）
    engine.append(
        ("quantile_return", QuantileReturnAnalysis(quantile=5, benchmark="000300.XSHG"))
    )

    result = engine.analysis(
        factor_data,
        returns,
        ascending=ascending,
        periods=periods,
        keep_preprocess_result=True,
    )

    return result


def print_ic_summary(result):
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
        ic_mean = ic_result.ic.mean()
        ic_std = ic_result.ic.std()
        ir = ic_mean / ic_std if ic_std != 0 else 0
        print(f"\nIC 均值: {ic_mean:.4f}")
        print(f"IC 标准差: {ic_std:.4f}")
        print(f"IR (IC/Std): {ir:.4f}")
        print(f"IC > 0 占比: {(ic_result.ic > 0).mean():.2%}")


# ── Step 4: 主流程 ──────────────────────────────────────────────────────────

def main():
    """运行完整的因子研究流程"""
    print("=" * 60)
    print("RQFactor 因子挖掘与检验示例")
    print("=" * 60)

    # 参数设置
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    index_id = "000300.XSHG"  # 沪深300

    # 获取股票池
    stock_ids = rqdatac.index_components(index_id, end_date)
    print(f"股票池: {index_id}, 股票数: {len(stock_ids)}")

    # ── 1. 定义因子 ──
    print("\n--- Step 1: 定义因子 ---")
    factor = define_simple_factor()

    # ── 2. 计算因子值 ──
    print("\n--- Step 2: 计算因子值 ---")
    factor_data = compute_factor(factor, stock_ids, start_date, end_date)

    # ── 3. 准备收益率数据 ──
    print("\n--- Step 3: 准备收益率 ---")
    price = rqdatac.get_price(
        stock_ids,
        start_date=start_date,
        end_date=end_date,
        frequency="1d",
        fields="close",
        adjust_type="pre",
        expect_df=True,
    )
    # 计算日收益率
    returns = price.groupby(level="order_book_id").pct_change()
    print(f"收益率形状: {returns.shape}")

    # ── 4. 因子检验 ──
    print("\n--- Step 4: 因子检验 ---")
    result = run_factor_test(factor_data, returns, ascending=True, periods=1)

    # ── 5. 结果解读 ──
    print_ic_summary(result)

    print("\n因子研究流程完成！")


if __name__ == "__main__":
    main()
