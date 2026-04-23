# Architecture

**Analysis Date:** 2026-04-23

## Pattern Overview

**Overall:** Script-driven data pipeline with flat module structure

**Key Characteristics:**
- Single-purpose scripts orchestrated by manual step-by-step execution
- Procedural style: functions organized by data category, no class-based abstractions
- JSON-based state tracking for resumability (not a database)
- Data flows one direction: RQData API -> local Parquet files -> (future downstream consumers)
- Credentials isolated in `config/credentials.py`, excluded from version control
- All data output in Parquet format (pyarrow engine, snappy compression)

## Layers

**Configuration Layer:**
- Purpose: Provide credentials and environment setup
- Location: `config/credentials.py`, `config/credentials.example.py`
- Contains: `RQSDK_LICENSE_KEY` constant, connection instructions in docstring
- Depends on: Nothing (leaf node)
- Used by: Any script that initializes `rqdatac`

**Data Acquisition Layer:**
- Purpose: Download data from RQData API to local Parquet cache
- Location: `scripts/data/download.py`
- Contains: 12 step functions, each targeting a data category; utility functions for quota checking, logging, safe download
- Depends on: `rqdatac` (RQData SDK), `pandas`, `config/` (implicit via `rqdatac.init()`)
- Used by: Human operator via CLI

**Data Storage Layer:**
- Purpose: Persist downloaded data as Parquet/JSON files on local filesystem
- Location: `data/` (gitignored, tracked only by `DOWNLOAD_PROGRESS.md`)
- Contains: 17 subdirectories mirroring RQData API categories
- Depends on: Data Acquisition Layer writes here
- Used by: Future downstream modules (backtest, factor analysis, optimizer)

**Documentation Layer:**
- Purpose: Provide offline reference for all Ricequant SDK APIs
- Location: `docs/`
- Contains: 9 markdown files covering RQSDK, RQData, RQFactor, RQAlpha Plus, RQOptimizer, RQPAttr
- Depends on: Nothing (static reference)
- Used by: Developers and Claude Code when implementing features

**Design Spec Layer:**
- Purpose: Record planning documents and design decisions
- Location: `docs/specs/`
- Contains: `2026-04-23-rqdata-download-plan.md` (data download design)
- Depends on: Nothing
- Used by: Developers for reference

## Data Flow

**Primary Flow (Data Download):**

1. Operator sets `RQDATAC2_CONF` environment variable or relies on `rqdatac.init()` auto-config
2. `scripts/data/download.py` reads step argument from CLI
3. Each step function calls `rqdatac.*` API functions
4. `safe_download()` wraps each API call with quota check, retry logic, and logging
5. Results serialized to Parquet files under `data/{category}/`
6. `data/download_log.json` records status per download key per day
7. `data/DOWNLOAD_PROGRESS.md` provides human-readable summary

**State Management:**
- Resumability via `download_log.json`: `is_done(key)` checks prior completions
- Quota-aware: `check_quota()` reads `rqdatac.user.get_quota()` before each download
- Three-attempt retry with 5-second sleep between failures
- Failed downloads logged with truncated error message

**Future Flow (Backtest - not yet implemented):**

1. Read Parquet data from `data/` or use `rqdatac` live connection
2. Define strategy using RQAlpha Plus API (`init`, `handle_bar`)
3. Run backtest via `rqalpha_plus.run_func()` or CLI `rqalpha-plus run`
4. Access RQOptimizer for portfolio optimization within strategy
5. Access RQPAttr for post-hoc attribution analysis on backtest results

## Key Abstractions

**safe_download() - Universal Download Wrapper:**
- Purpose: Encapsulate the download-check-retry-log cycle for any RQData API call
- Location: `scripts/data/download.py` lines 96-136
- Pattern: Template method - accepts a callable `func`, a `key` for logging, a `path` for output
- Features:
  - Skip-if-done (idempotent resume)
  - Quota gate (prevents overuse)
  - Three-attempt retry with exponential backoff (5s fixed)
  - DataFrame -> Parquet, non-DataFrame -> JSON
  - Automatic directory creation (`path.parent.mkdir(parents=True, exist_ok=True)`)

**STEPS dict - Step Registry:**
- Purpose: Map step names to download functions for CLI dispatch
- Location: `scripts/data/download.py` lines 610-623
- Pattern: Command pattern via dict lookup
- Usage: `python scripts/data/download.py <step>` dispatches to `STEPS[step]()`

**download_log.json - State Store:**
- Purpose: Track download progress across sessions
- Location: `data/download_log.json`
- Schema: `{ "YYYY-MM-DD": { "key": { "status": "done"|"failed", "rows": N, "bytes_est": N, "ts": "ISO" } } }`
- Pattern: Append-only daily log with key-level deduplication

## Entry Points

**CLI - Data Download:**
- Location: `scripts/data/download.py`
- Triggers: Human operator via command line
- Responsibilities: Download all or specific categories of RQData
- Usage: `python scripts/data/download.py [step]` where step is one of: `metadata`, `stock_price`, `stock_finance`, `stock_factor`, `stock_events`, `index`, `futures`, `options`, `convertible`, `fund`, `risk_factor`, `macro_alt_spot`, `all`

**RQSDK CLI (external):**
- Location: Installed by `rqsdk` package (not in repo)
- Triggers: Human operator
- Responsibilities: License management, component installation, data download (sample)

**RQAlpha Plus CLI (external, not yet used in project):**
- Location: Installed by `rqsdk install rqalpha_plus`
- Triggers: Human operator
- Responsibilities: Run backtests with strategy files

## Error Handling

**Strategy:** Retry with logging, fail-safe quota protection

**Patterns:**
- Three-attempt retry in `safe_download()` with 5-second sleep between attempts
- Failed downloads recorded with truncated error message (first 200 chars)
- Quota check before every download: if remaining < `QUOTA_MARGIN_MB` (100MB), stop entirely
- Empty data treated as success (marked done with 0 rows)
- Stock ID list retrieval (`all_instruments(type="CS")`) has no retry - if this fails, the entire step fails since stock_ids is needed for subsequent calls

**Missing patterns (not yet needed):**
- No centralized error type hierarchy
- No structured logging framework (uses `print()` to stdout)
- No alerting on failures

## Cross-Cutting Concerns

**Logging:** Plain `print()` to stdout with prefixes `[跳过]`, `[下载]`, `[流量不足]`, `[流量紧张]`. JSON-based download log for machine-readable progress. `DOWNLOAD_PROGRESS.md` for human-readable summary (manually updated).

**Validation:** Post-hoc verification planned in spec (Step 12) but not yet implemented. No schema validation on downloaded data. Parquet integrity assumed from successful `to_parquet()` call.

**Authentication:** RQData connection via `rqdatac.init()` which reads `RQDATAC2_CONF` environment variable containing license key and server address. Credentials template at `config/credentials.example.py`. Actual credentials at `config/credentials.py` (gitignored).

**Quota Management:** Daily 1GB limit enforced by `remaining_quota_mb()` and `check_quota()`. Safety margin of 100MB. Each download estimates its need via `need_mb` parameter.

## Extensibility Assessment

**Adding a Backtest Module:**
- Natural fit as a new script or package alongside `scripts/data/download.py`
- Can consume downloaded Parquet files from `data/` or use `rqdatac` live
- RQAlpha Plus provides `run_func()` API for programmatic backtesting
- Key question: standalone script vs. reusable module. Current pattern is standalone scripts. A `scripts/backtest/` directory or `rq_lab/backtest/` package both work.
- Constraint: RQAlpha Plus strategies must define `init(context)` and `handle_bar(context, bar_dict)` callback functions

**Adding a Factor Analysis Module:**
- Depends on RQFactor package (installed via `rqsdk install rqalpha_plus`)
- Uses `rqfactor.Factor`, `execute_factor()`, `FactorAnalysisEngine`
- Can consume factor data from `data/factor/` or compute on-the-fly
- Natural location: `scripts/factor/` or `rq_lab/factor/`

**Adding an Optimizer Module:**
- Depends on RQOptimizer (installed with rqalpha_plus)
- Two APIs: stock selection (`rqoptimize.select_stock()`) and portfolio optimization (`rqoptimize.optimize()`)
- Typically used within RQAlpha Plus strategies, not standalone
- Natural location: `scripts/optimizer/` or integrated into backtest strategies

**Adding Attribution Analysis:**
- Depends on RQPAttr package
- Post-hoc analysis on backtest results
- Uses `rqalpha_plus.run_func()` results as input to RQPAttr APIs
- Natural location: `scripts/attribution/` or as post-processing step after backtest

**Key Design Constraints:**
1. RQData daily quota (1GB trial) limits how much data can be fetched per session
2. Trial license expires 2026-05-22 - all features must work within this window
3. No database - flat files only (Parquet + JSON)
4. Windows platform (path handling, multiprocessing considerations)
5. Single-user, single-machine context - no concurrency or distributed concerns
6. `rqsdk` manages package installation - do not pip-install Ricequant packages directly

---

*Architecture analysis: 2026-04-23*
