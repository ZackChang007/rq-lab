# RiceQuant 数据下载进度

> 更新时间: 2026-04-28 11:30

## 已完成数据

### 元数据（完整）
| 类别 | 文件 | 行数 | 备注 |
|------|------|------|------|
| 合约列表（11类） | `instruments/all_instruments_*.parquet` | 236,655 | CS/ETF/LOF/INDX/Future/Spot/Option/Convertible/Repo/REITs/FUND |
| 交易日历 | `calendar/trading_dates.json` | 5,343 | - |
| 收益率曲线 | `yield_curve/yield_curve.parquet` | 6,072 | - |
| 因子名称 | `stock/factor_names.json` | 13,482 | - |

### A股行情（完整）
| 类别 | 文件 | 行数 | 大小 |
|------|------|------|------|
| 日线行情（2005-2026） | `stock/price_1d.parquet` | 15,739,615 | 859 MB |
| 价格变化率 | `stock/price_change_rate.parquet` | 5,173 | 132 MB |

### A股财务（完整）
| 类别 | 文件 | 行数 | 大小 |
|------|------|------|------|
| PIT财务（2005-2026） | `stock/pit_financials/*.parquet` (22年) | 969,907 | 92 MB |
| 财务快报 | `stock/current_performance.parquet` | 4,018 | 727 KB |
| 业绩预告 | `stock/performance_forecast.parquet` | 14,696 | 454 KB |

### A股事件（完整）
| 类别 | 文件 | 行数 |
|------|------|------|
| 分红 | `stock/dividend.parquet` | 50,325 |
| 拆股 | `stock/split.parquet` | 12,934 |
| 股本 | `stock/shares.parquet` | 302,945 |
| 换手率 | `stock/turnover_rate.parquet` | 295,894 |
| 停牌列表 | `stock/suspended.parquet` | 58 |
| ST股票 | `stock/st_stock.parquet` | 58 |
| 融资融券交易 | `stock/securities_margin.parquet` | 198,986 |
| 融资融券标的 | `stock/margin_stocks.parquet` | 4,109 |
| 沪港通 | `stock/stock_connect.parquet` | 3,750 |
| 行业分类 | `stock/instrument_industry.parquet` | 5,207 |
| 概念股 | `stock/concept_*.parquet` | 255 |

### 指数数据（完整）
| 类别 | 文件 | 状态 |
|------|------|------|
| 日线行情（7832指数） | `index/price_1d.parquet` | ✅ 16,431,631 行 |
| 成分股（9指数） | `index/components/*.parquet` | ✅ 序列化已修复 |
| 权重（9指数） | `index/weights/*.parquet` | ✅ 已完成 |

**主要指数**: 上证、沪深300、中证500/800/1000、上证50、深证成指、创业板指、中小板指

### 期货数据（完整）
| 类别 | 文件 | 行数 |
|------|------|------|
| 合约信息 | `futures/contracts_IF.parquet` | 4 |
| 会员排名 | `futures/member_rank.parquet` | 59,840 |
| 仓单数据 | `futures/warehouse_stocks.parquet` | 136,246 |
| 期现价差 | `futures/basis.parquet` | 0 |
| 展期收益 | `futures/roll_yield.parquet` | 142,585 |

### 可转债数据（完整）
| 类别 | 文件 | 行数 |
|------|------|------|
| 合约列表 | `convertible/all_instruments.parquet` | 1,088 |
| 转股价调整 | `convertible/conversion_price.parquet` | 5,346 |
| 转股信息 | `convertible/conversion_info.parquet` | 98,599 |
| 赎回信息 | `convertible/call_info.parquet` | 543 |
| 回售信息 | `convertible/put_info.parquet` | 447 |
| 现金流 | `convertible/cash_flow.parquet` | 3,595 |
| 估值指标 | `convertible/indicators.parquet` | 744,976 |
| 信用评级 | `convertible/credit_rating.parquet` | 4,585 |
| 收盘价 | `convertible/close_price.parquet` | 747,896 |
| 折溢价率 | `convertible/std_discount.parquet` | 75,187 |
| 赎回公告 | `convertible/call_announcement.parquet` | 1,525 |

### 期权数据（部分）
| 类别 | 文件 | 状态 |
|------|------|------|
| 期权合约（4品种） | `options/contracts_*.parquet` | ✅ 完成 |
| 希腊值 | `options/greeks.parquet` | ❌ 无有效合约代码 |
| 合约属性 | `options/contract_property.parquet` | ❌ 无有效合约代码 |

### 风险因子数据（部分）
| 类别 | 文件 | 行数 |
|------|------|------|
| 因子暴露 v1 | `risk_factor/factor_exposure_v1.parquet` | 1,328,534 |
| 因子暴露 v2 | `risk_factor/factor_exposure_v2.parquet` | 1,328,534 |
| 股票Beta | `risk_factor/stock_beta.parquet` | 2,993 |

---

## 流量使用情况

| 日期 | 使用量 | 备注 |
|------|--------|------|
| 2026-04-23 | 1,055 MB | 元数据+A股核心数据 |
| 2026-04-24 | ~0 MB | 尝试下载因子失败 |
| 2026-04-25 | ~1053 MB | 配额耗尽 |
| 2026-04-26 | ~17 MB | 尝试因子失败 |
| 2026-04-27 | ~28 MB | 因子+指数权重+期货 |
| 2026-04-28 | ~926 MB | 指数行情+可转债+期权+风险因子 |

**当前状态**: 已用 926.4 MB / 限额 1024.0 MB

---

## 待下载任务（明日继续）

| # | 步骤 | 状态 | 备注 |
|---|------|------|------|
| 1 | 公募基金数据 | ⏳ 待下载 | 基金列表、净值、持仓等 |
| 2 | 宏观+另类+现货 | ⏳ 待下载 | 宏观经济、另类数据、现货数据 |
| 3 | 补充期权希腊值 | ⏳ 待修复 | 需获取有效期权合约代码 |

**因子数据策略**: 因子数据总量约 1TB（13,482 个因子 × 80MB/因子），无法全量下载。建议按需下载关键因子，或使用 RQFactor 在线计算。

---

## 运行命令

```bash
# 检查配额
python -c "import rqdatac; from utils.common import setup_license; setup_license(); rqdatac.init(); print(rqdatac.user.get_quota())"

# 运行下载脚本
python scripts/data/download.py fund            # 公募基金
python scripts/data/download.py macro_alt_spot  # 宏观+另类
```

---

## 文件统计

**已下载文件**: 100+ 个 Parquet + JSON 文件
**存储大小**: ~2.5 GB
