# Coding Conventions

**Analysis Date:** 2026-04-23

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (e.g., `download.py`, `credentials.py`)
- Config files: `snake_case.py` for Python config (e.g., `credentials.example.py`)
- Data files: `snake_case.ext` (e.g., `download_log.json`, `price_1d.parquet`)
- Directory names: `snake_case` (e.g., `scripts/data/`, `data/stock/`)

**Functions:**
- `snake_case` with verb prefixes for actions (e.g., `download_metadata()`, `safe_download()`, `load_log()`, `mark_done()`, `check_quota()`)
- Boolean check functions use `is_` prefix (e.g., `is_done(key)`)
- Query functions use `get_` or describe the value (e.g., `remaining_quota_mb()`)

**Variables:**
- Module-level constants: `UPPER_SNAKE_CASE` (e.g., `DATA_ROOT`, `LOG_PATH`, `DAILY_QUOTA_MB`, `QUOTA_MARGIN_MB`, `PYTHON`, `STEPS`, `STEP_ORDER`)
- Local variables: `snake_case` (e.g., `stock_ids`, `date_ranges`, `all_frames`, `last_error`)
- Loop variables: short `snake_case` (e.g., `t` for instrument type, `s` for step name)

**Types:**
- No custom type annotations observed in current codebase
- Standard library types used implicitly (e.g., `Path`, `dict`, `str`, `int`)

## Code Style

**Formatting:**
- No automated formatter configured (no Black, Ruff, or autopep8)
- Indentation: 4 spaces
- Line length: Practical limit ~120 chars (f-strings and lambda calls occasionally longer)
- Trailing commas in multi-line collections (observed in `apis = [...]` lists)
- String style: f-strings for dynamic content, plain strings for static

**Linting:**
- No linter configured (no flake8, pylint, ruff, or mypy strict mode)
- VSCode `python.analysis.typeCheckingMode: "basic"` - minimal type checking
- No pre-commit hooks configured

**Docstrings:**
- Module-level docstrings: Triple-quoted strings at file top, Chinese language
  ```python
  """
  RQData 全量数据下载工具

  用法:
      export RQDATAC2_CONF='tcp://license:...@rqdatad-pro.ricequant.com:16011'
      python scripts/download.py [step]
      ...
  """
  ```
- Function docstrings: Single-line Chinese descriptions on key functions only
  ```python
  def safe_download(key, func, path, need_mb=50, **to_parquet_kwargs):
      """安全下载：断点续传 + 流量检查 + 错误重试"""
  ```
- Most functions lack docstrings - code is self-documenting via descriptive names
- Comments: Section separators using `# ── ... ──` pattern with unicode lines
  ```python
  # ── 配置 ──────────────────────────────────────────────────────────────────
  # ── 日志系统 ──────────────────────────────────────────────────────────────
  # ── 通用下载函数 ──────────────────────────────────────────────────────────
  ```

**Language:**
- Code identifiers: English (function names, variable names)
- Docstrings and comments: Chinese
- User-facing messages: Chinese (print statements like `"[跳过] {key} 已下载"`, `"[流量不足]"`)

## Import Organization

**Order:**
1. Standard library (`json`, `os`, `sys`, `time`, `traceback`, `datetime`, `pathlib`)
2. Third-party (`pandas`, `rqdatac`)
3. Local modules (none currently)

**Pattern:**
```python
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd
import rqdatac
```

**Path Aliases:**
- None configured (no `[tool.poetry.packages]` or path aliases)

**Config imports:**
```python
from config.credentials import RQSDK_LICENSE_KEY
```

## Error Handling

**Patterns:**
- Generic exception catch with retry: `except Exception as e` + retry loop
  ```python
  for attempt in range(3):
      try:
          df = func()
          ...
          return True
      except Exception as e:
          last_error = e
          print(f"失败 (尝试 {attempt+1}/3): {e}")
          traceback.print_exc()
          time.sleep(5)
  mark_failed(key, str(last_error))
  ```
- Silent exception suppression for non-critical operations:
  ```python
  try:
      concept_names = [...]
      for name in concept_names:
          apis.append(...)
  except Exception:
      pass
  ```
- No custom exception classes defined
- No exception hierarchy - all errors treated as `Exception`
- Error logging via `mark_failed()` which records to JSON log file

**No raise patterns:**
- Functions return `True`/`False` for success/failure rather than raising exceptions
- Download functions never raise - they catch, log, and continue

## Logging

**Framework:** `print()` statements - No `logging` module usage

**Patterns:**
- Progress messages: `print(f"  [下载] {key} ...", end=" ", flush=True)`
- Status prefixes in Chinese: `[跳过]`, `[下载]`, `[流量不足]`, `[流量紧张]`, `[合并]`, `[停止]`
- Step headers: `print("\n=== Step N: 名称 ===")`
- Summary: `print(f"RQData 全量下载工具 | 剩余流量: {remaining_quota_mb():.1f} MB")`
- Error output: `traceback.print_exc()` for full stack traces

**Structured logging:**
- Download progress tracked in `data/download_log.json` (not via logging module)
- Format: `{date: {key: {status, rows, bytes_est, ts}}}` or `{date: {key: {status, error, ts}}}`

## Configuration Management

**Pattern:** Python module constants (not YAML, not dataclass)

**Credential config** (`config/credentials.py`):
```python
RQSDK_LICENSE_KEY = ""
RQSDK_ACCOUNT_TYPE = ""
RQSDK_EXPIRY_DATE = ""
```

**Script config** (module-level constants):
```python
DATA_ROOT = Path(__file__).resolve().parent.parent / "data"
LOG_PATH = DATA_ROOT / "download_log.json"
DAILY_QUOTA_MB = 1024
QUOTA_MARGIN_MB = 100
PYTHON = sys.executable
```

**Step dispatch** (dict + ordered list):
```python
STEPS = {
    "metadata": download_metadata,
    "stock_price": download_stock_price,
    ...
}
STEP_ORDER = ["metadata", "stock_price", ...]
```

**VSCode Snippets** (`.vscode/snippets.code-snippets`):
- `rqinit` - RQData initialization
- `rqstrategy` - RQAlpha strategy template
- `rqfinancials` - Financial data query
- `rqfactor` - Factor definition

## Function Design

**Size:** Functions range from 3 lines (`load_log`) to ~80 lines (`download_stock_price`). Step functions follow a consistent pattern of listing APIs then iterating.

**Parameters:**
- Descriptive names with default values for optional params (e.g., `need_mb=50`)
- `**kwargs` pass-through for parquet options (e.g., `**to_parquet_kwargs`)
- Lambda closures for deferred execution (e.g., `lambda t=t: rqdatac.all_instruments(type=t)`)

**Return Values:**
- Boolean success/failure for download operations (`True`/`False`)
- Data objects for query functions (DataFrame or dict)
- None for void functions (log management)

**Closure pattern for lambdas:**
```python
# Default argument captures current value
lambda t=t: rqdatac.all_instruments(type=t)
```

## Module Design

**Exports:** No explicit `__all__` definitions. `config/__init__.py` contains only comments.

**Barrel Files:** `config/__init__.py` acts as package marker with usage documentation in comments only.

**Script entry point:**
```python
if __name__ == "__main__":
    main()
```

**Data flow pattern:**
- Scripts call RQData API -> get DataFrame -> save to Parquet
- JSON log tracks completion status
- No intermediate processing pipelines yet

## Parquet Storage Convention

**Write pattern:**
```python
df.to_parquet(str(path), engine="pyarrow", compression="snappy", index=True)
```

- Engine: always `pyarrow`
- Compression: always `snappy` (speed/compression balance)
- Index: included by default
- Non-DataFrame results: saved as JSON with `ensure_ascii=False`

## Credential Security

- Credentials in `config/credentials.py` - gitignored
- Template in `config/credentials.example.py` with empty values
- Import pattern: `from config.credentials import RQSDK_LICENSE_KEY`
- Never log or print credential values
- `.gitignore` explicitly lists `config/credentials.py`

---

*Convention analysis: 2026-04-23*
