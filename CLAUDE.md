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
