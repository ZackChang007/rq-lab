"""RQOptimizer 组合优化示例

完整演示 RQOptimizer 组合优化流程：
1. 准备因子得分（来自 RQFactor）
2. 设置优化目标
3. 设置约束条件
4. 执行优化
5. 查看优化结果

官方文档: docs/rqoptimizer/RQOPTIMIZER_DOCS.md
API 参考: docs/rqoptimizer/RQOPTIMIZER_API.md

运行:
    python scripts/portfolio/portfolio_optimization.py
"""
import rqdatac
from utils.common import setup_license

setup_license()
rqdatac.init()


# ── Step 1: 准备因子得分 ─────────────────────────────────────────────────────

def get_factor_scores(stock_ids, date, factor_name="pe_ratio_ttm"):
    """获取因子得分

    可以从多种来源获取:
    1. RQFactor 计算的自定义因子
    2. RQData 内置因子 get_factor()
    """
    from rqfactor import Factor, execute_factor

    # 方法 1: 使用内置因子
    # scores = rqdatac.get_factor(stock_ids, [factor_name], date, date, expect_df=True).iloc[0]

    # 方法 2: 使用 RQFactor 计算自定义因子
    factor = 1 / Factor("pe_ratio_ttm")  # EP-TTM，因子值越大越好
    df = execute_factor(factor, stock_ids, date, date)
    scores = df.iloc[0]

    print(f"因子得分形状: {scores.shape}")
    print(f"得分范围: [{scores.min():.4f}, {scores.max():.4f}]")
    return scores


# ── Step 2: 组合优化 ────────────────────────────────────────────────────────

def optimize_indicator_max(scores, date, benchmark="000300.XSHG"):
    """指标最大化优化

    适用场景: 有明确的 Alpha 因子，希望最大化因子暴露
    约束: 个股权重约束 + 行业偏离约束
    """
    from rqoptimizer import (
        CovModel,
        MaxIndicator,
        WildcardIndustryConstraint,
        portfolio_optimize,
    )

    print("\n--- 指标最大化优化 ---")
    print(f"目标: 最大化因子得分")
    print(f"基准: {benchmark}")
    print(f"约束: 个股权重0-5%, 行业偏离±3%")

    weights = portfolio_optimize(
        order_book_ids=scores.index.tolist(),
        date=date,
        objective=MaxIndicator(scores),
        benchmark=benchmark,
        bnds={"weight": (0, 0.05)},  # 个股权重上限 5%
        cons=[
            WildcardIndustryConstraint(
                lower_limit=-0.03, upper_limit=0.03, relative=True
            ),  # 行业偏离基准±3%
        ],
        cov_model=CovModel.FACTOR_MODEL_DAILY,
    )

    return weights


def optimize_min_tracking_error(stock_ids, date, benchmark="000300.XSHG"):
    """跟踪误差最小化

    适用场景: 指数增强，在控制跟踪误差的同时获得超额收益
    """
    from rqoptimizer import (
        CovModel,
        MinTrackingError,
        TrackingErrorLimit,
        WildcardIndustryConstraint,
        portfolio_optimize,
    )
    import pandas as pd

    print("\n--- 跟踪误差最小化优化 ---")
    print(f"目标: 最小化跟踪误差")
    print(f"约束: TE < 2%, 行业中性")

    weights = portfolio_optimize(
        order_book_ids=stock_ids,
        date=date,
        objective=MinTrackingError(),
        benchmark=benchmark,
        cons=[
            TrackingErrorLimit(upper_limit=0.05),  # 放宽到 5%（小股票池约束放宽）
        ],
        cov_model=CovModel.FACTOR_MODEL_DAILY,
    )

    return weights


def optimize_risk_parity(stock_ids, date):
    """风险平价优化

    适用场景: 风险均衡配置，不依赖收益预测
    """
    from rqoptimizer import CovModel, RiskParity, portfolio_optimize

    print("\n--- 风险平价优化 ---")
    print("目标: 各股票风险贡献相等")

    weights = portfolio_optimize(
        order_book_ids=stock_ids,
        date=date,
        objective=RiskParity(),
        bnds={"weight": (0.01, 0.1)},  # 权重范围 1% ~ 10%
        cov_model=CovModel.FACTOR_MODEL_DAILY,
    )

    return weights


# ── Step 3: 分析优化结果 ───────────────────────────────────────────────────

def analyze_weights(weights, benchmark="000300.XSHG"):
    """分析优化后的权重分布"""
    import pandas as pd

    print("\n=== 优化结果分析 ===")

    if weights is None or weights.empty:
        print("无权重数据")
        return

    print(f"持仓股票数: {len(weights)}")
    print(f"权重总和: {weights.sum():.4f}")
    print(f"最大权重: {weights.max():.4f}")
    print(f"最小权重: {weights.min():.4f}")
    print(f"权重标准差: {weights.std():.4f}")

    # Top 10 持仓
    top10 = weights.nlargest(10)
    print("\nTop 10 持仓:")
    for stock_id, weight in top10.items():
        name = rqdatac.instruments(stock_id).symbol
        print(f"  {stock_id} ({name}): {weight:.2%}")


# ── Step 4: 与回测集成 ─────────────────────────────────────────────────────

def make_strategy_from_weights(weights_generator, rebalance_freq=20):
    """生成基于优化权重的策略函数

    Args:
        weights_generator: 接收 (stocks, date) 返回权重 Series 的函数
        rebalance_freq: 调仓频率（交易日）
    """
    from rqalpha.api import get_trading_dates, order_target_portfolio, update_universe

    def init(context):
        context.days_since_rebalance = 0
        context.rebalance_freq = rebalance_freq

    def handle_bar(context, bar_dict):
        context.days_since_rebalance += 1
        if context.days_since_rebalance >= context.rebalance_freq:
            context.days_since_rebalance = 0

            # 获取当前股票池
            stock_ids = list(bar_dict.keys())

            # 生成优化权重
            date = context.now.strftime("%Y-%m-%d")
            try:
                weights = weights_generator(stock_ids, date)
                # 执行调仓
                order_target_portfolio(weights.to_dict())
                print(f"[{date}] 调仓完成，持仓数: {len(weights)}")
            except Exception as e:
                print(f"[{date}] 优化失败: {e}")

    return init, handle_bar


# ── Step 5: 主流程 ──────────────────────────────────────────────────────────

def main():
    """运行组合优化流程"""
    import pandas as pd

    print("=" * 60)
    print("RQOptimizer 组合优化示例")
    print("=" * 60)

    # 参数设置
    date = "2023-06-30"
    index_id = "000300.XSHG"

    # 获取股票池
    stock_ids = rqdatac.index_components(index_id, date)
    print(f"股票池: {index_id}, 股票数: {len(stock_ids)}")

    # ── 1. 获取因子得分 ──
    print("\n--- Step 1: 准备因子得分 ---")
    scores = get_factor_scores(stock_ids, date)

    # ── 2. 指标最大化优化 ──
    weights = optimize_indicator_max(scores, date)
    analyze_weights(weights)

    # ── 3. 跟踪误差最小化 ──
    weights2 = optimize_min_tracking_error(stock_ids[:50], date)  # 限制数量加快速度
    analyze_weights(weights2)

    # ── 4. 风险平价优化 ──
    weights3 = optimize_risk_parity(stock_ids[:30], date)  # 限制数量加快速度
    analyze_weights(weights3)

    print("\n组合优化流程完成！")


if __name__ == "__main__":
    main()
