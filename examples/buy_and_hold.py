"""买入持有策略样例

演示 rq_lab.backtest.run_backtest() 的基本用法。
策略：首个交易日全仓买入平安银行(000001.XSHE)，持有到期末。

运行:
    python examples/buy_and_hold.py
"""
from rqalpha.api import order_target_percent

from rq_lab.backtest import run_backtest


def init(context):
    """策略初始化。"""
    context.stock = "000001.XSHE"  # 平安银行
    context.fired = False


def handle_bar(context, bar_dict):
    """行情处理：首日全仓买入，之后持有。"""
    if not context.fired:
        # order_target_percent: 调整至目标仓位比例（1 = 100%）
        order_target_percent(context.stock, 1)
        context.fired = True


if __name__ == "__main__":
    print("运行买入持有策略回测...")
    print("-" * 50)

    result = run_backtest(
        init=init,
        handle_bar=handle_bar,
        start_date="2020-01-01",
        end_date="2020-12-31",
        capital=100000,
        benchmark="000300.XSHG",  # 沪深300作为基准
    )

    summary = result["sys_analyser"]["summary"]

    print("回测结果:")
    print(f"  总收益率:   {summary['total_returns']:.2%}")
    print(f"  年化收益率: {summary['annualized_returns']:.2%}")
    print(f"  夏普比率:   {summary['sharpe']:.4f}")
    print(f"  最大回撤:   {summary['max_drawdown']:.2%}")
    print(f"  Alpha:      {summary['alpha']:.4f}")
    print(f"  Beta:       {summary['beta']:.4f}")
    print("-" * 50)

    # 访问交易记录
    trades = result["sys_analyser"].get("trades")
    if trades is not None and len(trades) > 0:
        print(f"交易次数: {len(trades)}")
