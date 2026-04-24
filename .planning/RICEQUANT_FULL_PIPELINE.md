# Ricequant 全链条流程计划

> 目标：在试用期内（截至 2026-05-22）完整跑通 Ricequant 全链条流程
> 创建日期：2026-04-24

---

## 全链条概览

```
数据下载 → 因子挖掘 → 因子检验 → 组合优化 → 策略回测 → 业绩归因
   (RQData)   (RQFactor)  (RQFactor)  (RQOptimizer) (RQAlpha+)  (RQPAttr)
```

---

## Phase 0: 数据下载 (RQData)

**状态**: 进行中 (Day 1 完成，剩余 ~800MB)

### 已完成 (Day 1)
- 元数据：合约列表、交易日历、收益率曲线、因子名称
- A股行情：日线行情、价格变化率
- A股财务：PIT财务、财务快报、业绩预告
- A股公司事件：分红、拆股、股本、换手率、停牌/ST、融资融券等

### 待下载 (流量刷新后)
- A股因子 (~100MB)
- 指数数据 (~150MB)
- 期货数据 (~100MB)
- 期权数据 (~50MB)
- 可转债数据 (~100MB)
- 公募基金数据 (~150MB)
- 风险因子 (~100MB)
- 宏观+另类+现货 (~50MB)

### 执行命令
```bash
python scripts/data/download.py stock_factor
python scripts/data/download.py index
python scripts/data/download.py futures
python scripts/data/download.py options
python scripts/data/download.py convertible
python scripts/data/download.py fund
python scripts/data/download.py risk_factor
python scripts/data/download.py macro_alt_spot
```

### 验收标准
- [ ] download_log.json 无 status=failed 记录
- [ ] 所有 parquet 文件可正常读取
- [ ] 生成 DATA_MANIFEST.md 完整清单

---

## Phase 1: 回测模块 (RQAlpha Plus)

**状态**: 已完成

### 成果
- `utils/common.py` - 共享配置（`setup_license()` + `QUOTA_SAFE_CONFIG`）
- `scripts/backtest/buy_and_hold.py` - 买入持有策略，遵循官方模板
- 使用 `--sample` 免费数据完成验证

---

## Phase 2: 因子挖掘与检验 (RQFactor)

**目标**: 跑通因子研究全流程

### 官方文档推荐流程

1. **定义因子**
   ```python
   from rqfactor import Factor
   f = 1 / Factor('pe_ratio_ttm')  # PE-TTM 倒数
   ```

2. **计算因子值**
   ```python
   from rqfactor import execute_factor
   import rqdatac
   rqdatac.init()

   ids = rqdatac.index_components('000300.XSHG', '20230101')
   df = execute_factor(f, ids, '20230101', '20231231')
   ```

3. **准备收益率数据**
   ```python
   price = rqdatac.get_price(ids, '20230101', '20231231', frequency='1d', fields='close')
   returns = price.pct_change()
   ```

4. **构建检验管道**
   ```python
   from rqfactor.analysis import FactorAnalysisEngine, Winzorization, ICAnalysis

   engine = FactorAnalysisEngine()
   engine.append(('winzorization', Winzorization(method='mad')))
   engine.append(('ic_analysis', ICAnalysis(rank_ic=True, industry_classification='sws')))

   result = engine.analysis(df, returns, ascending=True, periods=1)
   ```

5. **解读结果**
   - `result['ic_analysis'].summary()` - IC 统计指标
   - `result['ic_analysis'].show()` - 可视化

### 输出
- `scripts/factor/factor_research.py` - 完整因子研究示例

### 验收标准
- [ ] 因子计算成功
- [ ] IC 分析输出有效结果
- [ ] 理解 IC、IR、显著性等指标含义

---

## Phase 3: 组合优化 (RQOptimizer)

**目标**: 使用优化器生成目标权重

### 官方文档推荐场景

**场景：有 Alpha 因子需风控**
- 目标：指标最大化
- 约束：风格/行业/个股仓位约束

### 典型流程

1. **准备因子数据**（来自 Phase 2）
   ```python
   factor_data = execute_factor(custom_factor, stock_pool, start_date, end_date)
   ```

2. **设置优化参数**
   ```python
   from rqoptimizer import *

   # 目标函数
   objective = Objective('maximize_indicator')

   # 约束条件
   constraints = {
       'style': {'size': (-0.5, 0.5)},      # 市值因子偏离
       'industry': {'industry_neutral': True},  # 行业中性
       'position': {'min': 0, 'max': 0.05}  # 个股权重 0-5%
   }
   ```

3. **执行优化**
   ```python
   result = optimize(
       order_book_ids=stock_pool,
       current_weights=current_weights,
       target_indicator=factor_data,
       objective=objective,
       constraints=constraints
   )
   ```

### 输出
- `scripts/portfolio/portfolio_optimization.py` - 组合优化示例

### 验收标准
- [ ] 优化器返回有效权重
- [ ] 约束条件得到满足
- [ ] 理解目标函数和约束参数

---

## Phase 4: 业绩归因 (RQPAttr)

**目标**: 分析回测结果收益来源

### 官方文档推荐流程

1. **准备输入数据**
   ```python
   # 从回测结果提取权重
   positions = result['sys_analyser']['stock_positions']
   portfolio = result['sys_analyser']['portfolio']

   positions = positions.join(portfolio['total_value'])
   positions['asset_type'] = 'stock'
   positions = positions.reset_index()
   positions = positions.set_index(['date', 'order_book_id', 'asset_type'])
   weights = positions['market_value'] / positions['total_value']

   # 准备收益率
   daily_return = portfolio['unit_net_value'].pct_change().dropna()
   ```

2. **执行归因分析**
   ```python
   from rqpattr.api import performance_attribute

   result = performance_attribute(
       model="equity/factor_v2",
       daily_weights=weights,
       daily_return=daily_return,
       benchmark_info={'type': 'index', 'detail': '000300.XSHG'}
   )
   ```

3. **解读结果**
   - `result['returns_decomposition']` - Brinson 归因树
   - `result['attribution']['factor_attribution']` - 因子归因详情

### 输出
- `scripts/attribution/performance_attribution.py` - 归因分析示例

### 验收标准
- [ ] 归因分析成功执行
- [ ] 理解配置收益、选择收益、因子收益概念
- [ ] 可视化归因结果

---

## Phase 5: 全链条集成

**目标**: 构建端到端完整示例

### 流程设计

```
Day T: 因子计算 (Phase 2)
    ↓
Day T+1: 组合优化 (Phase 3)
    ↓
Day T+1~T+N: 策略回测 (Phase 1)
    ↓
Day T+N: 业绩归因 (Phase 4)
```

### 集成示例结构

```python
# scripts/full_pipeline.py

# 1. 因子定义与检验
factor = define_factor()
validate_factor(factor)

# 2. 组合优化
target_weights = optimize_portfolio(factor)

# 3. 策略回测
def init(context):
    context.target_weights = target_weights

def handle_bar(context, bar_dict):
    # 按目标权重调仓
    rebalance(context, context.target_weights)

config = copy.deepcopy(QUOTA_SAFE_CONFIG)
config["base"].update({...})
result = run_func(config=config, init=init, handle_bar=handle_bar)

# 4. 业绩归因
attribution = analyze_performance(result)
```

### 输出
- `scripts/full_pipeline.py` - 完整流程示例
- `docs/FULL_PIPELINE_GUIDE.md` - 使用指南

### 验收标准
- [ ] 全流程无报错运行
- [ ] 每个阶段输出可验证
- [ ] 文档清晰说明各阶段衔接

---

## 时间规划

| Phase | 预计时长 | 依赖 |
|-------|----------|------|
| Phase 0 (剩余) | 2-3 天 | - |
| Phase 2 | 1-2 天 | Phase 0 |
| Phase 3 | 1-2 天 | Phase 2 |
| Phase 4 | 1 天 | Phase 3 |
| Phase 5 | 1-2 天 | Phase 4 |

**总计**: 6-10 天（在试用期内完成）

---

## 官方文档参考

| 模块 | 本地文档 |
|------|----------|
| RQData | `docs/rqdata/RQDATA_DOCS.md` |
| RQFactor | `docs/rqfactor/RQFACTOR_DOCS.md`, `RQFACTOR_ADVANCED.md` |
| RQOptimizer | `docs/rqoptimizer/RQOPTIMIZER_DOCS.md`, `RQOPTIMIZER_API.md` |
| RQAlpha Plus | `docs/rqalpha-plus/RQALPHA_PLUS_DOCS.md`, `RQALPHA_PLUS_API_REFERENCE.md` |
| RQPAttr | `docs/rqpattr/RQPATTR_DOCS.md` |

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 流量不足 | 优先下载核心数据，非必要数据延后 |
| API 调用限制 | 严格遵循官方文档，不做过度设计 |
| 模块兼容性 | 使用官方推荐版本和配置 |
| 时间不足 | 聚焦核心流程，可选功能降级处理 |

---

## 更新日志

- 2026-04-24: 创建全链条计划
