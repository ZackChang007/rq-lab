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

## 环境配置

**Python**: 3.12.13 | **环境名**: `rq-lab` | **包管理**: Poetry

```bash
conda activate rq-lab
poetry install          # 安装依赖（使用清华 PyPI 镜像源，见 pyproject.toml）
poetry add <package>    # 添加新依赖
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

### rq_lab 包

可安装的 Python 包，提供量化研究工具：

```python
from rq_lab.backtest import run_backtest
```

#### 回测模块 (`rq_lab/backtest.py`)

封装 RQAlpha Plus 回测引擎，关键特性：
- `auto_update_bundle=False`：禁用自动更新，避免消耗付费配额
- `rqdatac_uri="disabled"`：仅使用本地 Bundle 数据
- 禁用期权/可转债/基金/期货/现货模块（避免 API 调用）
- 自动从 `config/credentials.py` 读取许可证

```python
result = run_backtest(
    init=init, handle_bar=handle_bar,
    start_date="2020-01-01", end_date="2020-12-31",
    capital=100000, benchmark="000300.XSHG",
)
summary = result["sys_analyser"]["summary"]
```

样例：`python examples/buy_and_hold.py`

### 数据下载 (`scripts/data/download.py`)

RQData 全量数据下载工具，输出到 `data/` (Parquet)。详见 `data/DOWNLOAD_PROGRESS.md`。

### 数据路径策略

| 数据源 | 存储 | 格式 | 用途 | 计费 |
|--------|------|------|------|------|
| RQSDK Bundle | `~/.rqalpha-plus/bundle/` | HDF5 | 回测行情数据 | `--sample` 免费 |
| 自定义下载 | `data/` | Parquet | 财务、因子等补充数据 | API 计费 |

**原则**：尽量使用官方默认设置和规则。`--sample` 数据不消耗配额，优先使用。
