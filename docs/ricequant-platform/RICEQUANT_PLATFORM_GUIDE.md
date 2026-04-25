# 米筐量化平台使用指南

> RiceQuant Web 平台操作手册 | https://www.ricequant.com/doc/quant/

---

## 一、平台概述

米筐量化平台提供基于浏览器的量化交易和分析工具，用户可开发交易策略并验证投资想法。平台提供策略回测和模拟交易功能。

### 1.1 企业版与基础版对比

| 功能 | 基础版 | 企业版 |
|------|--------|--------|
| 回测内存 | 2G | 4G |
| 回测品种 | 股票、指数、基金、期货 | 新增可转债、期权、现货 |
| 回测频率 | 日、分钟 | 日、分钟、Tick |
| 并发回测 | 3 | 8 |
| 模拟交易 | 0 | 20 |
| 因子研究 | 编辑、检验 | 新增发布、预计算、跟踪 |

### 1.2 数据差异

| 数据类型 | 基础版 | 企业版 |
|----------|--------|--------|
| 股票/ETF/LOF/指数/期货基础数据 | ✓ | ✓ |
| 历史日/分钟数据 | ✓ | ✓ |
| 实时分钟数据 | ✓ | ✓ |
| 股票财务数据 | ✓ | ✓ |
| 财务/技术/Alpha101 因子数据 | ✓ | ✓ |
| 宏观数据 | ✓ | ✓ |
| Tick 数据（历史&实时） | ✗ | ✓ |
| 期权数据及风险指标 | ✗ | ✓ |
| 可转债数据 | ✗ | ✓ |
| 资金流向数据 | ✗ | ✓ |
| 债券数据（需授权） | ✗ | ✓ |

### 1.3 工作空间（Workspace）

协作开发模块，团队可共享资源：
- 用户可加入多个工作空间
- 资源归属于工作空间
- 管理员可邀请/移除成员、转让管理权、解散空间
- 删除成员时可转移资源给其他用户

---

## 二、投资研究

基于 IPython Notebook 的 Python 分析环境，提供高质量金融数据（每日更新）。

### 2.1 RQPortal API

用于获取回测结果的 API：

```python
import rqportal

# 获取回测基本信息
rqportal.info(run_id)
# 返回: name, start_date, end_date, time_unit, type, init_cash

# 获取风险指标
rqportal.risk(run_id)
# 返回: alpha, beta, max_drawdown, sharpe, volatility

# 获取组合收益数据
rqportal.portfolio(run_id, start_date, end_date)
# 返回: DataFrame，每日收益

# 获取持仓数据
rqportal.positions(run_id, start_date, end_date)
# 返回: DataFrame，每日持仓

# 获取交易记录
rqportal.trades(run_id, start_date, end_date)
# 返回: DataFrame，symbol, price, quantity, direction
```

### 2.2 三种回测调用方式

#### 方式一：Magic Command `%%rqalpha_plus`

```python
%%rqalpha_plus -s 20160301 -e 20160901 --account stock 10000 -fq 1d -p -bm 000001.XSHG

def init(context):
    context.stocks = ['000001.XSHE', '000002.XSHE']

def handle_bar(context, bar_dict):
    for stock in context.stocks:
        order_target_percent(stock, 0.5)
```

#### 方式二：`run_func()` 函数式调用

```python
from rqalpha_plus import run_func

config = {
    'base': {
        'start_date': '2016-03-01',
        'end_date': '2016-09-01',
        'frequency': '1d',
        'accounts': {'stock': 10000}
    },
    'mod.sys_analyser': {
        'benchmark': '000001.XSHG',
        'plot': True
    }
}

run_func(init=init, handle_bar=handle_bar, config=config)
```

#### 方式三：`run_code()` 字符串式调用

```python
from rqalpha_plus import run_code

code = '''
def init(context):
    context.stock = '000001.XSHE'

def handle_bar(context, bar_dict):
    order_target_percent(context.stock, 1.0)
'''

run_code(code, config=config)
```

### 2.3 配置参数

| 参数组 | 参数 | 说明 |
|--------|------|------|
| base | start_date | 回测起始日期 |
| | end_date | 回测结束日期 |
| | frequency | 频率: '1d', '1m', 'tick' |
| | accounts | 账户初始资金: {'stock': 100000} |
| | init_positions | 初始持仓 |
| mod.sys_simulation | matching_type | 撮合方式 |
| | slippage_model | 滑点模型 |
| | volume_limit | 成交量限制 |
| mod.sys_analyser | benchmark | 基准合约 |
| | plot | 是否绘图 |
| | report_save_path | 报告保存路径 |

### 2.4 其他功能

```python
# 读取私有上传文件
data = get_file('my_data.csv')

# 保存 CSV 文件
df.to_csv('output.csv')

# 安装第三方包（需重启内核）
# pip install PackageName --user
```

---

## 三、因子研究

米筐因子研究系统提供因子创建、检验、发布和管理的完整工具。

### 3.1 因子类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 基础因子 | 直接从财务报表或交易所行情数据获取 | 行情因子、财务指标 |
| 复合因子 | 通过基础因子转换和组合得到 | PE 排名、动量因子 |

**复合因子分类**：
- **截面因子**：数值依赖于整个股票池内的相对排名（如 `pe_ratio` 排名）
- **非截面因子**：数值独立于股票池中其他股票

### 3.2 因子定义

#### 简单因子

```python
from rqfactor import *

# 价格变动因子
f = (Factor('close') - Factor('open')) / (Factor('high') - Factor('low'))
```

#### 引用因子

```python
# 公共因子
Factor('factor_name')

# 产品库因子
Factor('private.factor_name')

# 技术指标
from rqfactor.indicators import KDJ
```

### 3.3 内置函数

#### 时间序列函数

| 函数 | 说明 |
|------|------|
| `MA(f, window)` | 移动平均 |
| `EMA(f, window)` | 指数移动平均 |
| `STD(f, window)` | 标准差 |
| `SUM(f, window)` | 滚动求和 |
| `REF(f, n)` | 引用 n 期前的值 |
| `DELAY(f, n)` | 延迟 n 期 |
| `HHV(f, window)` | 最高值 |
| `LLV(f, window)` | 最低值 |
| `CORR(f1, f2, window)` | 相关系数 |
| `TS_RANK(f, window)` | 时间序列排名 |
| `TS_ZSCORE(f, window)` | 时间序列标准化 |

#### 截面函数

| 函数 | 说明 |
|------|------|
| `CS_ZSCORE(f)` | 截面标准化 |
| `RANK(f)` | 排名 |
| `DEMEAN(f)` | 去均值 |
| `SCALE(f)` | 标准化 |
| `INDUSTRY_NEUTRALIZE(f)` | 行业中性化 |
| `TOP(f, n)` | 取前 n 名 |
| `BOTTOM(f, n)` | 取后 n 名 |
| `QUANTILE(f, n)` | 分位数分组 |

### 3.4 技术指标

内置支持的技术指标：

| 指标 | 说明 |
|------|------|
| MACD | 指数平滑异同移动平均线 |
| KDJ | 随机指标 |
| DMI | 动向指标 |
| RSI | 相对强弱指标 |
| BOLL | 布林带 |
| WR | 威廉指标 |
| BIAS | 乖离率 |
| ASI | 振动升降指标 |
| VR | 容量比率 |
| ARBR | 人气买卖意愿指标 |
| DPO | 区间震荡线 |
| TRIX | 三重指数平滑移动平均 |

### 3.5 因子检验

```python
from rqfactor.analysis import factor_analysis

result = factor_analysis(
    f,                              # 因子表达式
    period=20,                      # 调仓周期
    start_date='2020-01-01',
    end_date='2023-12-31',
    universe='000300.XSHG',         # 股票池: CSI300, SSE50, CSI500, CSI800
    shift=1,                        # 偏移天数
    rank_ic=True,                   # 使用 RankIC
    quantile=5,                     # 分组数
    ascending=True,                 # 升序排序
    winsorization='mad',            # 去极值方法: 'mad', '3sigma', 'quantile'
    normalization=True,             # 标准化
    neutralization='none',          # 中性化: 'none', 'industry', 'style'
    include_st=True,                # 包含 ST 股
    include_new=True,               # 包含新股
    benchmark='000300.XSHG'         # 基准指数
)
```

### 3.6 IC 分析指标

| 指标 | 说明 |
|------|------|
| IR | 信息比率 |
| mean | IC 均值 |
| std | IC 标准差 |
| significance_ratio | 显著性比例 |
| t_stat | t 统计量 |
| p_value | p 值 |
| skewness | 偏度 |
| kurtosis | 峰度 |

### 3.7 自定义算子

```python
from rqfactor.rolling import RollingWindowFactor
import numpy as np

def my_ema(series, window):
    """自定义 EMA 算子"""
    q = 0.5 ** (1 / 22)
    weight = np.array(list(reversed([q ** i for i in range(window)])))
    r = rolling_window(series, window)
    return np.dot(r, weight) / window

def MY_EMA(f, window):
    return RollingWindowFactor(my_ema, window, f)
```

### 3.8 自定义基础因子

```python
from rqfactor.interface import UserDefinedLeafFactor

def get_factor_value(order_book_id, start_date, end_date):
    """
    自定义因子数据获取函数
    返回: 1D numpy array
    """
    # 实现数据获取逻辑
    pass

f = UserDefinedLeafFactor('my_factor', get_factor_value)
```

### 3.9 因子生命周期

| 状态 | 说明 |
|------|------|
| Creating | 因子开发中 |
| Under Review | 已申请发布，等待审核 |
| Published | 已发布，产品库可用 |
| Rejected | 被拒绝，需修改 |
| Delisted | 已下架 |

### 3.10 重要注意事项

1. **价格因子使用后复权价格**，如需未复权价格使用 `_unadjusted` 后缀
2. **停牌期间数据会被过滤**
3. 截面操作中 Inf 值被视为 NaN
4. 产品库因子引用使用 `private.` 前缀

---

## 四、回测

### 4.1 策略结构

```python
def init(context):
    """初始化策略逻辑"""
    context.stocks = ['000001.XSHE', '000002.XSHE']
    set_slippage(FixedSlippage(0.002))

def before_trading(context):
    """盘前操作"""
    pass

def handle_bar(context, bar_dict):
    """每个 Bar 执行的主逻辑"""
    for stock in context.stocks:
        order_target_percent(stock, 0.5)
```

### 4.2 回测参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| start_date | 起始日期 | - |
| end_date | 结束日期 | - |
| initial_capital | 初始资金 | - |
| frequency | 频率 | '1d' |
| benchmark | 基准合约 | '000300.XSHG' |
| commission_multiplier | 手续费倍数 | 1.0 |
| margin_multiplier | 保证金倍数 | 1.0 |

### 4.3 撮合机制

| 类型 | 说明 |
|------|------|
| 当前 Bar 收盘价 | 默认方式 |
| 下一 Bar 开盘价 | 更保守的方式 |
| 最佳价格 | 按最优可成交价格 |

**成交量限制**：日/分钟回测限制为 Bar 成交量的 25%，Tick 回测无限制。

### 4.4 复权方式

使用"动态复权"——基于回测日期计算复权因子，避免未来数据偏差。

### 4.5 手续费

**A股默认手续费**：万分之八

**印花税**：卖出时收取 0.1%

**期货手续费**：按合约类型区分（按金额或按手数）

### 4.6 持仓管理

- 股票：T+1 交易制度
- 期货：每日无负债结算

### 4.7 绩效指标

| 类别 | 指标 |
|------|------|
| 收益类 | 总收益率、年化收益率、Alpha、每日收益率 |
| 风险类 | 波动率、跟踪误差、下行风险、Beta、最大回撤 |
| 风险调整类 | Sharpe比率、Sortino比率、信息比率 |

### 4.8 Wizard 策略构建器

可视化界面，支持：
- 股票筛选
- 因子选择
- 排序条件
- 风控设置（止损、择时）

---

## 五、模拟交易

### 5.1 数据源

- 使用实时 Level-1 数据（约 3-5 秒延迟）
- 分钟 Bar 由实时行情切片合成
- `handle_bar` 在每分钟 Bar 完成后触发
- A 股第一个分钟 Bar 在 09:31 触发

### 5.2 启动流程

1. 运行完整的分钟级回测
2. 在回测结果页点击"模拟交易"
3. 启动后至少等待一个交易日更新

### 5.3 控制选项

| 操作 | 说明 |
|------|------|
| 暂停 | 策略暂停，接收行情但不下单 |
| 启动 | 恢复下单逻辑 |
| 停止 | 完全停止，不可恢复 |

### 5.4 仪表盘功能

| 功能 | 说明 |
|------|------|
| 历史收益 | 累计收益曲线（每日一个点） |
| 当日收益 | 当日累计收益（每分钟一个点） |
| 最新持仓 | 当前持仓状态 |
| 成交记录 | 每日交易记录 |

### 5.5 代码替换

- 可替换为当前策略或其他策略代码
- 保留原有持仓、交易和资金信息
- 若勾选"立即运行 init 及 before_trading"，会清空原 `context` 内容

### 5.6 微信通知

- 在通知设置中启用
- 扫码绑定微信账号
- 实时推送调仓记录
- 链接到米筐组合调仓界面

### 5.7 状态保存

每日收盘后保存：
- 用户账户和持仓信息
- `context` 对象（pickle 序列化）

**警告**：无法序列化的变量不会被保存。例如 `query()` 对象不可 pickle，正确做法是在 `before_trading()` 中调用，而非 `init(context)`。

---

## 六、策略开发 API

### 6.1 生命周期方法

```python
def init(context):
    """必须实现 - 策略初始化"""
    context.cash_limit = 5000

def handle_bar(context, bar_dict):
    """必须实现 - 每个 Bar 执行"""
    order_shares('000001.XSHE', 500)

def handle_tick(context, tick):
    """可选 - Tick 数据更新"""
    logger.info(tick.last)

def open_auction(context, bar_dict):
    """可选 - 盘前集合竞价"""
    pass

def before_trading(context):
    """可选 - 每日开盘前"""
    pass

def after_trading(context):
    """可选 - 每日收盘后（实时模拟中 15:30）"""
    pass
```

### 6.2 股票交易函数

```python
# 指定股数（正数买入，负数卖出）
order_shares('000001.XSHE', 2000)
order_shares('000001.XSHE', -2000)

# 指定手数
order_lots('000001.XSHE', 20)

# 指定价值
order_value('000001.XSHE', 10000)

# 指定比例（占组合价值的比例）
order_percent('000001.XSHE', 0.5)

# 目标价值
order_target_value('000001.XSHE', 10000)

# 目标比例
order_target_percent('000001.XSHE', 0.3)

# 限价单
order_shares('000001.XSHE', 1000, style=LimitOrder(10))
```

### 6.3 期货交易函数

```python
# 买开
buy_open('AG1607', amount=2, price=3500)

# 卖平
sell_close('AG1607', amount=2, close_today=False)

# 卖开
sell_open('AG1607', amount=2)

# 买平
buy_close('AG1607', amount=2, close_today=False)
```

### 6.4 订单管理

```python
# 撤单
cancel_order(order)

# 获取未成交订单
orders = get_open_orders()
```

### 6.5 期权行权

```python
exercise("M1905C2350", 1)
```

### 6.6 持仓查询

```python
# 单个持仓
pos = get_position('000001.XSHE')

# 全部持仓
positions = get_positions()
```

### 6.7 定时任务 Scheduler

```python
def init(context):
    # 每日运行
    scheduler.run_daily(my_func)
    
    # 每周运行（weekday: 0=周一）
    scheduler.run_weekly(my_func, weekday=2)
    
    # 每月运行（tradingday: 交易日）
    scheduler.run_monthly(my_func, tradingday=15)
    
    # 指定时间运行
    scheduler.run_daily(my_func, time_rule=market_open(minute=10))
    scheduler.run_daily(my_func, time_rule=market_close(hour=1))
    scheduler.run_daily(my_func, time_rule='before_trading')
```

### 6.8 数据查询函数

#### 合约信息

```python
# 所有合约列表
all_instruments(type='CS')  # 'CS':股票, 'ETF', 'LOF', 'INDX':指数, 'Future', 'Option'

# 合约详细信息
instruments('000001.XSHE')
instruments('000001.XSHE').days_from_listed()
```

#### 历史行情

```python
# 历史 Bars
history_bars('000002.XSHE', 5, '1d', 'close')
history_bars(context.s1, 2, '5m', ['datetime', 'volume'])

# 历史 Tick
history_ticks('000001.XSHE', 100)

# 历史价格（支持多合约）
get_price(['000001.XSHE', '000002.XSHE'], 
          start_date='2020-01-01', 
          end_date='2020-12-31',
          frequency='1d',
          fields=['open', 'close', 'high', 'low'],
          adjust_type='pre')

# 当前快照
current_snapshot('000001.XSHE')
```

#### 因子数据

```python
# 获取因子
get_factor(order_book_ids, factors, count=1)

# 财务数据（季度）
get_pit_financials_ex(order_book_ids, fields, count, statements='latest')
```

#### 期货相关

```python
# 主力合约
get_dominant_future('AG', rule=0)

# 可交易合约列表
get_future_contracts('AG')
```

#### 市场数据

```python
# 交易日历
get_trading_dates('2020-01-01', '2020-12-31')
get_previous_trading_date('2020-06-01', n=1)
get_next_trading_date('2020-06-01', n=1)

# 分红拆分
get_dividend('000001.XSHE', '2020-01-01')
get_split('000001.XSHE', '2020-01-01')

# 换手率
get_turnover_rate('000001.XSHE', count=20)

# 涨跌幅
get_price_change_rate('000001.XSHE', count=5)

# 收益率曲线
get_yield_curve(date=None, tenor=None)
```

#### 股票筛选

```python
# 行业股票
industry('sw_l1', '银行')

# 板块股票
sector('Energy')  # Energy, Materials, Financials, InformationTechnology...

# 概念股票
concept('国企改革', '一带一路')

# 指数成分股
index_components('000300.XSHG', date=None)

# 融资融券
get_securities_margin('000001.XSHE', count=10)

# 沪深港通
get_stock_connect('000001.XSHE', count=10)

# 流通股
get_shares('000001.XSHE', count=10)
```

#### 状态判断

```python
# 停牌判断
is_suspended('000001.XSHE', count=5)

# ST 判断
is_st_stock('000001.XSHE', count=5)
```

### 6.9 Context 对象

| 属性 | 说明 |
|------|------|
| `context.now` | 当前时间 |
| `context.portfolio` | 投资组合信息 |
| `context.stock_account` | 股票资金账户 |
| `context.future_account` | 期货资金账户 |
| `context.run_info` | 策略运行信息 |
| `context.universe` | 策略合约池 |

### 6.10 重要数据对象

#### Bar 对象

```python
bar.order_book_id
bar.symbol
bar.datetime
bar.open, bar.close, bar.high, bar.low
bar.volume
bar.total_turnover
bar.prev_close
bar.limit_up, bar.limit_down
bar.isnan
bar.suspended
bar.prev_settlement  # 期货
bar.settlement       # 期货
```

#### Order 对象

```python
order.order_id
order.order_book_id
order.datetime
order.side           # BUY, SELL
order.price
order.quantity
order.filled_quantity
order.unfilled_quantity
order.type           # MARKET, LIMIT
order.transaction_cost
order.avg_price
order.status         # PENDING_NEW, ACTIVE, FILLED, CANCELLED, REJECTED
order.message
```

#### Tick 对象

```python
tick.order_book_id
tick.datetime
tick.open, tick.high, tick.low, tick.last
tick.prev_settlement, tick.prev_close
tick.volume
tick.limit_up, tick.limit_down
tick.open_interest
tick.asks          # list of ask prices
tick.ask_vols      # list of ask volumes
tick.bids          # list of bid prices
tick.bid_vols      # list of bid volumes
```

#### Portfolio 对象

```python
portfolio.total_returns
portfolio.daily_returns
portfolio.daily_pnl
portfolio.total_value
portfolio.unit_net_value
portfolio.annualized_returns
portfolio.positions
```

#### Position 对象

```python
position.order_book_id
position.direction   # LONG, SHORT
position.quantity
position.market_value
position.trading_pnl
position.position_pnl
position.last_price
```

---

## 七、技术分析

### 7.1 内置指标

| 指标 | 说明 |
|------|------|
| MACD | 指数平滑异同移动平均线 |
| KDJ | 随机指标 |
| DMI | 动向指标 |
| RSI | 相对强弱指标 |
| BOLL | 布林带 |
| WR | 威廉指标 |
| BIAS | 乖离率 |
| ASI | 振动升降指标 |
| VR | 容量比率 |
| ARBR | 人气买卖意愿指标 |
| DPO | 区间震荡线 |
| TRIX | 三重指数平滑移动平均 |

### 7.2 自定义指标

```python
def MA_SIGNAL():
    """自定义均线交叉信号"""
    return CROSS(MA(CLOSE, 5), MA(CLOSE, 10))

def init(context):
    # 注册指标（名称, 函数, 频率, 窗口大小）
    reg_indicator('ma', MA_SIGNAL, '5m', win_size=20)

def handle_bar(context, bar_dict):
    # 获取指标值
    ma_cross = get_indicator(context.s1, 'ma')
```

### 7.3 可用变量和函数

| 类别 | 名称 |
|------|------|
| 价格 | CLOSE, OPEN, HIGH, LOW |
| 成交量 | VOLUME |
| 移动平均 | MA(series, window) |
| 指数平均 | EMA(series, window) |
| 交叉 | CROSS(series1, series2) |
| 引用 | REF(series, n) |
| 最高值 | HHV(series, window) |
| 最低值 | LLV(series, window) |
| 求和 | SUM(series, window) |
| 最大值 | MAX(a, b) |
| 最小值 | MIN(a, b) |
| 绝对值 | ABS(series) |
| 标准差 | STD(series, window) |
| 条件判断 | IF(condition, true_val, false_val) |
| 全部满足 | EVERY(condition, window) |
| 计数 | COUNT(condition, window) |

**注意**：当前技术指标计算未包含"不完整"分钟线数据。

---

## 八、策略实例

### 8.1 买入持有策略

```python
def init(context):
    context.stock = '000001.XSHE'

def handle_bar(context, bar_dict):
    order_target_percent(context.stock, 1.0)
```

### 8.2 均线金叉策略

```python
import talib

def init(context):
    context.stock = '000001.XSHE'

def handle_bar(context, bar_dict):
    prices = history_bars(context.stock, 30, '1d', 'close')
    ma5 = talib.SMA(prices, 5)
    ma20 = talib.SMA(prices, 20)
    
    if ma5[-1] > ma20[-1] and ma5[-2] <= ma20[-2]:
        order_target_percent(context.stock, 1.0)
    elif ma5[-1] < ma20[-1] and ma5[-2] >= ma20[-2]:
        order_target_percent(context.stock, 0.0)
```

### 8.3 MACD 策略

```python
import talib

def init(context):
    context.stock = '000001.XSHE'

def handle_bar(context, bar_dict):
    prices = history_bars(context.stock, 50, '1d', 'close')
    macd, signal, hist = talib.MACD(prices)
    
    if hist[-1] > 0 and hist[-2] <= 0:
        order_target_percent(context.stock, 1.0)
    elif hist[-1] < 0 and hist[-2] >= 0:
        order_target_percent(context.stock, 0.0)
```

### 8.4 RSI 多股票策略

```python
import talib

def init(context):
    context.stocks = ['000001.XSHE', '000002.XSHE', '600000.XSHG']

def handle_bar(context, bar_dict):
    for stock in context.stocks:
        prices = history_bars(stock, 30, '1d', 'close')
        rsi = talib.RSI(prices, timeperiod=14)
        
        if rsi[-1] < 30:
            order_target_percent(stock, 0.33)
        elif rsi[-1] > 70:
            order_target_percent(stock, 0.0)
```

### 8.5 财务数据选股策略

```python
from rqdatac import get_pit_financials_ex

def init(context):
    context.rebalance_days = 20
    context.days = 0

def handle_bar(context, bar_dict):
    context.days += 1
    if context.days % context.rebalance_days != 0:
        return
    
    # 查询市盈率 55-60 且营业总收入前 10
    df = get_pit_financials_ex(
        query=context.stock_pool,
        fields=['pe_ratio', 'operating_revenue'],
        count=1
    )
    
    df = df[(df['pe_ratio'] > 55) & (df['pe_ratio'] < 60)]
    df = df.nlargest(10, 'operating_revenue')
    
    for stock in context.portfolio.positions:
        if stock not in df.index:
            order_target_percent(stock, 0.0)
    
    for stock in df.index:
        order_target_percent(stock, 1.0 / len(df))
```

### 8.6 海龟交易系统

```python
def init(context):
    context.stock = '000001.XSHE'
    context.entry_window = 20
    context.exit_window = 10
    context.atr_window = 20
    context.unit_limit = 4

def handle_bar(context, bar_dict):
    prices = history_bars(context.stock, 60, '1d', 'close')
    
    entry_high = max(prices[-context.entry_window:])
    exit_low = min(prices[-context.exit_window:])
    
    atr = talib.ATR(high, low, close, context.atr_window)[-1]
    
    position = context.portfolio.positions.get(context.stock)
    
    if position is None:
        if prices[-1] >= entry_high:
            unit = context.portfolio.total_value * 0.01 / atr
            order_shares(context.stock, int(unit / prices[-1]) * 100)
    else:
        if prices[-1] <= exit_low:
            order_target_percent(context.stock, 0.0)
```

### 8.7 期货 MACD 策略

```python
import talib

def init(context):
    subscribe('IF2501')
    context.future = 'IF2501'

def handle_bar(context, bar_dict):
    prices = history_bars(context.future, 50, '1d', 'close')
    macd, signal, hist = talib.MACD(prices)
    
    if hist[-1] > 0 and hist[-2] <= 0:
        buy_open(context.future, 1)
    elif hist[-1] < 0 and hist[-2] >= 0:
        sell_close(context.future, 1)
```

### 8.8 商品期货配对交易

```python
import talib

def init(context):
    context.pair = ['RB2501', 'HC2501']
    subscribe(context.pair)

def handle_bar(context, bar_dict):
    s1, s2 = context.pair
    prices1 = history_bars(s1, 100, '1m', 'close')
    prices2 = history_bars(s2, 100, '1m', 'close')
    
    spread = prices1 - prices2
    mean = spread.mean()
    std = spread.std()
    zscore = (spread[-1] - mean) / std
    
    if zscore > 2:
        sell_open(s1, 1)
        buy_open(s2, 1)
    elif zscore < -2:
        buy_open(s1, 1)
        sell_open(s2, 1)
    elif abs(zscore) < 0.5:
        sell_close(s1, 1)
        buy_close(s2, 1)
```

### 8.9 Alpha 多因子对冲策略

```python
def init(context):
    context.factors = ['market_cap', 'pe_ratio', 'pb_ratio']
    context.stock_pool = '000300.XSHG'
    context.rebalance_days = 5
    context.days = 0

def before_trading(context):
    # 每日更新股票池
    context.stocks = index_components(context.stock_pool)

def handle_bar(context, bar_dict):
    context.days += 1
    if context.days % context.rebalance_days != 0:
        return
    
    # 获取因子数据
    factor_data = get_factor(context.stocks, context.factors, count=1)
    
    # 因子标准化和打分
    scores = {}
    for stock in context.stocks:
        score = 0
        for factor in context.factors:
            value = factor_data.loc[stock, factor]
            # 根据因子方向调整
            if factor in ['market_cap', 'pe_ratio']:
                score -= value  # 偏好小市值、低PE
            else:
                score += value
        scores[stock] = score
    
    # 选取 Top 30
    sorted_stocks = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:30]
    
    # 等权买入
    for stock in context.portfolio.positions:
        if stock not in sorted_stocks:
            order_target_percent(stock, 0.0)
    
    for stock in sorted_stocks:
        order_target_percent(stock, 1.0 / 30)
```

---

## 九、枚举常量

### 9.1 订单状态

```python
ORDER_STATUS.PENDING_NEW    # 待提交
ORDER_STATUS.ACTIVE         # 已生效
ORDER_STATUS.FILLED         # 已成交
ORDER_STATUS.PENDING_CANCEL # 待撤销
ORDER_STATUS.CANCELLED      # 已撤销
ORDER_STATUS.REJECTED       # 已拒绝
```

### 9.2 交易方向

```python
SIDE.BUY   # 买入
SIDE.SELL  # 卖出
```

### 9.3 开平仓

```python
POSITION_EFFECT.OPEN        # 开仓
POSITION_EFFECT.CLOSE       # 平仓
POSITION_EFFECT.CLOSE_TODAY # 平今仓
POSITION_EFFECT.EXERCISE    # 行权
POSITION_EFFECT.MATCH       # 配对
```

### 9.4 订单类型

```python
ORDER_TYPE.MARKET  # 市价单
ORDER_TYPE.LIMIT   # 限价单
```

### 9.5 运行类型

```python
RUN_TYPE.BACKTEST      # 回测
RUN_TYPE.PAPER_TRADING # 模拟交易
RUN_TYPE.LIVE_TRADING  # 实盘交易
```

### 9.6 持仓方向

```python
POSITION_DIRECTION.LONG  # 多头
POSITION_DIRECTION.SHORT # 空头
```

### 9.7 事件类型

```python
EVENT.ORDER_PENDING_NEW      # 订单待提交
EVENT.ORDER_CREATION_PASS    # 订单创建通过
EVENT.ORDER_UNSOLICITED_UPDATE # 订单状态更新
EVENT.ORDER_PENDING_CANCEL   # 订单待撤销
EVENT.ORDER_CANCELLATION_PASS # 订单撤销通过
EVENT.ORDER_CREATION_REJECT  # 订单创建拒绝
EVENT.TRADE                  # 成交
```

---

## 十、常见问题

### 10.1 如何处理停牌股票？

```python
def handle_bar(context, bar_dict):
    for stock in context.stocks:
        if bar_dict[stock].suspended:
            continue
        # 正常交易逻辑
```

### 10.2 如何避免未来数据？

- 使用 `get_pit_financials_ex()` 获取时点财务数据
- 使用动态复权价格
- 注意因子计算窗口的影响

### 10.3 如何处理涨跌停？

```python
def handle_bar(context, bar_dict):
    stock = context.stock
    bar = bar_dict[stock]
    
    if bar.close >= bar.limit_up * 0.995:
        # 接近涨停，可能无法买入
        return
    if bar.close <= bar.limit_down * 1.005:
        # 接近跌停，可能无法卖出
        return
```

### 10.4 如何进行行业中性化？

```python
from rqfactor import INDUSTRY_NEUTRALIZE

f_neutral = INDUSTRY_NEUTRALIZE(Factor('pe_ratio'))
```

### 10.5 如何保存自定义数据？

```python
# 存储文件
put_file('my_data.csv', data)

# 读取文件
data = get_file('my_data.csv')

# 读取 CSV
df = get_csv('my_data.csv')
```

---

## 附录：快速参考

### A. 交易函数速查

| 函数 | 用途 | 参数 |
|------|------|------|
| `order_shares` | 指定股数 | id, amount, style |
| `order_lots` | 指定手数 | id, amount, style |
| `order_value` | 指定价值 | id, cash, style |
| `order_percent` | 指定比例 | id, percent, style |
| `order_target_value` | 目标价值 | id, cash, style |
| `order_target_percent` | 目标比例 | id, percent, style |
| `buy_open` | 期货买开 | id, amount, price |
| `sell_close` | 期货卖平 | id, amount, close_today |
| `sell_open` | 期货卖开 | id, amount, price |
| `buy_close` | 期货买平 | id, amount, close_today |

### B. 数据函数速查

| 函数 | 用途 |
|------|------|
| `history_bars` | 历史 Bars |
| `get_price` | 历史价格 |
| `get_factor` | 因子数据 |
| `get_pit_financials_ex` | 财务数据 |
| `index_components` | 指数成分 |
| `industry` | 行业股票 |
| `get_trading_dates` | 交易日 |

### C. 文档链接

- 量化平台: https://www.ricequant.com/doc/quant/
- 投资研究: https://www.ricequant.com/doc/quant/research
- 因子研究: https://www.ricequant.com/doc/quant/factor-system
- 回测: https://www.ricequant.com/doc/quant/backtest
- 模拟交易: https://www.ricequant.com/doc/quant/pt
- 策略API: https://www.ricequant.com/doc/quant/strategy-api
- 策略实例: https://www.ricequant.com/doc/quant/strategy-sample
- 技术分析: https://www.ricequant.com/doc/quant/technical-analysis
