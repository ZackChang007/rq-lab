# RiceQuant 数据下载进度

> 更新时间: 2026-05-09

## 下载状态：⚠️ 配额已用完

**流量使用**: 已用完（配额 1024 MB）
**重置时间**: 每日午夜 00:00 Beijing Time

---

## 已完成数据

### 元数据（完整）
| 类别 | 文件 | 行数 |
|------|------|------|
| 合约列表（11类） | `instruments/` | 236,655 |
| 交易日历 | `calendar/trading_dates.json` | 5,343 |
| 收益率曲线 | `yield_curve/` | 6,072 |
| 因子名称 | `stock/factor_names.json` | 13,482 |

### A股数据（完整）
| 类别 | 文件 | 行数 | 时间范围 |
|------|------|------|----------|
| 日线行情 | `stock/price_1d.parquet` + 分年批次 | 15.7M+ | 2005-2026 |
| 分钟行情 | `stock/price_1m_sample.parquet` | 174,240 | 2024样本 |
| PIT财务 | `stock/pit_financials/` | 969,907 | 2005-2026 |
| 财务快报/预告 | `stock/current_performance.parquet` 等 | 18,714 | - |
| 分红/拆股 | `stock/dividend.parquet`, `stock/split.parquet` | 63,259 | - |
| 股本/换手率 | `stock/shares.parquet`, `stock/turnover_rate.parquet` | 598,839 | - |
| 停牌/ST | `stock/suspended.parquet`, `stock/st_stock.parquet` | 116 | - |
| 融资融券 | `stock/securities_margin.parquet` | 198,986 | - |
| 资金流向 | `stock/capital_flow.parquet` | 7,240,680 | 2020-至今 ✅ 2026-05-03 补全 |
| 行业分类 | `stock/instrument_industry.parquet` | 5,207 | - |
| 概念股 | `stock/concept_*.parquet` | 255 | - |
| 大宗交易 | `stock/block_trade.parquet` | 177,718 | ✅ 2026-05-07 新增 |
| 龙虎榜 | `stock/leader_shares_change.parquet` | 82,819 | ✅ 2026-05-07 新增 |
| 定向增发 | `stock/private_placement.parquet` | 3,915 | ✅ 2026-05-07 新增 |
| 限售股解禁 | `stock/restricted_shares.parquet` | 4,446,571 | ✅ 2026-05-07 新增 |
| 沪深通持股明细 | `stock/stock_connect_holding_details.parquet` | 56,542,831 | ✅ 2026-05-07 新增 |
| 股东户数 | `stock/holder_number.parquet` | 400,953 | ✅ 2026-05-07 新增 |

### 因子数据（三时间维度 - 完整）
| 类别 | 数量 | 文件 | 说明 |
|------|------|------|------|
| 年报因子（LYR） | 359 | `factor/*_lyr_0.parquet` | 最新年报值，2020-至今 |
| 季报因子（MRQ） | 359 | `factor/*_mrq_0.parquet` | 最新季报值，2020-至今 |
| 滚动因子（TTM） | 359 | `factor/*_ttm_0.parquet` | 滚动12月值，2020-至今 |
| 估值因子 | 23 | `factor/pe_*.parquet`, `factor/pb_*.parquet`, `factor/ps_*.parquet`, `factor/pcf_*.parquet` | PE/PB/PS/PCF 及其 ttm/lyr 变体，2020-至今 ✅ 2026-05-02 下载完成 |
| 技术因子 | 48 | `factor/*.parquet` | ACCER, ADTM, ADX, ADXR, AMP系列, AMV系列, AR, AROON, ASI, ATR, BBI, BBIBOLL, BIAS等 + MA/MACD/RSI/KDJ/BOLL/CCI/VOL ✅ 2026-05-03 |
| 财务细分+其他因子 | 1305 | `factor/*.parquet` | ✅ 2026-05-09 新增 389 个 |

**因子总计**: 2453 个 Parquet 文件（三时间维度完整 + 估值因子 + 技术因子 + 财务细分/其他因子）

### 指数数据（完整）
| 类别 | 文件 | 行数 |
|------|------|------|
| 日线行情（7832指数） | `index/price_1d.parquet` | 16,431,631 |
| 行业指数行情 | `index/industry_price.parquet` | 550,200 |
| 分钟行情（3指数） | `index/minute_*.parquet` | 174,240 |
| 成分股（9指数） | `index/components/` | 28,378 |
| 权重（9指数） | `index/weights/` | 15,355,048 |

### 期货数据（完整）
| 类别 | 文件 | 行数 |
|------|------|------|
| 主力合约（15品种） | `futures/dominant_*.parquet` | 19,868 |
| 会员排名 | `futures/member_rank.parquet` | 59,840 |
| 仓单数据 | `futures/warehouse_stocks.parquet` | 136,246 |
| 展期收益 | `futures/roll_yield.parquet` | 142,585 |

### 可转债数据（完整）
| 类别 | 文件 | 行数 |
|------|------|------|
| 合约列表 | `convertible/all_instruments.parquet` | 1,088 |
| 日线行情 | `convertible/price_1d_*.parquet` | 748,824 |
| 估值指标 | `convertible/indicators.parquet` | 744,976 |
| 其他（转股/赎回/评级等） | `convertible/*.parquet` | 110,000+ |

### 期权数据（部分）
| 类别 | 文件 | 行数 |
|------|------|------|
| 合约列表 | `options/all_instruments.parquet` | 207,768 |
| 合约详情 | `options/contracts_*.json` | 7,722 |

### 基金数据（完整）
| 类别 | 文件 | 行数 |
|------|------|------|
| 基金列表 | `fund/all_instruments.parquet` | 30,478 |
| 净值数据 | `fund/nav.parquet` | 1,199,200 |
| 分红/拆分 | `fund/dividend.parquet`, `fund/split.parquet` | 59,061 |
| 持仓/配置（52季度） | `fund/holdings_*.parquet` 等 | 200,000+ |

### 风险因子数据（完整）
| 类别 | 文件 | 行数 |
|------|------|------|
| 因子暴露 v1 | `risk_factor/factor_exposure_v1.parquet` | 1,328,534 |
| 因子暴露 v2 | `risk_factor/factor_exposure_v2.parquet` | 1,328,534 |
| 股票Beta | `risk_factor/stock_beta.parquet` | 2,993 |

### 另类数据（完整）
| 类别 | 文件 | 行数 |
|------|------|------|
| 一致预期综合指标 | `alternative/consensus/comp_indicators.parquet` | 272,392 |
| 一致预期指标 | `alternative/consensus/indicator.parquet` | 8,908 |
| 行业评级（20行业） | `alternative/consensus/industry_rating.parquet` | 212,136 |
| 行业评级（全部） | `alternative/consensus/industry_rating_all.parquet` | 601,658 |

### 宏观数据（完整）
| 类别 | 文件 | 行数 |
|------|------|------|
| 准备金率 | `macro/reserve_ratio.parquet` | 44 |
| 货币供应 | `macro/money_supply.parquet` | 363 |
| 同业拆借利率 | `macro/interbank_offered_rate.parquet` | 3,073 |
| 宏观因子（3901种） | `macro/factors/all_factors.parquet` | 823,432 | ✅ 2026-05-07 |

**宏观因子类别**：GDP、CPI、PPI、PMI、社会融资规模、政府债务、房地产开发投资等

### ETF/LOF数据
| 类别 | 文件 | 行数 |
|------|------|------|
| ETF行情 | `etf/price_1d_*.parquet` | 1,424,316 |
| LOF行情 | `lof/price_1d_*.parquet` | 883,061 |

---

## 不可用API（试用账号权限限制）

| API | 原因 |
|-----|------|
| `rqdatac.news` | 模块不存在 |
| `rqdatac.esg` | 模块不存在 |
| `rqdatac.macro` | 模块不存在 |
| `rqdatac.spot` | 模块不存在 |
| `options.get_greeks` | 返回空数据 |
| `options.get_contract_property` | 返回空数据 |
| 因子数据全量下载 | 总量约1TB，无法完成 |

---

## 文件统计

**总文件数**: 2453 个因子 Parquet 文件 + 其他数据文件
**总存储大小**: ~25 GB

---

## 备注

1. **财务因子数据（完整）**:
   - LYR（年报）: 359 个完整
   - MRQ（季报）: 359 个完整
   - TTM（滚动）: 359 个完整 ✅ 2026-05-01 下载完成
2. **估值因子**: 23 个完整 ✅ 2026-05-02 下载完成
3. **资金流向**: 7.24M 行 ✅ 2026-05-03 补全完成
4. **宏观因子**: 3901 种因子，823K 行 ✅ 2026-05-07 下载完成
5. **股票扩展数据**: 大宗交易/龙虎榜/定向增发/限售股解禁/沪深通持股明细 ✅ 2026-05-07 下载完成
6. **财务细分+其他因子**: 已下载 1305 个，剩余 ~1078 个待下载 ✅ 2026-05-09 新增 389 个
7. 期权希腊值数据在试用账号下不可用
8. 新闻、ESG、行业资金流向等模块需要更高级别权限
