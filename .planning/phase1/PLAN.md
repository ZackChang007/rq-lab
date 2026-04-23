# Phase 1 Plan: 回测模块最小实现

**日期**: 2026-04-23
**目标**: 跑通最简单的回测样例
**需求文档**: `docs/brainstorms/2026-04-23-backtest-module-requirements.md`

---

## 任务分解

### Task 1: 初始化 Bundle 数据
- 运行 `rqsdk download-data --sample` 下载免费样例数据
- 检查 bundle 目录确认数据可用
- 记录可用日期范围和证券列表
- **验证**: bundle 目录存在且包含 HDF5 文件

### Task 2: 创建 rq_lab 包骨架
- 创建 `rq_lab/__init__.py`
- 创建 `rq_lab/backtest.py`
- 更新 `pyproject.toml` 添加包配置（packages 配置）
- **验证**: `python -c "import rq_lab"` 成功

### Task 3: 实现 run_backtest() 函数
- 封装 `rqalpha_plus.run_func()`
- 设置 `auto_update_bundle=False`
- 接受策略函数 + 配置参数
- 返回完整结果字典
- 提取 `result['sys_analyser']['summary']` 的关键指标
- **验证**: 函数可调用，返回包含 summary 键的字典

### Task 4: 买入持有策略样例
- 编写 `examples/buy_and_hold.py` 使用 `run_backtest()`
- 策略: 首日全仓买入指定股票，持有到期末
- 使用 --sample 数据覆盖的日期范围
- 输出 total_returns, sharpe, max_drawdown
- **验证**: 运行成功，输出三个指标

### Task 5: 更新文档
- 更新 CLAUDE.md 添加回测模块说明
- 更新 README.md（如存在）
- **验证**: 文档内容与代码一致

---

## 依赖关系

```
Task 1 (Bundle 数据) ──→ Task 4 (样例运行)
Task 2 (包骨架) ──→ Task 3 (函数实现) ──→ Task 4 (样例运行)
Task 4 ──→ Task 5 (文档更新)
```

## 关键决策

1. **auto_update_bundle=False** - 禁用，避免消耗付费配额
2. **单文件方案** - `rq_lab/backtest.py`，不创建子目录
3. **日期范围** - 需在 Task 1 中确认 --sample 数据覆盖范围后确定

## 风险缓解

| 风险 | 缓解 |
|------|------|
| --sample 数据范围不足 | Task 1 先确认，调整回测参数 |
| rqalpha_plus 未安装 | 检查并运行 `rqsdk install rqalpha_plus` |
| 许可证未配置 | 检查 `config/credentials.py` |
