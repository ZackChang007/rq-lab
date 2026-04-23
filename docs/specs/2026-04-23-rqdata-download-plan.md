# RiceQuant 全量数据下载计划

> 目标：在试用期内（截至 2026-05-22）完整下载全部可获取数据，零遗漏
> 约束：每日 1GB 流量限制 | 仅日线频率 | Parquet 格式存储

## 一、数据下载总量估算与日程

### 流量估算（日线级别，每日 1GB 上限）

| 类别 | 主要 API | 预估流量 | 预估天数 |
|------|----------|----------|----------|
| 合约基本信息 | all_instruments, instruments | < 50MB | 0.1 |
| 交易日历 | get_trading_dates 等 | < 10MB | 0.1 |
| A股日线行情 | get_price(1d) | ~800MB | 2-3 |
| A股财务数据 | get_pit_financials_ex, current_performance, performance_forecast | ~300MB | 1 |
| A股因子 | get_factor + get_all_factor_names | ~500MB | 1-2 |
| A股公司事件 | get_dividend, get_split, get_shares, get_turnover_rate, is_suspended, is_st_stock, get_securities_margin, concept, get_margin_stocks, get_stock_connect, get_industry, get_instrument_industry | ~200MB | 1 |
| 收益率曲线 | get_yield_curve | < 20MB | 0.1 |
| 指数数据 | index_components, index_weights, get_price(1d) | ~400MB | 1-2 |
| 期货数据 | futures.* (11个API) | ~200MB | 1 |
| 期权数据 | options.* (5个API) | ~100MB | 0.5 |
| 可转债数据 | convertible.* (16个API) | ~100MB | 0.5 |
| 公募基金 | fund.* (25+个API) | ~300MB | 1-2 |
| 风险因子 | get_factor_exposure 等 7个API | ~300MB | 1 |
| 宏观经济 | econ.*, get_interbank_offered_rate | < 50MB | 0.1 |
| 另类数据 | consensus.*, news.*, esg.* | ~200MB | 1 |
| 现货数据 | get_spot_benchmark_price | < 20MB | 0.1 |
| **合计** | | **~3.5GB** | **~12-15 天** |

> 二进制压缩后实际传输量约为原始的 1/3，3.5GB 原始数据 ≈ 1.2GB 传输量
> 但加上请求开销和元数据，预留余量，计划 15-20 个工作日完成

## 二、目录结构

```
data/
├── instruments/          # 合约基本信息
│   ├── all_instruments_{type}.parquet
│   └── instruments_{obid}.parquet
├── calendar/             # 交易日历
│   └── trading_dates.parquet
├── yield_curve/          # 收益率曲线
│   └── yield_curve.parquet
├── stock/                # A 股数据
│   ├── price_1d.parquet
│   ├── price_change_rate.parquet
│   ├── vwap.parquet
│   ├── pit_financials.parquet
│   ├── current_performance.parquet
│   ├── performance_forecast.parquet
│   ├── dividend.parquet
│   ├── split.parquet
│   ├── shares.parquet
│   ├── turnover_rate.parquet
│   ├── suspended.parquet
│   ├── st_stock.parquet
│   ├── securities_margin.parquet
│   ├── margin_stocks.parquet
│   ├── stock_connect.parquet
│   ├── industry.parquet
│   ├── instrument_industry.parquet
│   ├── concept.parquet
│   └── factor_names.json
├── factor/               # A 股因子
│   ├── factor_{batch}.parquet
│   └── factor_names.json
├── index/                # 指数数据
│   ├── components/
│   │   └── {index_id}.parquet
│   ├── weights/
│   │   └── {index_id}.parquet
│   └── price_1d.parquet
├── futures/              # 期货数据
│   ├── dominant.parquet
│   ├── contracts.parquet
│   ├── dominant_price.parquet
│   ├── ex_factor.parquet
│   ├── contract_multiplier.parquet
│   ├── exchange_daily.parquet
│   ├── continuous_contracts.parquet
│   ├── member_rank.parquet
│   ├── warehouse_stocks.parquet
│   ├── basis.parquet
│   ├── trading_parameters.parquet
│   └── roll_yield.parquet
├── options/              # 期权数据
│   ├── contracts.parquet
│   ├── greeks.parquet
│   ├── contract_property.parquet
│   ├── dominant_month.parquet
│   └── indicators.parquet
├── convertible/          # 可转债数据
│   ├── all_instruments.parquet
│   ├── conversion_price.parquet
│   ├── conversion_info.parquet
│   ├── call_info.parquet
│   ├── put_info.parquet
│   ├── cash_flow.parquet
│   ├── indicators.parquet
│   ├── credit_rating.parquet
│   ├── close_price.parquet
│   ├── std_discount.parquet
│   ├── call_announcement.parquet
│   └── convertible_suspended.parquet
├── fund/                 # 公募基金数据
│   ├── all_instruments.parquet
│   ├── nav.parquet
│   ├── holdings.parquet
│   ├── asset_allocation.parquet
│   ├── industry_allocation.parquet
│   ├── bond_structure.parquet
│   ├── etf_components.parquet
│   ├── etf_cash_components.parquet
│   ├── dividend.parquet
│   ├── split.parquet
│   ├── fee.parquet
│   ├── ratings.parquet
│   ├── holder_structure.parquet
│   ├── units_change.parquet
│   ├── daily_units.parquet
│   ├── benchmark.parquet
│   ├── benchmark_price.parquet
│   ├── credit_quality.parquet
│   ├── financials.parquet
│   ├── indicators.parquet
│   ├── snapshot.parquet
│   ├── manager.parquet
│   ├── manager_info.parquet
│   ├── manager_indicators.parquet
│   ├── manager_weight_info.parquet
│   ├── qdii_scope.parquet
│   ├── instrument_category.parquet
│   ├── category_mapping.parquet
│   ├── related_code.parquet
│   └── transition_info.parquet
├── risk_factor/          # 风险因子数据
│   ├── factor_exposure_v1.parquet
│   ├── factor_exposure_v2.parquet
│   ├── descriptor_exposure.parquet
│   ├── stock_beta.parquet
│   ├── factor_return.parquet
│   ├── specific_return.parquet
│   ├── factor_covariance_daily.parquet
│   └── specific_risk_daily.parquet
├── macro/                # 宏观经济
│   ├── reserve_ratio.parquet
│   ├── money_supply.parquet
│   ├── macro_factors.parquet
│   └── interbank_offered_rate.parquet
├── alternative/          # 另类数据
│   ├── consensus/
│   │   ├── comp_indicators.parquet
│   │   ├── indicator.parquet
│   │   ├── price.parquet
│   │   ├── industry_rating.parquet
│   │   ├── market_estimate.parquet
│   │   ├── security_change.parquet
│   │   ├── expect_appr_exceed.parquet
│   │   ├── expect_prob.parquet
│   │   ├── factor.parquet
│   │   └── analyst_momentum.parquet
│   ├── news/
│   │   └── stock_news.parquet
│   └── esg/
│       └── rating.parquet
├── spot/                 # 现货数据
│   └── spot_benchmark_price.parquet
└── download_log.json     # 下载日志
```

## 三、执行步骤

### Step 1: 基础设施搭建
1. 创建 `data/` 目录结构
2. 编写通用下载工具函数（流量追踪、断点续传、错误重试）
3. 编写 `download_log.json` 日志系统（记录每次下载的 API、参数、行数、流量、时间戳）

### Step 2: 元数据下载（Day 1，低流量）
- `all_instruments()` 全品种（CS/ETF/LOF/INDX/Future/Spot/Option/Convertible/Repo/REITs/FUND）
- `get_trading_dates()` 全部交易日
- `get_yield_curve()` 全部收益率曲线
- `get_all_factor_names()` 因子名称列表
- 各品种 `instruments()` 详情

### Step 3: A 股核心数据（Day 2-5）
- `get_price(1d)` 全 A 股日线行情（分批，按日期范围）
- `get_pit_financials_ex()` 财务数据（按季度分批）
- `current_performance()` + `performance_forecast()`
- `get_factor()` 因子数据（按因子批次分批）

### Step 4: A 股公司事件数据（Day 6）
- `get_dividend()`, `get_split()`, `get_shares()`, `get_turnover_rate()`
- `is_suspended()`, `is_st_stock()`
- `get_securities_margin()`, `get_margin_stocks()`, `get_stock_connect()`
- `concept()`, `get_industry()`, `get_instrument_industry()`

### Step 5: 指数数据（Day 7-8）
- `index_components()` + `index_weights()` 按主要指数
- 指数日线行情 `get_price(1d)`

### Step 6: 期货数据（Day 9）
- futures.* 全部 11 个 API

### Step 7: 期权数据（Day 10）
- options.* 全部 5 个 API

### Step 8: 可转债数据（Day 11）
- convertible.* 全部 16 个 API

### Step 9: 公募基金数据（Day 12-13）
- fund.* 全部 25+ 个 API

### Step 10: 风险因子数据（Day 14-15）
- get_factor_exposure 等 7 个 API（v1/v2 模型分别下载）
- 因子协方差按日下载

### Step 11: 宏观 + 另类 + 现货（Day 16-17）
- econ.*, Shibor, 现货基准价
- consensus.* 全部 10 个 API
- news.*, esg.*

### Step 12: 验证与补缺（Day 18-20）
- 逐 API 校验下载完整性（行数、字段数）
- 补充失败/中断的数据
- 生成数据清单 `data/DATA_MANIFEST.md`

## 四、关键技术设计

### 流量控制
```python
# 每日下载前检查剩余流量
quota = rqdatac.user.get_quota()
remaining = quota['bytes_limit'] - quota['bytes_used']
# 当日流量接近 900MB 时停止，留 100MB 余量
```

### 断点续传
```python
# download_log.json 记录每次成功下载
# 重启时跳过已完成的任务
{
    "2026-04-23": {
        "stock/price_1d": {"status": "done", "rows": 1234567, "bytes": 800000000},
        "stock/pit_financials": {"status": "done", "rows": 500000, "bytes": 300000000}
    }
}
```

### 错误处理
- 单个 API 调用失败：重试 3 次，间隔 10s
- 超出流量限制：当日停止，次日继续
- 数据为空：记录警告但标记为 done

### Parquet 写入规范
```python
df.to_parquet(
    f'data/{category}/{api_name}.parquet',
    engine='pyarrow',
    compression='snappy',  # 速度与压缩率平衡
    index=True
)
```

## 五、验收标准

- [ ] 12 大类 80+ API 全部调用完成
- [ ] download_log.json 无 status=failed 的记录
- [ ] 每个 parquet 文件可正常读取且行数 > 0
- [ ] 总数据量与预估值在合理范围内
- [ ] 生成 DATA_MANIFEST.md 完整清单
