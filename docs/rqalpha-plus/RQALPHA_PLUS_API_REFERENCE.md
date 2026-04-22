# RQAlpha Plus API 参考

## 配置参数

配置分为三个部分：**Base**、**Mod** 和 **Extra**。

### Base 配置

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `data_bundle_path` | `"~/.rqalpha-plus/bundle"` | 数据包存储路径 |
| `start_date` | `"2015-06-01"` | 策略开始日期 |
| `end_date` | `"2050-01-01"` | 策略结束日期 |
| `margin_multiplier` | `1` | 保证金率乘数 |
| `frequency` | `"1d"` | 回测频率：`"1d"`/`"1m"`/`"tick"` |
| `accounts` | `{}` | 账户设置及初始资金 |
| `init_positions` | `""` | 初始持仓，格式：`000001.XSHE:1000,IF1701:-1` |
| `rqdatac_uri` | `""` | 设为 `'disabled'` 禁用 |
| `futures_time_series_trading_parameters` | `True` | 启用期货历史交易参数 |
| `auto_update_bundle` | `True` | 回测时自动下载数据包 |
| `auto_update_bundle_path` | `None` | 自动下载数据包的自定义路径 |

### Extra 配置

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `log_level` | `"info"` | 日志级别：`"debug"`/`"info"`/`"warning"`/`"error"` |
| `enable_profiler` | `False` | 启用性能分析 |
| `log_file` | `None` | 日志文件输出路径 |

### Mod 配置

#### sys_accounts（股票/期货账户）

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `stock_t1` | `True` | 启用股票 T+1 限制 |
| `dividend_reinvestment` | `False` | 自动红利再投资 |
| `cash_return_by_stock_delisted` | `True` | 退市时按退市价返还现金 |
| `auto_switch_order_value` | `False` | 资金不足时使用剩余资金 |
| `validate_stock_position` | `True` | 检查股票持仓是否可平仓 |
| `validate_future_position` | `True` | 检查期货持仓是否可平仓 |
| `financing_rate` | `0.00` | 年化融资利率 |
| `financing_stocks_restriction_enabled` | `False` | 启用融资股票限制 |
| `futures_settlement_price_type` | `"close"` | 日结算价：`"settlement"`/`"close"` |

#### sys_risk（风控）

| 参数 | 默认值 |
|------|--------|
| `validate_price` | `True` |
| `validate_is_trading` | `True` |
| `validate_cash` | `True` |
| `validate_self_trade` | `False` |

#### sys_simulation（撮合）

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `signal` | `False` | 信号模式，跳过撮合逻辑 |
| `matching_type` | `None` | 日频：`"current_bar"`/`"vwap"`；分钟：增加`"next_bar"`；Tick：`"last"`/`"best_own"`/`"best_counterparty"`/`"counterparty_offer"` |
| `price_limit` | `True` | 涨跌停限制交易 |
| `liquidity_limit` | `False` | 流动性限制（仅 tick） |
| `volume_limit` | `True` | 每 bar/tick 成交量限制 |
| `volume_percent` | `0.25` | 最大可成交比例 |
| `slippage_model` | `"PriceRatioSlippage"` | 滑点模型 |
| `slippage` | `0` | 滑点值 |
| `inactive_limit` | `True` | 限制零成交量证券 |
| `management_fee` | `[]` | 日账户费用：`[("STOCK", 0.0001), ...]` |

#### sys_transaction_cost（交易费用）

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `cn_stock_min_commission` | `5` | 股票最低佣金（元） |
| `stock_commission_multiplier` | `1` | 股票佣金乘数（默认0.08‰） |
| `futures_commission_multiplier` | `1` | 期货佣金乘数 |
| `tax_multiplier` | `1` | 印花税乘数（默认0.05‰） |
| `pit_tax` | `False` | 使用历史印花税率 |

#### sys_analyser（分析）

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `benchmark` | `None` | 单基准：`"000300.XSHG"`；复合基准：`"000300.XSHG:0.2,000905.XSHG:0.8"` |
| `record` | `True` | 回测时收集数据 |
| `strategy_name` | `None` | 报告中的策略名称 |
| `output_file` | `None` | Pickle 输出路径 |
| `report_save_path` | `None` | CSV 报告目录 |
| `plot` | `False` | 绘制结果图表 |
| `plot_save_file` | `None` | 图表 PNG 保存路径 |
| `plot_config.open_close_points` | `False` | 显示买卖点 |
| `plot_config.weekly_indicators` | `False` | 显示周指标 |

---

## 入口函数

### run_func

通过传入约定函数和策略配置运行回测。

**参数：**
- `config` (dict): 策略配置字典
- `init` (Callable): 策略初始化函数，仅在策略开始时调用一次
- `before_trading` (Callable): 盘前函数，每日盘前调用一次
- `open_auction` (Callable): 集合竞价函数，每日盘前集合竞价阶段调用
- `handle_bar` (Callable): K线处理函数，盘中K线更新时调用，适用于日/分钟级别回测
- `handle_tick` (Callable): 快照数据处理函数，每个 tick 到达时调用，适用于 tick 回测
- `after_trading` (Callable): 盘后函数，每日交易结束后调用一次

**返回：** dict

### run_file

```python
rqalpha.run_file(strategy_file_path, config=None)
```

通过传入策略代码文件运行回测。

**参数：**
- `strategy_file_path` (str): 策略文件路径
- `config` (Optional[dict]): 策略配置项字典，优先级高于策略内 config

**返回：** dict

### run_code

```python
rqalpha.run_code(code, config=None)
```

通过传入策略代码字符串运行回测。

**参数：**
- `code` (str): 策略代码字符串
- `config` (Optional[dict]): 策略配置项字典

**返回：** dict

---

## 类型与类

### Context（策略上下文）

`rqalpha.core.strategy_context.StrategyContext`

关键属性：
- `future_account`、`stock_account` - 账户对象
- `now` - 当前 Bar/Tick 时间
- `portfolio` - 投资组合对象，包含账户/持仓信息
- `run_info` - 策略运行信息
- `universe` - 合约池（触发 handle_bar）

### RunInfo（策略运行信息）

`rqalpha.core.strategy_context.RunInfo(config)`

包含：`commission_multiplier`、`start_date`、`end_date`、`frequency`、`margin_multiplier`、`matching_type`、`slippage`、`starting_cash` 等股票/期货账户配置值。

### BarObject（K线数据）

`rqalpha.model.bar.BarObject(instrument, data, dt=None)`

属性：`open`、`high`、`low`、`close`、`volume`、`total_turnover`、`datetime`、`last`、`limit_up`、`limit_down`、`prev_close`、`prev_settlement`、`settlement`、`open_interest`（期货）、`is_trading`、`order_book_id`、`symbol`。

### TickObject（快照数据）

`rqalpha.model.tick.TickObject(instrument, tick_dict)`

属性：`bids`/`asks`（价格列表）、`bid_vols`/`ask_vols`（成交量列表）、`datetime`、`last`、`high`、`low`、`open`、`volume`、`total_turnover`、`limit_up`、`limit_down`、`prev_close`、`prev_settlement`、`open_interest`。

### Order

`rqalpha.model.order.Order`

关键属性：`order_id`、`order_book_id`、`side`、`position_effect`、`status`、`style`、`type`、`price`、`quantity`、`filled_quantity`、`unfilled_quantity`、`avg_price`、`frozen_price`、`init_frozen_cash`、`transaction_cost`、`datetime`、`message`。

### Portfolio

`rqalpha.portfolio.Portfolio(starting_cash, init_positions, ...)`

关键属性：`accounts`（dict）、`positions`（dict）、`cash`、`frozen_cash`、`total_value`、`market_value`、`pnl`、`daily_pnl`、`daily_returns`、`total_returns`、`annualized_returns`、`unit_net_value`、`transaction_cost`、`starting_cash`、`start_date`。

方法：`deposit_withdraw()`、`finance_repay()`。

### Account

`rqalpha.portfolio.account.Account(account_type, total_cash, ...)`

关键属性：`cash`、`frozen_cash`、`cash_liabilities`、`market_value`、`position_equity`、`daily_pnl`、`position_pnl`、`trading_pnl`、`transaction_cost`、`buy_margin`、`sell_margin`（期货）、`total_value`、`total_cash`。

方法：`get_position(order_book_id, direction)`、`get_positions()`、`deposit_withdraw()`、`finance_repay()`、`set_management_fee_rate()`、`register_management_fee_calculator()`。

### StockPosition

`rqalpha.mod.rqalpha_mod_sys_accounts.position_model.StockPosition`

属性：`order_book_id`、`direction`、`quantity`、`closable`、`today_closable`、`avg_price`、`last_price`、`prev_close`、`market_value`、`pnl`、`position_pnl`、`trading_pnl`、`dividend_receivable`。

### FuturePosition

`rqalpha.mod.rqalpha_mod_sys_accounts.position_model.FuturePosition`

与 StockPosition 相同，另加 `margin` = quantity × latest_price × contract_multiplier × margin_rate。

### Instrument

`rqalpha.model.instrument.Instrument`

关键属性：`order_book_id`、`symbol`、`abbrev_symbol`、`round_lot`、`sector_code`、`industry_code`、`listed_date`、`de_listed_date`、`type`、`exchange`、`board_type`、`status`、`special_type`（股票）、`contract_multiplier`、`underlying_symbol`、`maturity_date`、`settlement_method`、`product`（期货）。

方法：`days_from_listed()`、`days_to_expire()`、`tick_size()`。

---

## 其他接口

### 通用接口

**update_universe(id_or_symbols)** - 更新当前合约池。接受单个或多个合约代码/名称。覆盖现有池。

**subscribe(id_or_symbols)** - 订阅合约行情（分钟/tick 级回测用）。

**unsubscribe(id_or_symbols)** - 取消订阅并从合约池移除。

**subscribe_event(event_type, handler)** - 订阅框架事件（订单创建、成交、撤单），传入回调函数。

**plot(series_name, value)** - 向策略结果图表添加自定义数据点，同名点连成曲线。

### 技术分析

**reg_indicator(name, factor, freq='1d', win_size=10)** - 注册技术指标计算规则。支持日（'1d'）和分钟频率。

**get_indicator(order_book_id, name)** - 获取指定证券的指标计算结果。

### 组合优化器

**portfolio_optimize(order_book_ids, objective, bnds, cons, benchmark, cov_model, factor_risk_aversion, specific_risk_aversion)** - 计算最优组合权重。

**目标函数：** MinVariance、MeanVariance、RiskParity、MinTrackingError、MaxInformationRatio、MaxSharpeRatio、MaxIndicator、MinStyleDeviation

**约束类型：** TrackingErrorLimit、TurnoverLimit、BenchmarkComponentWeightLimit、IndustryConstraint、StyleConstraint

### 定时器

**scheduler.run_daily(function)** - 每日在 handle_bar 后运行。

**scheduler.run_weekly(function, weekday=x, tradingday=t)** - 每周指定工作日（1-5）或交易日运行。

**scheduler.run_monthly(function, tradingday=t)** - 每月指定交易日运行（范围：-23 到 23）。

**time_rule** - 精确定时：
- `market_open(hour=x, minute=y)` - 开盘后
- `market_close(hour=x, minute=y)` - 收盘前
- `physical_time(hour=x, minute=y)` - 绝对时间
- `'before_trading'` - 开盘前
