# RQData 金融数据 API 文档

> 基于 Python 的金融数据工具包

## 简介

RQData 是一个基于 Python 的金融数据工具包，为量化工程师提供丰富整齐的历史数据以及简单高效的 API 接口，最大限度地免除数据搜索、清洗的烦恼。

### 数据覆盖范围

| 品种 | 数据内容 |
|------|----------|
| 中国 A 股 | 基本信息；10+年历史日/分钟/tick行情；实时行情；上市以来所有财务数据 |
| 场内基金 (ETF/LOF) | 基本信息；10+年历史行情；实时行情；ETF每日市场数据 |
| 可转债 | 基本信息；历史日/分钟/tick行情；实时行情 |
| 中国期货 | 基本信息；历史日/分钟/tick行情；实时行情 |
| 中国期权 | 基本信息；历史日/分钟/tick行情；实时行情 |
| 国债逆回购 | 基本信息；历史行情；实时行情 |
| 现货（上金所） | 基本信息；历史行情；实时行情 |
| 舆情大数据 | 情绪数据 |
| 因子数据 | 因子协方差、特异风险、收益率（需另行商务洽谈） |

---

## 安装与初始化

### 安装

```bash
pip install rqdatac

# 额外包（基金、新闻）
pip install "rqdatac[fund,news]"
```

### 初始化

```python
import rqdatac
rqdatac.init()
```

在 RQSDK 的 iPython 环境中，只需 `import rqdatac`。

### 常用信息查询

```python
# 版本信息
rqdatac.info()  # 返回版本、服务器地址、账户信息

# 流量配额查询
rqdatac.user.get_quota()  # 返回 bytes_limit, bytes_used, remaining_days, license_type
```

### 日期格式支持

- 数字：`20150101`
- 字符串：`"2015-01-01"`
- datetime/date 对象
- Pandas Timestamp

### 数据导出

API 返回 Pandas DataFrame；使用 `.to_csv('filename.csv')` 导出。

### 关键术语

**order_book_id**: 米筐内部对于合约代码、股票代码、债券代号等指向某个金融产品实例的编号的统称，跨市场全局唯一。

### 使用环境

1. **在线平台**: 无需设置，API 预导入
2. **本地安装**: 需要 Ricequant SDK 设置
3. **私有部署**: 联系商务安装本地服务器

### 流量说明

试用账户每日 1GB 流量限制。传输使用二进制协议和压缩，实际数据量约为原始的1/3。

---

## 跨品种通用 API

### 1. all_instruments

```python
all_instruments(type=None, date=None, market='cn')
```

获取指定市场所有合约基本信息。

**type 参数值：**
| 值 | 说明 |
|----|------|
| `'CS'` | 股票 |
| `'ETF'` | 交易型开放式基金 |
| `'LOF'` | 上市开放式基金 |
| `'INDX'` | 指数 |
| `'Future'` | 期货 |
| `'Spot'` | 现货 |
| `'Option'` | 期权 |
| `'Convertible'` | 可转债 |
| `'Repo'` | 回购 |
| `'REITs'` | 不动产投资信托 |
| `'FUND'` | 其他基金 |

**返回：** pandas DataFrame，列：abbrev_symbol, order_book_id, sector_code, symbol

---

### 2. instruments

```python
instruments(order_book_ids, market='cn')
```

获取一个或多个合约的详细信息。

**返回 Instrument 对象属性：**
- `order_book_id`、`symbol`、`abbrev_symbol`、`round_lot`
- `sector_code`、`sector_code_name`、`industry_code`、`industry_name`
- `listed_date`、`de_listed_date`、`issue_price`、`type`
- `exchange`、`board_type`、`status`、`special_type`
- `trading_hours`、`market_tplus`

**Instrument 方法：**
- `days_from_listed(date=None)` - 上市天数
- `days_to_expire(date=None)` - 到期天数
- `tick_size()` - 最小价格变动

---

### 3. id_convert

```python
id_convert(order_book_ids, to=None)
```

交易所/其他平台代码与米筐标准代码互转。
- `to='normal'` - 米筐格式转交易所格式
- `to=None` - 交易所格式转米筐格式

---

### 4. get_price

```python
get_price(order_book_ids, start_date=None, end_date=None, frequency='1d',
          fields=None, adjust_type='pre', skip_suspended=False,
          expect_df=True, time_slice=None, market='cn')
```

获取合约行情数据，支持周/日/分钟/tick 数据。

**频率选项：** `'1d'`、`'1w'`、`'1m'`、`'5m'`、`'15m'`、`'60m'`、`'tick'`

**复权类型：** `'none'`、`'pre'`、`'post'`、`'pre_volume'`、`'post_volume'`

**Bar 数据字段：** open, close, high, low, limit_up, limit_down, total_turnover, volume, num_trades, prev_close, settlement, prev_settlement, open_interest, trading_date, dominant_id, strike_price, contract_multiplier, iopv, day_session_open

**Tick 数据字段：** datetime, open, high, low, last, prev_close, total_turnover, volume, num_trades, limit_up, limit_down, open_interest, a1~a5, a1_v~a5_v, b1~b5, b1_v~b5_v, change_rate, trading_date, prev_settlement, iopv

---

### 5. get_auction_info

```python
get_auction_info(order_book_ids, start_date=None, end_date=None,
                 frequency='1d', fields=None, market='cn')
```

获取盘后固定价格交易数据（科创板、创业板）。

**频率：** `'1d'`、`'1m'`、`'tick'`

---

### 6. get_ticks

```python
get_ticks(order_book_id, start_date=None, end_date=None, expect_df=True, market='cn')
```

获取当日 level1 tick 快照（试用版无历史数据）。

---

### 7. get_live_ticks

```python
get_live_ticks(order_book_ids, start_dt=None, end_dt=None, fields=None, market='cn')
```

获取当前交易日 level1 tick，支持时间段切分。

---

### 8. get_open_auction_info

```python
get_open_auction_info(order_book_ids, start_date=None, end_date=None, fields=None, market='cn')
```

获取盘前集合竞价 level1 快照数据。

---

### 9. current_minute

```python
current_minute(order_book_ids, skip_suspended=False, fields=None, market='cn')
```

获取当日最新1分钟K线（仅股票）。

---

### 10. get_price_change_rate

```python
get_price_change_rate(order_book_ids, start_date=None, end_date=None, expect_df=True, market='cn')
```

获取历史价格变化率（仅股票、期货、指数、可转债）。基于前复权价格计算。

---

### 11. current_snapshot

```python
current_snapshot(order_book_ids, market='cn')
```

获取当前 level1 行情快照，支持集合竞价数据。

**返回 Tick 对象属性：** datetime, order_book_id, open, high, low, last, prev_settlement, prev_close, volume, total_turnover, limit_up, limit_down, open_interest, trading_phase_code, asks, ask_vols, bids, bid_vols, iopv, prev_iopv, close, settlement

**交易阶段代码：** 'T' - 正常交易, 'H' - 临时停牌, 'P' - 全天停牌

---

### 12-15. 交易日历

| 函数 | 说明 | 返回 |
|------|------|------|
| `get_trading_dates(start_date, end_date, market='cn')` | 获取日期范围内交易日列表 | `datetime.date list` |
| `get_previous_trading_date(date, n=1, market='cn')` | 获取前n个交易日 | `datetime.date` |
| `get_next_trading_date(date, n=1, market='cn')` | 获取后n个交易日 | `datetime.date` |
| `get_latest_trading_date(market='cn')` | 获取最新交易日（今日为交易日则返回今日） | `datetime.date` |

---

### 16-17. 交易时段

```python
# 已弃用
get_trading_hours(order_book_id, date=None, expected_fmt='str', frequency='1m', market='cn')

# 新 API
get_trading_periods(order_book_ids, start_date=None, end_date=None, frequency='1m', market='cn')
```

获取连续竞价交易时段。格式选项：`'str'`、`'time'`、`'datetime'`

---

### 18. get_yield_curve

```python
get_yield_curve(start_date=None, end_date=None, tenor=None, market='cn')
```

获取国债收益率曲线数据（2002年至今）。

**期限示例：** `'0S'`(隔夜)、`'1M'`(1个月)、`'1Y'`(1年)

**返回列：** 0S, 1M, 2M, 3M, 6M, 9M, 1Y, 2Y, 3Y, 4Y, 6Y, 7Y, 8Y, 9Y, 10Y...

---

### 19. get_live_minute_price_change_rate

```python
get_live_minute_price_change_rate(order_book_ids)
```

获取日内分钟累计收益率（股票和指数）。

---

### 20. get_future_latest_trading_date

```python
get_future_latest_trading_date(market='cn')
```

获取期货最新交易日（夜盘开盘 = 新交易日开始）。

---

### 21. get_vwap

```python
get_vwap(order_book_ids, start_date=None, end_date=None, frequency='1d')
```

获取成交量加权平均价数据。

**频率：** `'1d'`、`'1m'`、`'5m'` 等

---

### 22. LiveMarketDataClient（WebSocket 实时数据）

```python
from rqdatac import LiveMarketDataClient
client = LiveMarketDataClient()
client.subscribe('tick_000001.XSHE')     # 订阅 tick
client.subscribe('bar_000001.XSHE')      # 订阅 1分钟 bar
client.subscribe('bar_000001.XSHE_3m')   # 订阅 3分钟 bar
client.unsubscribe('tick_000002.XSHE')   # 取消订阅

# 阻塞模式
for market in client.listen():
    print(market)

# 非阻塞模式
client.listen(handler=handle_msg)
```

**支持资产：** A股、ETF、LOF、可转债、期货、期权、回购、现货

**支持频率：**
- Level1 tick 五档行情
- 1, 3, 5, 15, 30, 60 分钟 bar（合成）

---

## 合约类型 Instrument 字段

### 股票/ETF/指数

order_book_id, symbol, abbrev_symbol, round_lot, sector_code, sector_code_name, industry_code, industry_name, listed_date, de_listed_date, issue_price, exchange, board_type, status, special_type, trading_hours, market_tplus

### 期货

order_book_id, symbol, margin_rate, round_lot, listed_date, de_listed_date, contract_multiplier, underlying_symbol, maturity_date, exchange, trading_hours, product, start_delivery_date, end_delivery_date

### 期权

order_book_id, symbol, round_lot, listed_date, maturity_date, exchange, underlying_order_book_id, underlying_symbol, strike_price, option_type, exercise_type ('E'欧式/'A'美式), contract_multiplier

### 现货

order_book_id, symbol, exchange ('SGEX'), listed_date, de_listed_date, type ('Spot'), trading_hours, market_tplus

### 可转债

order_book_id, symbol, exchange, listed_date, de_listed_date, type ('Convertible'), market_tplus

---

## A 股 API

### 财务数据

#### get_pit_financials_ex - Point-in-Time 季度财务数据

```python
get_pit_financials_ex(order_book_ids, fields, start_quarter, end_quarter,
                      date=None, statements='latest', market='cn')
```

| 参数 | 类型 | 说明 |
|------|------|------|
| order_book_ids | str/str list | 必填，合约代码 |
| fields | list | 必填，利润表/资产负债表/现金流量表字段 |
| start_quarter | str | 必填，起始季度（如 '2015q2'） |
| end_quarter | str | 必填，结束季度（如 '2015q4'） |
| date | int/str/datetime | 查询日期，默认当前 |
| statements | str | 'all' 或 'latest'，默认 'latest' |
| market | str | 'cn'（默认）或 'hk' |

**返回：** pandas DataFrame，列：quarter, info_date, fields, if_adjusted

```python
get_pit_financials_ex(
    fields=['revenue', 'net_profit'],
    start_quarter='2018q2',
    end_quarter='2018q3',
    order_book_ids=['000001.XSHE', '000048.XSHE']
)
```

#### current_performance - 财务快报

```python
current_performance(order_book_ids, info_date=None, quarter=None,
                    interval='1q', fields=None, market='cn')
```

**关键字段：** operating_revenue, gross_profit, operating_profit, total_profit, np_parent_owners, basic_eps, roe 等

#### performance_forecast - 业绩预告

```python
performance_forecast(order_book_ids, info_date=None, end_date=None,
                     fields=None, market='cn')
```

**关键字段：** forecast_type, forecast_description, forecast_growth_rate_floor/ceiling, forecast_earning_floor/ceiling, forecast_np_floor/ceiling

---

### A 股因子数据

#### 数据处理方式

| 后缀 | 方式 | 说明 | 期数 |
|------|------|------|------|
| `_mrq_n` | 单季度 | 提供最近12期单季度数据，PIT处理避免前视偏差 | 12 |
| `_ttm_n` | TTM | 最近4个季度滚动合计（利润表/现金流量表）或平均（资产负债表） | 9 |
| `_lyr_n` | LYR | 最新年报数据 | 9 |

#### get_factor - 获取因子值

```python
get_factor(order_book_ids, factor, start_date=None, end_date=None,
           universe=None, expect_df=True, market='cn')
```

| 参数 | 类型 | 说明 |
|------|------|------|
| order_book_ids | str/str list | 必填 |
| factor | str/str list | 必填，因子名称（`get_all_factor_names()` 查看所有） |
| start_date | int/str/datetime | 起始日期 |
| end_date | int/str/datetime | 结束日期 |
| expect_df | boolean | 默认True，返回DataFrame |
| market | str | 'cn'（默认）或 'hk' |

---

### 财务衍生指标

#### 估值衍生指标

| 字段 | 描述 | 公式 |
|------|------|------|
| pe_ratio_lyr/ttm | 市盈率 | market_cap_3 / net_profit_parent_company |
| pb_ratio_lyr/ttm/lf | 市净率 | market_cap_3 / equity_parent_company |
| ps_ratio_lyr/ttm | 市销率 | market_cap_3 / operating_revenue |
| pcf_ratio_lyr/ttm | 市现率 | market_cap_3 / cash_flow_from_operating |
| dividend_yield_ttm | 股息率 | dividend_ttm / close_price |
| market_cap | 总市值 | total × close_price |
| ev_lyr/ttm/lf | 企业价值 | market_cap_3 + total_liabilities |

#### 经营衍生指标

| 字段 | 描述 | 公式 |
|------|------|------|
| diluted_earnings_per_share_lyr/ttm | 稀释每股收益 | net_profit_parent_company / total_shares |
| return_on_equity_lyr/ttm | ROE | net_profit_parent_company × 2 / (equity + prev_equity) |
| return_on_asset_lyr/ttm | ROA | ebit / total_assets |
| net_profit_margin_lyr/ttm | 净利率 | net_profit / operating_revenue |
| gross_profit_margin_lyr/ttm | 毛利率 | (revenue - cost) / revenue |

#### 现金流衍生指标

| 字段 | 描述 |
|------|------|
| cash_flow_per_share_lyr/ttm | 每股现金流 |
| fcff_lyr/ttm | 公司自由现金流 |
| fcfe_lyr/ttm | 股权自由现金流 |
| operating_cash_flow_per_share_lyr/ttm | 每股经营现金流 |

#### 财务衍生指标

| 字段 | 描述 |
|------|------|
| interest_bearing_debt_lyr/ttm/lf | 有息负债 |
| debt_to_asset_ratio_lyr/ttm/lf | 资产负债率 |
| current_ratio_lyr/ttm/lf | 流动比率 |
| quick_ratio_lyr/ttm/lf | 速动比率 |
| book_value_per_share_lyr/ttm/lf | 每股净资产 |

#### 增长衍生指标

| 字段 | 描述 |
|------|------|
| inc_revenue_lyr/ttm | 营收增长率 |
| net_profit_growth_ratio_lyr/ttm | 净利润增长率 |
| total_asset_growth_ratio_lyr/ttm/lf | 总资产增长率 |

---

### 技术指标因子

#### 均线类

- **MACD**: DIFF = EMA(CLOSE,12) - EMA(CLOSE,26), DEA = EMA(DIFF,9), HIST = (DIFF-DEA)×2
- **BOLL**: BOLL = MA(CLOSE,20), UP = BOLL + 2×STD, DOWN = BOLL - 2×STD
- **MA/EMA**: 3, 5, 10, 20, 30, 55, 60, 120, 250 周期

#### 超买超卖指标

- **KDJ**: RSV = (CLOSE-LLV(LOW,9))/(HHV(HIGH,9)-LLV(LOW,9))×100
- **RSI**: MA(MAX(CLOSE-LC,0),N) / MA(ABS(CLOSE-LC),N) × 100
- **WR**: (HHV(HIGH,N)-CLOSE)/(HHV(HIGH,N)-LLV(LOW,N)) × 100

#### 能量指标

- **OBV**: 基于价格方向的累计成交量
- **VOL**: 成交量移动平均
- **VWAP**: 成交量加权平均价

---

## 期货 API

### 连续合约类型

| 类型 | 代码后缀 | 说明 |
|------|----------|------|
| 主力连续 | 88/888/889 | IF88简单拼接，IF888前复权平滑，IF889后复权平滑 |
| 次主力连续 | 88A2 | 次主力合约 |
| 指数连续 | 99 | 按持仓量加权平均 |

### 主力合约切换规则

| 规则 | 说明 |
|------|------|
| rule=0 | 持仓量超过1.1倍时切换（默认） |
| rule=1 | 仅考虑最大昨仓 |
| rule=2 | 成交量与持仓量同为最大 |
| rule=3 | rule=0基础排除最后交易日 |

### API 函数

#### futures.get_dominant - 获取主力合约

```python
futures.get_dominant(underlying_symbol, start_date=None, end_date=None,
                     rule=0, rank=1, market='cn')
```

| 参数 | 类型 | 说明 |
|------|------|------|
| underlying_symbol | str | 必填，期货品种如'IF' |
| start_date/end_date | int/str/date | 日期范围 |
| rule | int | 主力选取规则(0-3) |
| rank | int | 1-主力，2-次主力，3-次次主力 |

**返回：** Pandas.Series

#### futures.get_contracts - 获取可交易合约

```python
futures.get_contracts(underlying_symbol, date=None, market='cn')
```

**返回：** str list

#### futures.get_dominant_price - 获取主力连续合约行情

```python
futures.get_dominant_price(underlying_symbols, start_date=None, end_date=None,
                           frequency='1d', fields=None, adjust_type='pre',
                           adjust_method='prev_close_spread', rule=0, rank=1,
                           time_slice=None)
```

**返回字段：** open, close, high, low, volume, total_turnover, settlement, open_interest, limit_up, limit_down, prev_settlement, dominant_id, trading_date

#### futures.get_ex_factor - 获取复权因子

```python
futures.get_ex_factor(underlying_symbols, start_date=None, end_date=None,
                      adjust_method=None, rule=0, rank=1, market='cn')
```

**返回：** DataFrame 含 ex_date, ex_factor, ex_cum_factor, ex_end_date

#### futures.get_contract_multiplier - 获取合约乘数

```python
futures.get_contract_multiplier(underlying_symbols, start_date=None,
                                end_date=None, market='cn')
```

**返回：** DataFrame 含 contract_multiplier, exchange

#### futures.get_exchange_daily - 获取交易所日线

```python
futures.get_exchange_daily(order_book_ids, start_date=None, end_date=None,
                           fields=None, market='cn')
```

#### futures.get_continuous_contracts - 获取连续合约

```python
futures.get_continuous_contracts(underlying_symbol, start_date=None,
                                end_date=None, type='front_month', market='cn')
```

**type 选项：** `'front_month'`(近月)、`'next_month'`(次月)、`'current_quarter'`(当季)、`'next_quarter'`(下季)

**返回：** Pandas Series

#### futures.get_member_rank - 获取会员持仓排名

```python
futures.get_member_rank(obj, trading_date=None, start_date=None, end_date=None,
                        rank_by='short')
```

**rank_by 选项：** `'volume'`、`'long'`、`'short'`

**返回：** DataFrame 含 member_name, rank, volume, volume_change

#### futures.get_warehouse_stocks - 获取仓单数据

```python
futures.get_warehouse_stocks(underlying_symbols, start_date=None,
                             end_date=None, market='cn')
```

**返回：** DataFrame 含 on_warrant, exchange, effective_forecast, warrant_units, deliverable

#### futures.get_basis - 获取升贴水数据

```python
futures.get_basis(order_book_ids, start_date=None, end_date=None,
                  fields=None, frequency='1d')
```

**返回字段：** basis, basis_rate, basis_annual_rate, settle_basis, settle_basis_rate, settle_basis_annual_rate, index, close_index

#### futures.get_trading_parameters - 获取交易参数

```python
futures.get_trading_parameters(order_book_ids, start_date, end_date,
                               fields=None, market='cn')
```

**返回字段：** long_margin_ratio, short_margin_ratio, commission_type, open_commission, close_commission, close_commission_today, discount_rate, non_member_limit, client_limit, min_order_quantity, max_order_quantity

#### futures.get_roll_yield - 获取展期收益率

```python
futures.get_roll_yield(underlying_symbol, start_date=None, end_date=None,
                       type='main_sub', rule=0, market='cn')
```

**type 选项：** `'main_sub'`(主力-次主力)、`'near_main'`(近月-主力)

**返回字段：** from_contract, to_contract, yield, annualized_yield, annualized_yield_trading

---

## market 参数

| 值 | 说明 |
|----|------|
| `'cn'` | 中国大陆（默认） |
| `'hk'` | 香港市场 |

---

## 文档链接

- 使用说明: `/doc/rqdata/python/manual`
- 跨品种通用API: `/doc/rqdata/python/generic-api`
- A股: `/doc/rqdata/python/stock-mod`
- 港股: `/doc/rqdata/python/stock-hk`
- 期货: `/doc/rqdata/python/futures-mod`
- 期权: `/doc/rqdata/python/options-mod`
- 指数、场内基金: `/doc/rqdata/python/indices-mod`
- 基金: `/doc/rqdata/python/fund-mod`
- 可转债: `/doc/rqdata/python/convertible-mod`
- 风险因子: `/doc/rqdata/python/risk-factors-mod`
- 现货: `/doc/rqdata/python/spot-goods`
- 货币市场: `/doc/rqdata/python/repo`
- 宏观经济: `/doc/rqdata/python/macro-economy`
- 另类数据: `/doc/rqdata/python/alternative-data`
- 米筐特色指数: `/doc/rqdata/python/ricequant-index`
