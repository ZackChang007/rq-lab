"""RQPAttr 业绩归因示例

完整演示 RQPAttr 业绩归因分析流程：
1. 从回测结果提取权重和收益数据
2. 执行 Brinson 行业归因
3. 执行因子归因
4. 解读归因结果

官方文档: docs/rqpattr/RQPATTR_DOCS.md

运行:
    python scripts/attribution/performance_attribution.py
"""
import pandas as pd
import rqdatac
from utils.common import setup_license

setup_license()
rqdatac.init()


# ── Step 1: 从回测结果提取数据 ──────────────────────────────────────────────

def extract_weights_and_returns(backtest_result):
    """从 RQAlpha Plus 回测结果中提取权重和收益率数据

    Args:
        backtest_result: run_func() 返回的结果字典

    Returns:
        weights: pd.Series, MultiIndex [date, order_book_id, asset_type]
        daily_return: pd.Series, Index [date]
    """
    positions = backtest_result["sys_analyser"]["stock_positions"]
    portfolio = backtest_result["sys_analyser"]["portfolio"]

    # 合并总市值
    positions = positions.join(portfolio["total_value"])

    # 设置资产类型
    positions["asset_type"] = "stock"

    # 重置索引并设置三级索引
    positions = positions.reset_index()
    positions = positions.set_index(["date", "order_book_id", "asset_type"])

    # 计算权重
    weights = positions["market_value"] / positions["total_value"]

    # 计算日收益率
    daily_return = portfolio["unit_net_value"].pct_change().dropna()

    print(f"权重数据形状: {weights.shape}")
    print(f"收益率数据形状: {daily_return.shape}")
    print(f"日期范围: {daily_return.index.min()} ~ {daily_return.index.max()}")

    return weights, daily_return


# ── Step 2: Brinson 行业归因 ────────────────────────────────────────────────

def run_brinson_attribution(weights, daily_return, benchmark="000300.XSHG"):
    """执行 Brinson 行业归因

    将主动收益分解为:
    - 配置收益: 行业权重偏离带来的收益
    - 选择收益: 行业内选股带来的收益
    """
    import rqpattr

    print("\n=== Brinson 行业归因 ===")

    result = rqpattr.performance_attribute(
        model="equity/brinson",
        daily_weights=weights,
        daily_return=daily_return,
        benchmark_info={"type": "index", "name": "沪深300", "detail": benchmark},
        standard="sws",  # 申万行业分类
    )

    return result


# ── Step 3: 因子归因 ────────────────────────────────────────────────────────

def run_factor_attribution(weights, daily_return, benchmark="000300.XSHG"):
    """执行因子归因

    将收益分解为:
    - 风格偏好: 市值、动量、价值等风格因子贡献
    - 行业偏好: 行业配置贡献
    - 市场联动: 市场整体涨跌贡献
    - 特异收益: 个股特异因素贡献
    """
    import rqpattr

    print("\n=== 因子归因 (v2模型) ===")

    result = rqpattr.performance_attribute(
        model="equity/factor_v2",
        daily_weights=weights,
        daily_return=daily_return,
        benchmark_info={"type": "index", "name": "沪深300", "detail": benchmark},
    )

    return result


# ── Step 4: 解读归因结果 ────────────────────────────────────────────────────

def print_brinson_result(result):
    """打印 Brinson 归因结果"""
    decomposition = result.get("returns_decomposition")
    if not decomposition:
        print("无 Brinson 归因结果")
        return

    print("\n--- 收益分解树 ---")
    print_tree(decomposition)


def print_tree(nodes, indent=0):
    """递归打印树状结构"""
    for node in nodes:
        factor = node.get("factor", "")
        value = node.get("value", 0)
        print("  " * indent + f"- {factor}: {value:.4%}")
        children = node.get("children")
        if children:
            print_tree(children, indent + 1)


def print_factor_result(result):
    """打印因子归因结果"""
    attr = result.get("attribution", {}).get("equity/factor_v2", {})
    factor_attr = attr.get("factor_attribution", [])

    if not factor_attr:
        print("无因子归因结果")
        return

    print("\n--- 因子贡献详情 ---")
    for fa in factor_attr[:1]:  # 只打印第一个时间点的数据
        factors = fa.get("factors", [])
        print(f"\n{'因子名称':<20} {'主动暴露':>12} {'主动收益':>12}")
        print("-" * 46)
        for f in factors[:15]:  # 只打印前15个因子
            name = f.get("factor", "")[:18]
            exposure = f.get("active_exposure", 0)
            ret = f.get("active_return", 0)
            print(f"{name:<20} {exposure:>12.4f} {ret:>12.4%}")


# ── Step 5: 完整流程示例 ────────────────────────────────────────────────────

def run_backtest_for_attribution():
    """运行一个简单策略并返回结果用于归因"""
    import copy

    from rqalpha.api import order_target_percent
    from rqalpha_plus import run_func

    from utils.common import QUOTA_SAFE_CONFIG

    def init(context):
        context.stock = "000001.XSHE"
        context.rebalanced = False

    def handle_bar(context, bar_dict):
        if not context.rebalanced:
            order_target_percent(context.stock, 1)
            context.rebalanced = True

    config = copy.deepcopy(QUOTA_SAFE_CONFIG)
    config["base"].update({
        "accounts": {"STOCK": 100000},
        "start_date": "2020-01-01",
        "end_date": "2020-12-31",
    })
    config["mod"]["sys_analyser"] = {
        "benchmark": "000300.XSHG",
    }

    result = run_func(config=config, init=init, handle_bar=handle_bar)
    return result


def main():
    """运行业绩归因分析"""
    print("=" * 60)
    print("RQPAttr 业绩归因示例")
    print("=" * 60)

    # ── 1. 运行回测 ──
    print("\n--- Step 1: 运行回测 ---")
    backtest_result = run_backtest_for_attribution()
    print("回测完成")

    # ── 2. 提取数据 ──
    print("\n--- Step 2: 提取权重和收益 ---")
    weights, daily_return = extract_weights_and_returns(backtest_result)

    # ── 3. Brinson 归因 ──
    brinson_result = run_brinson_attribution(weights, daily_return)
    print_brinson_result(brinson_result)

    # ── 4. 因子归因 ──
    factor_result = run_factor_attribution(weights, daily_return)
    print_factor_result(factor_result)

    print("\n业绩归因流程完成！")


if __name__ == "__main__":
    main()
