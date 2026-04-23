# Testing Patterns

**Analysis Date:** 2026-04-23

## Test Framework

**Runner:**
- Not configured - No test framework installed or configured
- `pyproject.toml` has no `[tool.pytest]`, `[tool.coverage]`, or test dependencies
- No `pytest`, `unittest`, `hypothesis`, or `coverage` in project dependencies

**Assertion Library:**
- Not applicable

**Run Commands:**
```bash
# No test commands configured
# Recommended setup (see below):
poetry add --group dev pytest pytest-cov
pytest                          # Run all tests
pytest -x                       # Stop on first failure
pytest --cov                    # Coverage report
pytest -q scripts/              # Run tests for specific directory
```

## Test File Organization

**Location:**
- No test directory or test files exist currently
- Recommended structure: `tests/` at project root

**Naming:**
- Recommended: `test_<module>.py` matching source file names
  - `tests/test_download.py` for `scripts/data/download.py`
  - `tests/test_config.py` for `config/`

**Recommended Structure:**
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures (rqdatac mock, tmp paths)
├── test_download.py         # Tests for scripts/data/download.py
├── test_config.py           # Tests for config/ module
└── data/                    # Test fixtures (sample parquet files)
    └── sample_instruments.parquet
```

## Test Structure

**Suite Organization:**
```python
# Recommended pattern based on project style
import pytest
from pathlib import Path
import json

class TestDownloadLog:
    """Tests for download log management functions."""

    def test_load_log_creates_empty_on_missing(self, tmp_path):
        log_path = tmp_path / "download_log.json"
        # Patch LOG_PATH or pass as parameter
        result = load_log()
        assert result == {}

    def test_mark_done_records_entry(self, tmp_path):
        mark_done("stock/price_1d", rows=1000, bytes_est=500000)
        log = load_log()
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in log
        assert log[today]["stock/price_1d"]["status"] == "done"
        assert log[today]["stock/price_1d"]["rows"] == 1000

    def test_is_done_finds_completed_key(self):
        mark_done("test_key", rows=10, bytes_est=100)
        assert is_done("test_key") is True

    def test_is_done_returns_false_for_missing(self):
        assert is_done("nonexistent_key") is False
```

**Patterns:**
- Setup: Use `tmp_path` fixture for file operations (pytest built-in)
- Teardown: `tmp_path` auto-cleaned by pytest
- Assertion: Standard `assert` statements (pytest style)

## Mocking

**Framework:** Recommended: `pytest-mock` (wraps `unittest.mock`)

**Patterns:**
```python
# Mock RQData API calls (requires license, cannot run in CI)
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_rqdatac():
    """Mock rqdatac for testing without license."""
    with patch("rqdatac.init"), \
         patch("rqdatac.all_instruments") as mock_instruments, \
         patch("rqdatac.get_price") as mock_price:
        mock_instruments.return_value = pd.DataFrame({
            "order_book_id": ["000001.XSHE", "600000.XSHG"]
        })
        mock_price.return_value = pd.DataFrame({
            "open": [10.0, 20.0],
            "close": [11.0, 21.0]
        })
        yield {
            "init": mock_instruments,
            "all_instruments": mock_instruments,
            "get_price": mock_price,
        }

# Mock quota API
@pytest.fixture
def mock_quota():
    with patch("rqdatac.user.get_quota") as mock:
        mock.return_value = {"bytes_limit": 1073741824, "bytes_used": 0}
        yield mock
```

**What to Mock:**
- All `rqdatac.*` API calls - they require a license and network access
- `rqdatac.init()` - license initialization
- `rqdatac.user.get_quota()` - quota checking
- File system paths - use `tmp_path` instead of `DATA_ROOT`

**What NOT to Mock:**
- `json.loads` / `json.dumps` - standard library, reliable
- `Path` operations - use `tmp_path` fixture
- `pd.DataFrame.to_parquet()` / `pd.read_parquet()` - well-tested in pandas

## Fixtures and Factories

**Test Data:**
```python
# conftest.py
import pytest
import pandas as pd
from pathlib import Path

@pytest.fixture
def sample_instruments_df():
    """Sample instruments DataFrame for testing."""
    return pd.DataFrame({
        "order_book_id": ["000001.XSHE", "600000.XSHG", "000300.XSHG"],
        "symbol": ["平安银行", "浦发银行", "沪深300"],
        "listed_date": ["1991-04-03", "1999-11-10", "2005-04-08"],
        "de_listed_date": ["None", "None", "None"],
    })

@pytest.fixture
def sample_stock_price_df():
    """Sample stock price DataFrame for testing."""
    return pd.DataFrame({
        "open": [10.0, 10.5, 11.0],
        "close": [10.5, 11.0, 10.8],
        "high": [10.8, 11.2, 11.5],
        "low": [9.8, 10.2, 10.5],
        "volume": [100000, 120000, 80000],
    })

@pytest.fixture
def log_dir(tmp_path):
    """Provide a temporary directory with a log file."""
    log_path = tmp_path / "download_log.json"
    return tmp_path, log_path
```

**Location:**
- `tests/conftest.py` for shared fixtures
- Inline fixtures in test files for module-specific data

## Coverage

**Requirements:** None enforced currently

**Recommended Configuration** (add to `pyproject.toml`):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"

[tool.coverage.run]
source = ["scripts", "config"]
omit = ["tests/*", "config/credentials.py"]

[tool.coverage.report]
show_missing = true
fail_under = 60  # Start with achievable target, raise over time
```

**View Coverage:**
```bash
pytest --cov --cov-report=term-missing    # Terminal report with line numbers
pytest --cov --cov-report=html             # HTML report in htmlcov/
```

## Test Types

**Unit Tests:**
- Scope: Individual functions from `scripts/data/download.py`
- Priority targets:
  - `load_log()` / `save_log()` - JSON log read/write
  - `mark_done()` / `mark_failed()` / `is_done()` - log state management
  - `check_quota()` - quota threshold logic
  - `safe_download()` - retry and error handling logic (mock rqdatac)
- Approach: Test each function in isolation with mocked dependencies

**Integration Tests:**
- Scope: End-to-end download workflow with mocked rqdatac
- Priority targets:
  - Full download step (e.g., `download_metadata()` with mocked API)
  - Parquet file creation and validation
  - Log file consistency after multi-step runs
- Approach: Mock rqdatac at the module level, verify file outputs

**E2E Tests:**
- Not applicable currently - requires active RQData license
- Could be added as manual/smoke tests with `@pytest.mark.skipif` guard

## Specific Testing Recommendations

### 1. Download Script (`scripts/data/download.py`)

**Testable functions (no rqdatac dependency):**
- `load_log()` - reads JSON, returns empty dict if file missing
- `save_log(log)` - writes JSON with proper encoding
- `mark_done(key, rows, bytes_est)` - adds completion entry
- `mark_failed(key, err_msg)` - adds failure entry
- `is_done(key)` - checks if key exists in any day's log
- `check_quota(need_mb)` - threshold comparison logic

**Key test scenarios:**
```python
# Log management
test_load_log_missing_file_returns_empty
test_save_log_creates_file_with_proper_encoding
test_mark_done_creates_today_entry
test_mark_done_appends_to_existing_day
test_mark_failed_truncates_error_message_at_200_chars
test_is_done_finds_key_across_multiple_days
test_is_done_returns_false_for_missing_key

# Quota checking
test_check_quota_returns_true_when_sufficient
test_check_quota_returns_false_below_margin
test_check_quota_returns_false_below_need
test_remaining_quota_mb_calculation

# Safe download
test_safe_download_skips_completed_key
test_safe_download_retries_on_failure
test_safe_download_marks_failed_after_3_retries
test_safe_download_handles_empty_dataframe
test_safe_download_handles_none_response
test_safe_download_saves_parquet_correctly
test_safe_download_saves_json_for_non_dataframe

# Step functions (mocked rqdatac)
test_download_metadata_calls_all_instruments_for_each_type
test_download_stock_price_splits_date_ranges
test_download_stock_finance_iterates_years
```

### 2. Config Module (`config/`)

**Test scenarios:**
```python
test_credentials_example_has_empty_values
test_credentials_importable  # (only with actual credentials.py)
test_init_module_contains_usage_comments
```

### 3. Parquet Data Validation

**Validate downloaded data integrity:**
```python
import pandas as pd
from pathlib import Path

class TestDataIntegrity:
    """Validate downloaded Parquet files."""

    @pytest.fixture
    def data_dir(self):
        return Path("data")

    @pytest.mark.skipif(
        not Path("data/stock/price_1d.parquet").exists(),
        reason="Data files not downloaded yet"
    )
    def test_stock_price_parquet_readable(self, data_dir):
        df = pd.read_parquet(data_dir / "stock/price_1d.parquet")
        assert not df.empty
        assert "close" in df.columns

    @pytest.mark.skipif(
        not Path("data/instruments").exists(),
        reason="Data files not downloaded yet"
    )
    def test_instruments_parquet_has_order_book_id(self, data_dir):
        for f in (data_dir / "instruments").glob("*.parquet"):
            df = pd.read_parquet(f)
            assert "order_book_id" in df.columns
```

### 4. RQAlpha Plus Backtest Testing

**Strategy validation pattern:**
```python
# Recommended approach for testing trading strategies
from rqalpha_plus import run_func

def test_buy_and_hold_strategy():
    """Smoke test: strategy runs without error on small date range."""
    from rqalpha.api import *

    def init(context):
        context.stock = "000001.XSHE"

    def handle_bar(context, bar_dict):
        if get_position(context.stock).quantity == 0:
            order_target_percent(context.stock, 1)

    config = {
        "base": {
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",  # Short period for fast tests
            "accounts": {"STOCK": 100000},
        }
    }

    result = run_func(config=config, init=init, handle_bar=handle_bar)
    assert "sys_analyser" in result
    assert "summary" in result["sys_analyser"]

def test_strategy_no_invalid_orders():
    """Verify strategy does not generate invalid orders."""
    # ... run strategy and check order validity
```

**RQAlpha Plus testing considerations:**
- Requires RQData connection (mock or real)
- Use short date ranges for fast test execution
- Validate `result["sys_analyser"]["summary"]` keys exist
- Check that `stock_account.total_value` is non-negative
- Verify no duplicate orders in same bar
- Test edge cases: suspended stocks, limit up/down, delisted stocks

### 5. Refactoring for Testability

**Current issue:** Download script functions depend on module-level constants and `rqdatac.init()` at import time.

**Recommended refactoring:**
```python
# Make functions accept paths as parameters instead of using globals
def load_log(log_path: Path = LOG_PATH):  # Default keeps backward compat
    ...

def safe_download(key, func, path, need_mb=50, log_path=LOG_PATH, **kwargs):
    ...

# Move rqdatac.init() into main() instead of module level
def main():
    rqdatac.init()  # Initialize only when script is actually run
    ...
```

This allows tests to call functions without triggering license initialization.

## Common Patterns

**Async Testing:**
- Not applicable - No async code in current codebase

**Error Testing:**
```python
# Test that errors are properly caught and logged
def test_safe_download_logs_failure(mocker, tmp_path):
    mock_func = MagicMock(side_effect=ConnectionError("Network error"))
    log_path = tmp_path / "download_log.json"

    result = safe_download("test_key", mock_func, tmp_path / "out.parquet",
                          need_mb=5, log_path=log_path)

    assert result is False
    log = json.loads(log_path.read_text())
    today = datetime.now().strftime("%Y-%m-%d")
    assert log[today]["test_key"]["status"] == "failed"
    assert "Network error" in log[today]["test_key"]["error"]
```

**Temp File Testing:**
```python
# Use pytest tmp_path for all file operations
def test_parquet_roundtrip(tmp_path, sample_stock_price_df):
    out_path = tmp_path / "test.parquet"
    sample_stock_price_df.to_parquet(str(out_path), engine="pyarrow",
                                     compression="snappy", index=True)

    loaded = pd.read_parquet(out_path)
    pd.testing.assert_frame_equal(loaded, sample_stock_price_df)
```

## Setup Checklist

To add testing infrastructure:

1. **Install test dependencies:**
   ```bash
   poetry add --group dev pytest pytest-cov pytest-mock
   ```

2. **Create test directory:**
   ```bash
   mkdir tests
   touch tests/__init__.py
   touch tests/conftest.py
   ```

3. **Add pytest config to `pyproject.toml`:**
   ```toml
   [tool.pytest.ini_options]
   testpaths = ["tests"]
   ```

4. **Refactor for testability:**
   - Move `rqdatac.init()` from module-level to `main()`
   - Make `LOG_PATH` / `DATA_ROOT` injectable (parameter or fixture)
   - Add type hints to function signatures for clarity

5. **Write initial tests:**
   - Start with pure functions: `load_log`, `save_log`, `mark_done`, `is_done`
   - Add mocked tests: `check_quota`, `safe_download`
   - Skip data validation tests when data files don't exist

---

*Testing analysis: 2026-04-23*
