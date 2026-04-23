# Codebase Structure

**Analysis Date:** 2026-04-23

## Directory Layout

```
C:/gh/rq-lab/
├── .claude/                    # Claude Code 配置
│   ├── commands/               # 自定义命令和文档索引
│   │   └── ricequant-doc-index.md  # Ricequant SDK API 文档快速索引
│   └── settings.local.json    # 本地权限设置（gitignored）
├── .planning/                  # 计划文档（GSD 工作流）
│   └── codebase/              # 代码库分析文档
├── .vscode/                    # VS Code 配置
│   ├── settings.json          # Python 分析路径、类型检查级别
│   └── snippets.code-snippets # 自定义代码片段（rqinit, rqstrategy 等）
├── config/                     # 配置文件
│   ├── __init__.py             # 导入说明
│   ├── credentials.py          # 凭证（gitignored，包含 RQSDK_LICENSE_KEY）
│   └── credentials.example.py  # 凭证模板（提交到版本库）
├── data/                       # 数据缓存（gitignored，仅跟踪进度文档）
│   ├── DOWNLOAD_PROGRESS.md    # 下载进度人工摘要（手动更新）
│   ├── download_log.json       # 机器可读下载日志
│   ├── instruments/            # 合约基本信息（11 类品种）
│   ├── calendar/               # 交易日历
│   ├── yield_curve/            # 收益率曲线
│   ├── stock/                  # A 股数据（行情、财务、事件、因子名）
│   ├── factor/                 # A 股因子数据（批量）
│   ├── index/                  # 指数数据（行情、成分、权重）
│   ├── futures/                # 期货数据
│   ├── options/                # 期权数据
│   ├── convertible/            # 可转债数据
│   ├── fund/                   # 公募基金数据
│   ├── risk_factor/            # 风险因子数据
│   ├── macro/                  # 宏观经济数据
│   ├── alternative/            # 另类数据（consensus, news, esg）
│   └── spot/                   # 现货数据
├── docs/                       # Ricequant SDK 文档
│   ├── README.md               # 文档索引与快速开始
│   ├── specs/                  # 设计规格文档
│   │   └── 2026-04-23-rqdata-download-plan.md  # 数据下载计划
│   ├── rqsdk/                  # RQSDK 文档
│   ├── rqdata/                 # RQData 文档
│   ├── rqfactor/               # RQFactor 文档
│   ├── rqalpha-plus/           # RQAlpha Plus 文档
│   ├── rqoptimizer/            # RQOptimizer 文档
│   └── rqpattr/                # RQPAttr 文档
├── scripts/                    # 脚本目录
│   └── data/                   # 数据相关脚本
│       └── download.py          # RQData 全量下载工具（656行）
├── .gitignore                  # Git 忽略规则
├── CLAUDE.md                   # 项目指引（Claude Code 读取）
├── poetry.lock                 # Poetry 锁文件
└── pyproject.toml              # 项目配置与依赖声明
```

## Directory Purposes

**config/**
- Purpose: 存放凭证和配置，`credentials.py` 包含 `RQSDK_LICENSE_KEY`
- Contains: Python 模块，导出凭证常量
- Key files: `credentials.py` (gitignored, 实际凭证), `credentials.example.py` (模板)
- Usage pattern: `from config.credentials import RQSDK_LICENSE_KEY; rqdatac.init(RQSDK_LICENSE_KEY)` 或通过环境变量 `RQDATAC2_CONF`

**data/**
- Purpose: 本地 Parquet 数据缓存，按 RQData API 类别组织
- Contains: 17 个子目录 + 2 个进度文件
- Key files: `download_log.json` (机器可读日志), `DOWNLOAD_PROGRESS.md` (人工摘要)
- Special: 整个目录在 `.gitignore` 中，仅 `DOWNLOAD_PROGRESS.md` 被例外跟踪
- 数据量: ~1.1GB 已下载（截至 2026-04-23），预计总计 ~3.5GB

**docs/**
- Purpose: Ricequant SDK 离线文档，供开发和 Claude Code 参考
- Contains: 6 个子目录对应 6 个组件，9 个 markdown 文件
- Key files: `README.md` (文档索引), 各组件 DOC.md 文件
- Special: `specs/` 子目录存放设计规格文档

**scripts/**
- Purpose: 可执行脚本，按功能分类
- Contains: 当前仅有 `data/download.py`
- Key files: `scripts/data/download.py` (数据下载工具)

**.claude/**
- Purpose: Claude Code 配置和自定义命令
- Contains: 文档索引、本地设置
- Key files: `commands/ricequant-doc-index.md` (API 快速定位)

**.vscode/**
- Purpose: VS Code 工作区设置
- Contains: Python 分析配置、代码片段
- Key files: `snippets.code-snippets` (rqinit, rqstrategy 等快捷片段)

## Key File Locations

**Entry Points:**
- `scripts/data/download.py`: 数据下载工具，CLI 入口

**Configuration:**
- `config/credentials.py`: RQSDK 许可证密钥（环境变量 `RQDATAC2_CONF` 替代方案）
- `config/credentials.example.py`: 凭证模板
- `pyproject.toml`: Poetry 项目定义，依赖 `rqsdk>=1.7.1`
- `.gitignore`: 忽略凭证文件和数据目录

**Core Logic:**
- `scripts/data/download.py`: 完整的数据下载逻辑
  - `safe_download()`: 通用下载包装器（lines 96-136）
  - `download_*()`: 12 个步骤函数（lines 140-607）
  - `STEPS` dict: 步骤名到函数的映射（lines 610-623）
  - `main()`: CLI 入口（lines 632-652）

**Progress Tracking:**
- `data/download_log.json`: JSON 格式下载状态（按日期、按 key）
- `data/DOWNLOAD_PROGRESS.md`: 人工更新的进度摘要

**Documentation:**
- `docs/README.md`: 文档索引
- `.claude/commands/ricequant-doc-index.md`: API 快速定位索引
- `CLAUDE.md`: 项目指引（架构概览、常用命令、约定）

**Planning (GSD):**
- `docs/specs/2026-04-23-rqdata-download-plan.md`: 数据下载计划设计文档
- `.planning/codebase/`: 代码库分析文档（本文件所在目录）

## Naming Conventions

**Files:**
- Python 模块: `snake_case.py` (如 `download.py`, `credentials.py`)
- Markdown 文档: `UPPERCASE.md` 或 `UPERCASE_WITH_UNDERSCORES.md` (如 `README.md`, `RQDATA_DOCS.md`)
- 数据文件: `{category}/{api_name}.parquet` (如 `stock/price_1d.parquet`)
- 日志文件: `snake_case.json` (如 `download_log.json`)

**Directories:**
- 功能目录: `snake_case` (如 `scripts/`, `config/`, `docs/`)
- 数据子目录: 与 RQData API 模块对应 (如 `stock/`, `futures/`, `options/`, `convertible/`, `fund/`)
- 文档子目录: 与 Ricequant 组件对应 (如 `rqsdk/`, `rqdata/`, `rqfactor/`, `rqalpha-plus/`)

**Functions:**
- 步骤函数: `download_{category}()` (如 `download_stock_price()`, `download_index()`)
- 工具函数: `snake_case()` (如 `safe_download()`, `check_quota()`, `mark_done()`)
- RQData API 包装: 直接调用 `rqdatac.{api_name}()`

**Constants:**
- 全大写: `DATA_ROOT`, `LOG_PATH`, `DAILY_QUOTA_MB`, `QUOTA_MARGIN_MB`, `PYTHON`

## Where to Add New Code

**New Feature (Backtest Module):**
- Option A (脚本风格，与现有模式一致): `scripts/backtest/` 目录
- Option B (包风格): `rq_lab/backtest/` 包
- Tests: `tests/test_backtest.py`（如需要）
- Recommended: 先作为 `scripts/backtest/` 开始，成熟后考虑提取为包

**New Feature (Factor Analysis):**
- Primary code: `scripts/factor/` 或 `rq_lab/factor/`
- Integration: 在回测脚本中导入使用

**New Feature (Optimizer):**
- Primary code: 集成到回测策略中，或单独脚本 `scripts/optimizer/`
- Note: RQOptimizer 通常在策略内部调用，较少独立使用

**New Feature (Attribution):**
- Primary code: `scripts/attribution/` 作为回测后处理

**New Utility Functions:**
- 如果复用性高: 考虑创建 `lib/` 或 `rq_lab/utils/`
- 如果仅脚本内使用: 直接放在脚本文件顶部

**New Data Category:**
- 在 `scripts/data/download.py` 中添加步骤函数
- 注册到 `STEPS` dict 和 `STEP_ORDER` list
- 在 `data/` 下创建对应子目录

**New Documentation:**
- 组件文档: 放入 `docs/{component}/`
- 设计规格: 放入 `docs/specs/`
- API 索引: 更新 `.claude/commands/ricequant-doc-index.md`

## Special Directories

**.claude/**
- Purpose: Claude Code 用户配置
- Generated: 部分（settings.local.json 动态生成）
- Committed:部分（commands/ 下的文件通常提交）

**data/**
- Purpose: 数据缓存
- Generated: 是，由 `scripts/data/download.py` 生成
- Committed: 否（在 `.gitignore` 中），仅 `DOWNLOAD_PROGRESS.md` 例外

**docs/specs/**
- Purpose: 设计规格文档
- Generated: 否，人工编写
- Committed: 是

**.planning/**
- Purpose: GSD 工作流计划文档
- Generated: 是，由 GSD 命令生成
- Committed: 是（建议）

**.playwright-mcp/**
- Purpose: Playwright 浏览器自动化会话数据
- Generated: 是
- Committed: 否（在 `.gitignore` 中）

## Import Paths

**项目根目录下的模块导入:**
- `config` 模块: `from config.credentials import RQSDK_LICENSE_KEY`

**RQSDK 包导入:**
- `import rqdatac` - RQData API
- `from rqalpha.api import *` - RQAlpha Plus 策略 API
- `from rqfactor import Factor, execute_factor` - RQFactor 因子 API
- `import rqoptimizer` - RQOptimizer 组合优化

**VS Code Python 分析路径:**
- `~/.rqsdk/python` 添加到 `python.analysis.extraPaths`（在 `.vscode/settings.json`）

## File Size Reference

**Large Files (developers should know):**
- `data/stock/price_1d.parquet`: ~859 MB (A股日线行情，~1570万行)
- `docs/rqalpha-plus/RQALPHA_PLUS_API_REFERENCE.md`: ~800+ lines (API 参考)
- `scripts/data/download.py`: 656 lines (数据下载工具)

## Environment Setup Files

- `pyproject.toml`: Poetry 配置，定义 Python 3.12 和 `rqsdk` 依赖
- `poetry.lock`: 依赖锁定文件
- `.gitignore`: 排除 `.env`, `.venv`, `config/credentials.py`, `data/`, `.rqalpha-plus/`

---

*Structure analysis: 2026-04-23*
