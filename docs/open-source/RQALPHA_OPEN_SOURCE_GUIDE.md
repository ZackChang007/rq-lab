# RQAlpha 开源版使用指南

> 开源回测框架 | GitHub: https://github.com/ricequant/rqalpha | 文档: https://rqalpha.readthedocs.io

---

## 一、开源版概述

### 1.1 什么是 RQAlpha 开源版

RQAlpha 是一个可扩展、可替换的 Python 算法回测和交易框架，支持多种证券类型。提供从数据获取、算法交易、回测引擎、模拟交易到数据分析的全套解决方案。

**许可证**：非商业使用免费，商业使用需联系米筐官方。

### 1.2 与商业版 (RQAlpha Plus) 对比

| 功能 | RQAlpha 开源版 | RQAlpha Plus 商业版 |
|------|----------------|---------------------|
| 回测引擎 | ✅ 完整 | ✅ 完整 |
| 策略 API | ✅ 核心 API | ✅ 扩展 API |
| 股票交易 | ✅ 支持 | ✅ 支持 |
| 期货交易 | ✅ 支持 | ✅ 支持 |
| 数据源 | ⚠️ Bundle 免费 | ✅ RQData API |
| 分钟数据 | ❌ 需自行配置 | ✅ 官方提供 |
| 因子分析 | ❌ 无 | ✅ RQFactor |
| 组合优化 | ❌ 无 | ✅ RQOptimizer |
| 业绩归因 | ❌ 无 | ✅ RQPAttr |
| 模拟交易 | ⚠️ 需配置 | ✅ 官方平台 |
| 技术支持 | ⚠️ 社区 | ✅ 官方 |

**核心结论**：开源版提供完整的回测引擎和策略 API，可作为授权结束后的替代方案。

---

## 二、安装与配置

### 2.1 安装

```bash
# 使用豆瓣镜像（国内更快）
pip install -i https://pypi.douban.com/simple rqalpha

# 验证安装
rqalpha version
```

### 2.2 下载数据 Bundle

```bash
# 默认下载到 ~/.rqalpha/bundle/
rqalpha download-bundle

# 指定路径
rqalpha download-bundle -d /path/to/bundle
```

**Bundle 内容**：
- A股日线数据（免费）
- 合约基础信息
- 交易日历
- 分红拆分数据

### 2.3 生成配置文件

```bash
rqalpha generate-config
```

配置文件位置：`~/.rqalpha/config.yml`

---

## 三、策略运行

### 3.1 命令行运行

```bash
rqalpha run -f strategy.py -s 2016-06-01 -e 2016-12-01 \
    --account stock 100000 \
    --benchmark 000300.XSHG \
    --plot \
    -o result.pkl
```

**参数说明**：

| 参数 | 说明 |
|------|------|
| `-f` | 策略文件路径 |
| `-s` | 回测起始日期 |
| `-e` | 回测结束日期 |
| `--account stock 100000` | 股票账户初始资金 |
| `--benchmark` | 基准指数 |
| `--plot` | 图形化显示结果 |
| `-o result.pkl` | 保存结果文件 |

### 3.2 Python 调用

```python
from rqalpha import run_func

def init(context):
    context.stock = '000001.XSHE'

def handle_bar(context, bar_dict):
    order_target_percent(context.stock, 1.0)

config = {
    'base': {
        'start_date': '2016-06-01',
        'end_date': '2016-12-01',
        'accounts': {'stock': 100000},
        'benchmark': '000300.XSHG'
    }
}

result = run_func(init=init, handle_bar=handle_bar, config=config)
```

### 3.3 结果分析

```python
import pickle

# 加载结果
result = pickle.load(open('result.pkl', 'rb'))

# 结果结构
result.keys()
# ['summary', 'stock_portfolio', 'benchmark_portfolio', 
#  'positions', 'trades', 'plot_data']

# 查看绩效摘要
print(result['summary'])
```

---

## 四、策略编写框架

### 4.1 约定函数

```python
def init(context):
    """策略初始化，启动时触发一次"""
    context.stock = '000001.XSHE'
    context.window = 20

def before_trading(context):
    """每日开盘前调用，不可下单"""
    pass

def handle_bar(context, bar_dict):
    """每个 Bar 触发，核心策略逻辑"""
    prices = history_bars(context.stock, 20, '1d', 'close')
    # 交易逻辑...

def after_trading(context):
    """每日收盘后调用，不可下单"""
    pass

def handle_tick(context, tick):
    """Tick 数据触发（需启用 tick 频率）"""
    pass

def open_auction(context, bar_dict):
    """盘前集合竞价触发"""
    pass
```

### 4.2 Context 对象

```python
context.now            # 当前时间 (datetime)
context.portfolio      # 投资组合对象
context.universe       # 合约池
context.config         # 策略配置
```

### 4.3 Portfolio 对象

```python
portfolio.total_value      # 总资产
portfolio.cash             # 可用现金
portfolio.market_value     # 持仓市值
portfolio.daily_pnl        # 当日盈亏
portfolio.total_returns    # 累计收益率
portfolio.units            # 份额
portfolio.accounts         # 账户字典 {'stock': Account}
portfolio.positions        # 持仓字典
```

### 4.4 Position 对象

```python
position.order_book_id     # 合约代码
position.quantity          # 持仓数量
position.market_value      # 持仓市值
position.avg_price         # 平均成本
position.last_price        # 最新价格
position.pnl               # 累计盈亏
position.trading_pnl       # 交易盈亏
position.position_pnl      # 持仓盈亏
```

---

## 五、交易 API

### 5.1 订单类型

```python
from rqalpha.const import ORDER_TYPE

# 市价单
MarketOrder()

# 限价单
LimitOrder(limit_price=10.5)

# 算法订单（需扩展 Mod）
TWAPOrder(start_min=0, end_min=30)  # 时间加权
VWAPOrder(start_min=0, end_min=30)  # 成交量加权
```

### 5.2 股票交易函数

```python
# 指定股数（正数买入，负数卖出）
order_shares('000001.XSHE', 1000)
order_shares('000001.XSHE', -500, style=LimitOrder(10))

# 指定手数（1手=100股）
order_lots('000001.XSHE', 10)

# 指定金额
order_value('000001.XSHE', 10000)

# 指定比例（占总资产）
order_percent('000001.XSHE', 0.3)

# 目标价值（调整到指定市值）
order_target_value('000001.XSHE', 20000)

# 目标比例（调整到指定比例）
order_target_percent('000001.XSHE', 0.5)

# 批量调仓
target_portfolio = {
    '000001.XSHE': 0.3,
    '000002.XSHE': 0.3,
    '600000.XSHG': 0.4
}
order_target_portfolio(target_portfolio)
```

### 5.3 期货交易函数

```python
# 买开
buy_open('IF2501', 2)

# 卖平
sell_close('IF2501', 2, close_today=False)

# 卖开
sell_open('IF2501', 2)

# 买平
buy_close('IF2501', 2, close_today=False)

# 行权（期权）
exercise('M1905C2350', 1)
```

### 5.4 订单管理

```python
# 撤销订单
cancel_order(order)

# 获取未成交订单
orders = get_open_orders()
for order in orders:
    print(order.order_id, order.status)
```

### 5.5 持仓查询

```python
# 单个持仓
pos = get_position('000001.XSHE')
print(pos.quantity, pos.market_value)

# 全部持仓
positions = get_positions()
for obid, pos in positions.items():
    print(obid, pos.quantity)
```

---

## 六、数据查询 API

### 6.1 合约信息

```python
# 所有合约列表
all_instruments(type='CS')  # 'CS': 股票, 'INDX': 指数, 'ETF', 'Future'

# 合约详细信息
inst = instruments('000001.XSHE')
print(inst.symbol, inst.display_name, inst.listed_date)
```

### 6.2 历史行情

```python
# 历史 Bars
bars = history_bars('000001.XSHE', 20, '1d', 'close')
bars = history_bars('000001.XSHE', 10, '1d', ['open', 'close', 'high', 'low'])

# 历史 Tick（需配置）
ticks = history_ticks('000001.XSHE', 100)
```

### 6.3 当前数据

```python
# 当前快照
snapshot = current_snapshot('000001.XSHE')
print(snapshot.last, snapshot.bid, snapshot.ask)

# Bar 数据（handle_bar 中）
bar = bar_dict['000001.XSHE']
print(bar.open, bar.close, bar.high, bar.low, bar.volume)
```

### 6.4 交易日历

```python
# 交易日列表
dates = get_trading_dates('2016-01-01', '2016-12-31')

# 上一交易日
prev = get_previous_trading_date('2016-06-01')

# 下一交易日
next = get_next_trading_date('2016-06-01')
```

### 6.5 股票筛选

```python
# 行业股票
stocks = industry('bank')  # sw_l1 银行行业

# 板块股票
stocks = sector('Financials')

# 指数成分（需数据支持）
# components = index_components('000300.XSHG')
```

### 6.6 状态判断

```python
# 停牌判断
is_suspended('000001.XSHE', count=5)

# ST 判断
is_st_stock('000001.XSHE', count=5)
```

### 6.7 分红拆分

```python
# 分红数据
dividend = get_dividend('000001.XSHE', '2016-01-01')

# 拆分数据
split = get_split('000001.XSHE', '2016-01-01')
```

---

## 七、定时任务 Scheduler

### 7.1 每日运行

```python
def init(context):
    scheduler.run_daily(my_func)

def my_func(context, bar_dict):
    logger.info("Daily task executed")
```

### 7.2 定时间运行

```python
def init(context):
    # 开盘后 10 分钟运行
    scheduler.run_daily(my_func, time_rule=market_open(minute=10))
    
    # 收盘前 30 分钟运行
    scheduler.run_daily(my_func, time_rule=market_close(minute=30))
```

### 7.3 每周运行

```python
def init(context):
    # 每周一运行
    scheduler.run_weekly(my_func, weekday=0)
    
    # 每月第 10 个交易日运行
    scheduler.run_monthly(my_func, tradingday=10)
```

---

## 八、Mod 扩展系统

### 8.1 Mod 概述

Mod 是 RQAlpha 的扩展机制，通过实现接口可以组合各种功能逻辑。

### 8.2 内置 Mod

| Mod | 说明 |
|------|------|
| sys_accounts | 股票/期货订单 API 和持仓模型 |
| sys_analyser | 记录订单、交易、持仓；计算风险指标；输出 CSV/图表 |
| sys_progress | 回测进度显示 |
| sys_risk | 订单预风控验证 |
| sys_scheduler | 定时器执行周期任务 |
| sys_simulation | 模拟撮合引擎和回测事件源 |
| sys_transaction_cost | 股票/期货交易税费计算 |

### 8.3 Mod 管理

```bash
# 查看已安装 Mod
rqalpha mod list

# 启用 Mod
rqalpha mod enable xxx

# 禁用 Mod
rqalpha mod disable xxx
```

### 8.4 自定义 Mod

```python
from rqalpha.mod import AbstractMod

class MyMod(AbstractMod):
    def start_up(self, env, mod_config):
        """启动时初始化"""
        pass
    
    def tear_down(self, code, exception=None):
        """结束时清理"""
        pass

# 配置参数
__mod_config__ = """
my_param: 100
"""

def load_mod():
    return MyMod()
```

---

## 九、策略示例

### 9.1 买入持有策略

```python
def init(context):
    context.stock = '000001.XSHE'

def handle_bar(context, bar_dict):
    if get_position(context.stock).quantity == 0:
        order_target_percent(context.stock, 1.0)
```

### 9.2 金叉策略

```python
import talib

def init(context):
    context.stock = '000001.XSHE'
    context.short_period = 20
    context.long_period = 120

def handle_bar(context, bar_dict):
    prices = history_bars(context.stock, context.long_period + 1, '1d', 'close')
    
    short_ma = talib.SMA(prices, context.short_period)
    long_ma = talib.SMA(prices, context.long_period)
    
    cur_pos = get_position(context.stock).quantity
    shares = context.portfolio.cash / bar_dict[context.stock].close
    
    # 死叉卖出
    if short_ma[-1] - long_ma[-1] < 0 and short_ma[-2] - long_ma[-2] > 0 and cur_pos > 0:
        order_target_value(context.stock, 0)
    
    # 金叉买入
    if short_ma[-1] - long_ma[-1] > 0 and short_ma[-2] - long_ma[-2] < 0:
        order_shares(context.stock, int(shares))
```

### 9.3 MACD 策略

```python
import talib

def init(context):
    context.stock = '000001.XSHE'

def handle_bar(context, bar_dict):
    prices = history_bars(context.stock, 50, '1d', 'close')
    macd, signal, hist = talib.MACD(prices)
    
    cur_pos = get_position(context.stock).quantity
    
    # MACD 上穿信号线买入
    if hist[-1] > 0 and hist[-2] <= 0:
        order_target_percent(context.stock, 1.0)
    
    # MACD 下穿信号线卖出
    if hist[-1] < 0 and hist[-2] >= 0 and cur_pos > 0:
        order_target_percent(context.stock, 0)
```

### 9.4 双均线策略（多股票）

```python
import talib

def init(context):
    context.stocks = ['000001.XSHE', '000002.XSHE', '600000.XSHG']
    context.short_period = 5
    context.long_period = 20

def handle_bar(context, bar_dict):
    for stock in context.stocks:
        prices = history_bars(stock, 25, '1d', 'close')
        short_ma = talib.SMA(prices, context.short_period)
        long_ma = talib.SMA(prices, context.long_period)
        
        if short_ma[-1] > long_ma[-1] and short_ma[-2] <= long_ma[-2]:
            order_target_percent(stock, 0.33)
        elif short_ma[-1] < long_ma[-1] and short_ma[-2] >= long_ma[-2]:
            order_target_percent(stock, 0)
```

### 9.5 期货策略

```python
def init(context):
    context.future = 'IF2501'

def handle_bar(context, bar_dict):
    prices = history_bars(context.future, 20, '1d', 'close')
    ma = talib.SMA(prices, 10)
    
    pos = get_position(context.future)
    
    if prices[-1] > ma[-1] and pos.quantity == 0:
        buy_open(context.future, 1)
    elif prices[-1] < ma[-1] and pos.quantity > 0:
        sell_close(context.future, 1)
```

---

## 十、开源版使用场景

### 10.1 授权结束后可用功能

| 用途 | 开源版能力 | 需补充 |
|------|-----------|--------|
| 策略回测 | ✅ 完整支持 | 无 |
| 策略研究 | ✅ 支持 | 需自定义数据 |
| 股票交易 | ✅ 完整 API | 无 |
| 期货交易 | ✅ 完整 API | 需期货数据 |
| 技术分析 | ✅ TA-Lib 集成 | 无 |
| 绩效分析 | ✅ sys_analyser | 无 |

### 10.2 需要自行解决的部分

| 需求 | 解决方案 |
|------|----------|
| 分钟数据 | Tushare / AKShare / 自建数据库 |
| 财务数据 | Tushare / 东财 Choice |
| 因子分析 | Alphalens + TA-Lib |
| 组合优化 | 自研 / Riskfolio-lib |
| 模拟交易 | 接券商 API |

### 10.3 与开源工具组合方案

**推荐组合**：

```
RQAlpha (回测引擎)
    + Tushare/AKShare (数据源)
    + TA-Lib (技术指标)
    + Alphalens (因子分析)
    + Riskfolio-lib (组合优化)
```

### 10.4 数据源替代方案

| 数据类型 | Tushare | AKShare | 其他 |
|----------|---------|---------|------|
| 日线行情 | ✅ 免费 | ✅ 免费 | - |
| 分钟行情 | ⚠️ 积分 | ✅ 免费 | - |
| 财务数据 | ✅ 免费 | ⚠️ 部分 | 东财 |
| 因子数据 | ❌ | ❌ | 自建 |
| 行业分类 | ✅ | ✅ | - |

---

## 十一、迁移指南

### 11.1 从 RQAlpha Plus 迁移

**策略代码兼容性**：

```python
# RQAlpha Plus 策略
def init(context):
    context.stock = '000001.XSHE'

def handle_bar(context, bar_dict):
    order_target_percent(context.stock, 1.0)

# 直接可在开源版运行（无需修改）
```

**差异点**：

| RQAlpha Plus | RQAlpha 开源版 | 处理方式 |
|--------------|----------------|----------|
| `get_factor()` | ❌ 无 | 用 Tushare 替代 |
| `get_financials()` | ❌ 无 | 用 Tushare 替代 |
| `index_components()` | ❌ 无 | 用 Tushare 替代 |
| 分钟回测 | ✅ 支持 | 需自建分钟数据 |

### 11.2 数据源迁移示例

```python
# 原 RQData 方式
# import rqdatac
# rqdatac.init()
# df = rqdatac.get_price('000001.XSHE', '2020-01-01', '2023-12-31')

# 替换为 Tushare
import tushare as ts
ts.set_token('your_token')
pro = ts.pro_api()

df = pro.daily(ts_code='000001.SZ', 
               start_date='20200101', 
               end_date='20231231')

# 数据格式转换（适配 RQAlpha）
df = df.rename(columns={
    'ts_code': 'order_book_id',
    'trade_date': 'date',
    'vol': 'volume'
})
df['order_book_id'] = df['order_book_id'].str.replace('.SZ', '.XSHE')
df['order_book_id'] = df['order_book_id'].str.replace('.SH', '.XSHG')
```

---

## 附录：快速参考

### A. 常用命令

```bash
rqalpha version              # 查看版本
rqalpha download-bundle      # 下载数据
rqalpha generate-config      # 生成配置
rqalpha run -f xxx.py ...    # 运行回测
rqalpha mod list             # 查看 Mod
```

### B. 交易函数速查

| 函数 | 用途 | 示例 |
|------|------|------|
| `order_shares` | 指定股数 | `order_shares('000001.XSHE', 1000)` |
| `order_lots` | 指定手数 | `order_lots('000001.XSHE', 10)` |
| `order_value` | 指定金额 | `order_value('000001.XSHE', 10000)` |
| `order_percent` | 指定比例 | `order_percent('000001.XSHE', 0.3)` |
| `order_target_value` | 目标金额 | `order_target_value('000001.XSHE', 20000)` |
| `order_target_percent` | 目标比例 | `order_target_percent('000001.XSHE', 0.5)` |

### C. 数据函数速查

| 函数 | 用途 |
|------|------|
| `history_bars` | 历史 K 线 |
| `all_instruments` | 合约列表 |
| `instruments` | 合约详情 |
| `get_trading_dates` | 交易日 |
| `is_suspended` | 停牌判断 |
| `is_st_stock` | ST 判断 |
| `get_position` | 持仓查询 |

### D. 资源链接

- GitHub: https://github.com/ricequant/rqalpha
- 文档: https://rqalpha.readthedocs.io
- 社区: https://www.ricequant.com/community
- QQ群: 487188429