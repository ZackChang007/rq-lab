"""Ricequant 全链条集成示例

完整演示从因子到归因的端到端流程:
1. 因子定义与检验 (RQFactor)
2. 组合优化 (RQOptimizer)
3. 策略回测 (RQAlpha Plus)
4. 业绩归因 (RQPAttr)

官方文档:
- RQFactor: docs/rqfactor/RQFACTOR_DOCS.md
- RQOptimizer: docs/rqoptimizer/RQOPTIMIZER_DOCS.md
- RQAlpha Plus: docs/rqalpha-plus/RQALPHA_PLUS_DOCS.md
- RQPAttr: docs/rqpattr/RQPATTR_DOCS.md

运行:
    python scripts/full_pipeline.py
"""
import copy

import rqdatac
from rqalpha.api import order_target_portfolio
from rqalpha_plus import run_func

from utils.common import setup_license, QUOTA_SAFE_CONFIG

setup_license()
rqdatac.init()


# ── Phase 1: 因子研究 ────────────────────────────────────────────────────────

def phase1_factor_research(stock_ids, start_date, end_date):
    """因子研究阶段

    目标: 定义并检验一个因子，生成因子得分
    """
    print("\n" + "=" * 60)
    print("Phase 1: 因子研究 (RQFactor)")
    print("=" * 60)

    from rqfactor import Factor, execute_factor
    from rqfactor.analysis import FactorAnalysisEngine, ICAnalysis, Winzorization

    # 定义因子：EP-TTM（市盈率倒数）
    # 逻辑：低估值股票可能被低估，有超额收益
    factor = 1 / Factor("pe_ratio_ttm")

    print(f"因子定义: EP-TTM = 1 / PE-TTM")
    print(f"股票池: {len(stock_ids)} 只股票")
    print(f"日期范围: {start_date} ~ {end_date}")

    # 计算因子值
    print("\n计算因子值...")
    factor_data = execute_factor(factor, stock_ids, start_date, end_date)
    print(f"因子值形状: {factor_data.shape}")

    # 准备收益率
    print("计算收益率...")
    price = rqdatac.get_price(
        stock_ids, start_date, end_date, frequency="1d", fields="close", adjust_type="pre", expect_df=True
    )
    returns = price.groupby(level="order_book_id").pct_change()

    # 因子检验
    print("运行因子检验...")
    engine = FactorAnalysisEngine()
    engine.append(("winzorization", Winzorization(method="mad")))
    engine.append(("ic_analysis", ICAnalysis(rank_ic=True, industry_classification="sws")))

    result = engine.analysis(factor_data, returns, ascending=True, periods=1)

    # 打印 IC 摘要
    ic_result = result.get("ic_analysis")
    if ic_result is not None:
        ic_mean = ic_result.ic.mean()
        ic_std = ic_result.ic.std()
        ir = ic_mean / ic_std if ic_std != 0 else 0
        print(f"\nIC 均值: {ic_mean:.4f}")
        print(f"IC 标准差: {ic_std:.4f}")
        print(f"IR: {ir:.4f}")

    # 返回最新一期因子得分（用于优化）
    scores = factor_data.iloc[-1].dropna()
    print(f"\n因子得分: {len(scores)} 只股票")
    return scores


# ── Phase 2: 组合优化 ────────────────────────────────────────────────────────

def phase2_portfolio_optimization(scores, date, benchmark="000300.XSHG"):
    """组合优化阶段

    目标: 根据因子得分计算最优权重
    """
    print("\n" + "=" * 60)
    print("Phase 2: 组合优化 (RQOptimizer)")
    print("=" * 60)

    from rqoptimizer import (
        CovModel,
        IndustryConstraint,
        MaxIndicator,
        StyleConstraint,
        portfolio_optimize,
    )

    print(f"优化目标: 最大化因子得分")
    print(f"基准: {benchmark}")
    print(f"约束: 行业中性 + 风格中性")

    # 执行优化
    weights = portfolio_optimize(
        order_book_ids=scores.index.tolist(),
        date=date,
        objective=MaxIndicator(scores),
        benchmark=benchmark,
        bnds={"weight": (0, 0.05)},  # 单只股票最大 5%
        cons=[
            IndustryConstraint(neutral=True),
            StyleConstraint(neutral=True),
        ],
        cov_model=CovModel.FACTOR_MODEL_DAILY,
    )

    # 过滤掉零权重
    weights = weights[weights > 0]
    print(f"\n优化结果: {len(weights)} 只股票持仓")
    print(f"权重总和: {weights.sum():.4f}")
    print(f"Top 5 持仓:")
    for sid, w in weights.nlargest(5).items():
        print(f"  {sid}: {w:.2%}")

    return weights


# ── Phase 3: 策略回测 ────────────────────────────────────────────────────────

def phase3_backtest(weights, start_date, end_date, rebalance_freq=20, benchmark="000300.XSHG"):
    """策略回测阶段

    目标: 在历史数据上验证策略表现
    """
    print("\n" + "=" * 60)
    print("Phase 3: 策略回测 (RQAlpha Plus)")
    print("=" * 60)

    print(f"回测区间: {start_date} ~ {end_date}")
    print(f"调仓频率: 每 {rebalance_freq} 个交易日")
    print(f"初始持仓: {len(weights)} 只股票")

    # 策略状态
    state = {
        "days_since_rebalance": 0,
        "target_weights": weights.to_dict(),
        "rebalance_freq": rebalance_freq,
    }

    def init(context):
        context.state = state

    def handle_bar(context, bar_dict):
        context.state["days_since_rebalance"] += 1

        if context.state["days_since_rebalance"] >= context.state["rebalance_freq"]:
            context.state["days_since_rebalance"] = 0
            # 执行调仓
            order_target_portfolio(context.state["target_weights"])

    # 运行回测
    config = copy.deepcopy(QUOTA_SAFE_CONFIG)
    config["base"].update({
        "accounts": {"STOCK": 1000000},
        "start_date": start_date,
        "end_date": end_date,
    })
    config["mod"]["sys_analyser"] = {
        "benchmark": benchmark,
    }

    result = run_func(config=config, init=init, handle_bar=handle_bar)

    # 打印结果
    summary = result["sys_analyser"]["summary"]
    print(f"\n回测结果:")
    print(f"  总收益率: {summary['total_returns']:.2%}")
    print(f"  年化收益率: {summary['annualized_returns']:.2%}")
    print(f"  夏普比率: {summary['sharpe']:.4f}")
    print(f"  最大回撤: {summary['max_drawdown']:.2%}")
    print(f"  Alpha: {summary['alpha']:.4f}")
    print(f"  Beta: {summary['beta']:.4f}")

    return result


# ── Phase 4: 业绩归因 ────────────────────────────────────────────────────────

def phase4_attribution(backtest_result, benchmark="000300.XSHG"):
    """业绩归因阶段

    目标: 分解收益来源，评估策略有效性
    """
    print("\n" + "=" * 60)
    print("Phase 4: 业绩归因 (RQPAttr)")
    print("=" * 60)

    import rqpattr

    # 提取权重和收益
    positions = backtest_result["sys_analyser"]["stock_positions"]
    portfolio = backtest_result["sys_analyser"]["portfolio"]

    positions = positions.join(portfolio["total_value"])
    positions["asset_type"] = "stock"
    positions = positions.reset_index().set_index(["date", "order_book_id", "asset_type"])
    weights = positions["market_value"] / positions["total_value"]
    daily_return = portfolio["unit_net_value"].pct_change().dropna()

    print(f"权重数据: {weights.shape}")
    print(f"收益率数据: {daily_return.shape}")

    # 因子归因
    print("\n执行因子归因...")
    result = rqpattr.performance_attribute(
        model="equity/factor_v2",
        daily_weights=weights,
        daily_return=daily_return,
        benchmark_info={"type": "index", "name": "沪深300", "detail": benchmark},
    )

    # 打印结果
    attr = result.get("attribution", {}).get("equity/factor_v2", {})
    factor_attr = attr.get("factor_attribution", [])

    if factor_attr:
        print("\n因子贡献摘要:")
        factors = factor_attr[0].get("factors", [])[:10]
        print(f"{'因子':<20} {'主动暴露':>12} {'主动收益':>12}")
        print("-" * 46)
        for f in factors:
            name = f.get("factor", "")[:18]
            exposure = f.get("active_exposure", 0)
            ret = f.get("active_return", 0)
            print(f"{name:<20} {exposure:>12.4f} {ret:>12.4%}")

    return result


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    """运行完整的全链条流程"""
    print("=" * 60)
    print("Ricequant 全链条集成示例")
    print("=" * 60)
    print("因子研究 → 组合优化 → 策略回测 → 业绩归因")

    # 参数设置
    factor_start = "2022-01-01"
    factor_end = "2022-12-31"
    backtest_start = "2023-01-01"
    backtest_end = "2023-12-31"
    optimize_date = "2022-12-30"  # 优化日期（因子计算结束日）
    index_id = "000300.XSHG"

    # 获取股票池
    print("\n获取股票池...")
    stock_ids = rqdatac.index_components(index_id, optimize_date)
    print(f"股票池: {index_id}, {len(stock_ids)} 只股票")

    # ── Phase 1: 因子研究 ──
    scores = phase1_factor_research(stock_ids, factor_start, factor_end)

    # ── Phase 2: 组合优化 ──
    weights = phase2_portfolio_optimization(scores, optimize_date)

    # ── Phase 3: 策略回测 ──
    result = phase3_backtest(weights, backtest_start, backtest_end)

    # ── Phase 4: 业绩归因 ──
    attribution = phase4_attribution(result)

    print("\n" + "=" * 60)
    print("全链条流程完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
