# 聚宽因子研究功能文档

> JoinQuant 因子分析系统 | https://www.joinquant.com/help/api/help#name:factor

---

## 一、概述

聚宽因子研究系统提供完整的因子定义、计算、处理和分析功能，包括：

- **因子定义**：自定义因子类，支持多种数据依赖
- **因子计算**：`calc_factors()` 批量计算因子值
- **数据处理**：中性化、去极值、标准化
- **单因子分析**：IC 分析、收益分析、换手率分析

**开源分析框架**：[jqfactor_analyzer](https://github.com/JoinQuant/jqfactor_analyzer)

---

## 二、因子定义与计算

### 2.1 因子定义框架

用户需要实现一个自定义因子的类，继承 `Factor` 类，并实现 `calc` 方法：

```python
from jqfactor import Factor
import numpy as np

class MA5(Factor):
    # 因子名称（不能与基础因子冲突）
    name = 'ma5'
    
    # 获取数据的最长时间窗口（日级别）
    max_window = 5
    
    # 依赖的基础因子名称
    dependencies = ['close']
    
    # 计算因子的函数，需返回 pandas.Series
    # index 是股票代码，value 是因子值
    def calc(self, data):
        # data['close'] 是 DataFrame，index 是日期，column 是股票代码
        return data['close'][-5:].mean()
```

### 2.2 因子属性说明

| 属性 | 说明 |
|------|------|
| `name` | 因子名称，不能与基础因子冲突 |
| `max_window` | 获取数据的最长时间窗口（日级别） |
| `dependencies` | 依赖的基础因子名称列表 |
| `main_class` | 是否为主因子（单因子分析时有效） |

### 2.3 calc 方法参数

```python
def calc(self, data):
    # self._current_date: 当前数据的逻辑日期
    # data: dict，key 是 dependencies 中的因子名称
    # value 是 pandas.DataFrame：
    #   - column: 股票代码
    #   - index: 时间序列，结束时间是当前时间，长度是 max_window
    
    # 返回: pandas.Series，index 是股票代码，value 是因子值
    pass
```

### 2.4 因子计算 API

```python
from jqfactor import calc_factors

result = calc_factors(
    securities=['600000.XSHG', '600016.XSHG'],  # 股票代码列表
    factors=[ALPHA013(), GROSSPROFITABILITY()], # 因子对象列表
    start_date='2017-01-01',                     # 开始日期
    end_date='2017-02-01',                       # 结束日期（回测中应小于 context.current_dt）
    use_real_price=False,                        # 是否使用真实价格（False=后复权）
    skip_paused=False                            # 是否跳过停牌
)

# 返回: dict，key 是各 factors 的 name，value 是 pandas.DataFrame
# DataFrame 的 index 是日期，column 是股票代码
result['alpha013_name'].head()
```

### 2.5 获取额外数据

在 `calc` 方法中获取额外数据：

```python
class IndexClose(Factor):
    name = 'indice_close'
    max_window = 10
    dependencies = ['market_cap']

    def calc(self, data):
        # 获取指数的开盘收盘价
        index = self._get_extra_data(
            securities=['000001.XSHG', '000300.XSHG'],  # 股票或指数代码
            fields=['open', 'close']                    # 基础因子名称
        )
        # 返回 dict，结构与 data 类似
        print(index.keys())         # ['open', 'close']
        print(index['close'].columns)  # 指数代码
        return data['market_cap'].mean()
```

---

## 三、依赖的基础因子

### 3.1 可用数据类型

| 数据类型 | 说明 | 示例 |
|---------|------|------|
| **价量信息** | open/close/high/low/money/volume | `dependencies=['close']` |
| **聚宽因子库** | 质量、基础、情绪、成长、风险等数百个因子 | `dependencies=['OperatingCycle', 'MLEV']` |
| **单季度财务指标** | valuation/balance/cash_flow/income/indicator | `dependencies=['operating_revenue']` |
| **前N季度财务数据** | 前1-8季度的单季度财务指标 | `dependencies=['operating_revenue_1']` |
| **过去五年年度数据** | 年度财务数据 | `dependencies=['operating_revenue_y1']` |
| **行业因子** | 证监会、聚宽、申万行业分类（哑变量） | `dependencies=['HY001']` |
| **概念因子** | 概念板块（哑变量） | `dependencies=['GN028']` |
| **指数因子** | 指数成分（哑变量） | `dependencies=['000300.XSHG']` |
| **资金流因子** | get_money_flow API 数据 | `dependencies=['net_pct_main']` |

### 3.2 财务数据时间规则

**单季度财务数据**：
- `operating_revenue`: 最新单季度数据
- `operating_revenue_1`: 上一季度数据
- `operating_revenue_2`: 上两季度数据
- `operating_revenue_3`: 上三季度数据

**年度财务数据**：
- `operating_revenue_y`: 最新年度数据
- `operating_revenue_y1`: 上一年度数据
- `operating_revenue_y2`: 上两年度数据

**示例**：计算 TTM 数据

```python
class OR_TTM(Factor):
    name = 'operating_revenue_ttm'
    max_window = 1
    dependencies = [
        'operating_revenue',    # 最新季度
        'operating_revenue_1',  # 上季度
        'operating_revenue_2',  # 上上季度
        'operating_revenue_3'   # 上上上季度
    ]

    def calc(self, data):
        # TTM = 前四季度相加
        ttm = (data['operating_revenue'] + 
               data['operating_revenue_1'] + 
               data['operating_revenue_2'] + 
               data['operating_revenue_3'])
        return ttm.mean()
```

---

## 四、因子数据处理函数

### 4.1 中性化

```python
from jqfactor import neutralize

neutralize(data, how=None, date=None, axis=1)
```

**参数**：
- `data`: pd.Series/pd.DataFrame，待中性化的序列
- `how`: 中性化因子列表，默认 `['jq_l1', 'market_cap']`
  - 行业：`'jq_l1'`, `'jq_l2'`, `'sw_l1'`, `'sw_l2'`, `'sw_l3'`
  - 风险因子：`'size'`, `'beta'`, `'momentum'`, `'residual_volatility'`, `'non_linear_size'`, `'book_to_price_ratio'`, `'liquidity'`, `'earnings_yield'`, `'growth'`, `'leverage'`
- `date`: 日期
- `axis`: 0=对每列，1=对每行

**示例**：

```python
import pandas as pd
import numpy as np
from jqfactor import neutralize

# 生成数据
data = pd.DataFrame(
    np.random.rand(3, 300), 
    columns=get_index_stocks('000300.XSHG', date='2018-05-02'),
    index=['a', 'b', 'c']
)

# 行业市值中性化
neutralize(data, how=['jq_l1', 'market_cap'], date='2018-05-02', axis=1)
```

### 4.2 去极值（标准差法）

```python
from jqfactor import winsorize

winsorize(data, scale=None, range=None, qrange=None, inclusive=True, inf2nan=True, axis=1)
```

**参数**：
- `data`: 待缩尾的序列
- `scale`: 标准差倍数，边界 `[mu - scale*sigma, mu + scale*sigma]`
- `range`: 列表，缩尾的上下边界
- `qrange`: 列表，分位数边界，如 `[0.05, 0.95]`
- `inclusive`: True=替换为边界值，False=替换为 NaN
- `inf2nan`: 是否将 inf 替换为 NaN
- `axis`: 0=对每列，1=对每行

**示例**：

```python
# 分位数去极值
winsorize(data, qrange=[0.05, 0.95], inclusive=True, inf2nan=True, axis=1)

# 标准差去极值
winsorize(data, scale=3, inclusive=True, axis=1)
```

### 4.3 去极值（中位数法）

```python
from jqfactor import winsorize_med

winsorize_med(data, scale=1, inclusive=True, inf2nan=True, axis=1)
```

**参数**：
- `scale`: 倍数，边界 `[med - scale*distance, med + scale*distance]`
- `distance`: 中位数到上下四分位数的距离

**示例**：

```python
winsorize_med(data, scale=1, inclusive=True, inf2nan=True, axis=0)
```

### 4.4 标准化

```python
from jqfactor import standardlize

standardlize(data, inf2nan=True, axis=1)
```

**参数**：
- `data`: 待标准化的序列
- `inf2nan`: 是否将 inf 替换为 NaN
- `axis`: 0=对每列，1=对每行

**返回**：Z-score 标准化后的数据

---

## 五、因子分析 API

### 5.1 analyze_factor 函数

```python
from jqfactor import analyze_factor

far = analyze_factor(
    factor,                    # 因子值或因子定义类
    start_date='2017-01-01',   # 开始日期
    end_date='2017-12-31',     # 结束日期
    industry='jq_l1',          # 行业分类
    universe='000300.XSHG',    # 股票池
    quantiles=5,               # 分位数数量
    periods=(1, 5, 10),        # 调仓周期
    weight_method='avg',       # 加权方法
    use_real_price=False,      # 是否动态复权
    skip_paused=False,         # 是否跳过停牌
    max_loss=0.25,             # 最大数据损失比例
    factor_dep_definitions=[]  # 依赖因子定义
)
```

**参数说明**：

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `factor` | 因子值（DataFrame/Series）或因子定义类 | - |
| `industry` | 行业分类 | `'sw_l1'`, `'sw_l2'`, `'sw_l3'`, `'jq_l1'`, `'jq_l2'`, `'zjw'` |
| `universe` | 股票池 | 指数代码或股票列表 |
| `quantiles` | 分位数数量 | int，默认 5 |
| `periods` | 调仓周期 | int 或 list，默认 `(1, 5, 10)` |
| `weight_method` | 加权方法 | `'avg'`(平均), `'mktcap'`(市值加权) |
| `max_loss` | 最大数据损失 | float，默认 0.25 |

### 5.2 使用示例

**方式一：自定义因子类**

```python
from jqfactor import analyze_factor, Factor

class MA5(Factor):
    name = 'ma5'
    max_window = 5
    dependencies = ['close']
    
    def calc(self, data):
        return data['close'][-5:].mean()

# 直接使用因子类进行分析
far = analyze_factor(
    factor=MA5, 
    start_date='2018-01-01', 
    end_date='2018-03-01',
    weight_method='mktcap',
    universe='000300.XSHG',
    industry='jq_l1',
    quantiles=8,
    periods=(1, 5, 22)
)

# 获取分析结果
far.ic_monthly  # 月度 IC
```

**方式二：传入因子值 DataFrame**

```python
from jqfactor import analyze_factor, get_factor_values

# 获取因子值
factor_data = get_factor_values(
    securities=get_index_stocks('000300.XSHG', '2018-01-01'),
    factors=['Skewness60'],
    start_date='2018-01-01',
    end_date='2018-03-01'
)['Skewness60']

# 使用因子值进行分析
far = analyze_factor(
    factor=factor_data,
    start_date='2018-01-01',
    end_date='2018-03-01',
    weight_method='mktcap',
    industry='jq_l1',
    quantiles=8,
    periods=(1, 5, 22),
    max_loss=0.2
)

far.mean_return_std_by_quantile
```

---

## 六、分析结果属性

### 6.1 数据属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `far.factor_data` | Series | 因子值（MultiIndex: 日期+股票） |
| `far.clean_factor_data` | DataFrame | 清洗后的因子数据 |
| `far.mean_return_by_quantile` | DataFrame | 按分位数分组的平均收益 |
| `far.mean_return_std_by_quantile` | DataFrame | 按分位数分组的收益标准差 |
| `far.mean_return_by_date` | DataFrame | 按日期+分位数分组的平均收益 |
| `far.mean_return_by_group` | DataFrame | 按行业+分位数分组的平均收益 |
| `far.mean_return_spread_by_quantile` | DataFrame | 最高-最低分位数收益差 |
| `far.ic` | DataFrame | 信息系数（日度） |
| `far.ic_by_group` | DataFrame | 分行业 IC |
| `far.ic_monthly` | DataFrame | 月度 IC |
| `far.quantile_turnover` | dict | 换手率（按调仓周期） |

### 6.2 计算方法

```python
# 计算按分位数分组因子收益
mean, std = far.calc_mean_return_by_quantile(
    by_date=False,      # 是否按天计算
    by_group=False,     # 是否按行业计算
    demeaned=False,     # 是否使用超额收益
    group_adjust=False  # 是否行业中性化
)

# 计算因子 alpha 和 beta
far.calc_factor_alpha_beta(demeaned=True, group_adjust=False)

# 计算每日 IC
far.calc_factor_information_coefficient(
    group_adjust=False,
    by_group=False,
    method='rank'       # 'rank' 或 'normal'
)

# 计算因子自相关性
far.calc_autocorrelation(rank=True)

# 计算换手率
far.calc_quantile_turnover_mean_n_days_lag(n=10)
```

---

## 七、可视化方法

### 7.1 完整分析报告

```python
# 展示全部分析
far.create_full_tear_sheet(
    demeaned=False,          # 是否使用超额收益
    group_adjust=False,      # 是否行业中性化
    by_group=False,          # 是否按行业展示
    turnover_periods=None,   # 换手率周期
    avgretplot=(5, 15),      # 因子预测天数:(过去, 未来)
    std_bar=False            # 是否显示标准差
)
```

### 7.2 分项分析

```python
# 因子值特征分析
far.create_summary_tear_sheet(demeaned=False, group_adjust=False)

# 因子收益分析
far.create_returns_tear_sheet(demeaned=False, group_adjust=False, by_group=False)

# 因子 IC 分析
far.create_information_tear_sheet(group_adjust=False, by_group=False)

# 因子换手率分析
far.create_turnover_tear_sheet(turnover_periods=None)

# 因子预测能力分析
far.create_event_returns_tear_sheet(avgretplot=(5, 15), demeaned=False)
```

### 7.3 单独绘图

```python
# 打印表格
far.plot_returns_table(demeaned=False, group_adjust=False)
far.plot_turnover_table()
far.plot_information_table(group_adjust=False, method='rank')
far.plot_quantile_statistics_table()

# IC 相关图
far.plot_ic_ts(group_adjust=False, method='rank')         # IC 时间序列
far.plot_ic_hist(group_adjust=False, method='rank')       # IC 分布直方图
far.plot_ic_qq(group_adjust=False, method='rank')         # IC QQ 图
far.plot_monthly_ic_heatmap(group_adjust=False)           # 月度 IC 热力图
far.plot_ic_by_group(group_adjust=False, method='rank')   # 分行业 IC

# 收益相关图
far.plot_quantile_returns_bar(by_group=False, demeaned=False)  # 分位数收益柱状图
far.plot_cumulative_returns(period=1, demeaned=False)          # 累积收益
far.plot_cumulative_returns_by_quantile(period=1)              # 分位数累积收益
far.plot_mean_quantile_returns_spread_time_series()            # 多空收益差

# 换手率图
far.plot_top_bottom_quantile_turnover(periods=(1, 3, 9))
far.plot_factor_auto_correlation(periods=None, rank=True)

# 关闭中文图例
far.plot_disable_chinese_label()
```

---

## 八、因子示例

### 8.1 价量因子 - Alpha191 中的 013

```python
from jqfactor import Factor
import numpy as np 

class ALPHA013(Factor):
    name = 'alpha013'
    max_window = 1
    dependencies = ['high', 'low', 'volume', 'money']

    def calc(self, data):
        high = data['high']
        low = data['low']
        vwap = data['money'] / data['volume']
        return (np.power(high * low, 0.5) - vwap).mean()
```

### 8.2 基本面因子 - Gross Profitability

```python
from jqfactor import Factor

class GROSSPROFITABILITY(Factor):
    name = 'gross_profitability'
    max_window = 1
    dependencies = ['total_operating_revenue', 'total_operating_cost', 'total_assets']

    def calc(self, data):
        revenue = data['total_operating_revenue']
        cost = data['total_operating_cost']
        assets = data['total_assets']
        return ((revenue - cost) / assets).mean()
```

### 8.3 中性化因子 - 产权比率

```python
from jqfactor import Factor
import numpy as np
import pandas as pd
from statsmodels.api import OLS

class DebtEquityRatio(Factor):
    name = 'debt_to_equity_ratio'
    max_window = 1
    dependencies = [
        'total_liability', 'equities_parent_company_owners',
        'market_cap',
        'HY001', 'HY002', 'HY003', 'HY004', 'HY005',
        'HY006', 'HY007', 'HY008', 'HY009', 'HY010', 'HY011'
    ]

    def calc(self, data):
        tl = data['total_liability']
        epco = data['equities_parent_company_owners']
        factor = tl / epco
        
        # 行业市值中性化
        industry_exposure = pd.DataFrame(index=data['HY001'].columns)
        industry_list = ['HY001', 'HY002', 'HY003', 'HY004', 'HY005',
                        'HY006', 'HY007', 'HY008', 'HY009', 'HY010', 'HY011']
        for key in industry_list:
            industry_exposure[key] = data[key].iloc[-1]
        
        market_cap_exposure = data['market_cap'].iloc[-1]
        total_exposure = pd.concat([market_cap_exposure, industry_exposure], axis=1)
        result = OLS(factor.mean(), total_exposure, missing='drop').fit().resid
        return result
```

### 8.4 指数因子 - 近10日 Alpha

```python
from jqfactor import Factor

class Hs300Alpha(Factor):
    name = 'hs300_alpha'
    max_window = 10
    dependencies = ['close']

    def calc(self, data):
        close = data['close']
        stock_return = close.iloc[-1, :] / close.iloc[0, :] - 1
        
        # 获取指数收盘价
        index_close = self._get_extra_data(
            securities=['000300.XSHG'], 
            fields=['close']
        )['close']
        
        index_return = index_close.iat[-1, 0] / index_close.iat[0, 0] - 1
        return stock_return - index_return
```

### 8.5 成长因子 - 近两年净利润增长率

```python
from jqfactor import Factor

class NetProfitGrowth(Factor):
    name = 'net_profit_growth_rate'
    max_window = 1
    dependencies = ['net_profit_y', 'net_profit_y1']

    def calc(self, data):
        net_profit_y = data['net_profit_y']
        net_profit_y1 = data['net_profit_y1']
        growth = net_profit_y / net_profit_y1 - 1
        return growth.mean()
```

### 8.6 TTM 因子 - 资产回报率

```python
from jqfactor import Factor

class ROATTM(Factor):
    name = 'roa_ttm'
    max_window = 1
    dependencies = [
        'net_profit', 'net_profit_1', 'net_profit_2', 'net_profit_3',
        'total_assets'
    ]

    def calc(self, data):
        net_profit_ttm = (data['net_profit'] + data['net_profit_1'] + 
                          data['net_profit_2'] + data['net_profit_3'])
        result = net_profit_ttm / data['total_assets']
        return result.mean()
```

---

## 九、分析结果解读

### 9.1 收益分析

| 指标 | 说明 |
|------|------|
| 分位数收益 | 持仓 1/5/10 天后，各分位数的平均收益 |
| 分位数累积收益 | 各分位数持仓收益的累计值 |
| 多空组合收益 | 做多最大分位、做空最小分位的收益 |

**判断标准**：单调性越好、多空收益差越大，因子效果越好。

### 9.2 IC 分析

| 指标 | 说明 |
|------|------|
| Normal IC | 因子值与收益的相关系数 |
| Rank IC | 因子排序值与收益排序值的相关系数 |
| IC 均值 | >0.03 可认为因子有效 |
| ICIR | IC 均值/IC 标准差，>0.5 较好 |

**判断标准**：IC 均值 > 0.03，ICIR > 0.5，IC 时间序列稳定。

### 9.3 换手率分析

| 指标 | 说明 |
|------|------|
| 分位数换手率 | 不同时间周期下，分位数中个股的进出情况 |
| 因子自相关性 | 因子值的时间序列稳定性 |

**判断标准**：换手率低 = 因子稳定性好，交易成本低。

---

## 十、附录

### 10.1 Normal IC vs Rank IC

**Normal IC**：
- 因子值与下期收益的相关系数
- 假设数据服从正态分布

**Rank IC**：
- 因子排序值与收益排序值的相关系数
- 不要求正态分布，更稳健

**推荐**：金融数据通常不服从正态分布，建议使用 Rank IC。

### 10.2 常见问题

**Q: ValueError: No objects to concatenate**

A: 检查因子数据索引类型，应为 DatetimeIndex：
```python
factor_data.index = pd.to_datetime(factor_data.index)
```

**Q: IC 计算无意义**

A: 样本股票数应至少 100 只，IC 才有统计意义。

---

## 资源链接

- 官方文档: https://www.joinquant.com/help/api/help#name:factor
- 开源框架: https://github.com/JoinQuant/jqfactor_analyzer
- 经典教程: 因子及多因子分析
- 社区: https://www.joinquant.com/community
