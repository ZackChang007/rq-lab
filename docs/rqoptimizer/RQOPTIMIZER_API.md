# RQOptimizer API 参考

> 股票组合优化器 API 详细文档

## 安装

```bash
rqsdk install rqoptimizer
rqsdk update rqoptimizer
```

---

## 选股 API

### stock_select

```python
stock_select(pool, targets, date, score, benchmark=None)
```

从投资组合备选股票池中根据优先级和得分选出目标股票。

| 参数 | 类型 | 说明 |
|------|------|------|
| pool | pandas.Series | 投资组合备选股票池。index为股票代码，value为股票优先级系数（0-2，0为最高优先级） |
| targets | list | 选股目标列表 |
| date | string | 日期 |
| score | - | 个股评分 |
| benchmark | string | 基准组合，默认None。支持指数代码如 '000300.XSHG'、'000905.XSHG' |

**返回：** List of stock codes

---

## 组合优化 API

### portfolio_optimize

```python
portfolio_optimize(order_book_ids, date, objective=MinVariance(),
                   bnds=None, cons=None, benchmark=None,
                   cov_model=CovModel.FACTOR_MODEL_DAILY)
```

计算最优投资组合权重。

| 参数 | 类型 | 说明 |
|------|------|------|
| order_book_ids | list | 股票代码列表 |
| date | string | 日期 |
| objective | Objective | 优化目标函数，默认 MinVariance() |
| bnds | dict | 个股仓位约束 |
| cons | list | 约束条件列表 |
| benchmark | string | 基准组合，默认 None |
| cov_model | CovModel | 协方差估计模型，默认 FACTOR_MODEL_DAILY |

**返回：** pandas.Series - 优化权重（index为order_book_ids，value为归一化的优化权重）

---

## 目标函数

| 目标函数 | 说明 |
|----------|------|
| `MinVariance()` | 风险最小化 |
| `MeanVariance()` | 均值方差优化 |
| `RiskParity()` | 风险平价 |
| `MinTrackingError()` | 跟踪误差最小化 |
| `MaxInformationRatio()` | 信息比率最大化 |
| `MaxSharpeRatio()` | 夏普比率最大化 |
| `MaxIndicator()` | 指标最大化 |
| `MinStyleDeviation()` | 风格偏离最小化 |

---

## 约束条件

| 约束类型 | 说明 |
|----------|------|
| `TrackingErrorLimit` | 跟踪误差约束 |
| `TurnoverLimit` | 换手率约束 |
| `BenchmarkComponentWeightLimit` | 基准成分股权重约束 |
| `IndustryConstraint` | 行业约束 |
| `StyleConstraint` | 风格约束 |

---

## 协方差模型

| 模型 | 说明 |
|------|------|
| `CovModel.FACTOR_MODEL_DAILY` | 日度因子模型（默认） |
| `CovModel.FACTOR_MODEL_MONTHLY` | 月度因子模型 |
| `CovModel.FACTOR_MODEL_QUARTERLY` | 季度因子模型 |

---

## 典型使用场景

### 1. 指标最大化（有Alpha因子）

```python
from rqoptimizer import *

# 设置优化目标和约束
result = portfolio_optimize(
    order_book_ids=stock_list,
    date='2023-01-01',
    objective=MaxIndicator(scores),
    bnds={'weight': (0, 0.05)},  # 个股权重上限5%
    cons=[
        IndustryConstraint(neutral=True),      # 行业中性
        StyleConstraint(neutral=True),          # 风格中性
    ],
    benchmark='000300.XSHG',
    cov_model=CovModel.FACTOR_MODEL_DAILY
)
```

### 2. 跟踪误差最小化（指数增强）

```python
result = portfolio_optimize(
    order_book_ids=stock_list,
    date='2023-01-01',
    objective=MinTrackingError(),
    cons=[
        TrackingErrorLimit(upper=0.02),         # 跟踪误差上限2%
        IndustryConstraint(neutral=True),       # 行业中性
        StyleConstraint(neutral=True),           # 风格中性
        BenchmarkComponentWeightLimit(min=0.8), # 基准成分股权重下限80%
    ],
    benchmark='000300.XSHG'
)
```

### 3. 风险平价

```python
result = portfolio_optimize(
    order_book_ids=stock_list,
    date='2023-01-01',
    objective=RiskParity(),
    bnds={'weight': (0, 0.1)}
)
```

### 4. 选股 + 优化组合

```python
# 先选股
selected = stock_select(
    pool=stock_pool,
    targets=target_list,
    date='2023-01-01',
    score=alpha_scores,
    benchmark='000300.XSHG'
)

# 再优化
result = portfolio_optimize(
    order_book_ids=selected,
    date='2023-01-01',
    objective=MaxIndicator(alpha_scores),
    cons=[
        IndustryConstraint(neutral=True),
        StyleConstraint(neutral=True),
    ],
    benchmark='000300.XSHG'
)
```

---

## 与 RQFactor 集成

```python
from rqfactor import Factor, execute_factor

# 使用RQFactor生成因子数据
factor_data = execute_factor(custom_factor, stock_pool, start_date, end_date)

# 将因子得分传入优化器
scores = factor_data.iloc[-1]  # 最新一期因子值
result = portfolio_optimize(
    order_book_ids=scores.index.tolist(),
    date=end_date,
    objective=MaxIndicator(scores),
    benchmark='000300.XSHG'
)
```

---

## 与 RQAlpha Plus 集成

```python
def rebalance(context, bar_dict):
    # 定期调仓
    stock_pool = rqdatac.index_components('000300.XSHG', context.now.date())
    scores = calculate_alpha(stock_pool)
    weights = portfolio_optimize(
        order_book_ids=stock_pool,
        date=context.now.strftime('%Y-%m-%d'),
        objective=MaxIndicator(scores),
        benchmark='000300.XSHG'
    )
    # 执行调仓
    order_target_portfolio(weights.to_dict())
```

---

## 注意事项

1. **数据依赖**: 需要 RQData 订阅获取股票数据和因子数据
2. **风险模型**: 建议理解米筐多因子风险模型的因子定义和计算方式
3. **约束设置**: 过多约束可能导致无可行解，需合理设置
4. **性能**: 大规模股票池优化可能需要较长时间
5. **权重归一化**: 返回权重已归一化，所有权重之和为1
