# 聚宽与米筐因子研究资源对比调研报告

> 2026-04-25 | 用于平台选择与参考文档

---

## 一、摘要

| 维度 | 聚宽 (JoinQuant) | 米筐 (Ricequant) | 结论 |
|------|------------------|------------------|------|
| **数据字段数量** | 300+ 内置因子 | 100+ 内置因子 | 聚宽更丰富 |
| **算子支持** | 60+ 函数 | 40+ 函数 | 聚宽更丰富 |
| **因子定义方式** | Factor 类继承 | Factor 表达式 | 各有特点 |
| **财务 PIT 处理** | ✅ 支持 | ✅ 支持 | 相当 |
| **风格因子模型** | CNE5 + CNE6 Pro | CNE5 | 聚宽更完整 |
| **另类数据** | 新闻舆情、ESG | 新闻舆情、ESG | 相当 |
| **开源分析框架** | jqfactor_analyzer | 无 | 聚宽优势 |

**推荐结论**：对于因子研究，**聚宽的数据字段和算子更丰富**，且有开源分析框架可参考；米筐在基础功能上与聚宽相当，但在预定义因子数量上略少。

---

## 二、数据字段详细对比

### 2.1 价量数据字段

| 字段类别 | 聚宽 (JoinQuant) | 米筐 (Ricequant) | 字段说明 |
|----------|------------------|------------------|----------|
| **基础行情** | open, close, high, low, volume, money | open, close, high, low, volume, total_turnover | 开盘价、收盘价、最高价、最低价、成交量、成交额 |
| **价格衍生** | vwap (成交额/成交量) | vwap | 成交量加权平均价 |
| **涨跌幅** | change_rate | change_rate | 涨跌幅 |
| **换手率** | VOL5, VOL10, VOL20, VOL60, VOL120, VOL240 | turnover_rate | 各周期平均换手率 |
| **换手率衍生** | DAVOL5, DAVOL10, DAVOL20 | - | 短期换手率/长期换手率比值 |
| **量变动速率** | VROC6, VROC12 | - | 成交量变动速率 |
| **量标准差** | VSTD10, VSTD20 | - | 成交量标准差 |
| **成交额统计** | TVMA6, TVMA20, TVSTD6, TVSTD20 | - | 成交额均值/标准差 |
| **量指数移动平均** | VEMA5, VEMA10, VEMA12, VEMA26 | - | 成交量 EMA |
| **VMACD** | VDIFF, VDEA, VMACD | - | 成交量 MACD |
| **VOSC** | VOSC | - | 成交量震荡指标 |
| **ARBR** | AR, BR, ARBR | - | 人气意愿指标 |
| **VR** | VR | - | 成交量比率 |
| **WVAD** | WVAD, MAWVAD | - | 威廉变异离散量 |
| **ATR** | ATR6, ATR14 | ATR | 均幅指标（真实波幅移动平均） |
| **PSY** | PSY | - | 心理线指标 |

**价量数据小结**：聚宽提供 ~25 种量价衍生字段，米筐提供 ~8 种基础字段。聚宽在情绪类量价因子上明显更丰富。

---

### 2.2 技术指标字段

| 字段类别 | 聚宽 (JoinQuant) | 米筐 (Ricequant) | 字段说明 |
|----------|------------------|------------------|----------|
| **移动均线** | MAC5, MAC10, MAC20, MAC60, MAC120 | MA_N | 简单移动均线 |
| **指数均线** | EMA5, EMA10, EMA12, EMA20, EMA26, EMA120 | EMA_N | 指数移动均线 |
| **MACD** | MACDC | MACD | 平滑异同移动平均线 |
| **布林带** | boll_up, boll_down | BOLL | 布林带上下轨 |
| **乖离率** | BIAS5, BIAS10, BIAS20, BIAS60 | BIAS_N | 收盘价偏离均线程度 |
| **CCI** | CCI10, CCI15, CCI20, CCI88 | CCI | 顺势指标 |
| **RSI** | - | RSI_N | 相对强弱指标 |
| **KDJ** | - | KDJ | 随机指标 |
| **MFI** | MFI14 | MFI | 资金流量指标 |
| **TRIX** | TRIX5, TRIX10 | TRIX | 三重指数平滑 |
| **MASS** | MASS | - | 梅斯线 |
| **CR** | CR20 | - | CR 指标 |
| **Aroon** | arron_up_25, arron_down_25 | - | Aroon 指标 |
| **Bull/Bear Power** | bull_power, bear_power | - | 多空力道 |

**技术指标小结**：聚宽侧重均线和趋势类指标；米筐通过 RQFactor 支持更灵活的技术指标定义（MACD, KDJ, RSI 等）。

---

### 2.3 财务基本面字段

#### 2.3.1 盈利能力因子

| 字段代码 | 聚宽 | 米筐 | 字段说明 |
|----------|------|------|----------|
| `roe_ttm` | ✅ | ✅ (return_on_equity_ttm) | 净资产收益率 = 净利润 / 股东权益 |
| `roa_ttm` | ✅ | ✅ (return_on_asset_ttm) | 总资产回报率 = 净利润 / 总资产 |
| `roic_ttm` | ✅ | ✅ | 投入资本回报率 |
| `rnoa_ttm` | ✅ | - | 经营资产回报率 |
| `net_profit_ratio` | ✅ | ✅ (net_profit_margin) | 销售净利率 = 净利润 / 营业收入 |
| `gross_income_ratio` | ✅ | ✅ (gross_profit_margin) | 销售毛利率 = (营收-成本) / 营收 |
| `operating_profit_ratio` | ✅ | - | 营业利润率 |
| `operating_profit_to_operating_revenue` | ✅ | - | 营业利润/营业总收入比 |

#### 2.3.2 运营能力因子

| 字段代码 | 聚宽 | 米筐 | 字段说明 |
|----------|------|------|----------|
| `total_asset_turnover_rate` | ✅ | ✅ | 总资产周转率 = 营收 / 总资产 |
| `current_asset_turnover_rate` | ✅ | - | 流动资产周转率 |
| `fixed_assets_turnover_rate` | ✅ | - | 固定资产周转率 |
| `equity_turnover_rate` | ✅ | - | 股东权益周转率 |
| `inventory_turnover_rate` | ✅ | ✅ | 存货周转率 |
| `inventory_turnover_days` | ✅ | - | 存货周转天数 |
| `account_receivable_turnover_rate` | ✅ | ✅ | 应收账款周转率 |
| `account_receivable_turnover_days` | ✅ | - | 应收账款周转天数 |
| `accounts_payable_turnover_rate` | ✅ | - | 应付账款周转率 |
| `OperatingCycle` | ✅ | - | 营业周期 = 应收账款天数 + 存货天数 |

#### 2.3.3 偿债能力因子

| 字段代码 | 聚宽 | 米筐 | 字段说明 |
|----------|------|------|----------|
| `current_ratio` | ✅ | ✅ | 流动比率 = 流动资产 / 流动负债 |
| `quick_ratio` | ✅ | ✅ | 速动比率 = (流动资产-存货) / 流动负债 |
| `super_quick_ratio` | ✅ | - | 超速动比率 |
| `debt_to_asset_ratio` | ✅ | ✅ | 资产负债率 = 负债 / 总资产 |
| `debt_to_equity_ratio` | ✅ | ✅ | 产权比率 = 负债 / 股东权益 |
| `debt_to_tangible_equity_ratio` | ✅ | - | 有形净值债务率 |
| `equity_to_asset_ratio` | ✅ | - | 股东权益比率 |
| `MLEV` | ✅ | - | 市场杠杆 |
| `long_term_debt_to_asset_ratio` | ✅ | - | 长期负债/总资产 |

#### 2.3.4 成长能力因子

| 字段代码 | 聚宽 | 米筐 | 字段说明 |
|----------|------|------|----------|
| `operating_revenue_growth_rate` | ✅ | ✅ (inc_revenue) | 营收增长率 |
| `net_profit_growth_rate` | ✅ | ✅ | 净利润增长率 |
| `total_asset_growth_rate` | ✅ | ✅ | 总资产增长率 |
| `net_asset_growth_rate` | ✅ | - | 净资产增长率 |
| `DEGM` | ✅ | - | 毛利率增长 |
| `operating_profit_growth_rate` | ✅ | - | 营业利润增长率 |
| `PEG` | ✅ | ✅ | 市盈率相对盈利增长比率 |
| `total_profit_growth_rate` | ✅ | - | 利润总额增长率 |
| `net_operate_cashflow_growth_rate` | ✅ | - | 经营现金流增长率 |

#### 2.3.5 现金流因子

| 字段代码 | 聚宽 | 米筐 | 字段说明 |
|----------|------|------|----------|
| `net_operate_cash_flow_to_total_liability` | ✅ | ✅ (`ocf_to_debt_ttm`) | 经营现金流/负债合计 |
| `net_operate_cash_flow_coverage` | ✅ | ✅ (`surplus_cash_protection_multiples_ttm`) | 净利润现金含量（盈余现金保障倍数） |
| `cash_rate_of_sales` | ✅ | ✅ | 经营现金流/营业收入 |
| `net_operate_cash_flow_to_asset` | ✅ | - | 总资产现金回收率 |
| `cash_to_current_liability` | ✅ | - | 现金比率 |
| `ACCA` | ✅ | - | 现金流资产比与资产回报率之差 |
| `operating_cash_flow_per_share` | - | ✅ (`operating_cash_flow_per_share_ttm`) | 每股经营现金流 |
| `fcff` | - | ✅ (`fcff_ttm`) | 企业自由现金流量 |
| `fcfe` | - | ✅ (`fcfe_ttm`) | 股权自由现金流量 |
| `ocf_to_interest_bearing_debt` | - | ✅ (`ocf_to_interest_bearing_debt_ttm`) | 经营现金流/带息债务 |

> **修正说明**：经核实，米筐的财务衍生指标覆盖了大部分聚宽的现金流因子，但命名体系不同。聚宽用直观命名，米筐用财务术语命名。

---

### 2.4 估值因子

| 字段代码 | 聚宽 | 米筐 | 字段说明 |
|----------|------|------|----------|
| `pe_ratio` | ✅ | ✅ | 市盈率 = 市值 / 净利润 |
| `pb_ratio` | ✅ | ✅ | 市净率 = 市值 / 净资产 |
| `ps_ratio` | ✅ | ✅ | 市销率 = 市值 / 营业收入 |
| `pcf_ratio` | ✅ | ✅ | 市现率 = 市值 / 经营现金流 |
| `market_cap` | ✅ | ✅ | 总市值 |
| `circulating_market_cap` | ✅ | ✅ | 流通市值 |
| `ev` | ✅ | ✅ | 企业价值 |
| `dividend_yield` | ✅ | ✅ | 股息率 |
| `cash_flow_to_price_ratio` | ✅ | - | 现金流市值比 |
| `sales_to_price_ratio` | ✅ | - | 营收市值比 |

---

### 2.5 风险因子（风格因子）

#### 聚宽风格因子 (CNE5 模型)

| 因子代码 | 因子名称 | 说明 |
|----------|----------|------|
| `size` | 市值因子 | 捕捉大盘股和小盘股收益差异 |
| `beta` | 贝塔因子 | 股票相对市场的波动敏感度 |
| `momentum` | 动量因子 | 过去两年相对强势股与弱势股差异 |
| `residual_volatility` | 残差波动率因子 | 剥离市场风险后的波动率收益差异 |
| `non_linear_size` | 非线性市值因子 | 中盘股效应 |
| `book_to_price_ratio` | 账面市值比因子 | 价值因子 |
| `liquidity` | 流动性因子 | 交易活跃度收益差异 |
| `earnings_yield` | 盈利能力因子 | 盈利收益差异 |
| `growth` | 成长因子 | 销售/盈利增长预期收益差异 |
| `leverage` | 杠杆因子 | 高杠杆与低杠杆股票收益差异 |

#### 米筐风险因子

| 因子代码 | 因子名称 | 说明 |
|----------|----------|------|
| `size` | 规模因子 | 对数市值 |
| `beta` | 贝塔因子 | CAPM 贝塔 |
| `momentum` | 动量因子 | 相对强弱 |
| `residual_volatility` | 残差波动率 | 特质波动率 |
| `non_linear_size` | 非线性市值 | 中市值效应 |
| `book_to_price` | 价值因子 | PB 倒数 |
| `liquidity` | 流动性因子 | 换手率衍生 |
| `earnings_yield` | 盈利因子 | EP 相关 |
| `growth` | 成长因子 | 增长率衍生 |
| `leverage` | 杠杆因子 | 财务杠杆 |

**风格因子小结**：两家都支持 CNE5 十因子模型，聚宽额外提供 CNE6 Pro 扩展因子。

---

### 2.6 另类数据字段

| 数据类别 | 聚宽 (JoinQuant) | 米筐 (Ricequant) | 说明 |
|----------|------------------|------------------|------|
| **新闻舆情** | 新闻联播文本 (CCTV_NEWS) | 舆情大数据 | 新闻情绪分析 |
| **分析师预期** | 一致预期数据 | 一致预期 | 分析师盈利预测 |
| **ESG 评级** | ✅ | ✅ | ESG 评分 |
| **资金流** | get_money_flow | get_money_flow | 主力/散户资金流向 |
| **龙虎榜** | get_billboard_list | 公告相关 | 异常交易数据 |
| **融资融券** | get_mtss | get_mtss | 融资融券数据 |
| **沪深港通** | STK_HK_HOLD_INFO | 南北向资金 | 北向资金持股 |
| **机构持仓** | 公募基金持仓 | 基金持仓 | 机构持股变动 |

---

## 三、算子详细对比

### 3.1 时间序列算子

| 算子名称 | 聚宽 | 米筐 | 功能说明 |
|----------|------|------|----------|
| `MA/N日均值` | ✅ | ✅ | 简单移动平均 |
| `EMA` | ✅ | ✅ | 指数移动平均 |
| `STD` | ✅ | ✅ | 标准差 |
| `SUM` | ✅ | ✅ | 滚动求和 |
| `MAX` | ✅ | ✅ | 滚动最大值 |
| `MIN` | ✅ | ✅ | 滚动最小值 |
| `HHV` | ✅ | ✅ | 最高值 |
| `LLV` | ✅ | ✅ | 最低值 |
| `REF` | ✅ | ✅ | 引用 N 期前的值 |
| `DELAY` | ✅ | ✅ | 延迟 N 期 |
| `DELTA` | ✅ | ✅ | 时序变化值 (当前值 - N期前值) |
| `PCT_CHANGE` | ✅ | ✅ | 时序变化率 |
| `DIFF` | ✅ | ✅ | 差分 |
| `CORR` | ✅ | ✅ | 相关系数 |
| `COVAR` | ✅ | ✅ | 协方差 |
| `TS_RANK` | ✅ | ✅ | 时间序列排名 |
| `TS_ZSCORE` | ✅ | ✅ | 时间序列 Z 分数 |
| `TS_REG` | - | ✅ | 时间序列回归 |
| `TS_AVG` | ✅ | - | 时间序列平均 |

### 3.2 截面算子

| 算子名称 | 聚宽 | 米筐 | 功能说明 |
|----------|------|------|----------|
| `RANK` | ✅ | ✅ | 截面排名 |
| `CS_RANK` | ✅ | ✅ | 截面排名（归一化） |
| `CS_ZSCORE` | ✅ | ✅ | 截面标准化 |
| `DEMEAN` | ✅ | ✅ | 截面去均值 |
| `SCALE` | ✅ | ✅ | 截面缩放 |
| `NORMALIZE` | ✅ | ✅ | 截面归一化 |
| `TOP/BOTTOM` | ✅ | ✅ | 取前/后 N 名 |
| `QUANTILE` | ✅ | ✅ | 分位数分组 |

### 3.3 数学运算算子

| 算子名称 | 聚宽 | 米筐 | 功能说明 |
|----------|------|------|----------|
| `ABS` | ✅ | ✅ | 绝对值 |
| `LOG` | ✅ | ✅ | 对数 |
| `EXP` | ✅ | ✅ | 指数 |
| `POWER` | ✅ | ✅ | 幂运算 |
| `SQRT` | ✅ | ✅ | 平方根 |
| `SIGN` | ✅ | ✅ | 符号函数 |
| `IF` | ✅ | ✅ | 条件判断 |
| `MAX2/MIN2` | ✅ | ✅ | 两值取大/小 |
| `CLIP` | ✅ | - | 截断 |

### 3.4 统计算子

| 算子名称 | 聚宽 | 米筐 | 功能说明 |
|----------|------|------|----------|
| `WINSORIZE` | ✅ | ✅ | 去极值（分位数/标准差法） |
| `WINSORIZE_MED` | ✅ | - | 去极值（中位数法） |
| `STANDARDLIZE` | ✅ | ✅ | Z-score 标准化 |
| `NEUTRALIZE` | ✅ | ✅ | 行业/市值中性化 |
| `DECAY` | ✅ | ✅ | 线性衰减 |

### 3.5 行业算子

| 算子名称 | 聚宽 | 米筐 | 功能说明 |
|----------|------|------|----------|
| `INDUSTRY_NEUTRALIZE` | ✅ | ✅ | 行业中性化 |
| `INDUSTRY_RANK` | ✅ | ✅ | 行业内排名 |
| `INDUSTRY_MEAN` | ✅ | - | 行业均值 |
| `INDUSTRY_STD` | ✅ | - | 行业标准差 |

**行业分类支持**：

| 分类体系 | 聚宽 | 米筐 |
|----------|------|------|
| 申万一级行业 (sw_l1) | ✅ | ✅ |
| 申万二级行业 (sw_l2) | ✅ | ✅ |
| 申万三级行业 (sw_l3) | ✅ | ✅ |
| 聚宽一级行业 (jq_l1) | ✅ | - |
| 聚宽二级行业 (jq_l2) | ✅ | - |
| 证监会行业 (zjw) | ✅ | ✅ |

---

## 四、因子定义方式对比

### 4.1 聚宽：Factor 类继承方式

```python
from jqfactor import Factor

class MA5(Factor):
    name = 'ma5'                  # 因子名称
    max_window = 5                # 时间窗口
    dependencies = ['close']      # 依赖数据
    
    def calc(self, data):
        # data['close'] 是 DataFrame
        return data['close'][-5:].mean()
```

**特点**：
- 面向对象，逻辑更清晰
- 需要实现 `calc` 方法
- 支持多因子组合
- 支持在 `dependencies` 中引用其他自定义因子

### 4.2 米筐：Factor 表达式方式

```python
from rqfactor import Factor

# 简单因子表达式
f = (Factor('close') - Factor('open')) / (Factor('high') - Factor('low'))

# 引用内置因子
f = 1 / Factor('pe_ratio')

# 引用私有因子
f = Factor('private.my_factor')
```

**特点**：
- 声明式，表达式更简洁
- 支持链式调用
- 内置算子可直接使用
- 支持引用技术指标（from rqfactor.indicators import KDJ）

---

## 五、数据处理能力对比

### 5.1 财务数据 PIT 处理

| 功能 | 聚宽 | 米筐 | 说明 |
|------|------|------|------|
| PIT 财务查询 | `get_fundamentals()` | `get_pit_financials_ex()` | 防止未来数据 |
| 报告期字段 | 单季度/年度 | `_mrq_n`, `_ttm_n`, `_lyr_n` 后缀 | 多报告期支持 |
| 财务衍生因子 | 自动计算 | 自动计算 | TTM、增长率等 |

### 5.2 数据预处理函数

| 功能 | 聚宽函数 | 米筐函数 | 说明 |
|------|----------|----------|------|
| 中性化 | `neutralize()` | `INDUSTRY_NEUTRALIZE()` | 行业/市值中性化 |
| 去极值 | `winsorize()`, `winsorize_med()` | `winsorize()` | 分位数/标准差法 |
| 标准化 | `standardlize()` | `standardize()` | Z-score |
| 缺失值处理 | `fillna` | `fillna` | 可选填充方式 |

---

## 六、API 完整性对比

### 6.1 因子分析 API

| 功能 | 聚宽 | 米筐 |
|------|------|------|
| 单因子分析 | `analyze_factor()` | `factor_analysis()` |
| IC 计算 | RankIC / NormalIC | RankIC / NormalIC |
| 分组收益 | ✅ | ✅ |
| 换手率分析 | ✅ | ✅ |
| 可视化报告 | `create_full_tear_sheet()` | `create_full_tear_sheet()` |
| 因子缓存 | `save_factor_values_by_group()` | 支持 |

### 6.2 因子库获取

| 功能 | 聚宽 | 米筐 |
|------|------|------|
| 获取所有因子 | `get_all_factors()` | `get_all_factor_names()` |
| 获取因子值 | `get_factor_values()` | `get_factor()` |
| 因子看板 | `get_factor_kanban_values()` | - |
| 风格因子暴露 | `get_factor_style_returns()` | 风险因子模块 |

---

## 七、结论与建议

### 7.1 平台选择建议

| 用户需求 | 推荐平台 | 理由 |
|----------|----------|------|
| **因子数量优先** | 聚宽 | 300+ 内置因子，覆盖更全面 |
| **技术指标优先** | 米筐 | 表达式灵活，技术指标库完善 |
| **风格因子模型** | 聚宽 | CNE5 + CNE6 Pro，更完整 |
| **学习参考** | 聚宽 | 开源 jqfactor_analyzer 可学习 |
| **因子定义灵活** | 米筐 | 表达式方式更简洁 |

### 7.2 综合评价

**聚宽优势**：
1. 内置因子数量多（300+）
2. 风格因子模型更完整（CNE5 + CNE6 Pro）
3. 有开源分析框架可参考学习
4. 因子看板功能更丰富
5. 情绪类量价因子完整

**米筐优势**：
1. 因子定义表达式更简洁直观
2. 技术指标库完善（MACD, KDJ, RSI 等）
3. 与 RQAlpha Plus 回测框架无缝集成
4. 文档质量较高，示例丰富

**建议**：
- 如果您的因子研究主要是**利用平台内置因子进行组合和检验**，推荐选择**聚宽**
- 如果您的因子研究需要**频繁自定义复杂因子**，米筐的表达式方式可能更便捷
- 建议优先使用聚宽完成因子初筛，再结合米筐进行回测验证

---

## 附录：参考链接

- 聚宽因子库文档: https://www.joinquant.com/help/api/help#name:factor_values
- 聚宽 JQData 文档: https://www.joinquant.com/help/api/help#name:JQData
- 米筐 RQData 文档: https://www.ricequant.com/doc/rqdata/python/index-rqdatac
- 米筐 RQFactor 文档: https://www.ricequant.com/doc/rqfactor/manual/index-rqfactor
- jqfactor_analyzer 开源库: https://github.com/JoinQuant/jqfactor_analyzer

---

## 附录A：聚宽完整因子清单（约230个）

> 数据来源：聚宽官方文档因子库页面（登录后获取）

### A.1 风格因子（CNE5 + 扩展）

| 因子代码 | 因子名称 | 说明 |
|----------|----------|------|
| size | 市值 | 市值因子 |
| beta | 贝塔 | 贝塔因子 |
| momentum | 传统动量 | 动量因子 |
| residual_volatility | 残差波动率 | 残差波动率因子 |
| non_linear_size | 非线性市值 | 非线性市值因子 |
| book_to_price_ratio | 账面市值比 | 账面市值比因子 |
| liquidity | 流动性 | 流动性因子 |
| earnings_yield | 盈利能力 | 盈利能力因子 |
| growth | 成长 | 成长因子 |
| leverage | 杠杆 | 杠杆因子 |
| btop | 市净率因子 | BP因子 |
| divyild | 分红因子 | 股息率因子 |
| earnqlty | 盈利质量因子 | 盈利质量 |
| earnvar | 盈利变动率因子 | 盈利波动 |
| earnyild | 收益因子 | 收益率 |
| financial_leverage | 财务杠杆因子 | 财务杠杆 |
| invsqlty | 投资能力因子 | 投资质量 |
| liquidty | 流动性因子 | 流动性 |
| long_growth | 长期成长因子 | 长期增长 |
| ltrevrsl | 长期反转因子 | 长期反转 |
| market_beta | 市场波动率因子 | 市场贝塔 |
| market_size | 市值规模因子 | 市值规模 |
| midcap | 中等市值因子 | 中市值 |
| profit | 盈利能力因子 | 盈利能力 |
| relative_momentum | 相对动量因子 | 相对动量 |
| resvol | 残余波动率因子 | 残余波动率 |

### A.2 财务因子（约100个）

**盈利能力**：roe_ttm, roa_ttm, roic_ttm, rnoa_ttm, net_profit_ratio, gross_income_ratio, operating_profit_ratio, ROAEBITTTM, profit_margin_ttm, roe_ttm_8y, roa_ttm_8y, DEGM, DEGM_8y, maximum_margin, margin_stability

**运营能力**：total_asset_turnover_rate, current_asset_turnover_rate, fixed_assets_turnover_rate, equity_turnover_rate, inventory_turnover_rate, inventory_turnover_days, account_receivable_turnover_rate, account_receivable_turnover_days, accounts_payable_turnover_rate, accounts_payable_turnover_days, OperatingCycle, asset_turnover_ttm

**偿债能力**：current_ratio, quick_ratio, super_quick_ratio, debt_to_asset_ratio, debt_to_equity_ratio, debt_to_tangible_equity_ratio, equity_to_asset_ratio, equity_to_fixed_asset_ratio, long_debt_to_asset_ratio, long_term_debt_to_asset_ratio, long_debt_to_working_capital_ratio

**成长能力**：operating_revenue_growth_rate, net_profit_growth_rate, total_asset_growth_rate, net_asset_growth_rate, total_profit_growth_rate, net_operate_cashflow_growth_rate, financing_cash_growth_rate, operating_profit_growth_rate

**现金流**：net_operate_cash_flow_to_total_liability, net_operate_cash_flow_coverage, cash_rate_of_sales, net_operate_cash_flow_to_asset, cash_to_current_liability, ACCA

**估值因子**：market_cap, circulating_market_cap, cash_flow_to_price_ratio, sales_to_price_ratio, operating_assets, financial_assets, operating_liability, financial_liability

**每股指标**：eps_ttm, cashflow_per_share_ttm, net_asset_per_share, operating_revenue_per_share, operating_profit_per_share, retained_earnings_per_share, capital_reserve_fund_per_share, surplus_reserve_fund_per_share

### A.3 量价因子（约50个）

**换手率系列**：VOL5, VOL10, VOL20, VOL60, VOL120, VOL240, DAVOL5, DAVOL10, DAVOL20, turnover_volatility

**成交量系列**：VROC6, VROC12, VSTD10, VSTD20, VEMA5, VEMA10, VEMA12, VEMA26, VDIFF, VDEA, VMACD, VOSC

**成交额系列**：TVMA6, TVMA20, TVSTD6, TVSTD20

**情绪指标**：AR, BR, ARBR, VR, WVAD, MAWVAD, PSY, money_flow_20

**波动指标**：ATR6, ATR14, Variance20, Variance60, Variance120

**分布统计**：Skewness20, Skewness60, Skewness120, Kurtosis20, Kurtosis60, Kurtosis120, sharpe_ratio_20, sharpe_ratio_60, sharpe_ratio_120

### A.4 技术指标（约40个）

**均线系列**：MAC5, MAC10, MAC20, MAC60, MAC120, EMA5, EMA10, EMA12, EMA20, EMA26, EMA120, MACDC

**布林带**：boll_up, boll_down, BBIC

**乖离率**：BIAS5, BIAS10, BIAS20, BIAS60

**顺势指标**：CCI10, CCI15, CCI20, CCI88, CR20, MASS

**动量指标**：ROC6, ROC12, ROC20, ROC60, ROC120, TRIX5, TRIX10

**多空指标**：bull_power, bear_power, arron_up_25, arron_down_25

**价格位置**：fifty_two_week_close_rank, Price1M, Price3M, Price1Y, Rank1M, MFI14

**回归系数**：PLRC6, PLRC12, PLRC24

**价量趋势**：single_day_VPT, single_day_VPT_6, single_day_VPT_12

---

## 附录B：米筐风险因子模型详情

> 支持多种风险模型，满足不同调仓频率需求

### B.1 模型版本

| 模型名称 | 因子结构 | 适用场景 |
|----------|----------|----------|
| v1 | CNE5 | 标准10因子模型 |
| v2 | CNLT | 扩展17因子模型（含港股） |
| v2trd | CNTR | 交易型19因子模型 |
| v2_bjse | CNLT | 北交所版本 |
| v2trd_bjse | CNTR | 北交所交易版 |
| HKv1 | CNTR | 港股模型（公测） |

### B.2 风格因子明细

**CNE5 基础因子（10个）**：

| 风格因子 | 细分因子 |
|----------|----------|
| Liquidity | STOM |
| Leverage | MLEV |
| BTOP | BTOP |
| Earnings Yield | ETOP |
| Growth | EGRLF |
| Momentum | RSTR |
| Non_linear_size | MIDCAP |
| Size | LSIZE |
| Beta | BETA |
| Residual Volatility | HSIGMA |

**CNLT 扩展因子（17个）**：

| 风格因子 | 细分因子 |
|----------|----------|
| Liquidity | STOM |
| Leverage | MLEV |
| Earning Variability | VSAL |
| Earnings Quality | ACBS |
| Profitability | ATO |
| Investment Quality | AGRO |
| BTOP | BTOP |
| Earnings Yield | ETOP |
| Long Term reversal | LTRSTR |
| Growth | EGRLF |
| Momentum | RSTR |
| Mid cap | MIDCAP |
| Size | LSIZE |
| Beta | BETA |
| Residual Volatility | HSIGMA |
| Dividend Yield | DTOP |

**CNTR 交易型因子（19个）**：

在 CNLT 基础上增加：
- Sentiment (RREVR)
- Short term reversal (STREVRSL)
- Seasonality (SEASON)
- Industry momentum (INDMOM)

### B.3 因子数据类型

| 数据类型 | 说明 |
|----------|------|
| 风格因子暴露度 | 个股对风格因子的风险暴露 |
| 细分风格因子暴露度 | 细分维度的风险暴露 |
| 个股对指数贝塔 | 对上证50、沪深300、中证500的贝塔 |
| 因子收益率 | 全市场/沪深300/中证500/中证800股票池 |
| 特异收益率 | 无法被因子解释的个股收益 |
| 因子协方差 | 日度/月度/季度预测期限 |
| 特异风险 | 日度/月度/季度预测期限 |

---

## 附录C：米筐另类数据详情

### C.1 一致预期数据

| 字段类别 | 字段示例 |
|----------|----------|
| 营业收入预期 | comp_con_operating_revenue_t1/t2/t3/ftm |
| 净利润预期 | comp_con_net_profit_t1/t2/t3/ftm |
| EPS预期 | comp_con_eps_t1/t2/t3/ftm |
| ROE预期 | comp_con_roe_t1/t2/t3/ftm |
| 估值预期 | comp_con_pe/ps/pb_t1/t2/t3 |
| 增长率预期 | comp_con_operating_revenue_growth_ratio |
| 评级系数 | con_grd_coef, con_targ_price |

### C.2 新闻舆情数据

| 字段 | 说明 |
|------|------|
| news_emotion_indicator | 新闻情绪指标 |
| news_neutral_weight | 中性权重 |
| news_positive_weight | 正面权重 |
| news_negative_weight | 负面权重 |
| company_relevance | 公司相关度 |
| company_emotion_indicator | 公司情绪指标 |

### C.3 ESG评价数据

| Level | 内容 |
|-------|------|
| Level 0 | ESG综合评价等级（AAA-C）和得分（0-100） |
| Level 1 | 环境(E)、社会责任(S)、治理(G)三级评价 |
| Level 2 | 14个二级维度评价（4+5+5） |

---

## 附录D：对比总结

| 维度 | 聚宽 | 米筐 |
|------|------|------|
| 内置因子总数 | ~230 | ~100 |
| 风格因子模型 | CNE5 + CNE6 Pro | CNE5 + CNLT + CNTR |
| 风险模型版本 | 2个 | 6个（含港股、北交所） |
| 另类数据 | 新闻、ESG | 新闻、ESG、一致预期 |
| 因子定义方式 | 类继承 | 表达式 |
| 开源工具 | jqfactor_analyzer | 无 |
