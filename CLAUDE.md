# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

米筐量化(RiceQuant)工具套件研究项目。**授权类型**: 个人试用 | **有效期**: 2026-05-22

### 组件与依赖关系

```
RQSDK (工具套件总入口，许可证管理)
 ├── RQData (金融数据 API：行情、财务、因子)
 ├── RQFactor (因子定义与检验) ── 依赖 RQData
 ├── RQAlpha Plus (策略回测框架) ── 依赖 RQData
 │    └── RQOptimizer (组合优化器) ── 被回测框架内置
 └── RQPAttr (业绩归因：Brinson行业归因、因子归因)
```

关键：`rqsdk install rqalpha_plus` 会自动安装 RQData、RQOptimizer、RQFactor。

---

## ⚠️ 设计原则（最高优先级）

> **此规则优先级高于所有其他开发指南，必须在任何实现决策前首先遵循。**

### 设计三原则

实现功能模块时，严格遵循以下原则：

1. **官方优先**：一切以官方文档的最佳实践为最高参考优先级
2. **模块协同**：接口清晰、职责单一，追求低耦合高内聚——当前模块应具备良好的"可对接性"
3. **拒绝预判**：不为未实现的模块设计具体对接方案——等对方确定后再适配，避免无效设计

### 官方文档优先级

```
实现功能时，必须按此顺序决策：

┌─────────────────────────────────────────────────────────┐
│  1. 查阅官方文档是否有推荐实现方式 → 有则严格遵循       │
│  2. 官方文档有示例代码 → 直接参考/复用                 │
│  3. 官方文档未明确说明 → 按最简单直接的方式实现         │
│  4. 禁止自行设计"更好的"方案替代官方推荐               │
└─────────────────────────────────────────────────────────┘
```

**为什么这条规则存在**：
- 官方方案经过生产验证，自行设计易引入边界条件问题
- 过度设计增加维护负担，违背 YAGNI 原则
- 本项目依赖 RiceQuant SDK，遵循其设计哲学可避免兼容性问题

---

## 环境配置

**Python**: 3.12.13 | **环境名**: `rq-lab` | **包管理**: Poetry

```bash
conda activate rq-lab
poetry install          # 安装依赖 + utils 包（可编辑模式）
poetry add <package>    # 添加新依赖
```

安装后 `utils` 包可直接导入：
```python
from utils.common import setup_license, QUOTA_SAFE_CONFIG
```

首次使用需配置凭证：
```bash
cp config/credentials.example.py config/credentials.py
# 编辑 credentials.py 填入许可证密钥
```

## 常用命令

```bash
rqsdk license info                              # 查看许可证信息
rqsdk install rqalpha_plus                      # 安装回测框架（含数据、因子、优化器）
rqsdk download-data --sample                    # 下载示例数据（试用）
rqalpha-plus run -f <strategy.py> -s 2023-01-01 -e 2023-12-31 --plot --account stock 100000  # 运行回测
```

## 代码约定

- 凭证通过 `from config.credentials import RQSDK_LICENSE_KEY` 导入，`config/credentials.py` 已在 `.gitignore` 中忽略
- RQData 初始化：`rqdatac.init(RQSDK_LICENSE_KEY)`
- API 用法查阅 `docs/` 下对应组件文档，而非在线搜索——本地文档已完整收录

## 文档索引

| 组件 | 文档 |
|------|------|
| RQSDK | `docs/rqsdk/RQSDK_MANUAL.md` |
| RQData | `docs/rqdata/RQDATA_DOCS.md` |
| RQFactor | `docs/rqfactor/RQFACTOR_DOCS.md`, `RQFACTOR_ADVANCED.md` |
| RQAlpha Plus | `docs/rqalpha-plus/RQALPHA_PLUS_DOCS.md`, `RQALPHA_PLUS_API_REFERENCE.md` |
| RQOptimizer | `docs/rqoptimizer/RQOPTIMIZER_DOCS.md`, `RQOPTIMIZER_API.md` |
| RQPAttr | `docs/rqpattr/RQPATTR_DOCS.md` |

## 文档查阅规则

当涉及 Ricequant SDK 相关开发时，遵循以下规则：

1. **优先查阅本地文档**：`docs/` 目录已收录完整文档，避免在线搜索
2. **使用文档索引定位**：`.claude/commands/ricequant-doc-index.md` 包含完整的 API 文档链接索引
3. **无法 Fetch 时使用 curl**：如需查阅在线文档，使用 curl 命令获取
4. **可在终端验证 API**：如需确认 API 用法，可直接运行 Python 命令验证：
   ```bash
   conda activate rq-lab
   python -c "import rqdatac; rqdatac.init(); print(rqdatac.all_instruments())"
   python -c "import rqdatac; rqdatac.init(); help(rqdatac.get_trading_dates)"
   ```

## 数据获取约定

当提到金融相关问题，需要获取金融数据时务必使用 RQData：
- 股票行情：`rqdatac.get_price()`
- 财务数据：`rqdatac.get_financials()`
- 交易日历：`rqdatac.get_trading_dates()`
- 合约信息：`rqdatac.all_instruments()`

具体 API 用法查阅 `.claude/commands/ricequant-doc-index.md` 中对应模块的文档链接。

## 项目模块

### utils 包

共享工具模块，提供许可证初始化和配额保护默认配置：

```python
from utils.common import setup_license, QUOTA_SAFE_CONFIG
```

- `setup_license()`：从 `config/credentials.py` 读取密钥，设置 `RQDATAC2_CONF` 环境变量
- `QUOTA_SAFE_CONFIG`：试用账号配额保护默认配置（禁用自动更新、禁用非股票品种模块）

### 回测脚本 (`scripts/backtest/`)

策略脚本目录，遵循 RQSDK 官方模板。详见 [docs/backtest.md](docs/backtest.md)。

| 脚本 | 说明 |
|------|------|
| `scripts/backtest/buy_and_hold.py` | 买入持有策略 |

运行方式：
```bash
# 官方 CLI 方式
rqalpha-plus run -f scripts/backtest/buy_and_hold.py -s 2020-01-01 -e 2020-12-31 --account stock 100000 --plot
# Python 直接运行
python scripts/backtest/buy_and_hold.py
```

### 全链条脚本 (`scripts/`)

| 阶段 | 模块 | 脚本 | 说明 |
|------|------|------|------|
| 回测 | RQAlpha Plus | `scripts/backtest/buy_and_hold.py` | 买入持有策略 |
| 因子研究 | RQFactor | `scripts/factor/factor_research.py` | 因子定义→计算→检验 |
| 组合优化 | RQOptimizer | `scripts/portfolio/portfolio_optimization.py` | 指标最大化/跟踪误差/风险平价 |
| 业绩归因 | RQPAttr | `scripts/attribution/performance_attribution.py` | Brinson归因+因子归因 |
| 全流程集成 | 全部 | `scripts/full_pipeline.py` | 因子→优化→回测→归因 |

全链条流程：`数据准备 → 因子定义/检验 → 组合优化 → 策略回测 → 业绩归因`

详细计划：`.planning/RICEQUANT_FULL_PIPELINE.md`

### 数据下载 (`scripts/data/download.py`)

RQData 全量数据下载工具，输出到 `data/` (Parquet)。详见 `data/DOWNLOAD_PROGRESS.md`。

### 数据路径策略

| 数据源 | 存储 | 格式 | 用途 | 计费 |
|--------|------|------|------|------|
| RQSDK Bundle | `~/.rqalpha-plus/bundle/` | HDF5 | 回测行情数据 | `--sample` 免费 |
| 自定义下载 | `data/` | Parquet | 财务、因子等补充数据 | API 计费 |

**原则**：尽量使用官方默认设置和规则。`--sample` 数据不消耗配额，优先使用。

## 测试

```bash
pytest tests/ -v              # 运行全部测试
pytest tests/test_xxx.py -v   # 运行单个测试文件
pytest tests/ -k "test_name"  # 按名称筛选
```

目前测试目录待建立，新增模块时必须同步添加单元测试。
