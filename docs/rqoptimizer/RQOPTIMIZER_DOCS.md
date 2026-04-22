# RQOptimizer 股票组合优化器文档

> 股票多因子优化器

## 产品概述

RQOptimizer 是米筐为中国 A 股市场开发的股票组合优化器。它计算最优资产权重，以在满足约束和风险管理要求的同时最大化投资效用。

---

## 功能列表

### 目标函数

| 类别 | 内容 |
|------|------|
| 风险类 | 风险最小化、主动风险最小化、跟踪误差最小化 |
| 收益类 | 均值方差、夏普比率最大化、信息比率最大化 |
| 其他 | 风格偏离最小化、风险平价、指标最大化 |

### 约束条件

| 类别 | 内容 |
|------|------|
| 仓位约束 | 个股仓位、行业内仓位 |
| 风格约束 | 风格因子偏离度约束 |
| 行业约束 | 行业权重约束 |
| 其他约束 | 换手率、跟踪误差、基准成分股比例 |

### 特色功能

- 投资白名单选股
- 股票优先级设置
- 自定义基准
- 因子优先级设置
- 软/硬约束设置
- 多种行业分类（中信一级、申万一级、申万一级非银金融细分）

---

## 风险模型

使用米筐多因子风险模型（v1 和 v2），支持：
- 日度、月度、季度风险预测周期
- 与自定义因子和 RQFactor 多因子研究系统集成

---

## 推荐使用场景

| 场景 | 推荐方法 |
|------|----------|
| 有Alpha因子需风控 | 指标最大化 + 风格/行业/个股约束 |
| 风格/行业增强 | 指标最大化 + 增强风险因子偏离约束 |
| 主观选股 | 方差最小化 + 风格/行业中性 + 个股约束 |
| 无选股因子的Smart Beta | 选股API + 风格偏离最小化 + 行业约束 |
| 指数增强 | 跟踪误差最小化 + 风格/行业中性 + 基准成分股约束 |
| 低成本指数跟踪 | 跟踪误差最小化 + 换手约束 |
| 市场下跌风险控制 | 方差或跟踪误差最小化 + 风格/行业中性 |

---

## 核心特性

### 选股功能

- 指数增强策略的股票优先级设置
- 支持自定义基准（股票指数或用户自定义）
- 软约束和硬约束设置

### 行业分类支持

- 中信一级（CITIC L1）
- 申万一级（Shenwan L1）
- 申万一级非银金融细分

---

## 文档链接

- 快速上手指南
- 代码示例
- API 参考（选股 API、优化器 API）

---

## 典型工作流程

### 1. 指标最大化优化

适用于有明确Alpha因子的场景：

```python
# 伪代码示例
optimizer.objective = 'maximize_indicator'
optimizer.constraints = {
    'style': {...},      # 风格约束
    'industry': {...},   # 行业约束
    'position': {...}    # 个股仓位约束
}
result = optimizer.optimize()
```

### 2. 跟踪误差最小化

适用于指数增强或被动跟踪：

```python
# 伪代码示例
optimizer.objective = 'minimize_tracking_error'
optimizer.constraints = {
    'benchmark': '000300.XSHG',  # 沪深300
    'tracking_error': 0.02,       # 2%跟踪误差上限
    'turnover': 0.3               # 30%换手率上限
}
result = optimizer.optimize()
```

### 3. 风险平价

适用于风险均衡配置：

```python
# 伪代码示例
optimizer.objective = 'risk_parity'
optimizer.constraints = {
    'position': {'min': 0, 'max': 0.05}  # 个股权重限制
}
result = optimizer.optimize()
```

---

## 与其他组件集成

### 与 RQFactor 集成

```python
# 使用RQFactor生成的因子作为优化输入
from rqfactor import Factor, execute_factor

factor_data = execute_factor(custom_factor, stock_pool, start_date, end_date)
# 将factor_data传入优化器
```

### 与 RQAlpha Plus 集成

```python
# 在策略中使用优化器调整仓位
def rebalance(context, bar_dict):
    # 获取优化结果
    target_weights = optimizer.optimize(...)
    # 执行调仓
    order_target_portfolio(target_weights)
```

---

## 注意事项

1. **数据要求**: 需要订阅 RQData 获取股票数据和因子数据
2. **风险模型**: 建议理解多因子风险模型的因子定义和计算方式
3. **约束设置**: 过多约束可能导致无可行解，需合理设置
4. **性能**: 大规模股票池优化可能需要较长时间
