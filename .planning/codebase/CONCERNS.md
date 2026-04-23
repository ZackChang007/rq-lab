# Codebase Concerns

**Analysis Date:** 2026-04-23

## Flow Quota Management

**Trial Data vs Paid Data:**
- Issue: 不清楚三种数据来源的边界：`rqsdk download-data --sample`(试用数据)、`rqsdk update-data`(生产数据)、RQData API 直接调用(当前下载脚本)
- Files: `scripts/data/download.py`, `docs/rqsdk/RQSDK_MANUAL.md`
- Impact: 可能误用付费流量下载本应免费的试用数据，或因配额耗尽中断研究
- Fix approach:
  1. 明确 `download-data --sample` 不计入配额，但仅限日级别数据
  2. 当前 `download.py` 直接调用 RQData API，所有数据都计入配额
  3. 回测模块应优先使用 `--sample` 数据，仅在需要分钟/tick 数据时使用 `update-data`

**Daily Quota Exhaustion:**
- Issue: 已出现配额耗尽导致下载失败
- Files: `data/download_log.json` 行 370: `"status": "failed", "error": "Quota exceeded"`
- Impact: 数据下载中断，需等待次日配额刷新
- Current mitigation: 下载脚本设置了 100MB 安全余量 (`QUOTA_MARGIN_MB`)
- Recommendations: 
  - 新增回测模块前应检查当日剩余配额
  - 提供配额预警机制，避免关键研究时段配额耗尽

## Data Consistency

**Sample Data vs API Data:**
- Issue: `rqsdk download-data --sample` 数据与 RQData API 直接获取的数据可能存在差异
- Files: 
  - `docs/rqsdk/RQSDK_MANUAL.md` 行 72-76: 试用数据说明
  - `scripts/data/download.py`: 直接使用 API
- Impact: 回测结果可能因数据源不同而产生偏差
- Fix approach:
  1. 明确研究项目使用的数据来源
  2. 数据清单 (`DOWNLOAD_PROGRESS.md`) 标注数据来源类型
  3. 回测模块应明确数据依赖，统一使用同一来源

**Download Log Key Path Bug:**
- Issue: 下载日志中出现 Windows 反斜杠路径作为 key，可能影响跨平台兼容性
- Files: `data/download_log.json` 行 369: `"index\price_1d"` (应为 `index/price_1d`)
- Impact: 断点续传可能无法正确识别已下载项
- Fix approach: 统一使用正斜杠作为 key

## Concurrency Issues

**Data Update vs Backtest:**
- Issue: 文档明确禁止数据更新时运行回测
- Files: `docs/rqsdk/RQSDK_MANUAL.md` 行 87: "更新数据过程中请勿运行回测，避免同时读写"
- Impact: 数据损坏或回测结果异常
- Current mitigation: 无
- Recommendations:
  1. 回测模块启动前检查数据目录是否有写入锁
  2. 提供数据更新状态查询接口
  3. 在 CLAUDE.md 中明确并发规则

**RQAlpha Bundle vs Custom Data:**
- Issue: RQAlpha Plus 使用 `~/.rqalpha-plus/bundle/` 作为数据缓存，当前项目使用 `data/` 目录存储 Parquet 文件
- Files: 
  - `docs/rqalpha-plus/RQALPHA_PLUS_API_REFERENCE.md` 行 11: `data_bundle_path` 配置
  - `.gitignore` 行 15: 排除 `.rqalpha-plus/`
- Impact: 两套数据存储可能不同步，增加维护成本
- Fix approach:
  1. 明确回测数据来源策略：使用 RQAlpha bundle 还是自定义 Parquet
  2. 如使用自定义数据，需配置 `data_bundle_path` 或 `auto_update_bundle_path`

## Credential Security

**Hardcoded License Key Pattern:**
- Issue: `DOWNLOAD_PROGRESS.md` 中包含示例命令，展示了许可证格式
- Files: `data/DOWNLOAD_PROGRESS.md` 行 69
- Impact: 如不小心提交真实密钥将造成安全风险
- Current mitigation: `config/credentials.py` 已在 `.gitignore` 中
- Recommendations:
  1. 清理 `DOWNLOAD_PROGRESS.md` 中的示例命令，使用占位符
  2. 定期审计提交历史，确保无密钥泄露

**Environment Variable Exposure:**
- Issue: `download.py` 注释中包含环境变量设置方式，展示了许可证格式
- Files: `scripts/data/download.py` 行 5
- Impact: 新用户可能误解并在此处硬编码密钥
- Fix approach: 修改注释为安全的配置指引，指向 `credentials.py`

## Trial License Expiry

**License Expiration Date:**
- Issue: 试用授权于 2026-05-22 到期，距当前(2026-04-23)约 29 天
- Files: `CLAUDE.md` 行 5
- Impact: 到期后无法获取数据，所有研究工作停滞
- Current mitigation: 正在进行全量数据下载
- Recommendations:
  1. 优先完成核心数据下载（A股行情、财务、因子）
  2. 数据下载完成后验证完整性
  3. 考虑正式采购或续期方案

**Data Download Completion:**
- Issue: 数据下载未完成，剩余约 800MB 数据待下载
- Files: `data/DOWNLOAD_PROGRESS.md` 行 39-51
- Impact: 回测模块开发可能缺少必要数据
- Fix approach:
  1. 按优先级完成下载：stock_factor > index > risk_factor
  2. 每日检查配额并继续下载

## Architecture Extensibility

**Backtest Module Integration:**
- Issue: 新增回测模块需与现有组件衔接，接口设计需提前规划
- Files: 
  - `docs/rqfactor/RQFACTOR_DOCS.md`: 因子检验需回测结果
  - `docs/rqoptimizer/RQOPTIMIZER_DOCS.md`: 组合优化需策略信号
  - `docs/rqpattr/RQPATTR_DOCS.md`: 归因分析需组合权重
- Impact: 接口设计不当将导致重复开发
- Fix approach:
  1. 回测模块输出标准格式：
     - `daily_weights`: pd.Series (date, order_book_id, asset_type) -> weight
     - `daily_return`: pd.Series (date) -> return
     - `trades`: 交易记录 DataFrame
  2. 与 RQPAttr 归因分析接口对齐（见 `docs/rqpattr/RQPATTR_DOCS.md` 行 44-45）
  3. 因子检验输出可直接作为 RQOptimizer 输入

**Code Organization:**
- Issue: 当前仅有 `scripts/data/download.py`，无模块化结构
- Files: `scripts/` 目录
- Impact: 新增回测模块可能随意放置，导致代码混乱
- Fix approach:
  1. 建立清晰的模块结构：
     ```
     rq_lab/
     ├── data/          # 数据管理（已存在）
     ├── backtest/      # 回测引擎
     ├── factor/        # 因子研究
     ├── optimizer/     # 组合优化
     └── attribution/   # 归因分析
     ```
  2. 每个模块有独立的 `__init__.py` 和清晰的接口定义

## Windows Compatibility

**Path Handling:**
- Issue: 项目在 Windows 环境运行，路径处理需注意
- Files: 
  - `scripts/data/download.py` 行 26: `DATA_ROOT = Path(__file__).resolve().parent.parent / "data"`
  - `data/download_log.json` 行 369: Windows 反斜杠 key
- Impact: 跨平台开发可能出现路径问题
- Current mitigation: 使用 `pathlib.Path` 处理路径（推荐做法）
- Recommendations:
  1. 所有路径操作统一使用 `pathlib.Path`
  2. 日志 key 使用正斜杠：`f"{category}/{api_name}"`
  3. VS Code 配置统一换行符为 LF

**Multiprocessing Warning:**
- Issue: Python 在 Windows 上的多进程行为与 Linux 不同
- Files: 无（当前未使用多进程）
- Impact: 未来如需并行下载数据，可能出现问题
- Fix approach:
  1. 使用 `concurrent.futures` 而非 `multiprocessing`
  2. 或确保 `if __name__ == "__main__":` 保护入口点

## Test Coverage Gaps

**Download Script Untested:**
- Issue: 数据下载脚本无单元测试
- Files: `scripts/data/download.py` (656 行)
- Impact: 修改可能引入 bug，断点续传逻辑可能失效
- Risk: 高 - 数据完整性直接影响研究质量
- Priority: 高
- Recommendations:
  1. 添加核心函数测试：
     - `test_check_quota()` - 配额检查逻辑
     - `test_is_done()` - 断点续传识别
     - `test_mark_done/failed()` - 日志记录
  2. Mock `rqdatac` API 进行集成测试

**Data Validation Missing:**
- Issue: 下载数据后无验证步骤
- Files: `scripts/data/download.py`
- Impact: 数据损坏或缺失可能未被及时发现
- Recommendations:
  1. 下载后验证：行数 > 0、关键字段非空
  2. 生成数据清单摘要
  3. 提供数据完整性检查脚本

## Error Handling Fragility

**API Error Retries:**
- Issue: 当前重试机制为固定 3 次、间隔 5 秒
- Files: `scripts/data/download.py` 行 109-134
- Impact: 网络波动可能导致不必要的失败
- Fix approach:
  1. 使用指数退避：1s -> 2s -> 4s
  2. 区分可重试错误（网络超时）和不可重试错误（权限不足）

**Empty Data Handling:**
- Issue: 数据为空时标记为 done，但可能掩盖问题
- Files: `scripts/data/download.py` 行 113-116
- Impact: 预期有数据的 API 返回空结果可能被忽略
- Recommendations: 区分"真正的空数据"和"异常空数据"

## Documentation Gaps

**Missing Setup Guide:**
- Issue: 新用户快速启动指引不完整
- Files: `CLAUDE.md` 有环境配置，但缺少完整工作流
- Impact: 新研究任务时可能遗漏关键步骤
- Recommendations:
  1. 添加 `docs/quickstart.md`：
     - 环境配置 -> 数据下载 -> 运行示例 -> 开发新策略
  2. 更新 `CLAUDE.md` 添加回测模块开发指引

---

*Concerns audit: 2026-04-23*
