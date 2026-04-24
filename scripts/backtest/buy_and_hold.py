"""买入持有策略 - 遵循 RQSDK 官方模板"""
from rqalpha.api import *


def init(context):
    context.s1 = "000001.XSHE"
    update_universe(context.s1)
    context.fired = False


def before_trading(context):
    pass


def handle_bar(context, bar_dict):
    if not context.fired:
        order_target_percent(context.s1, 1)
        context.fired = True


def after_trading(context):
    pass


if __name__ == "__main__":
    import copy

    from utils.common import QUOTA_SAFE_CONFIG, setup_license
    from rqalpha_plus import run_func

    setup_license()

    config = copy.deepcopy(QUOTA_SAFE_CONFIG)
    config["base"].update({
        "accounts": {"STOCK": 100000},
        "start_date": "2020-01-01",
        "end_date": "2020-12-31",
    })
    config["mod"]["sys_analyser"] = {
        "plot": True,
        "benchmark": "000300.XSHG",
    }

    result = run_func(config=config, init=init, handle_bar=handle_bar)
    summary = result["sys_analyser"]["summary"]
    print(f"总收益率: {summary['total_returns']:.2%}")
    print(f"夏普比率: {summary['sharpe']:.4f}")
