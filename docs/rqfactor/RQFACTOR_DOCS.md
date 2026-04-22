# RQFactor 因子投研工具文档

> 因子编写及检验框架

## 概述

RQFactor 是米筐开发的量化因子研究框架，是连接"投资逻辑"与"量化策略"的核心工具。它解决了传统因子开发的三大痛点：

1. **数据处理繁琐** - 自动处理复权、停牌、缺失值
2. **计算逻辑重复** - 内置算子如 `MA(Factor('close'), 5)` 快速生成因子
3. **有效性检验复杂** - 集成 IC 分析、分组收益验证、多日调仓

---

## 基本概念

### 因子 (Factor)

因子是用于选股的指标，每个交易日每个股票计算一次。两类因子：

| 类型 | 说明 | 示例 |
|------|------|------|
| **基础因子** | 直接从财务报表或交易所数据获取 | 行情因子、财务因子 |
| **复合因子** | 通过算子组合基础因子构建 | 横截面因子、非横截面因子 |

### 算子 (Operator)

算子用于转换/组合因子：

| 前缀 | 类型 |
|------|------|
| `CS_` | 横截面算子 |
| `TS_` | 时间序列算子 |
| 无前缀 | 简单算子 |

### 因子检验

验证因子有效性，使用 IC (Information Coefficient) - 因子值与未来收益的相关性。

---

## 快速开始

### 简单因子示例

```python
from rqfactor import *

# 定义因子
f = (Factor('close') - Factor('open')) / (Factor('high') - Factor('low'))

# 查看依赖
f.dependencies  # Returns: [Factor('close'), Factor('open'), ...]

# 查看表达式树
f.expr  # Returns prefix expression tree

# 执行因子计算
execute_factor(f, ['000001.XSHE', '600000.XSHG'], '20180101', '20180201')
```

### 因子检验流程

**1. 计算基础因子：**
```python
import rqdatac
rqdatac.init()

f = Factor('pe_ratio_ttm')
ids = rqdatac.index_components('000300.XSHG', d1)
df = execute_factor(f, ids, d1, d2)
```

**2. 计算自定义收益：**
```python
price = rqdatac.get_price(ids, d1, d2, frequency='1m', fields='close')
target = datetime.time(14, 0)
mask = price.index.get_level_values('datetime').time == target
returns = price[mask].pct_change()
```

**3. 构建检验管道：**
```python
engine = FactorAnalysisEngine()
engine.append(('winzorization-mad', Winzorization(method='mad')))
engine.append(('rank_ic_analysis', ICAnalysis(rank_ic=True, industry_classification='sws')))

result = engine.analysis(df, returns, ascending=True, periods=1, keep_preprocess_result=True)
result['rank_ic_analysis'].summary()
result['rank_ic_analysis'].show()  # 可视化结果
```

**关键 `analysis()` 参数：**
- `df`: 因子值 DataFrame
- `returns`: 与因子时间范围/股票池匹配的收益数据
- `ascending`: True 表示因子越小越好（如 PE-TTM）
- `periods`: 调仓周期（1 = 日频）
- `keep_preprocess_result`: 是否保留预处理数据

---

## 内置因子

### 行情因子

```python
from rqfactor import *
Factor('factor_name')
```

| 因子 | 类型 | 描述 |
|------|------|------|
| open | float | 开盘价 |
| close | float | 收盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| total_turnover | float | 总成交额 |
| volume | float | 总成交量 |
| num_trades | float | 成交笔数 |

### 财务因子

参见：基础财务因子、财务衍生指标因子文档

### Alpha101 因子

参见：alpha101 因子文档

### 技术指标

参见：技术指标因子文档

### 使用示例

```python
# 行情因子
def compute():
    return Factor('open') + Factor('close')

# 财务因子
def compute():
    return Factor('pe_ratio')

# 技术指标
def compute():
    return KDJ_K

# 自定义财务因子
def compute():
    return 1/Factor('pe_ratio') + 1/Factor('pb_ratio') + Factor('return_on_equity')
```

---

## 内置算子

### 数学符号

| 符号 | 含义 |
|------|------|
| `+` | 加法 |
| `-` | 减法 |
| `*` | 乘法 |
| `/` | 除法 |
| `**` | 幂运算 (np.power) |
| `//` | 整除 |
| `%` | 取模 |
| `>` | 大于 |
| `<` | 小于 |
| `>=` | 大于等于 |
| `<=` | 小于等于 |
| `&` | 逻辑与 |
| `\|` | 逻辑或 |
| `~` | 逻辑非 |
| `!=` | 不等于 |

### 简单算子

| 算子 | 描述 |
|------|------|
| `ABS(X)` | 绝对值 |
| `LOG(X)` | 自然对数 |
| `EXP(X)` | e的x次方 |
| `EQUAL(A, B)` | 比较两个因子或因子与常数 |
| `SIGN(X)` | 因子值符号 (np.sign) |
| `SIGNEDPOWER(X, c)` | 保留符号的幂运算，c为常数 |
| `MIN(A, B)` | 两个因子的最小值 |
| `FMIN(A, B)` | 类似MIN，但一个为NaN时返回另一个 |
| `MAX(A, B)` | 两个因子的最大值 |
| `FMAX(A, B)` | 类似MAX，但一个为NaN时返回另一个 |
| `IF(C, A, B)` | C为True返回A，否则返回B |
| `AS_FLOAT(X)` | 转换为浮点类型 |
| `REF(X, n)` | n个交易日前的X值 |
| `DELAY(X, n)` | REF的别名 |
| `DELTA(X, n)` | `X - REF(X, n)` |
| `PCT_CHANGE(X, n)` | `X / REF(X, n) - 1.0` |

### 移动平均算子

| 算子 | 描述 |
|------|------|
| `DMA(X, c)` | 动态移动平均，c为常数权重 |
| `DMA(A, B)` | 因子加权衰减的动态MA |
| `SMA_CN(X, n, m)` | 中式SMA，等于 `DMA(X, m/n)` |
| `SMA(X, n)` | MA的别名 |
| `MA(X, n)` | 简单移动平均 |
| `EMA_CN(X, n)` | 指数MA，等于 `DMA(X, 2/(N+1))` |
| `EMA(X, n)` | 指数移动平均 |
| `WMA(X, n)` | 加权移动平均 (talib 兼容) |
| `DECAY_LINEAR(X, n)` | WMA的别名 |

### 横截面算子

| 算子 | 参数 | 描述 |
|------|------|------|
| `RANK` | `(X, method='average', ascending=True)` | 归一化排名 (rank/count)；NaN返回NaN |
| `SCALE` | `(X, to=1)` | 缩放使绝对值之和等于to |
| `DEMEAN` | `(X)` | 中心化使和为0 |
| `CS_ZSCORE` | `(X)` | 横截面zscore |
| `QUANTILE` | `(X, bins=5, ascending=True)` | 分组；返回组号 |
| `TOP` | `(X, threshold=50, pct=False)` | 前threshold股票返回1，其他0；pct=True使用百分位 |
| `BOTTOM` | `(X, threshold=50, pct=False)` | 类似TOP但为底部排名 |
| `INDUSTRY_NEUTRALIZE` | `(X)` | 行业中性化（申万一级分类） |
| `CS_REGRESSION_RESIDUAL` | `(Y, *X, add_const=True)` | 使用X作为预测变量的回归残差 |
| `CS_FILLNA` | `(X)` | 用行业均值填充缺失值 |
| `FIX` | `(X, order_book_id)` | 返回指定证券的X值 |

### 其他算子

| 算子 | 描述 |
|------|------|
| `AVEDEV(X, n)` | n期内平均绝对偏差 |
| `STD(X, n)` | n期内标准差 |
| `STDDEV(X, n)` | STD的别名 |
| `VAR(X, n)` | n期内方差 |
| `CROSS(A, B)` | A上穿B时返回True |
| `TS_SKEW(X, n)` | n期内偏度 |
| `TS_KURT(X, n)` | n期内峰度 |
| `SLOPE(X, n)` | n期内线性回归斜率 |
| `SUM(X, n)` | n期内求和 |
| `PRODUCT(X, n)` | n期内乘积 |
| `TS_MIN(X, n)` | n期内最小值 |
| `TS_MAX(X, n)` | n期内最大值 |
| `LLV(X, n)` | TS_MIN的别名 |
| `HHV(X, n)` | TS_MAX的别名 |
| `TS_ARGMIN(X, n)` | 最小值位置索引 |
| `TS_ARGMAX(X, n)` | 最大值位置索引 |
| `CORR(A, B, n)` | n期内A与B的相关系数 |
| `CORRELATION(A, B, n)` | CORR的别名 |
| `COVARIANCE(A, B, n)` | n期内A与B的协方差 |
| `COV(A, B, n)` | COVARIANCE的别名 |
| `COUNT(X, n)` | n期内True值计数 |
| `EVERY(X, n)` | n期全部为True返回True |
| `TS_RANK(X, n)` | 当前值在n期内的百分位排名 |
| `TS_ZSCORE(X, n)` | 当前值在n期内的zscore |
| `TS_REGRESSION(Y, X, n)` | n期内回归系数 |
| `TS_FILLNA(X, nv, method='value')` | 填充缺失值：'value'=用nv替换，'MA'=用均值，'forward'=前向填充 |

---

## 自定义算子

`rqfactor.extension` 包提供抽象类和辅助函数用于开发自定义算子。

### 抽象类

**CombinedFactor** - 简单复合算子，接受函数和一个或多个因子进行当期计算。
```python
class CombinedFactor:
    func(*series)  # 接收时间序列数组，返回计算序列
    *factors       # 输入因子
```

**RollingWindowFactor** - 单因子滚动窗口算子。
```python
class RollingWindowFactor:
    func(series, window)  # series是1D数组，window是窗口大小
    window                # 滚动窗口大小
    factor                # 单个输入因子
```

**CombinedRollingWindowFactor** - 多因子复合滚动窗口。
```python
class CombinedRollingWindowFactor:
    func(window, *series)  # 注意window在前
    window                 # 滚动窗口大小
    *factors               # 输入因子
```

**CombinedCrossSectionalFactor** - 横截面复合算子。
```python
class CombinedCrossSectionalFactor:
    func(df1, df2, ...)  # 接收DataFrame（索引=交易日期，列=order_book_id）
    # 返回计算后的DataFrame
```

**UserDefinedLeafFactor** - 创建自定义基础因子。
```python
class UserDefinedLeafFactor:
    name                                # 因子名称
    func(order_book_ids, start_date, end_date)  # 返回DataFrame
```

### 辅助函数

**rolling_window(series, window)** - 从1D时间序列生成滑动窗口数据。返回2D数组，每行是一个连续窗口切片。

---

## 因子检验

### 核心组件：FactorAnalysisEngine

通过 `append()` 方法构建检验管道的容器，支持一键执行多维度检验。

### 预处理选项

**1. 去极值 (Winzorization)**
- 方法：`mad`（3绝对值差中位数法）、`std`（3标准差法）、`percentile`（2.5%百分位法）

**2. 标准化 (Normalization)**
- 标准化因子值

**3. 中性化 (Neutralization)**
- `industry`: `citics_2019`、`sws` 或 `None`
- `style_factors`: `all`、`None` 或列表（包括 size, beta, momentum, earnings_yield, growth, liquidity, leverage, book_to_price, residual_volatility, non_linear_size）

### 因子分析器

**ICAnalysis**
- `rank_ic`: True/False（使用排名值）
- `industry_classification`: `sws`、`citics_2019` 或自定义分组
- `max_decay`: IC衰减的最大滞后期数

**QuantileReturnAnalysis**
- `quantile`: 组数
- `benchmark`: 基准指数代码

**FactorReturnAnalysis**
- 计算因子收益序列

### 执行参数

```python
engine.analysis(factor_data, returns, ascending, periods, keep_preprocess_result)
```

| 参数 | 说明 |
|------|------|
| `factor_data` | DataFrame，索引为datetime，列为order_book_id |
| `returns` | `daily` 或 DataFrame（T期因子值与T+1期收益率计算） |
| `ascending` | 排序方向 |
| `periods` | 调仓周期，最多3个 |
| `keep_preprocess_result` | 保存预处理数据 |

### 结果解读

**ICAnalysisResult**:
- `ic` 序列、`ic_decay`、`ic_industry_distribute`
- `summary()` 返回指标：mean、std、显著性（p<0.01占比）、t_value、p_value、skew、kurtosis、IR（IC均值/标准差比值）

**QuantileReturnAnalysisResult**:
- `quantile_returns`、`quantile_turnover`、`top_minus_bottom_return`、`benchmark_return`

**FactorReturnAnalysisResult**:
- `factor_returns`、`max_drawdown()`、`std()`

---

## 文档链接

- 快速上手: `/doc/rqfactor/manual/quick-start`
- 进阶理解: `/doc/rqfactor/manual/advance-tutorial`
- 使用示例: `/doc/rqfactor/manual/example`
- API 手册: `/doc/rqfactor/api/index-rqfactor`
