# RiceQuant 数据下载进度

> 更新时间: 2026-04-23 16:30

## 今日完成（Day 1）

| 类别 | 文件 | 行数 | 大小 |
|------|------|------|------|
| **元数据** | | | |
| - 合约列表（11类） | `instruments/all_instruments_*.parquet` | 236,655 | 7.2 MB |
| - 交易日历 | `calendar/trading_dates.parquet` | 5,343 | 17 KB |
| - 收益率曲线 | `yield_curve/yield_curve.parquet` | 6,072 | 1 MB |
| - 因子名称 | `stock/factor_names.json` | 13,482 | - |
| **A股行情** | | | |
| - 日线行情 | `stock/price_1d.parquet` | 15,739,615 | 859 MB |
| - 价格变化率 | `stock/price_change_rate.parquet` | 5,173 | 132 MB |
| **A股财务** | | | |
| - PIT财务(2005-2026) | `stock/pit_financials/*.parquet` (22年) | 969,907 | 85 MB |
| - 财务快报 | `stock/current_performance.parquet` | - | 727 KB |
| - 业绩预告 | `stock/performance_forecast.parquet` | - | 454 KB |
| **A股公司事件** | | | |
| - 分红 | `stock/dividend.parquet` | 50,325 | 733 KB |
| - 拆股 | `stock/split.parquet` | 12,934 | 250 KB |
| - 股本 | `stock/shares.parquet` | 302,945 | 392 KB |
| - 换手率 | `stock/turnover_rate.parquet` | 295,894 | 5.6 MB |
| - 停牌/ST | `stock/suspended.parquet` + `st_stock.parquet` | 116 | 5.2 MB |
| - 融资融券 | `stock/securities_margin.parquet` | 198,986 | 7.9 MB |
| - 标的列表 | `stock/margin_stocks.parquet` | 4,109 | 3 KB |
| - 沪港通 | `stock/stock_connect.parquet` | 3,750 | 85 KB |
| - 行业分类 | `stock/instrument_industry.parquet` | 5,207 | 41 KB |
| - 概念股 | `stock/concept_*.parquet` | 255 | - |

**今日下载文件数**: 58 个  
**今日存储大小**: ~1.1 GB  
**今日流量消耗**: 1,055 MB

---

## 待下载（流量刷新后继续）

| 类别 | 状态 | 预估流量 |
|------|------|----------|
| A股因子 | 待下载 | ~100 MB |
| 指数数据（行情+成分+权重） | 待下载 | ~150 MB |
| 期货数据（11个API） | 待下载 | ~100 MB |
| 期权数据（5个API） | 待下载 | ~50 MB |
| 可转债数据（16个API） | 待下载 | ~100 MB |
| 公募基金数据（25+API） | 待下载 | ~150 MB |
| 风险因子（v1/v2模型） | 待下载 | ~100 MB |
| 宏观+另类+现货 | 待下载 | ~50 MB |

**剩余预估流量**: ~800 MB（预计 2-3 天完成）

---

## 流量使用策略

1. **每日限额**: 1,024 MB
2. **安全余量**: 保留 100 MB，实际可用 ~900 MB
3. **优先级**: 核心数据优先，小文件填充空余

---

## 运行命令

```bash
# 设置环境变量
export RQDATAC2_CONF='tcp://license:DzrW...@rqdatad-pro.ricequant.com:16011'

# 运行下载脚本（从断点继续）
python scripts/download.py stock_factor    # A股因子
python scripts/download.py index           # 指数
python scripts/download.py futures         # 期货
python scripts/download.py options         # 期权
python scripts/download.py convertible    # 可转债
python scripts/download.py fund            # 公募基金
python scripts/download.py risk_factor     # 风险因子
python scripts/download.py macro_alt_spot  # 宏观+另类
```
