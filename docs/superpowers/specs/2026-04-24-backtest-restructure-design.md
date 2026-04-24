# 回测模块重构设计

> 日期：2026-04-24
> 状态：待审批

## 背景

当前回测模块存在以下问题：

1. `rq_lab/` 包名与项目名 `rq-lab` 冗余，架构不清晰
2. `examples/` 目录定位模糊，策略脚本缺少归属
3. 共享配置（许可证、配额保护）散落在回测模块内，其他模块无法复用
4. 未严格遵循官方最佳实践

## 设计原则

1. **官方优先**：策略脚本遵循 RQSDK 官方模板，回调函数签名与官方一致
2. **scripts 定位**：零散脚本分门别类存放，脚本间关联性弱，不被频繁调用
3. **共享基础设施独立**：许可证初始化、配额保护配置等被多类脚本依赖，抽取为独立模块

## 目录结构

```
rq-lab/
├── utils/
│   ├── __init__.py
│   └── common.py              # 许可证初始化 + 配额保护默认配置
├── scripts/
│   ├── backtest/
│   │   └── buy_and_hold.py    # 买入持有策略
│   ├── data/
│   │   └── download.py        # 数据下载脚本
│   ├── factor/                # 预留
│   ├── portfolio/             # 预留
│   └── optimize/              # 预留
├── examples/                  # 保留，非回测脚本不动
├── config/
│   └── credentials.py
├── docs/
│   └── backtest.md            # 回测说明文档
└── pyproject.toml
```

## 变更清单

| 操作 | 路径 | 说明 |
|------|------|------|
| 删除 | `rq_lab/` | 包名冗余，功能迁移 |
| 新增 | `utils/__init__.py` | 模块入口 |
| 新增 | `utils/common.py` | 共享配置（许可证初始化 + 配额保护） |
| 新增 | `scripts/backtest/buy_and_hold.py` | 买入持有策略，遵循官方模板 |
| 新增 | `docs/backtest.md` | 回测说明文档 |
| 迁移 | `examples/buy_and_hold.py` → `scripts/backtest/buy_and_hold.py` | 回测脚本归位 |
| 修改 | `pyproject.toml` | `packages = [{include = "utils"}]` |
| 修改 | `CLAUDE.md` | 更新模块描述 |

## utils/common.py

```python
"""共享工具：许可证初始化 + 配额保护默认配置"""
import os
from pathlib import Path

_CREDENTIALS_FILE = Path(__file__).resolve().parent.parent / "config" / "credentials.py"


def setup_license() -> None:
    """设置 RQDATAC2_CONF 环境变量，从 config/credentials.py 读取密钥。"""
    if os.environ.get("RQDATAC2_CONF"):
        return
    if _CREDENTIALS_FILE.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("credentials", str(_CREDENTIALS_FILE))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            key = getattr(mod, "RQSDK_LICENSE_KEY", "")
            if key:
                os.environ["RQDATAC2_CONF"] = f"tcp://license:{key}@rqdatad-pro.ricequant.com:16011"


# 配额保护默认配置（试用账号）
QUOTA_SAFE_CONFIG = {
    "base": {
        "auto_update_bundle": False,
        "rqdatac_uri": "disabled",
    },
    "mod": {
        "option": {"enabled": False},
        "convertible": {"enabled": False},
        "fund": {"enabled": False},
        "future": {"enabled": False},
        "spot": {"enabled": False},
    },
}
```

## 策略脚本模板

遵循 RQSDK 官方回调函数模板，`__main__` 块用于带配额保护运行：

```python
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
    from utils.common import setup_license, QUOTA_SAFE_CONFIG
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
```

## docs/backtest.md

涵盖：
1. 回测模块功能结构
2. 文件目录及策略脚本说明（Markdown 超链接）
3. 三种运行方式（CLI / Python 直接运行 / 函数入口调用）
4. 配额保护说明
5. 编写新策略指引

## 兼容性

- `scripts/data/download.py` 已有 `from config.credentials import RQSDK_LICENSE_KEY`，暂不改动，后续可迁移到 `utils.common`
- `scripts/` 下的 factor / portfolio / optimize 目录为空预留，未来模块可直接使用 `utils.common`
- `examples/` 目录保留，仅迁出回测相关脚本
