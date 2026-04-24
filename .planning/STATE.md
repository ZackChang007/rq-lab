# STATE.md

> Last updated: 2026-04-24

## Project Reference

**Project**: RiceQuant 全链条流程研究
**Core Value**: 在试用期内（截至 2026-05-22）完整跑通 Ricequant 全链条流程
**Current Focus**: Phase 2 离线因子研究已完成，等待流量刷新验证官方 API 流程

## Current Position

**Phase**: 2 of 5 (Phase 1 完成，Phase 2 离线版完成)
**Progress**: `[██████░░░░] 60%`

```
Phase 0: 数据下载 ──────── 进行中 (Day 1 完成, ~800MB 剩余，流量耗尽)
Phase 1: 回测模块 ──────── ✓ 已完成
Phase 2: 因子挖掘与检验 ── ✓ 离线版完成 (官方版待流量刷新)
Phase 3: 组合优化 ──────── 阻塞 (需要 rqdatac API)
Phase 4: 业绩归因 ──────── 阻塞 (需要 rqdatac API)
Phase 5: 全链条集成 ────── 阻塞 (依赖 Phase 3-4)
```

## Completed Work

### 项目架构重构 (2026-04-24)
- 删除 `rq_lab/` 嵌套包，改为 `utils/common.py` 共享工具
- 脚本按领域分目录：`scripts/{backtest,factor,portfolio,attribution}/`
- 共享配置：`QUOTA_SAFE_CONFIG` + `setup_license()`

### Phase 1: 回测模块
- `scripts/backtest/buy_and_hold.py` - 买入持有策略样例
- 使用 `--sample` 免费数据验证通过
- `utils/common.py` - 共享许可证初始化 + 配额保护配置

### Phase 2: 因子挖掘与检验 (离线版)
- `scripts/factor/factor_research_offline.py` - 使用本地 Parquet 数据
- 数据源：`data/stock/price_1d.parquet`
- 检验管道：完全遵循官方推荐（FactorAnalysisEngine + ICAnalysis + Winzorization）
- 测试结果：日内动量因子 IC=0.033, IR=0.25

### Phase 0: 数据下载 (Day 1)
- 已下载 ~1.1 GB 核心数据
- 元数据、A股行情、A股财务、公司事件全部完成
- 剩余 ~800 MB (因子、指数、期货、期权、可转债、基金、风险因子等)

## Pending Work

### Phase 0 (继续)
待下载类别（流量刷新后）:
- A股因子 (~100 MB)
- 指数数据 (~150 MB)
- 期货数据 (~100 MB)
- 期权数据 (~50 MB)
- 可转债数据 (~100 MB)
- 公募基金数据 (~150 MB)
- 风险因子 (~100 MB)
- 宏观+另类+现货 (~50 MB)

### Phase 2-5 官方 API 验证（流量刷新后）
- `scripts/factor/factor_research.py` - 使用 execute_factor() 官方流程
- `scripts/portfolio/portfolio_optimization.py` - 组合优化
- `scripts/attribution/performance_attribution.py` - 业绩归因
- `scripts/full_pipeline.py` - 全链条集成

## Session Continuity

**Last session**: 2026-04-24
**Status**: 离线因子研究已完成，等待流量刷新验证官方流程
**Next action**: 
1. 流量刷新后继续下载剩余数据
2. 使用官方 API 验证 Phase 2-5

## Key Decisions

1. **auto_update_bundle=False** - 禁用自动更新，避免消耗付费配额
2. **--sample 免费数据** - Phase 1 验证使用免费数据
3. **离线因子研究** - 流量耗尽时使用本地 Parquet 数据
4. **去封装化** - 删除 `rq_lab/` 包，直接使用 `utils/` 共享工具

## Constraints

- **试用期截止**: 2026-05-22
- **每日流量**: 1,024 MB
- **剩余流量**: ~800 MB 待下载
- **当前流量余额**: 已耗尽 (需要等待刷新)
