# RQPAttr 归因分析文档

> 业绩归因分析工具，基于 Brinson 行业归因和多因子风险模型

## 概述

RQPAttr 是米筐开发的业绩归因分析工具，用于分解投资组合收益来源，评估投资策略的主要收益及风险来源。支持两大归因模型：

1. **Brinson 行业归因** - 将主动收益分解为配置收益和选择收益
2. **因子归因** - 基于多因子风险模型，分解风格偏好、行业偏好、市场联动和特异收益

---

## 安装

```bash
rqsdk install rqpattr
```

依赖：`rqdatac`（RQData 数据 API）

---

## API 参考

### performance_attribute

```python
from rqpattr.api import performance_attribute

performance_attribute(
    model,
    daily_weights,
    daily_return=None,
    benchmark_info=None
)
```

#### 必填参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `model` | str 或 str list | 归因模型类型，可选：`"equity/brinson"`、`"equity/factor"`、`"equity/factor_v2"` |
| `daily_weights` | pd.Series | 每日每个合约的权重，index 为 `['date', 'order_book_id', 'asset_type']`，值为 weight。`asset_type` 支持 `'stock'` 和 `'cash'` |

#### 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `daily_return` | pd.Series | 每日总收益率，index 为 `date`，值为收益率。起始日期为权重的下一个交易日，结束日期为权重结束时间的下一个交易日 |
| `benchmark_info` | dict | 基准信息，无则默认上证300。支持4种类型（见下方） |
| `leverage_ratio` | pd.Series 或 float | 杠杆率，组合收益率当日的杠杆率 |
| `standard` | str | Brinson 行业归因标准，可选：`'sws'`（申万）、`'citics'`（中信） |
| `special_assets_return` | pd.Series | index 为 `date, order_book_id`，value 为 return，为真实组合收益率 |

#### 基准类型

```python
# 1. 指数基准
benchmark_info = {'type': 'index', 'name': '沪深300', 'detail': '000300.XSHG'}

# 2. 混合指数基准
benchmark_info = {'type': 'mixed_index', 'name': '20%沪深300+80%上证综指',
                  'detail': {'000300.XSHG': 0.2, '000008.XSHG': 0.8}}

# 3. 收益率基准
benchmark_info = {'type': 'yield_rate', 'name': '1年期国债', 'detail': 'YIELD1Y'}

# 4. 零收益现金
benchmark_info = {'type': 'cash', 'name': '零收益现金', 'detail': 0.0}
```

> `name` 为可选字段。

#### daily_return 日期说明

`daily_weights` 的 date 每一项都向后取一个交易日即为 `daily_return` 的日期。

#### 返回值

dict，包含以下内容：

| 键 | 类型 | 说明 |
|-----|------|------|
| `returns_decomposition` | list | 混合资产 Brinson 归因（树状结构） |
| `attribution` | dict | 根据选择的模型返回归因结果（见下方） |
| `excel_report` | dict | 收益趋势报告 |

#### attribution 返回结构

**`"equity/brinson"` 模型：**
- Brinson 归因结果

**`"equity/factor"` 或 `"equity/factor_v2"` 模型：**

| 键 | 说明 |
|-----|------|
| `factor_attribution` | 各因子对投资组合与基准组合收益贡献 |
| `factor_exposure` | 投资组合与基准组合对因子的风险暴露 |
| `sensitivity` | 敏感度分析 |

---

## 归因模型详解

### 1. 混合资产 Brinson 归因

采用无交互作用项、BHB 形式的 Brinson 模型，对混合型投资组合的收益进行归因。四级分解结构：

```
总收益
├── 交易收益         ← 成交价与日终价差 + 交易费用
├── 杠杆收益         ← 杠杆带来的收益
└── 持仓收益         ← 日终价格变化
    ├── 主动收益     ← 组合相对基准的超额收益
    │   ├── 股票收益
    │   │   ├── 股票配置收益  ← 超配/低配行业
    │   │   └── 股票选择收益  ← 行业内选股
    │   ├── 期货收益
    │   ├── 可转债收益
    │   ├── 基金收益
    │   ├── 现金收益
    │   └── ...
    └── 基准持仓收益
        ├── 基准收益
        └── 穿透效应
```

| 归因项 | 说明 |
|--------|------|
| 交易收益 | 交易成交价和日终价格之间的价差，以及交易费用所产生的收益 |
| 持仓收益 | 日终价格变化所带来的收益 |
| 主动收益 | 投资组合相对于基准的收益差 |
| 配置收益 | 投资组合相对于基准超配/低配某一类资产所产生的超额收益 |
| 选择收益 | 在各类资产中，投资组合相对于基准选择不同标的所产生的超额收益 |

使用联接算法，保证归因项之和等于累积持仓主动收益。

---

### 2. 股票行业 Brinson 归因

采用 BF 版本、无交互作用项的 Brinson 模型，对股票的行业收益进行"配置-选股"分解：

- **配置收益**：基于行业走势调整行业权重所带来的主动收益
- **选择收益**：在行业内挑选优质个股所带来的主动收益
- **现金**作为特殊板块与行业并列，现金板块的主动收益反映大盘择时收益

BF 归因公式：

```
配置收益 = Σ (w_p,i - w_b,i) × (r_b,i - r_b)

选择收益 = Σ w_p,i × (r_p,i - r_b,i)
```

其中：
- `w_p,i` 和 `w_b,i` 分别为投资组合和基准中资产 i 的权重
- `r_p,i` 和 `r_b,i` 分别为投资组合和基准中资产 i 的收益
- `r_b` 为基准收益（各类资产加权平均）

---

### 3. 因子归因

多因子风险模型将股票组合收益分解为四个来源：

| 收益来源 | 说明 |
|----------|------|
| **风格偏好** | 市值、盈利性、成长性、动量等共同风格因素。例如偏好小市值股票，小市值表现优异则带来超额收益 |
| **行业偏好** | 偏好某行业，该行业总体优于其他行业则带来超额收益 |
| **市场联动** | 股票市场整体涨落的影响。股票仓位比例越高，市场联动影响越大 |
| **特异收益** | 影响个股收益的特殊因素（管理层变动、政策优惠等） |

因子分解公式：

```
r_p^A = Σ X_i^A × f_i + μ^A
```

其中：
- `r_p^A` 为投资组合主动收益
- `X_i^A` 为投资组合对因子 i 的主动暴露度 `(X_p,i - X_b,i)`
- `f_i` 为因子 i 的因子收益
- `μ^A` 为投资组合主动残余收益 `(μ_p - μ_b)`

基于 MSCI Barra X-Sigma-Rho 归因模型，因子主动风险归因：

```
σ(r_p^A) = Σ X_i^A × σ(f_i) × ρ(f_i, r_p^A) + σ(μ^A) × ρ(μ^A, r_p^A)
```

因子对主动风险的贡献取决于：
1. **因子主动暴露度** `X_i^A` - 投资组合的因子风险暴露偏离基准的程度
2. **因子收益波动率** `σ(f_i)` - 市场风格/行业轮动变化带来的被动风险
3. **相关性** `ρ(f_i, r_p^A)` - 投资组合收益和因子表现的风险联动程度

---

## 代码示例

### 基本使用流程

该示例使用 RQAlpha Plus 回测结果作为输入数据。

```python
import pandas as pd
import rqdatac
import rqpattr
from rqpattr.api import performance_attribute

rqdatac.init()

# 1. 读取回测结果
result = pd.read_pickle('backtest_result.pkl')
positions = result['sys_analyser']['stock_positions']
portfolio = result['sys_analyser']['portfolio']

# 2. 准备权重数据
positions = positions.join(portfolio['total_value'])
positions['asset_type'] = 'stock'
positions = positions.reset_index()
positions = positions.set_index(['date', 'order_book_id', 'asset_type'])
weights = positions['market_value'] / positions['total_value']

# 3. 准备收益率数据
daily_return = portfolio['unit_net_value'].pct_change().dropna()

# 4. 执行归因分析
result = rqpattr.performance_attribute(
    model="equity/factor_v2",
    daily_weights=weights,
    daily_return=daily_return,
    benchmark_info={'type': 'index', 'name': '中证800', 'detail': '000906.XSHG'}
)
```

### 查看混合资产 Brinson 归因

```python
result['returns_decomposition']
# 返回树状结构：
# [{'factor': '总收益',
#   'value': 0.2037,
#   'children': [
#     {'factor': '交易收益', 'value': -0.0258, 'children': None},
#     {'factor': '杠杆收益', 'value': 0.0, 'children': None},
#     {'factor': '持仓收益', 'value': 0.2295,
#      'children': [
#        {'factor': '主动收益', 'value': 0.0663,
#         'children': [
#           {'factor': '股票收益', 'value': 0.0663,
#            'children': [
#              {'factor': '股票配置收益', 'value': 0.000003, 'children': None},
#              {'factor': '股票选择收益', 'value': 0.0663, 'children': None}
#            ]},
#           ...
#         ]},
#        {'factor': '基准持仓收益', 'value': 0.1632, ...}
#      ]}
#   ]}]
```

### 查看因子归因结果

```python
# 因子归因详情
factor_attr = pd.DataFrame(
    result['attribution']['factor_attribution'][0]['factors']
)

# 因子主动暴露度
print(factor_attr[['factor', 'active_exposure']])

# 因子主动收益
print(factor_attr[['factor', 'active_return']])
```

### 可视化因子归因

```python
import matplotlib.pyplot as plt

style_factor_attr = pd.DataFrame(
    result['attribution']['factor_attribution'][0]['factors']
)

# 组合风格因子主动暴露
plt.figure()
style_factor_attr.set_index('factor')['active_exposure'].plot(
    kind='bar', figsize=(15, 7), legend='active_exposure', fontsize=15
)

# 组合因子主动收益（%）
plt.figure()
(style_factor_attr.set_index('factor')['active_return'] * 100).plot(
    kind='bar', figsize=(15, 7), legend='active_return', fontsize=15
)
```

### 多模型混合归因

```python
# 同时运行 Brinson 和因子归因
result = rqpattr.performance_attribute(
    model=["equity/brinson", "equity/factor_v2"],
    daily_weights=weights,
    daily_return=daily_return,
    benchmark_info={'type': 'index', 'detail': '000300.XSHG'},
    standard='sws'  # 申万行业分类
)

# 访问 Brinson 归因
result['attribution']['equity/brinson']

# 访问因子归因
result['attribution']['equity/factor_v2']
```

---

## 与其他组件集成

### 与 RQAlpha Plus 集成

```python
# 回测完成后直接归因
from rqalpha_plus import run_func
import rqpattr

# 运行回测
backtest_result = run_func(config=config, init=init, handle_bar=handle_bar)

# 提取数据
positions = backtest_result['sys_analyser']['stock_positions']
portfolio = backtest_result['sys_analyser']['portfolio']

# 准备权重和收益
positions = positions.join(portfolio['total_value'])
positions['asset_type'] = 'stock'
positions = positions.reset_index().set_index(['date', 'order_book_id', 'asset_type'])
weights = positions['market_value'] / positions['total_value']
daily_return = portfolio['unit_net_value'].pct_change().dropna()

# 归因分析
attr_result = rqpattr.performance_attribute(
    model="equity/factor_v2",
    daily_weights=weights,
    daily_return=daily_return,
    benchmark_info={'type': 'index', 'detail': config['mod']['sys_analyser']['benchmark']}
)
```

---

## 注意事项

1. **数据依赖**: 需要 RQData 订阅获取股票数据和因子数据
2. **daily_return 日期对齐**: 收益率的起始日期须为权重起始日期的下一个交易日
3. **权重格式**: index 必须为 `['date', 'order_book_id', 'asset_type']` 三级 MultiIndex
4. **基准选择**: 因子归因需要基准数据，建议使用与回测相同的基准指数
5. **模型选择**: `factor_v2` 为因子归因升级版本，推荐使用

---

## 文档链接

- API 文档: https://www.ricequant.com/doc/sources/rqpattr/api/pattr-api.md
- 归因模型详解: https://www.ricequant.com/doc/sources/rqpattr/doc/model-introduction.md
- 代码示例: https://www.ricequant.com/doc/sources/rqpattr/doc/example.md
