# STATE.md

> Last updated: 2026-04-25

## Project Reference

**Project**: RiceQuant 全链条流程研究
**Core Value**: 在试用期内（截至 2026-05-22）完整跑通 Ricequant 全链条流程
**Current Focus**: 全链条验证完成 ✅

## Current Position

**Phase**: 全部完成 ✅
**Progress**: `[██████████] 100%`

```
Phase 0: 数据下载 ──────── 进行中 (股票核心数据已下载 ~1.1GB)
Phase 1: 回测模块 ──────── ✓ 已完成
Phase 2: 因子挖掘与检验 ── ✓ 已完成 (官方 + 离线版)
Phase 3: 组合优化 ──────── ✓ 已完成
Phase 4: 业绩归因 ──────── ✓ 已完成
Phase 5: 全链条集成 ────── ✓ 已完成
```

## Completed Work

### 项目架构重构 (2026-04-24)
- 删除 `rq_lab/` 嵌套包，改为 `utils/common.py` 共享工具
- 脚本按领域分目录：`scripts/{backtest,factor,portfolio,attribution}/`
- 共享配置：`QUOTA_SAFE_CONFIG` + `setup_license()`

### Phase 1: 回测模块 ✅
- `scripts/backtest/buy_and_hold.py` - 买入持有策略样例
- 使用 `--sample` 免费数据验证通过

### Phase 2: 因子挖掘与检验 ✅
- `scripts/factor/factor_research.py` - 官方 API 流程
- `scripts/factor/factor_research_offline.py` - 离线 Parquet 版本
- IC 分析、因子检验管道全部验证通过

### Phase 3: 组合优化 ✅
- `scripts/portfolio/portfolio_optimization.py`
- 三种优化方法：指标最大化、跟踪误差最小化、风险平价
- 适配 WildcardIndustryConstraint API

### Phase 4: 业绩归因 ✅
- `scripts/attribution/performance_attribution.py`
- Brinson 行业归因 + 因子归因
- 完整收益分解树

### Phase 5: 全链条集成 ✅
- `scripts/full_pipeline.py`
- 端到端流程：因子→优化→回测→归因
- 验证周期：2019-01~2020-04

## Pending Work

### Phase 0 数据下载（可选补充）
待下载类别（流量有余量时）:
- A股因子 (~100 MB)
- 指数数据 (~150 MB)
- 期货数据 (~100 MB)
- 期权数据 (~50 MB)
- 可转债数据 (~100 MB)
- 公募基金数据 (~150 MB)
- 风险因子 (~100 MB)
- 宏观+另类+现货 (~50 MB)

## Session Continuity

**Last session**: 2026-04-25
**Status**: 全链条验证完成 ✅
**Next action**: 
- 可继续下载补充数据
- 或开始实际因子研究

## Key Decisions

1. **auto_update_bundle=False** - 禁用自动更新，避免消耗付费配额
2. **--sample 免费数据** - Phase 1 验证使用免费数据
3. **离线因子研究** - 流量耗尽时使用本地 Parquet 数据
4. **去封装化** - 删除 `rq_lab/` 包，直接使用 `utils/` 共享工具
5. **Bundle 数据范围** - 截至 2020-04-28，回测日期需在此范围内

## Constraints

- **试用期截止**: 2026-05-22（剩余 27 天）
- **每日流量**: 1,024 MB
- **剩余流量**: ~950 MB（今日已用 ~70 MB）
- **Bundle 数据**: 截至 2020-04-28
