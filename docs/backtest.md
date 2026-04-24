# 回测模块说明

## 功能结构

回测模块用于运行股票策略的历史回测，基于 [RQAlpha Plus](../docs/rqalpha-plus/RQALPHA_PLUS_DOCS.md) 引擎。

核心组件：

- [utils/common.py](../utils/common.py) — 共享配置（许可证初始化、配额保护默认值）
- [scripts/backtest/](../scripts/backtest/) — 策略脚本目录

## 文件目录

| 文件 | 说明 |
|------|------|
| [scripts/backtest/buy_and_hold.py](../scripts/backtest/buy_and_hold.py) | 买入持有策略 |
| [utils/common.py](../utils/common.py) | 许可证初始化 + 配额保护默认配置 |

## 使用方法

### 方式一：命令行运行（官方方式）

```bash
rqalpha-plus run -f scripts/backtest/buy_and_hold.py -s 2020-01-01 -e 2020-12-31 --account stock 100000 --plot
```

### 方式二：Python 直接运行

```bash
python scripts/backtest/buy_and_hold.py
```

### 方式三：函数入口调用

```python
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
config["mod"]["sys_analyser"] = {"plot": True, "benchmark": "000300.XSHG"}

result = run_func(config=config, init=init, handle_bar=handle_bar)
```

## 配额保护

试用账号需注意以下限制（已通过 [QUOTA_SAFE_CONFIG](../utils/common.py) 预设）：

- `auto_update_bundle: False` — 不自动更新 Bundle，避免消耗付费配额
- `rqdatac_uri: "disabled"` — 不连接 RQData 在线服务，仅使用本地 Bundle 数据
- 禁用非股票品种模块（期权、可转债、基金、期货、现货），它们初始化时会调用 RQData API

## 编写新策略

1. 在 `scripts/backtest/` 下新建 `.py` 文件
2. 按官方模板定义回调函数：`init`、`before_trading`、`handle_bar`、`after_trading`
3. 在 `__main__` 块中导入配额保护配置并运行

官方回调函数签名详见 [RQAlpha Plus 文档](../docs/rqalpha-plus/RQALPHA_PLUS_DOCS.md)。
