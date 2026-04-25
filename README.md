# Ricequant 全链条研究项目

> 米筐量化(RiceQuant)工具套件研究项目
> 授权类型：个人试用 | 有效期：2026-05-22

## 项目概述

本项目用于验证和学习 Ricequant 量化研究全链条流程，涵盖：

```
数据下载 → 因子研究 → 组合优化 → 策略回测 → 业绩归因
 (RQData)   (RQFactor)  (RQOptimizer) (RQAlpha+)  (RQPAttr)
```

## 目录结构

```
rq-lab/
├── config/              # 配置文件
│   ├── credentials.py   # 许可证密钥（需自行配置）
│   └── credentials.example.py
├── data/                # 本地数据存储（Parquet 格式）
├── docs/                # 文档
│   ├── FULL_PIPELINE_GUIDE.md  # 全链条使用指南
│   ├── backtest.md              # 回测模块说明
│   ├── rqdata/                  # RQData 文档
│   ├── rqfactor/                # RQFactor 文档
│   ├── rqalpha-plus/            # RQAlpha Plus 文档
│   ├── rqoptimizer/             # RQOptimizer 文档
│   └── rqpattr/                 # RQPAttr 文档
├── scripts/             # 脚本
│   ├── backtest/        # 回测策略
│   ├── factor/          # 因子研究
│   ├── portfolio/       # 组合优化
│   ├── attribution/     # 业绩归因
│   ├── data/            # 数据下载
│   └── full_pipeline.py # 全链条集成
├── tests/               # 测试用例
├── utils/               # 共享工具模块
└── .planning/           # 项目计划和状态
```

## 环境配置

### 1. 创建 Conda 环境

```bash
conda create -n rq-lab python=3.12
conda activate rq-lab
```

### 2. 安装依赖

```bash
poetry install
```

### 3. 配置许可证

```bash
cp config/credentials.example.py config/credentials.py
# 编辑 credentials.py 填入许可证密钥
```

## 快速开始

### 全链条示例

```bash
python scripts/full_pipeline.py
```

### 单独运行各阶段

```bash
# 因子研究
python scripts/factor/factor_research.py

# 组合优化
python scripts/portfolio/portfolio_optimization.py

# 策略回测
python scripts/backtest/buy_and_hold.py

# 业绩归因
python scripts/attribution/performance_attribution.py
```

### 数据下载

```bash
python scripts/data/download.py
```

## 文档索引

| 文档 | 说明 |
|------|------|
| [全链条指南](docs/FULL_PIPELINE_GUIDE.md) | 从因子到归因的完整流程 |
| [回测模块](docs/backtest.md) | RQAlpha Plus 使用说明 |
| [项目计划](.planning/RICEQUANT_FULL_PIPELINE.md) | 全链条验证计划 |
| [项目状态](.planning/STATE.md) | 当前进度追踪 |

## 组件依赖关系

```
RQSDK (工具套件总入口)
 ├── RQData (金融数据 API)
 ├── RQFactor (因子定义与检验) ── 依赖 RQData
 ├── RQAlpha Plus (策略回测) ── 依赖 RQData
 │    └── RQOptimizer (组合优化器)
 └── RQPAttr (业绩归因)
```

## 注意事项

- **流量限制**：试用账号每日 1GB 流量
- **Bundle 数据**：免费回测数据截至 2020-04-28
- **离线模式**：使用 `factor_research_offline.py` 不消耗流量

## 许可证

本项目仅供个人学习和研究使用。
