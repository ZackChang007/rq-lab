# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

米筐量化(RiceQuant)工具套件研究项目，包含以下组件：

| 组件 | 用途 |
|------|------|
| RQSDK | 工具套件总入口，许可证管理 |
| RQData | 金融数据 API（行情、财务、因子） |
| RQFactor | 因子定义与检验工具 |
| RQAlpha Plus | 策略回测框架 |
| RQOptimizer | 股票组合优化器 |
| RQPAttr | 业绩归因分析（Brinson行业归因、因子归因） |

**授权类型**: 个人试用 | **有效期**: 2026-05-22

## 目录结构

```
rq-lab/
├── config/              # 凭证配置
│   ├── credentials.py   # 实际密钥（已忽略）
│   └── credentials.example.py  # 配置模板
├── docs/                # 组件文档
│   ├── rqsdk/           # RQSDK 手册
│   ├── rqdata/          # RQData API 文档
│   ├── rqfactor/        # RQFactor 文档
│   ├── rqalpha-plus/    # RQAlpha Plus 文档
│   ├── rqoptimizer/     # RQOptimizer 文档
│   └── rqpattr/         # RQPAttr 归因分析文档
└── examples/            # 示例代码
```

## 环境配置

**Python**: 3.12.13 | **环境名**: `rq-lab` | **包管理**: Poetry

```bash
# 激活环境
conda activate rq-lab

# 安装依赖
poetry install

# 添加新依赖
poetry add <package>
```

首次使用需配置凭证：
```bash
cp config/credentials.example.py config/credentials.py
# 编辑 credentials.py 填入许可证密钥
```

## 常用命令

```bash
# 查看许可证信息
rqsdk license info

# 安装完整组件
rqsdk install rqalpha_plus

# 下载示例数据（试用）
rqsdk download-data --sample

# 运行回测示例
rqalpha-plus run -f examples/buy_and_hold.py -s 2023-01-01 -e 2023-12-31 --plot --account stock 100000
```

## Python 使用示例

```python
# 初始化 RQData
import rqdatac
from config.credentials import RQSDK_LICENSE_KEY
rqdatac.init(RQSDK_LICENSE_KEY)

# 获取行情数据
df = rqdatac.get_price('000001.XSHE', '2023-01-01', '2023-12-31')

# 获取财务数据
rqdatac.get_financials('000001.XSHE', start_quarter='2023q1', end_quarter='2023q4')
```

## 文档索引

详细 API 文档位于 `docs/` 目录：
- RQData: `docs/rqdata/RQDATA_DOCS.md`
- RQFactor: `docs/rqfactor/RQFACTOR_DOCS.md`, `RQFACTOR_ADVANCED.md`
- RQAlpha Plus: `docs/rqalpha-plus/RQALPHA_PLUS_DOCS.md`, `RQALPHA_PLUS_API_REFERENCE.md`
- RQOptimizer: `docs/rqoptimizer/RQOPTIMIZER_DOCS.md`, `RQOPTIMIZER_API.md`
- RQPAttr: `docs/rqpattr/RQPATTR_DOCS.md`

## 凭证管理

- `config/credentials.py` 包含许可证密钥，已在 `.gitignore` 中忽略
- 使用时通过 `from config.credentials import RQSDK_LICENSE_KEY` 导入
