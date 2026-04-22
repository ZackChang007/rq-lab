# RQFactor 进阶理解

## 数据处理规范

### 复权处理

价格类因子对应后复权价格，`_unadjusted` 后缀提供不复权数据。建议因子输出为无量纲数值。

### 停牌处理

因子计算引擎在计算因子值时，会自动过滤停牌期间的数据；计算完成后，将停牌日期对应的因子值填充为 NaN。

### NaN 及 Inf 处理

横截面算子中 Inf 与 NaN 处理方式一致。

---

## 自定义算子

### 非横截面算子（时间序列处理）

**简单算子：** `CombinedFactor(func, *factors)` - 仅依赖当期值

**滑动窗口算子：** `RollingWindowFactor(func, window, factor)` - 单因子输入

**多因子滑动窗口：** `CombinedRollingWindowFactor(func, window, *factors)`

示例 - 实现 `MY_EMA` 指数加权平均算子：

```python
from rqfactor.extension import RollingWindowFactor

def my_ema(series, window):
    """指数加权平均"""
    weights = np.exp(np.linspace(-1, 0, window))
    weights /= weights.sum()
    return np.convolve(series, weights, mode='valid')[-1]

def MY_EMA(f, window):
    return RollingWindowFactor(my_ema, window, f)

# 使用
factor = MY_EMA(Factor('close'), 20)
```

### 横截面算子

**单因子横截面：** `UnaryCrossSectionalFactor(func, factor)`

**多因子横截面：** `CombinedCrossSectionalFactor(func, *factors)`

横截面算子输入为 DataFrame，index 为交易日，columns 为股票代码。

示例 - 实现自定义横截面标准化：

```python
from rqfactor.extension import UnaryCrossSectionalFactor

def my_standardize(df):
    """自定义标准化：减均值除标准差"""
    return (df - df.mean(axis=1)) / df.std(axis=1)

# 使用
factor = UnaryCrossSectionalFactor(my_standardize, Factor('pe_ratio'))
```

---

## 自定义基础因子

使用 `UserDefinedLeafFactor(name, func)` 创建，func 返回 DataFrame 需满足：

- index 为 `pd.DatetimeIndex` 类型
- column 为 order_book_id
- 仅包含交易日

示例：

```python
from rqfactor import UserDefinedLeafFactor
import pandas as pd
import rqdatac

def my_custom_data(order_book_ids, start_date, end_date):
    """获取自定义数据"""
    data = rqdatac.get_price(order_book_ids, start_date, end_date, fields='close')
    # 进行自定义处理
    processed = data.pct_change()
    return processed

# 创建因子
MyFactor = UserDefinedLeafFactor('my_factor', my_custom_data)

# 使用
result = execute_factor(MyFactor, ['000001.XSHE'], '20200101', '20201231')
```

---

## 因子缓存

### CachedExecContext.init

在计算大量因子时，可缓存必要数据，避免重复从 rqdatac 获取。

缓存数据包括：日行情因子（默认前复权）、财务因子、Alpha101 因子、技术指标。

```python
from rqfactor.exec_context import CachedExecContext

# 初始化缓存
CachedExecContext.init(
    order_book_ids,
    start_date,
    end_date,
    leaves=[Factor('close'), Factor('volume')]  # 指定的叶子因子
)

# 使用缓存执行因子
execute_factor(
    Factor('close'),
    order_book_ids,
    start_date,
    end_date,
    exec_context_class=CachedExecContext
)
```

---

## 因子检验进阶

### 多周期检验

```python
# 同时检验多个调仓周期
result = engine.analysis(
    factor_data,
    returns,
    ascending=True,
    periods=[1, 5, 10],  # 日、周、半月
    keep_preprocess_result=True
)
```

### 自定义收益计算

```python
# 使用自定义收益数据
custom_returns = calculate_custom_returns(factor_data)
result = engine.analysis(factor_data, custom_returns, ascending=True, periods=1)
```

### 行业分类选择

```python
# 使用中信行业分类
engine.append(('ic_analysis', ICAnalysis(industry_classification='citics_2019')))

# 使用申万行业分类
engine.append(('ic_analysis', ICAnalysis(industry_classification='sws')))

# 不做行业分析
engine.append(('ic_analysis', ICAnalysis(industry_classification=None)))
```

### 风格中性化

```python
from rqfactor.testing import Neutralization

# 对特定风格因子中性化
engine.append(('neutralization', Neutralization(
    industry='sws',
    style_factors=['size', 'beta', 'momentum', 'liquidity']
)))
```

---

## 因子表达式

### 前缀表达式

因子内部以逆波兰表示法（RPN）存储：

```python
f = Factor('close') / Factor('open')
print(f.expr)  # 显示前缀表达式树
```

### 依赖追踪

```python
f = MA(Factor('close'), 5) / MA(Factor('volume'), 5)
print(f.dependencies)  # 列出所有叶子因子
```

---

## 性能优化

### 批量计算

计算多个因子时，先初始化缓存：

```python
factors = [
    MA(Factor('close'), 5),
    MA(Factor('close'), 10),
    MA(Factor('close'), 20),
]

# 一次性初始化缓存
CachedExecContext.init(order_book_ids, start_date, end_date)

# 批量计算
results = {}
for f in factors:
    results[f] = execute_factor(f, order_book_ids, start_date, end_date,
                                 exec_context_class=CachedExecContext)
```

### 窄化数据范围

```python
# 只计算指定股票池
execute_factor(f, order_book_ids, start_date, end_date, universe='000300.XSHG')
```
