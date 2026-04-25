# jqfactor_analyzer 与 Alphalens 对比分析

> 因子分析开源库选型研究 | 2026-04-25

---

## 一、结论摘要

| 库 | 本地数据支持 | 外部 API 依赖 | 推荐度 |
|---|-------------|--------------|-------|
| **jqfactor_analyzer** | ❌ 部分支持 | ✅ 需要 jqdatasdk | ⭐⭐ 不推荐 |
| **Alphalens** | ✅ 完全支持 | ❌ 无需外部 API | ⭐⭐⭐⭐⭐ 强烈推荐 |

**核心结论**：jqfactor_analyzer 虽然是开源的，但**强依赖 jqdatasdk** 获取价格和行业数据，不适合无聚宽权限的用户。**推荐使用 Alphalens**，它完全支持本地数据输入。

---

## 二、jqfactor_analyzer 详细分析

### 2.1 库概述

- **GitHub**: https://github.com/JoinQuant/jqfactor_analyzer
- **许可证**: MIT
- **用途**: 单因子分析 + 归因分析

### 2.2 数据依赖

```
requirements.txt:
├── jqdatasdk        ← 硬性依赖
├── pandas>=1.0.0
├── numpy>=1.15.0
├── scipy
├── statsmodels
├── matplotlib
├── seaborn
└── pyarrow
```

### 2.3 本地数据支持情况

| 数据类型 | 能否本地输入 | 说明 |
|---------|-------------|------|
| 因子值 | ✅ 可以 | pandas.DataFrame 格式 |
| 价格数据 | ❌ 不能 | 必须通过 jqdatasdk 获取 |
| 行业分类 | ❌ 不能 | 必须通过 jqdatasdk 获取 |
| 权重数据 | ❌ 不能 | 必须通过 jqdatasdk 获取 |

### 2.4 代码示例（需要聚宽权限）

```python
import jqfactor_analyzer as ja
import jqdatasdk as jq

# 必须先登录聚宽
jq.auth("账号", "密码")  # ← 没有账号就无法使用！

# 因子分析（factor_data 可以是本地的，但内部会调用 jqdatasdk）
far = ja.analyze_factor(
    factor_data,        # 本地 DataFrame 可以
    quantiles=10,
    periods=(1, 10),
    industry='jq_l1',   # 行业数据从 jqdatasdk 获取
    weight_method='avg',
    max_loss=0.1
)

# 内部会执行:
# - jqdatasdk.get_price() 获取价格计算收益
# - jqdatasdk.get_industry() 获取行业分类
```

### 2.5 不推荐原因

1. **硬依赖 jqdatasdk**: 没有聚宽账号无法使用核心功能
2. **数据获取不透明**: 内部自动调用 API 获取价格/行业数据
3. **无法自定义数据源**: 代码设计绑定了聚宽平台

---

## 三、Alphalens 详细分析

### 3.1 库概述

- **GitHub**: https://github.com/quantopian/alphalens
- **许可证**: Apache 2.0
- **开发者**: Quantopian（已关闭，库仍维护）
- **用途**: 因子绩效分析

### 3.2 数据依赖

```
依赖项:
├── pandas        ← 无外部 API
├── numpy
├── scipy
├── statsmodels
├── matplotlib
└── seaborn
```

**关键优势**: 无任何外部 API 依赖，完全基于 pandas DataFrame 工作。

### 3.3 本地数据支持情况

| 数据类型 | 能否本地输入 | 说明 |
|---------|-------------|------|
| 因子值 | ✅ 可以 | pandas.DataFrame 或 Series |
| 价格数据 | ✅ 可以 | pandas.DataFrame |
| 行业分组 | ✅ 可以 | pandas.Series |
| 市值分组 | ✅ 可以 | pandas.Series |

### 3.4 数据格式要求

```python
# 因子数据格式
factor_data = pd.DataFrame({
    'date': ['2020-01-01', '2020-01-01', '2020-01-02', '2020-01-02'],
    'asset': ['000001.XSHE', '000002.XSHE', '000001.XSHE', '000002.XSHE'],
    'factor': [1.2, 0.8, 1.5, 0.6]
})
factor_data = factor_data.set_index(['date', 'asset'])

# 价格数据格式
pricing = pd.DataFrame(
    index=pd.DatetimeIndex(['2020-01-01', '2020-01-02', '2020-01-03']),
    columns=['000001.XSHE', '000002.XSHE'],
    data=[[10.0, 20.0], [10.5, 20.5], [11.0, 21.0]]
)

# 行业分组（可选）
sector = pd.Series({
    '000001.XSHE': '金融',
    '000002.XSHE': '房地产'
})
```

### 3.5 使用示例

```python
import alphalens
from alphalens.utils import get_clean_factor_and_forward_returns
from alphalens.tears import create_full_tear_sheet

# 准备数据（全部本地）
factor_data = get_clean_factor_and_forward_returns(
    factor=factor_values,    # 本地因子值
    prices=pricing,          # 本地价格
    quantiles=5,             # 分5组
    periods=(1, 5, 10),      # 持仓周期
    groupby=sector           # 行业分组（可选）
)

# 生成完整分析报告
create_full_tear_sheet(factor_data)
```

### 3.6 分析内容

| 分析类型 | 内容 |
|---------|------|
| **收益分析** | 分组收益、累计收益、多空收益 |
| **IC 分析** | IC 均值、IC 标准差、ICIR、t 统计量 |
| **换手率分析** | 分组换手率、因子值变化 |
| **分组分析** | 按行业/市值分组的因子表现 |

### 3.7 安装

```bash
# pip 安装
pip install alphalens-reloaded  # 社区维护版

# 或 conda 安装
conda install -c conda-forge alphalens
```

---

## 四、功能对比

| 功能 | jqfactor_analyzer | Alphalens |
|------|-------------------|-----------|
| 本地因子值 | ✅ | ✅ |
| 本地价格数据 | ❌ | ✅ |
| 本地行业数据 | ❌ | ✅ |
| IC 分析 | ✅ | ✅ |
| 分组收益 | ✅ | ✅ |
| 换手率分析 | ✅ | ✅ |
| 行业中性化 | ✅（需 API） | ✅（本地） |
| 归因分析 | ✅ | ❌ |
| 可视化 | ✅ | ✅ |
| 无需账号 | ❌ | ✅ |

---

## 五、推荐方案

### 5.1 首选：Alphalens

```python
# 完整本地数据因子分析流程
import pandas as pd
import alphalens
from alphalens.utils import get_clean_factor_and_forward_returns
from alphalens.tears import create_full_tear_sheet

# 1. 准备因子值（从本地数据库/Tushare/AKShare）
factor_values = pd.read_csv('factor_values.csv', index_col=0, parse_dates=True)

# 2. 准备价格数据（从本地数据库/Tushare/AKShare）
pricing = pd.read_csv('prices.csv', index_col=0, parse_dates=True)

# 3. 准备行业分组（可选）
sector = pd.read_csv('sectors.csv', index_col=0)['sector']

# 4. 数据清洗
factor_data = get_clean_factor_and_forward_returns(
    factor=factor_values.stack(),  # 转换为 MultiIndex
    prices=pricing,
    quantiles=5,
    periods=(1, 5, 10, 20),
    groupby=sector
)

# 5. 生成分析报告
create_full_tear_sheet(factor_data)
```

### 5.2 补充：自建归因分析

如果需要 jqfactor_analyzer 的归因分析功能，可参考以下开源方案：

```python
# Brinson 归因模型（自研）
def brinson_attribution(portfolio_weights, portfolio_returns, 
                        benchmark_weights, benchmark_returns):
    """
    Brinson 归因分析
    - 配置效应 = Σ(w_p - w_b) * R_b
    - 选择效应 = Σ w_b * (R_p - R_b)
    - 交互效应 = Σ (w_p - w_b) * (R_p - R_b)
    """
    allocation = (portfolio_weights - benchmark_weights) * benchmark_returns
    selection = benchmark_weights * (portfolio_returns - benchmark_returns)
    interaction = (portfolio_weights - benchmark_weights) * (portfolio_returns - benchmark_returns)
    
    return {
        'allocation': allocation.sum(),
        'selection': selection.sum(),
        'interaction': interaction.sum(),
        'total': allocation.sum() + selection.sum() + interaction.sum()
    }
```

---

## 六、结论

**不推荐 jqfactor_analyzer**：
- 硬依赖聚宽账号和数据接口
- 无聚宽权限则无法使用核心功能
- 不适合授权结束后的本地化需求

**推荐 Alphalens**：
- 完全支持本地数据
- 无需任何外部账号
- 功能完整、社区活跃
- 可配合 Tushare/AKShare 数据源使用

---

## 附录：资源链接

- Alphalens GitHub: https://github.com/quantopian/alphalens
- Alphalens 文档: https://alphalens.readthedocs.io
- jqfactor_analyzer GitHub: https://github.com/JoinQuant/jqfactor_analyzer
- Tushare: https://tushare.pro
- AKShare: https://akshare.akfamily.xyz
