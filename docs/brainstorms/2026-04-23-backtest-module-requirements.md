# 回测模块需求文档

**日期**: 2026-04-23
**状态**: 待实施

---

## 概述

为 rq-lab 项目添加回测模块，实现最小可用的回测能力，并为因子分析、组合优化等后续模块预留接口。

---

## 决策记录

### 1. 数据路径策略

**决策**: 双轨互补，各司其职

| 数据源 | 存储位置 | 格式 | 用途 | 计费 |
|--------|----------|------|------|------|
| RQSDK Bundle | `~/.rqalpha-plus/bundle/` | HDF5 | 回测行情数据 | `--sample` 免费 |
| 自定义下载 | `data/` | Parquet | 财务、因子等补充数据 | API 计费 |

**依据**:
- RQSDK Bundle 是 RQAlpha Plus 回测引擎的**唯一原生数据源**
- Bundle 只存储行情数据（OHLCV），不包含财务、因子、宏观数据
- 自定义下载脚本下载的数据是 Bundle 不包含的补充数据
- 两者格式不同（HDF5 vs Parquet），路径不同，职责不同，不存在真正的重复冲突

**去重机制验证**:
- `rqsdk update-data --smart`: 检查本地已有数据，增量更新
- `rqsdk download-data --sample`: 一次性下载样例，不重复
- 自定义脚本: `download_log.json` 记录已下载项，跳过已完成

**配额优化策略**:
1. 先运行 `rqsdk download-data --sample`（免费）获取基础数据
2. **禁用** `auto_update_bundle=False` —— 该选项使用 RQData API，**会消耗付费配额**
3. 自定义脚本优先下载 Bundle 不提供的财务、因子数据
4. 如需额外行情数据，显式使用 `rqsdk update-data --base`（计费，知情可控）
5. 回测仅使用 `--sample` 已有数据，如数据不全则回测报错提示

### 2. 模块架构

**决策**: 简化单文件方案（审阅修订：原方案过度设计）

```
rq_lab/
├── __init__.py
└── backtest.py      # run_backtest() + 结果提取 + 买入持有样例
```

**封装层价值主张**（Python API vs CLI 的理由）:
1. Jupyter 中直接访问结果字典，便于交互式分析
2. 为未来因子/优化器模块提供程序化集成点
3. 统一配置管理（配额感知、并发安全检查）

**扩展方式**: 当第二个策略类型出现时，拆分 `backtest.py` → `backtest/` 包。当因子模块需要时，创建 `rq_lab/factor.py`。按需演进，不预设空目录。

### 3. 首要里程碑

**目标**: 跑通最简单的回测样例

**验收标准**:
1. 运行 `rqsdk download-data --sample` 初始化 Bundle 数据，确认可用日期范围
2. 创建 `rq_lab/backtest.py`，实现 `run_backtest()` 函数
3. `run_backtest()` 封装 `rqalpha_plus.run_func()`，设置 `auto_update_bundle=False`
4. 提供买入持有策略样例，成功运行并输出结果
5. 结果包含: `result['sys_analyser']['summary']` 中的 total_returns, sharpe, max_drawdown

---

## 约束与原则

### 硬性约束

1. **使用官方默认设置** - 优先使用 RQSDK 官方命令和数据路径
2. **流量配额意识** - 区分免费（`--sample`）和计费（API 直接调用 / `auto_update_bundle`）
3. **并发安全** - 数据更新时禁止运行回测（文档明确要求）
4. **试用截止** - 2026-05-22 授权到期，需在此之前完成核心数据下载

### 设计原则

1. **最小可行** - 先跑通最简单样例，再迭代增强
2. **官方优先** - 使用 RQSDK/RQAlpha Plus 原生能力，不做不必要的封装
3. **按需演进** - 不预设空目录，功能需要时再创建模块

---

## 数据流程图（Phase 1）

```
┌──────────────────────────────────────────┐
│              数据获取层                    │
├──────────────────────┬───────────────────┤
│  rqsdk download-data │  download.py      │
│  --sample (免费)      │  (RQData API 计费)│
└──────────┬───────────┴────────┬──────────┘
           │                    │
           ▼                    ▼
┌─────────────────────┐  ┌──────────────────┐
│ ~/.rqalpha-plus/    │  │     data/         │
│ bundle/ (HDF5)      │  │  (Parquet)        │
│ 行情数据(OHLCV)     │  │  财务/因子/宏观    │
└──────────┬──────────┘  └──────────────────┘
           │              Phase 1 不消费 ↑
           ▼
┌──────────────────────────────────────────┐
│           回测引擎 (Phase 1)              │
│                                          │
│   rq_lab/backtest.py                     │
│   └── run_backtest()                     │
│       └── rqalpha_plus.run_func()        │
│           └── 仅读取 Bundle 数据          │
│               auto_update_bundle=False    │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│              结果输出层                    │
│  result['sys_analyser']['summary']       │
│  → {alpha, beta, sharpe, max_drawdown,   │
│     total_returns, ...}                  │
└──────────────────────────────────────────┘
```

**注意**: Phase 1 中 Parquet 数据 (`data/`) 不被回测引擎消费。
未来因子/优化器模块将消费 Parquet 数据，届时再设计集成路径。

---

## 排除范围

以下内容不在 Phase 1：

1. Bundle 数据与自定义 Parquet 数据的集成（Phase 2+）
2. 分钟级/Tick 级回测（仅支持日级）
3. 多品种混合回测（仅股票）
4. 实时模拟交易
5. 因子检验、组合优化、归因分析功能

---

## 后续规划

1. **Phase 2**: 因子分析模块（RQFactor 集成）→ 届时创建 `rq_lab/factor.py`
2. **Phase 3**: 组合优化模块（RQOptimizer 集成）→ 届时创建 `rq_lab/optimizer.py`
3. **Phase 4**: 归因分析模块（RQPAttr 集成）→ 届时创建 `rq_lab/attribution.py`
4. **持续**: 完成试用期全量数据下载（~800MB 剩余）

---

## 附录：关键命令速查

```bash
# 初始化 Bundle（免费，不消耗配额）
rqsdk download-data --sample

# 更新基础数据（计费，需知情使用）
rqsdk update-data --base

# 增量更新分钟/Tick 数据（计费）
rqsdk update-data --smart

# 运行回测（CLI 方式）
rqalpha-plus run -f strategy.py -s 2023-01-01 -e 2023-12-31 --account stock 100000 --plot
```
