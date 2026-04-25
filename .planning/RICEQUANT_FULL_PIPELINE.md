# Ricequant 全链条流程计划

> 目标：在试用期内（截至 2026-05-22）完整跑通 Ricequant 全链条流程
> 创建日期：2026-04-24
> 最后更新：2026-04-25

---

## 全链条概览

```
数据下载 → 因子挖掘 → 因子检验 → 组合优化 → 策略回测 → 业绩归因
   (RQData)   (RQFactor)  (RQFactor)  (RQOptimizer) (RQAlpha+)  (RQPAttr)
```

---

## Phase 0: 数据下载 (RQData)

**状态**: 进行中 (核心股票数据已下载 ~1.1GB)

> 注：数据下载工作由用户单独进行，此处仅记录状态

---

## Phase 1: 回测模块 (RQAlpha Plus)

**状态**: 已完成 ✅

### 成果
- `utils/common.py` - 共享配置（`setup_license()` + `QUOTA_SAFE_CONFIG`）
- `scripts/backtest/buy_and_hold.py` - 买入持有策略，遵循官方模板
- 使用 `--sample` 免费数据完成验证

---

## Phase 2: 因子挖掘与检验 (RQFactor)

**状态**: 已完成 ✅

### 验收标准
- [x] 因子计算成功
- [x] IC 分析输出有效结果
- [x] 理解 IC、IR、显著性等指标含义

### 成果
- `scripts/factor/factor_research.py` - 官方 API 流程
- `scripts/factor/factor_research_offline.py` - 离线 Parquet 版本

### 关键发现
- 日内动量因子 IC≈0.03, IR≈0.25（弱正相关）
- API 差异：`get_price()` 返回 MultiIndex 列名，需 `droplevel(0)` 处理
- `ICAnalysis(industry_classification="sws")` 在含 NaN 数据时兼容性问题

---

## Phase 3: 组合优化 (RQOptimizer)

**状态**: 已完成 ✅

### 验收标准
- [x] 优化器返回有效权重
- [x] 约束条件得到满足
- [x] 理解目标函数和约束参数

### 成果
- `scripts/portfolio/portfolio_optimization.py` - 三种优化方法示例

### 关键发现
- API 差异：`IndustryConstraint(neutral=True)` 不存在，需用 `WildcardIndustryConstraint(lower_limit=-0.03, upper_limit=0.03, relative=True)`
- 三种优化方法均验证通过：指标最大化、跟踪误差最小化、风险平价

---

## Phase 4: 业绩归因 (RQPAttr)

**状态**: 已完成 ✅

### 验收标准
- [x] 归因分析成功执行
- [x] 理解配置收益、选择收益、因子收益概念
- [x] 可视化归因结果（Brinson 归因树）

### 成果
- `scripts/attribution/performance_attribution.py` - Brinson + 因子归因

---

## Phase 5: 全链条集成

**状态**: 已完成 ✅

### 验收标准
- [x] 全流程无报错运行
- [x] 每个阶段输出可验证
- [x] 文档清晰说明各阶段衔接

### 成果
- `scripts/full_pipeline.py` - 端到端完整示例
- `docs/FULL_PIPELINE_GUIDE.md` - 使用指南

### 关键发现
- Bundle 数据范围：截至 2020-04-28，回测日期需在此范围内
- 验证周期：因子计算 2019 年 → 回测 2020-01~04

---

## 官方文档参考

| 模块 | 本地文档 |
|------|----------|
| RQData | `docs/rqdata/RQDATA_DOCS.md` |
| RQFactor | `docs/rqfactor/RQFACTOR_DOCS.md`, `RQFACTOR_ADVANCED.md` |
| RQOptimizer | `docs/rqoptimizer/RQOPTIMIZER_DOCS.md`, `RQOPTIMIZER_API.md` |
| RQAlpha Plus | `docs/rqalpha-plus/RQALPHA_PLUS_DOCS.md`, `RQALPHA_PLUS_API_REFERENCE.md` |
| RQPAttr | `docs/rqpattr/RQPATTR_DOCS.md` |

---

## 更新日志

- 2026-04-24: 创建全链条计划
- 2026-04-25: Phase 1-5 全部验证完成，更新验收标准