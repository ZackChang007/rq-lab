# 聚宽与米筐因子研究高级功能调研报告

> 2026-04-25 | 因子挖掘、合成、组合分析、回测对接

---

## 一、调研结论摘要

| 调研方向 | 聚宽 (JoinQuant) | 米筐 (Ricequant) | 结论 |
|----------|------------------|------------------|------|
| **因子挖掘工具** | ❌ 无自动挖掘 | ❌ 无自动挖掘 | 均需用户自行定义因子 |
| **因子合成功能** | ✅ Factor类组合 | ✅ 表达式合成 | 米筐更简洁直观 |
| **多因子组合分析** | ✅ neutralize() 支持10种风格因子 | ✅ Neutralization 支持9种风格因子 | 功能相当 |
| **共线性去除** | ⚠️ 中性化间接实现 | ⚠️ 中性化间接实现 | 均无显式正交化函数 |
| **因子回测对接** | ❌ 无一键对接 | ❌ 无一键对接 | 均需手动桥接 |

---

## 二、因子挖掘工具

### 2.1 平台能力分析

**聚宽与米筐均不提供自动因子挖掘工具**。

两家平台提供的都是"因子定义 + 检验"框架，而非"自动发现有效因子"的工具：

| 平台 | 提供能力 | 不提供能力 |
|------|----------|------------|
| 聚宽 | 因子类定义、内置因子库(300+)、因子检验 | 自动挖掘、遗传规划、符号回归 |
| 米筐 | 因子表达式、内置因子库(100+)、因子检验 | 自动挖掘、因子搜索、机器学习生成 |

### 2.2 用户需要自行实现

因子挖掘需要用户：
1. **提出假设**：基于金融逻辑或文献
2. **定义因子**：使用平台框架编写代码
3. **检验因子**：使用平台提供的 IC 分析、分组收益等工具

**结论**：如果需要自动因子挖掘，需借助第三方工具（如 Genetic Programming、Symbolic Regression）或自研算法，不在平台功能范围内。

---

## 三、因子合成功能

### 3.1 米筐因子合成

**表达式合成方式**（更简洁直观）：

```python
from rqfactor import Factor

# 简单相加合成
f1 = Factor('pe_ratio')
f2 = Factor('pb_ratio')
f3 = Factor('return_on_equity')
composite = 1/f1 + 1/f2 + f3  # 低PE + 低PB + 高ROE

# F-Score 九因子合成示例（Piotroski F-Score）
f1 = Fillter(Factor('return_on_asset_ttm'))
f2 = Fillter(Factor('net_profit_mrq_0')/Factor('total_assets_mrq_0')-...)
# ... 共 9 个因子
f_score = f1 + f2 + f3 + f4 + f5 + f6 + f7 + f8 + f9
```

**支持的合成运算符**：

| 运算符 | 说明 |
|--------|------|
| `+`, `-`, `*`, `/` | 四则运算 |
| `**` | 幂运算 |
| `//`, `%` | 整除、取模 |
| `>`, `<`, `>=`, `<=` | 比较运算 |
| `&`, `\|`, `~` | 逻辑运算 |

### 3.2 聚宽因子合成

**Factor 类继承方式**（面向对象）：

```python
from jqfactor import Factor

class CompositeFactor(Factor):
    name = 'composite_factor'
    max_window = 1
    dependencies = ['pe_ratio', 'pb_ratio', 'roe_ttm']
    
    def calc(self, data):
        pe = data['pe_ratio']
        pb = data['pb_ratio']
        roe = data['roe_ttm']
        # 合成逻辑
        return (1/pe + 1/pb + roe).mean()
```

### 3.3 对比结论

| 维度 | 聚宽 | 米筐 |
|------|------|------|
| 合成方式 | 类继承 + calc 方法 | 表达式直接运算 |
| 代码量 | 较多（需定义类） | 较少（一行表达式） |
| 灵活性 | 高（可在 calc 中实现复杂逻辑） | 中（依赖内置算子） |
| 学习曲线 | 较陡 | 平缓 |

**推荐**：简单因子合成优先使用米筐表达式，复杂逻辑可考虑聚宽类继承方式。

---

## 四、多因子组合分析

### 4.1 中性化功能（共线性处理的间接方式）

两家平台都通过"中性化"功能间接处理因子共线性问题，而非显式的正交化函数。

#### 米筐 Neutralization

```python
from rqfactor.testing import Neutralization

# 行业 + 风格因子中性化
engine.append(('neutralization', Neutralization(
    industry='sws',  # 申万一级行业
    style_factors=['size', 'beta', 'momentum', 'liquidity', 
                   'earnings_yield', 'growth', 'leverage', 
                   'book_to_price', 'residual_volatility']
)))
```

**支持的 9 种风格因子**：
- size（市值）
- beta（贝塔）
- momentum（动量）
- liquidity（流动性）
- earnings_yield（盈利收益）
- growth（成长）
- leverage（杠杆）
- book_to_price（账面市值比）
- residual_volatility（残差波动率）

#### 聚宽 neutralize()

```python
from jqfactor import neutralize

# 行业市值中性化
neutralize(data, how=['jq_l1', 'market_cap'], date='2018-05-02', axis=1)

# 风格因子中性化（10种）
neutralize(data, how=['size', 'beta', 'momentum', 'residual_volatility', 
                      'non_linear_size', 'book_to_price_ratio', 
                      'liquidity', 'earnings_yield', 'growth', 'leverage'], 
           date='2018-05-02')
```

### 4.2 共线性处理方式

**平台提供的方式**：

| 方式 | 说明 | 效果 |
|------|------|------|
| 风格因子中性化 | 剥离个股对风格因子的暴露 | 间接降低共线性 |
| 行业中性化 | 剥离行业效应 | 降低行业相关因子的共线性 |
| 回归残差 | `CS_REGRESSION_RESIDUAL(Y, *X)` | 米筐提供，用其他因子残差 |

**米筐横截面回归残差算子**：

```python
from rqfactor import CS_REGRESSION_RESIDUAL

# 使用其他因子做回归，取残差作为正交化后的因子
f_orthogonal = CS_REGRESSION_RESIDUAL(f1, f2, f3)  # f1 对 f2, f3 回归取残差
```

### 4.3 未提供的功能

两家平台均**未提供**以下显式共线性处理函数：
- Gram-Schmidt 正交化
- 主成分分析 (PCA)
- 方差膨胀因子 (VIF) 计算
- 条件数计算

**如需这些功能**，需用户自行实现：

```python
# 自实现正交化示例（需在投资研究环境中运行）
import numpy as np
from scipy import stats

def orthogonalize_factors(factor_df):
    """Gram-Schmidt 正交化"""
    factors = factor_df.values
    n_factors = factors.shape[1]
    orthogonal = np.zeros_like(factors)
    
    for i in range(n_factors):
        f = factors[:, i]
        for j in range(i):
            f = f - np.dot(f, orthogonal[:, j]) / np.dot(orthogonal[:, j], orthogonal[:, j]) * orthogonal[:, j]
        orthogonal[:, i] = f
    
    return pd.DataFrame(orthogonal, index=factor_df.index, columns=factor_df.columns)
```

---

## 五、因子回测对接流程

### 5.1 核心问题

**两家平台都没有"一键从因子检验进入回测"的功能**。

因子检验和回测是两个独立模块，需要手动桥接：

```
因子定义 → 因子检验 → [手动对接] → 策略回测
                              ↓
                        将因子逻辑迁移到 handle_bar
```

### 5.2 米筐对接方式

**方式一：在 handle_bar 中实现因子逻辑**

```python
def init(context):
    context.stock_pool = '000300.XSHG'
    context.rebalance_days = 20
    context.days = 0

def handle_bar(context, bar_dict):
    context.days += 1
    if context.days % context.rebalance_days != 0:
        return
    
    # 获取股票池
    stocks = index_components(context.stock_pool)
    
    # 计算因子值（需重新实现因子逻辑）
    pe_values = get_factor(stocks, ['pe_ratio'], count=1)
    
    # 因子打分
    scores = 1 / pe_values['pe_ratio']  # 低PE偏好
    
    # 选股
    selected = scores.nlargest(30).index
    
    # 调仓
    for stock in context.portfolio.positions:
        if stock not in selected:
            order_target_percent(stock, 0)
    for stock in selected:
        order_target_percent(stock, 1.0 / len(selected))
```

**方式二：使用 get_factor() 获取预计算因子**

```python
def handle_bar(context, bar_dict):
    stocks = index_components(context.stock_pool)
    
    # 获取已发布的公共因子或私有因子
    factor_data = get_factor(stocks, ['my_composite_factor'], count=1)
    
    # 选股逻辑...
```

### 5.3 聚宽对接方式

**方式一：在 handle_bar 中实现因子逻辑**

```python
def init(context):
    context.stocks = get_index_stocks('000300.XSHG')
    
def handle_bar(context, bar_dict):
    # 获取财务数据
    q = query(valuation.pe_ratio, valuation.pb_ratio)
    df = get_fundamentals(q)
    
    # 因子合成
    df['score'] = 1/df['pe_ratio'] + 1/df['pb_ratio']
    
    # 选股
    selected = df.nlargest(30, 'score').index
    
    # 调仓
    for stock in context.portfolio.positions:
        if stock not in selected:
            order_target_value(stock, 0)
    for stock in selected:
        order_target_value(stock, context.portfolio.total_value / len(selected))
```

### 5.4 对接难点

| 难点 | 说明 | 解决方案 |
|------|------|----------|
| **逻辑迁移** | 因子定义代码需重写到 handle_bar | 使用 get_factor() 获取预计算值 |
| **时机匹配** | 因子检验的调仓周期与 handle_bar 频率需一致 | 使用 scheduler 或计数器控制 |
| **数据对齐** | 因子值与 bar_dict 时间点需对齐 | 使用 count=1 获取最新值 |
| **停牌处理** | handle_bar 中需判断停牌 | 使用 bar_dict[stock].suspended |

### 5.5 推荐对接流程

```
1. 因子研究阶段：
   - 在因子研究环境中定义因子
   - 检验因子有效性（IC、分组收益）
   - 确定因子方向（ascending）和调仓周期

2. 因子发布阶段（米筐企业版）：
   - 发布因子到产品库
   - 设置预计算参数

3. 回测对接阶段：
   - 在策略中使用 get_factor() 获取因子值
   - 根据因子值排序选股
   - 实现调仓逻辑
```

---

## 六、综合建议

### 6.1 平台选择建议

| 需求场景 | 推荐平台 | 理由 |
|----------|----------|------|
| **因子合成频繁** | 米筐 | 表达式方式更简洁高效 |
| **复杂因子逻辑** | 聚宽 | 类继承方式更灵活 |
| **风格因子中性化** | 两者均可 | 均支持 CNE5 风格因子 |
| **正交化需求** | 需自研 | 两家均无显式函数 |
| **回测对接** | 两者相当 | 均需手动实现 |

### 6.2 工作流建议

```
推荐工作流：

1. 因子研究（米筐因子研究环境）
   ↓
2. 因子检验（FactorAnalysisEngine）
   ↓
3. 因子合成（表达式方式）
   ↓
4. 中性化处理（Neutralization）
   ↓
5. 发布因子（企业版功能）
   ↓
6. 回测策略（RQAlpha Plus）
   ↓
7. get_factor() 获取因子值
   ↓
8. handle_bar 中实现选股逻辑
```

### 6.3 待自行实现的功能

以下功能需要用户自行开发或借助第三方库：

| 功能 | 实现建议 |
|------|----------|
| 因子挖掘 | 遗传规划、符号回归、机器学习 |
| 正交化 | Gram-Schmidt、PCA |
| 共线性检测 | VIF 计算、条件数 |
| 因子权重优化 | 均值方差、风险平价 |
| 多因子 IC 矩阵 | pandas 计算相关系数矩阵 |

---

## 附录：快速参考

### A. 米筐因子合成示例

```python
# 复合因子：低估值 + 高盈利
from rqfactor import Factor, MA, RANK

# 估值因子（低PE、低PB）
valuation = 1/Factor('pe_ratio') + 1/Factor('pb_ratio')

# 盈利因子（高ROE、高ROA）
profitability = Factor('return_on_equity') + Factor('return_on_asset')

# 动量因子
momentum = MA(Factor('close'), 20) / MA(Factor('close'), 60) - 1

# 综合因子（加权合成）
composite = 0.4 * RANK(valuation) + 0.4 * RANK(profitability) + 0.2 * RANK(momentum)
```

### B. 中性化处理示例

```python
# 米筐风格因子中性化
from rqfactor.testing import FactorAnalysisEngine, Neutralization, ICAnalysis

engine = FactorAnalysisEngine()
engine.append(('neutralization', Neutralization(
    industry='sws',
    style_factors=['size', 'beta', 'momentum', 'liquidity']
)))
engine.append(('rank_ic_analysis', ICAnalysis(rank_ic=True)))
result = engine.analysis(factor_df, 'daily', ascending=False, periods=[1, 5, 10])
```

### C. 回测对接示例

```python
# 米筐回测中使用因子
def init(context):
    context.factors = ['pe_ratio', 'pb_ratio', 'return_on_equity']
    context.stock_pool = '000300.XSHG'
    scheduler.run_monthly(rebalance, tradingday=1)

def rebalance(context, bar_dict):
    stocks = index_components(context.stock_pool)
    factor_data = get_factor(stocks, context.factors, count=1)
    
    # 因子合成
    factor_data['score'] = (1/factor_data['pe_ratio'] + 
                            1/factor_data['pb_ratio'] + 
                            factor_data['return_on_equity'])
    
    # 选股
    selected = factor_data.nlargest(30, 'score').index
    
    # 调仓
    order_target_portfolio({s: 1/30 for s in selected})
```

---

## 文档版本

- 创建日期：2026-04-25
- 更新日期：2026-04-25
- 状态：调研完成
