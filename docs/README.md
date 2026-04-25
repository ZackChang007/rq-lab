# 米筐量化工具套件文档

> 本文档汇总了 RQSDK 各组件的官方文档内容，作为项目参考资料。

## 项目授权信息

- **授权类型**: 个人试用
- **有效期截止**: 2026-05-22

---

## 组件概览

| 组件 | 用途 | 文档链接 |
|------|------|----------|
| **开源替代** | 授权结束后可用 | [docs/open-source/](./open-source/RQALPHA_OPEN_SOURCE_GUIDE.md) |
| RiceQuant 平台 | Web 量化平台操作指南 | [docs/ricequant-platform/](./ricequant-platform/RICEQUANT_PLATFORM_GUIDE.md) |
| RQSDK | 工具套件总入口 | [docs/rqsdk/](./rqsdk/RQSDK_MANUAL.md) |
| RQData | 金融数据 API | [docs/rqdata/](./rqdata/RQDATA_DOCS.md) |
| RQFactor | 因子投研工具 | [docs/rqfactor/](./rqfactor/RQFACTOR_DOCS.md) |
| RQAlpha Plus | 回测框架 | [docs/rqalpha-plus/](./rqalpha-plus/RQALPHA_PLUS_DOCS.md) |
| RQOptimizer | 股票组合优化器 | [docs/rqoptimizer/](./rqoptimizer/RQOPTIMIZER_DOCS.md) |
| RQPAttr | 业绩归因分析 | [docs/rqpattr/](./rqpattr/RQPATTR_DOCS.md) |

---

## 文档文件清单

### 开源替代方案
- `RQALPHA_OPEN_SOURCE_GUIDE.md` - RQAlpha 开源版使用指南：授权结束后替代方案
- `FACTOR_ANALYZER_COMPARISON.md` - 因子分析库选型：jqfactor_analyzer vs Alphalens

### RiceQuant 平台
- `RICEQUANT_PLATFORM_GUIDE.md` - Web 平台操作指南：投资研究、因子研究、回测、模拟交易、策略API

### RQSDK
- `RQSDK_MANUAL.md` - 安装、配置、组件管理指南

### RQData
- `RQDATA_DOCS.md` - 金融数据 API 完整参考：通用API、A股、期货数据获取

### RQFactor
- `RQFACTOR_DOCS.md` - 因子定义、内置算子、因子检验完整指南
- `RQFACTOR_ADVANCED.md` - 自定义算子、自定义因子、因子缓存

### RQAlpha Plus
- `RQALPHA_PLUS_DOCS.md` - 回测框架使用指南：策略编写、数据查询、交易接口
- `RQALPHA_PLUS_API_REFERENCE.md` - 配置参数、类型类、其他 API 参考

### RQOptimizer
- `RQOPTIMIZER_DOCS.md` - 产品概览、功能列表、使用场景
- `RQOPTIMIZER_API.md` - 选股 API、组合优化 API 详细参考

### RQPAttr
- `RQPATTR_DOCS.md` - 归因分析 API、Brinson 行业归因、因子归因模型详解、代码示例

---

## 官方链接

### RQSDK
- 使用手册: https://www.ricequant.com/doc/rqsdk/manual-rqsdk

### RQData
- Python API 文档: https://www.ricequant.com/doc/rqdata/python/index-rqdatac

### RQFactor
- 使用文档: https://www.ricequant.com/doc/rqfactor/manual/index-rqfactor
- API 文档: https://www.ricequant.com/doc/rqfactor/api/index-rqfactor

### RQAlpha Plus
- 使用教程: https://www.ricequant.com/doc/rqalpha-plus/doc/index-rqalphaplus
- API 文档: https://www.ricequant.com/doc/rqalpha-plus/api/index-rqalphaplus

### RQOptimizer
- API 文档: https://www.ricequant.com/doc/rqoptimize/doc/index-rqoptimize

---

## 快速开始

### 1. 安装 RQSDK

```bash
# 激活项目环境（已配置 Python 3.12 + Poetry）
conda activate rq-lab

# 安装依赖（如需重新安装）
poetry install
```

### 2. 配置许可证

```bash
rqsdk license      # 交互式配置
rqsdk license info # 查看许可证信息
```

### 3. 安装组件

```bash
rqsdk install rqalpha_plus  # 安装回测框架（包含 RQData、RQOptimizer、RQFactor）
```

### 4. 准备数据

```bash
# 试用客户
rqsdk download-data --sample

# 生产环境
rqsdk update-data --base --minbar 000001.XSHE
```

### 5. 运行示例策略

```bash
rqalpha-plus examples
rqalpha-plus run -f examples/buy_and_hold.py -s 2018-01-01 -e 2018-12-31 --plot --account stock 100000
```

---

## Python 快速示例

### RQData 数据获取

```python
import rqdatac
rqdatac.init()

# 获取股票行情
rqdatac.get_price('000001.XSHE', '2023-01-01', '2023-12-31')

# 获取财务数据
rqdatac.get_financials('000001.XSHE', start_quarter='2023q1', end_quarter='2023q4')

# 获取因子数据
rqdatac.get_factor('000001.XSHE', 'pe_ratio', '2023-01-01', '2023-12-31')
```

### RQFactor 因子检验

```python
from rqfactor import Factor, execute_factor, FactorAnalysisEngine, ICAnalysis

# 定义因子
f = 1 / Factor('pe_ratio')

# 计算因子值
stock_pool = rqdatac.index_components('000300.XSHG')
df = execute_factor(f, stock_pool, '2023-01-01', '2023-12-31')

# 因子检验
engine = FactorAnalysisEngine()
result = engine.analysis(df, 'daily', ascending=False, periods=1)
result['ic_analysis'].summary()
```

### RQAlpha Plus 策略回测

```python
from rqalpha.api import *

def init(context):
    context.stock = '000001.XSHE'

def handle_bar(context, bar_dict):
    if get_position(context.stock).quantity == 0:
        order_target_percent(context.stock, 1)

# 运行回测
from rqalpha_plus import run_func
config = {
    'base': {
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
        'accounts': {'STOCK': 100000}
    }
}
result = run_func(config=config, init=init, handle_bar=handle_bar)
print(result['sys_analyser']['summary'])
```

---

## 技术支持

- 邮箱: support@ricequant.com
- QQ: 2098448759

---

## 文档状态

| 组件 | 状态 | 文件数 |
|------|------|--------|
| 开源替代 | ✅ 完成 | 1 |
| RiceQuant 平台 | ✅ 完成 | 1 |
| RQSDK | ✅ 完成 | 1 |
| RQData | ✅ 完成 | 1 |
| RQFactor | ✅ 完成 | 2 |
| RQAlpha Plus | ✅ 完成 | 2 |
| RQOptimizer | ✅ 完成 | 2 |
| RQPAttr | ✅ 完成 | 1 |

**文档整理日期**: 2026-04-25
