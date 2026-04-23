"""回测模块 - 封装 RQAlpha Plus 回测引擎

用法:
    from rq_lab.backtest import run_backtest

    result = run_backtest(
        init=init,
        handle_bar=handle_bar,
        start_date="2020-01-01",
        end_date="2020-12-31",
        capital=100000,
    )
    summary = result["sys_analyser"]["summary"]
    print(f"总收益: {summary['total_returns']:.2%}")
    print(f"夏普:   {summary['sharpe']:.4f}")
    print(f"最大回撤: {summary['max_drawdown']:.2%}")
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from rqalpha_plus import run_func


def _ensure_license() -> None:
    """确保 RQSDK 许可证已配置到环境变量中。"""
    if os.environ.get("RQDATAC2_CONF"):
        return
    # 从项目 config/credentials.py 读取许可证密钥
    project_root = Path(__file__).resolve().parent.parent
    credentials = project_root / "config" / "credentials.py"
    if credentials.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("credentials", str(credentials))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            key = getattr(mod, "RQSDK_LICENSE_KEY", "")
            if key:
                os.environ["RQDATAC2_CONF"] = f"tcp://license:{key}@rqdatad-pro.ricequant.com:16011"


def run_backtest(
    init: Callable,
    handle_bar: Callable,
    *,
    start_date: str = "2020-01-01",
    end_date: str = "2020-12-31",
    capital: float = 100000,
    benchmark: str | None = "000300.XSHG",
    frequency: str = "1d",
    plot: bool = False,
    before_trading: Callable | None = None,
    after_trading: Callable | None = None,
    extra_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """运行回测并返回结果字典。

    封装 rqalpha_plus.run_func()，预设合理默认值：
    - auto_update_bundle=False（避免消耗付费配额）
    - 仅使用本地 Bundle 数据

    Args:
        init: 策略初始化函数 init(context)
        handle_bar: 行情处理函数 handle_bar(context, bar_dict)
        start_date: 回测起始日期
        end_date: 回测结束日期
        capital: 初始资金
        benchmark: 基准指数，None 表示不设基准
        frequency: 回测频率 "1d" | "1m" | "tick"
        plot: 是否显示结果图表
        before_trading: 盘前回调
        after_trading: 盘后回调
        extra_config: 额外配置，覆盖默认值

    Returns:
        结果字典，关键键:
        - "sys_analyser"["summary"]: alpha, beta, sharpe, max_drawdown, total_returns 等
        - "sys_analyser"["trades"]: 交易记录 DataFrame
        - "sys_analyser"["portfolio"]: 组合净值
    """
    _ensure_license()  # 确保许可证已配置
    config: dict[str, Any] = {
        "base": {
            "accounts": {"STOCK": capital},
            "start_date": start_date,
            "end_date": end_date,
            "frequency": frequency,
            "auto_update_bundle": False,
            # 禁用实时数据源，仅使用本地 Bundle
            "rqdatac_uri": "disabled",
        },
        "mod": {
            "sys_analyser": {
                "plot": plot,
                "benchmark": benchmark,
                "enabled": True,
            },
            # 禁用非股票品种模块（避免调用 RQData API 消耗配额）
            "option": {"enabled": False},
            "convertible": {"enabled": False},
            "fund": {"enabled": False},
            "future": {"enabled": False},
            "spot": {"enabled": False},
        },
    }

    if extra_config:
        _deep_merge(config, extra_config)

    kwargs: dict[str, Any] = {"config": config, "init": init, "handle_bar": handle_bar}
    if before_trading is not None:
        kwargs["before_trading"] = before_trading
    if after_trading is not None:
        kwargs["after_trading"] = after_trading

    return run_func(**kwargs)


def _deep_merge(base: dict, override: dict) -> None:
    """递归合并 override 到 base（原地修改 base）。"""
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
