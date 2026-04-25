# Ricequant 全链条使用指南

> 从因子研究到业绩归因的完整流程
> 最后更新：2026-04-25

---

## 概述

本文档介绍 Ricequant 量化研究全链条的使用方法，涵盖四个核心阶段：

```
因子研究 → 组合优化 → 策略回测 → 业绩归因
(RQFactor)  (RQOptimizer) (RQAlpha+)  (RQPAttr)
```

---

## 环境准备

### 1. 许可证配置

```bash
cp config/credentials.example.py config/credentials.py
# 编辑 credentials.py 填入许可证密钥
```

### 2. 初始化代码

```python
from utils.common import setup_license, QUOTA_SAFE_CONFIG
import rqdatac

setup_license()  # 设置环境变量
rqdatac.init()   # 初始化 RQData
```

---

## Phase 1: 因子研究

### 运行方式

```bash
# 官方 API 流程（需要流量）
python scripts/factor/factor_research.py

# 离线版本（使用本地 Parquet 数据）
python scripts/factor/factor_research_offline.py
```

### 核心流程

1. **定义因子**
   ```python
   from rqfactor import Factor
   factor = 1 / Factor("pe_ratio_ttm")  # EP-TTM
   ```

2. **计算因子值**
   ```python
   from rqfactor import execute_factor
   factor_data = execute_factor(factor, stock_ids, start_date, end_date)
   ```

3. **因子检验**
   ```python
   from rqfactor.analysis import FactorAnalysisEngine, ICAnalysis, Winzorization
   
   engine = FactorAnalysisEngine()
   engine.append(("winzorization", Winzorization(method="mad")))
   engine.append(("ic_analysis", ICAnalysis(rank_ic=True)))
   result = engine.analysis(factor_data, returns)
   ```

### 注意事项

- `get_price()` 返回的 DataFrame 列名是 MultiIndex，需 `droplevel(0)` 处理
- `ICAnalysis(industry_classification="sws")` 在数据含 NaN 时可能报错
- 离线版本使用 `data/stock/price_1d.parquet`，不消耗 API 流量

---

## Phase 2: 组合优化

### 运行方式

```bash
python scripts/portfolio/portfolio_optimization.py
```

### 三种优化方法

#### 1. 指标最大化
适用场景：有明确的 Alpha 因子，希望最大化因子暴露

```python
from rqoptimizer import MaxIndicator, WildcardIndustryConstraint, portfolio_optimize

weights = portfolio_optimize(
    order_book_ids=stock_ids,
    date=date,
    objective=MaxIndicator(scores),
    benchmark="000300.XSHG",
    bnds={"weight": (0, 0.05)},
    cons=[
        WildcardIndustryConstraint(lower_limit=-0.03, upper_limit=0.03, relative=True),
    ],
)
```

#### 2. 跟踪误差最小化
适用场景：指数增强策略

```python
from rqoptimizer import MinTrackingError, TrackingErrorLimit

weights = portfolio_optimize(
    order_book_ids=stock_ids,
    objective=MinTrackingError(),
    cons=[TrackingErrorLimit(upper_limit=0.02)],
)
```

#### 3. 风险平价
适用场景：风险均衡配置

```python
from rqoptimizer import RiskParity

weights = portfolio_optimize(
    order_book_ids=stock_ids,
    objective=RiskParity(),
    bnds={"weight": (0.01, 0.1)},
)
```

### 注意事项

- `IndustryConstraint(neutral=True)` API 不存在，使用 `WildcardIndustryConstraint`
- `TrackingErrorLimit(upper=)` → `TrackingErrorLimit(upper_limit=)`
- 约束过严可能导致 `infeasible` 错误

---

## Phase 3: 策略回测

### 运行方式

```bash
# CLI 方式
rqalpha-plus run -f scripts/backtest/buy_and_hold.py \
    -s 2020-01-01 -e 2020-12-31 \
    --account stock 100000 --plot

# Python 方式
python scripts/backtest/buy_and_hold.py
```

### 数据范围

- Bundle 数据（免费）：截至 **2020-04-28**
- 回测日期需在此范围内
- 使用 `QUOTA_SAFE_CONFIG` 避免消耗流量

---

## Phase 4: 业绩归因

### 运行方式

```bash
python scripts/attribution/performance_attribution.py
```

### 核心流程

```python
import rqpattr

# 从回测结果提取数据
positions = result["sys_analyser"]["stock_positions"]
portfolio = result["sys_analyser"]["portfolio"]

# 计算权重
weights = positions["market_value"] / portfolio["total_value"]
daily_return = portfolio["unit_net_value"].pct_change().dropna()

# 执行归因
result = rqpattr.performance_attribute(
    model="equity/factor_v2",
    daily_weights=weights,
    daily_return=daily_return,
    benchmark_info={"type": "index", "detail": "000300.XSHG"},
)
```

### 输出解读

- **Brinson 归因树**：配置收益 + 选择收益分解
- **因子归因**：各风格/行业因子贡献明细

---

## 全链条集成

### 运行方式

```bash
python scripts/full_pipeline.py
```

### 流程示例

```python
# 1. 因子研究 → 获得 scores
scores = phase1_factor_research(stock_ids, factor_start, factor_end)

# 2. 组合优化 → 获得 weights
weights = phase2_portfolio_optimization(scores, optimize_date)

# 3. 策略回测 → 获得 result
result = phase3_backtest(weights, backtest_start, backtest_end)

# 4. 业绩归因 → 获得 attribution
attribution = phase4_attribution(result)
```

---

## 常见问题

### Q: 流量耗尽怎么办？
使用离线因子研究脚本 `factor_research_offline.py`，从本地 Parquet 数据读取。

### Q: 回测报错"未查询到数据"？
检查日期范围是否在 Bundle 数据范围内（截至 2020-04-28）。

### Q: 优化器报错 `infeasible`？
放宽约束条件，或减少股票池规模。

### Q: IC 分析返回全 NaN？
检查 returns 的列名格式，是否与 factor_data 对齐（需要 `unstack` + `droplevel`）。

---

## 相关文档

| 文档 | 路径 |
|------|------|
| 全链条计划 | `.planning/RICEQUANT_FULL_PIPELINE.md` |
| 项目状态 | `.planning/STATE.md` |
| RQFactor 文档 | `docs/rqfactor/RQFACTOR_DOCS.md` |
| RQOptimizer API | `docs/rqoptimizer/RQOPTIMIZER_API.md` |
| RQAlpha Plus 文档 | `docs/rqalpha-plus/RQALPHA_PLUS_DOCS.md` |
| RQPAttr 文档 | `docs/rqpattr/RQPATTR_DOCS.md` |