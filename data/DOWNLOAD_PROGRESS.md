# RiceQuant 数据下载进度

> 更新时间: 2026-04-25 14:30

## 已完成数据（截至 Day 2）

### 元数据（完整）
| 类别 | 文件 | 行数 | 大小 |
|------|------|------|------|
| 合约列表（11类） | `instruments/all_instruments_*.parquet` | 236,655 | 7.2 MB |
| 交易日历 | `calendar/trading_dates.json` | 5,343 | 74 KB |
| 收益率曲线 | `yield_curve/yield_curve.parquet` | 6,072 | 1 MB |
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

### A股事件（大部分完成）
| 类别 | 文件 | 行数 | 大小 |
|------|------|------|------|
| 分红 | `stock/dividend.parquet` | 50,325 | 733 KB |
| 拆股 | `stock/split.parquet` | 12,934 | 250 KB |
| 股本 | `stock/shares.parquet` | 302,945 | 392 KB |
| 换手率 | `stock/turnover_rate.parquet` | 295,894 | 5.6 MB |
| 停牌列表 | `stock/suspended.parquet` | 58 | 2.6 MB |
| ST股票 | `stock/st_stock.parquet` | 58 | 2.6 MB |
| 融资融券交易 | `stock/securities_margin.parquet` | 198,986 | 7.9 MB |
| 沪港通 | `stock/stock_connect.parquet` | 3,750 | 85 KB |
| 行业分类 | `stock/instrument_industry.parquet` | 5,207 | 41 KB |

**未完成**：
- `margin_stocks.parquet` - 融资融券标的列表
- `concept_*.parquet` - 概念股（日志显示完成但文件不存在）

**已下载文件总数**: 48 个 parquet + 2 个 JSON
**已存储大小**: ~1.1 GB

---

## 流量使用情况

| 日期 | 使用量 | 备注 |
|------|--------|------|
| 2026-04-23 | 1,055 MB | Day 1 下载元数据+A股核心数据 |
| 2026-04-24 | ~0 MB | 尝试下载因子失败 |
| 2026-04-25 | ~1053 MB | 今日配额已耗尽（显示初始921MB，实际调用超限） |

**今日状态**: 已用 1052.8 MB / 限额 1024 MB = 超限 -28.8 MB

---

## 待下载任务（流量刷新后继续）

按优先级排序：

| # | 步骤 | 预估流量 | 状态 |
|---|------|----------|------|
| 4 | A股因子（batch 0 失败） | ~100 MB | ⏳ 待重试 |
| 6 | 指数数据（行情+成分+权重） | ~150 MB | ⏳ 待下载 |
| 7 | 期货数据（11个API） | ~100 MB | ⏳ 待下载 |
| 8 | 期权数据（5个API） | ~50 MB | ⏳ 待下载 |
| 9 | 可转债数据（16个API） | ~100 MB | ⏳ 待下载 |
| 10 | 公募基金数据（25+API） | ~150 MB | ⏳ 待下载 |
| 11 | 风险因子（v1/v2模型） | ~100 MB | ⏳ 待下载 |
| 12 | 宏观+另类+现货 | ~50 MB | ⏳ 待下载 |
| 5 | 补缺 A股事件缺失文件 | ~5 MB | ⏳ 待补缺 |

**剩余预估总流量**: ~755 MB（预计 2-3 天完成）

---

## 运行命令（明日继续）

```bash
# 设置环境变量
export RQDATAC2_CONF='tcp://license:DzrW...@rqdatad-pro.ricequant.com:16011'

# 检查配额
python -c "import rqdatac; rqdatac.init(); print(rqdatac.user.get_quota())"

# 运行下载脚本（从断点继续）
python scripts/data/download.py stock_factor    # A股因子（优先）
python scripts/data/download.py index           # 指数
python scripts/data/download.py futures         # 期货
python scripts/data/download.py options         # 期权
python scripts/data/download.py convertible    # 可转债
python scripts/data/download.py fund            # 公募基金
python scripts/data/download.py risk_factor     # 风险因子
python scripts/data/download.py macro_alt_spot  # 宏观+另类
```

---

## 数据完整性检查

| 检查项 | 状态 |
|--------|------|
| 合约列表 11 类完整 | ✅ |
| 交易日历完整 | ✅ (JSON) |
| A股日线行情完整 | ✅ |
| A股PIT财务完整 | ✅ (22年) |
| A股事件大部分完成 | ⚠️ 缺 margin_stocks |
| 因子数据 | ❌ 失败 |
| 指数数据 | ❌ 未开始 |
| 期货数据 | ❌ 未开始 |
| 期权数据 | ❌ 未开始 |
| 可转债数据 | ❌ 未开始 |
| 公募基金数据 | ❌ 未开始 |
| 风险因子数据 | ❌ 未开始 |
| 宏观另类现货 | ❌ 未开始 |