# RQAlpha Plus 策略回测引擎文档

> 量化交易策略框架（引擎）

## 简介

RQAlphaPlus 是由 Ricequant 开发的量化交易策略框架。主要功能：

- 将金融模型和投资理念编写成代码脚本
- 在指定历史行情下进行回测以检验模型有效性
- 编写完善的交易系统
- 应用于模拟交易和实盘交易

### 核心特点

- 大幅降低量化投研门槛
- 高度封装量化交易全流程
- 事件驱动模型
- 基于 Python，支持第三方库调用
- 兼具易用性和扩展性

---

## 支持的品种

| 品种 | 回测频率 | 功能说明 | 数据更新时间 |
|------|----------|----------|--------------|
| 股票 | 日级别（基础版） | 日级别股票回测，支持 T+1、分红拆分等 | 每日收盘后 |
| 股票 | 分钟 | 分钟级别调仓，支持动态复权 | 每日收盘后 |
| 股票 | tick | tick 数据驱动，支持拟真撮合模型 | 每日收盘后 |
| 商品、股指、国债期货 | 日级别（基础版） | 日级别期货回测，逐日盯市 | 每日收盘后 |
| 商品、股指、股债期货 | 分钟和 tick | 多种撮合模型 | 每日收盘后 |
| 期权 | 日、分钟、Tick | 支持混合回测，支持行权操作 | 每日收盘后 |
| 可转债 | 日、分钟、Tick | 支持混合回测，自动处理还本付息 | 每日收盘后 |
| 指数 | 日级别（基础版） | 直接交易指数，混合回测 | 每日收盘后 |
| 场外公募基金 | 日级别 | 支持申购赎回，自动处理 T+N 逻辑 | 每日收盘后 |

---

## 快速开始

### 第一个策略

**简单买入持有策略：**
```python
def init(context):
    context.fired = False

def handle_bar(context, bar_dict):
    if not context.fired:
        order_target_percent("000001.XSHE", 0.5)
        context.fired = True
```

**MACD 策略：**
```python
import talib

def init(context):
    context.stock = "000001.XSHE"
    context.SHORTPERIOD = 12
    context.LONGPERIOD = 26
    context.SMOOTHPERIOD = 9
    context.OBSERVATION = 100

def handle_bar(context, bar_dict):
    prices = history_bars(context.stock, context.OBSERVATION, '1d', 'close')
    macd, macd_signal, _ = talib.MACD(
        prices, context.SHORTPERIOD, context.LONGPERIOD, context.SMOOTHPERIOD
    )
    if macd[-1] > macd_signal[-1] and macd[-2] < macd_signal[-2]:
        order_target_percent(context.stock, 1)
    if macd[-1] < macd_signal[-1] and macd[-2] > macd_signal[-2]:
        if get_position(context.stock).quantity > 0:
            order_target_percent(context.stock, 0)
```

### 核心概念

| 概念 | 说明 |
|------|------|
| **策略** | 用户编写的代码逻辑集合，.py文件、函数或字符串 |
| **回调函数** | `init()`、`before_trading()`、`handle_bar()` - 特定时间调用的函数 |
| **Data Bundle** | 本地数据文件（基础数据、交易日历、价格数据）用于加速策略执行 |
| **APIs** | 数据查询、仓位检查、下单函数 |

---

## 数据准备

### 下载数据

**样本数据（试用客户）：**
```bash
rqsdk download-data --sample
```

**更新数据：**
```bash
rqsdk update-data --minbar 000001.XSHE --minbar RB --tick IO2002C3900
```

**自定义目录：**
```bash
rqsdk update-data -d D:\\user_bundle_path --minbar 000001.XSHE
```

---

## 运行策略

### 命令行方式

```bash
rqalpha-plus run -f macd_000001.py -a stock 100000 -s 20190101 -e 20191231 -bm 000300.XSHG -p
```

**参数说明：**
- `-f`: 策略文件
- `-a` / `--account`: 账户类型和资金
- `-s`: 开始日期
- `-e`: 结束日期
- `-bm`: 基准
- `-p` / `--plot`: 显示图表

### 函数入口方式

```python
config = {
    "base": {
        "accounts": {"STOCK": 100000},
        "start_date": "20190101",
        "end_date": "20191231",
    },
    "mod": {
        "sys_analyser": {
            "plot": True,
            "benchmark": "000300.XSHG"
        }
    }
}

from rqalpha_plus import run_func
result = run_func(config=config, init=init, handle_bar=handle_bar)
```

### 获取结果

**获取汇总指标：**
```python
result['sys_analyser']["summary"]
# 返回: alpha, beta, sharpe, max_drawdown, total_returns 等
```

**可用结果键：** `summary`、`trades`、`portfolio`、`stock_account`、`stock_positions`

### 保存结果

```bash
rqalpha-plus run -f strategy.py -a stock 100000 -s 20190101 -e 20191231 -p -bm 000300.XSHG -o result.pkl --report report
```

输出文件：`report.xlsx`、`summary.csv`、`portfolio.csv`、`stock_account.csv`、`stock_positions.csv`、`trades.csv`

---

## 回调函数

### init(context)

策略初始化函数，在回测/实时模拟交易开始时触发一次。

```python
def init(context):
    context.stock = "000001.XSHE"
    context.fired = False
```

### handle_bar(context, bar_dict)

Bar 数据更新函数，用于日/分钟级策略。`bar_dict` 包含以 `order_book_id` 为键的 bar 对象数据。

```python
def handle_bar(context, bar_dict):
    price = bar_dict[context.stock].close
```

### handle_tick(context, tick)

Tick 级快照数据更新。支持多个合约分别触发，触发时间包括集合竞价和连续交易时段。

### open_auction(context, bar_dict)

盘前集合竞价阶段回调。`bar_dict` 包含不完整的 bar 对象，有 `open`、`limit_up`、`limit_down` 等集合竞价阶段数据。

### before_trading(context)

每日盘前回调。触发时间取决于当前订阅合约的交易时间（期货夜盘可能在前一晚触发）。

### after_trading(context)

收盘后回调。在实时模拟交易中，该回调会在每天 15:30 触发。

---

## 交易接口

### 订单类型

| 类型 | 参数 | 描述 |
|------|------|------|
| `MarketOrder()` | 无 | 市价单 |
| `LimitOrder(limit_price)` | float price | 限价单 |
| `TWAPOrder(start_min, end_min)` | int, int | 时间加权价格算法订单 |
| `VWAPOrder(start_min, end_min)` | int, int | 成交量加权价格算法订单 |

### 股票交易函数

**order_shares(id_or_ins, amount, price_or_style)** - 按股数下单
- `amount`: 正数买入，负数卖出，向下调整为100股倍数

**order_lots(id_or_ins, amount, price_or_style)** - 按手数下单

**order_value(id_or_ins, cash_amount, price_or_style)** - 按金额下单

**order_percent(id_or_ins, percent, price_or_style)** - 按投资组合总权益比例下单

**order_target_value(id_or_ins, cash_amount, price_or_style)** - 调整至目标价值

**order_target_percent(id_or_ins, percent, price_or_style)** - 调整至目标仓位比例

**order_target_portfolio(target_portfolio, price_or_styles)** - 批量调整股票组合仓位

### 期货/期权函数

**submit_order(id_or_ins, amount, side, price, position_effect)** - 通用下单接口

**order(order_book_id, quantity, price_or_style)** - 全品种通用智能下单

**order_to(order_book_id, quantity, price_or_style)** - 全品种通用智能调仓

**buy_open / sell_open** - 买入开仓 / 卖出开仓

**buy_close / sell_close** - 买入平仓 / 卖出平仓（支持 `close_today=True` 指定平今仓）

### 其他函数

**exercise(id_or_ins, amount, convert)** - 期权/转债行权

**cancel_order(order)** - 撤销指定订单

**get_open_orders()** - 获取当日未成交订单

### 基金申购赎回

| 函数 | 说明 |
|------|------|
| `subscribe_value` | 按金额申购 |
| `subscribe_percent` | 按比例申购 |
| `subscribe_shares` | 按份额申购 |
| `redeem_value` | 按金额赎回 |
| `redeem_percent` | 按比例赎回 |
| `redeem_shares` | 按份额赎回 |

---

## 仓位查询接口

### get_position

```python
get_position(order_book_id, direction=POSITION_DIRECTION.LONG)
```

获取指定标的和持仓方向的持仓对象。

**参数：**
| 名称 | 类型 | 描述 |
|------|------|------|
| order_book_id | str | 标的编号 |
| direction | Optional[POSITION_DIRECTION] | 持仓方向 |

**返回：** `Position`

**示例：**
```python
get_position('000001.XSHE', POSITION_DIRECTION.LONG)
# Output: StockPosition(order_book_id=000001.XSHE, direction=LONG, quantity=268600, ...)
```

### get_positions

```python
get_positions()
```

获取全部持仓对象数据。

**返回：** `List[Position]`

```python
get_positions()
# Output: [StockPosition(...), FuturePosition(...), ...]
```

---

## 数据查询接口

### 市场基础数据

| 函数 | 说明 |
|------|------|
| `all_instruments(type=None)` | 返回所有合约基本信息 DataFrame。type: 'CS', 'ETF', 'LOF', 'INDX', 'Future', 'Spot', 'Option', 'Convertible' |
| `instruments(id_or_symbols)` | 返回 Instrument 或 List[Instrument] 详细合约信息 |
| `get_trading_dates(start_date, end_date)` | 返回日期范围内的交易日 DatetimeIndex |
| `get_previous_trading_date(date, n=1)` | 返回前第n个交易日 |
| `get_next_trading_date(date, n=1)` | 返回后第n个交易日 |
| `get_yield_curve(date=None, tenor=None)` | 返回国债收益率曲线 DataFrame。tenor: '0S'(隔夜), '1M', '1Y' 等 |

### 行情数据

**history_bars(order_book_id, bar_count, frequency, fields=None, skip_suspended=True, include_now=False, adjust_type='pre')**

返回历史 bar 数据 ndarray。frequency: '1d', '1m', '1w'。fields 包括：datetime, open, high, low, close, volume, total_turnover, open_interest, basis_spread, settlement。

**current_snapshot(order_book_id)**

返回当前市场快照 TickObject。

**history_ticks(order_book_id, count)**

返回历史 tick 列表（仅 tick 级策略）。

**get_price(order_book_ids, start_date, end_date=None, frequency='1d', fields=None, adjust_type='pre', skip_suspended=False, expect_df=False)**

返回历史价格数据 DataFrame/Series/Panel。支持 tick 数据。

**get_price_change_rate(order_book_ids, count=1, expect_df=False)**

返回历史价格变化率 DataFrame/Series。

### 股票数据

| 函数 | 说明 |
|------|------|
| `industry(code)` | 返回指定行业的股票列表 |
| `sector(code)` | 返回指定板块的股票列表 |
| `get_dividend(order_book_id, start_date)` | 返回分红数据 ndarray |
| `is_suspended(order_book_id, count=None)` | 返回停牌状态 |
| `is_st_stock(order_book_id, count=None)` | 返回 ST 状态 |
| `get_split(order_book_ids, start_date=None)` | 返回拆股数据 DataFrame |
| `get_securities_margin(order_book_ids, count=1, fields=None)` | 返回融资融券数据 |
| `concept(*concept_names)` | 返回概念股列表 |
| `get_margin_stocks(exchange=None, margin_type='all')` | 返回融资标的列表 |
| `get_shares(order_book_ids, count=1, fields=None)` | 返回股本数据 |
| `get_turnover_rate(order_book_ids, count=1, fields=None)` | 返回换手率数据 |
| `get_factor(order_book_ids, factors, count=1, universe=None)` | 返回因子数据 |
| `get_industry(industry, source='citics')` | 返回行业分类数据 |
| `get_instrument_industry(order_book_ids, source='citics', level=1)` | 返回证券行业分类 |
| `get_stock_connect(order_book_ids, count=1, fields=None)` | 返回沪港通持股数据 |
| `current_performance(order_book_id, info_date=None, quarter=None, interval='1q')` | 返回财务快报 |
| `get_pit_financials_ex(order_book_ids, fields, count, statements='latest')` | 返回季度财务数据 |

### 指数数据

| 函数 | 说明 |
|------|------|
| `index_components(order_book_id, date=None)` | 返回指数成分股列表 |
| `index_weights(order_book_id, date=None)` | 返回指数成分股权重 Series |

### 期货数据

| 函数 | 说明 |
|------|------|
| `futures.get_dominant(underlying_symbol, rule=0)` | 返回主力合约代码 |
| `futures.get_member_rank(which, count=1, rank_by='short')` | 返回会员排名 DataFrame |
| `futures.get_warehouse_stocks(underlying_symbols, count=1)` | 返回仓单数据 DataFrame |
| `futures.get_dominant_price(underlying_symbols, start_date, end_date, frequency='1d', fields=None)` | 返回主力连续合约价格 MultiIndex DataFrame |

### 宏观经济

| 函数 | 说明 |
|------|------|
| `econ.get_reserve_ratio(reserve_type='all', n=1)` | 返回存款准备金率 DataFrame |
| `econ.get_money_supply(n=1)` | 返回货币供应量 DataFrame |

---

## 文档链接

- 文档目录: `/doc/rqalpha-plus/doc/index-rqalphaplus`
- 快速上手: `/doc/rqalpha-plus/doc/quick-start`
- 进阶教程: `/doc/rqalpha-plus/doc/advance-tutorial`
- 常见问题: `/doc/rqalpha-plus/doc/question`
- 示例策略: `/doc/rqalpha-plus/doc/example`
- API 手册: `/doc/rqalpha-plus/api/index-rqalphaplus`
