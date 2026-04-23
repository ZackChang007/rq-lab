# External Integrations

**Analysis Date:** 2026-04-23

## APIs & External Services

**Ricequant Data API (RQData):**
- Service: `rqdatac` - Financial data API
  - SDK: `rqdatac 3.4.7.8`
  - Auth: License key via `rqdatac.init(RQSDK_LICENSE_KEY)` or `rqsdk` auto-configuration
  - Endpoint: `tcp://license:...@rqdatad-pro.ricequant.com:16011` (via `RQDATAC2_CONF` env var)
  - Capabilities: Stock quotes, fundamentals, factors, indices, futures, options, convertible bonds, funds, macro data

**Ricequant SDK (RQSDK):**
- Service: `rqsdk 1.7.1` - SDK manager and CLI tool
  - Commands:
    - `rqsdk license info` - View license status
    - `rqsdk install rqalpha_plus` - Install backtesting framework (auto-installs RQData, RQOptimizer, RQFactor)
    - `rqsdk download-data --sample` - Download sample data (trial)
    - `rqsdk update-data` - Update local data bundle

## Data Storage

**Databases:**
- None - No database server used

**File Storage:**
- Local filesystem: `C:\gh\rq-lab\data\`
- Format: Parquet (Snappy compression) + JSON (for metadata)
- Structure:
  ```
  data/
  ├── instruments/      # Instrument metadata (all_instruments_*.parquet)
  ├── calendar/         # Trading calendar
  ├── stock/            # Stock data (prices, financials, events)
  ├── index/            # Index data (components, weights)
  ├── futures/          # Futures data
  ├── options/          # Options data
  ├── convertible/      # Convertible bonds
  ├── fund/             # Mutual fund data
  ├── factor/           # Factor data batches
  ├── risk_factor/      # Risk model factors
  ├── yield_curve/      # Yield curve data
  └── download_log.json # Progress tracking
  ```

**Caching:**
- RQAlpha Plus bundle: `~/.rqalpha-plus/bundle/` (not yet created)
- Local data cache: `data/` directory with Parquet files
- Quota tracking: `rqdatac.user.get_quota()` returns daily usage

## Authentication & Identity

**Auth Provider:**
- Ricequant License Service
  - Implementation: License key stored in `config/credentials.py`
  - Import pattern: `from config.credentials import RQSDK_LICENSE_KEY`
  - Init pattern: `rqdatac.init(RQSDK_LICENSE_KEY)`
  - Alternative: `rqsdk` CLI configures auto-init

**License Details:**
- Type: Personal trial
- Expiry: 2026-05-22
- Quota: 1GB/day (trial sample data doesn't count)

## Monitoring & Observability

**Error Tracking:**
- None configured

**Logs:**
- Download progress: `data/download_log.json` - JSON-based progress tracker
- Console output for scripts
- No centralized logging

## CI/CD & Deployment

**Hosting:**
- Local development only - Research project

**CI Pipeline:**
- None configured

## Environment Configuration

**Required env vars:**
- `RQDATAC2_CONF` - Optional: Direct RQData connection string (alternative to license key)
- `RQSDK_LICENSE_KEY` - Via `config/credentials.py`, not actual env var

**Secrets location:**
- `config/credentials.py` - Gitignored, contains license key
- Template: `config/credentials.example.py`

**Configuration Pattern:**
```python
# In config/credentials.py (gitignored)
RQSDK_LICENSE_KEY = "<your-license-key>"
RQSDK_ACCOUNT_TYPE = "trial"
RQSDK_EXPIRY_DATE = "2026-05-22"

# Usage in code
from config.credentials import RQSDK_LICENSE_KEY
import rqdatac
rqdatac.init(RQSDK_LICENSE_KEY)
```

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Data Download Tool

**Custom Tool:** `scripts/data/download.py`
- Purpose: Full RQData download with quota management
- Features:
  - 12 download steps (metadata, stock_price, stock_finance, stock_factor, stock_events, index, futures, options, convertible, fund, risk_factor, macro_alt_spot)
  - Resume capability via `download_log.json`
  - Daily quota checking (1GB limit with 100MB safety margin)
  - Retry logic (3 attempts per download)
  - Progress tracking
- Usage:
  ```bash
  export RQDATAC2_CONF='tcp://license:...@rqdatad-pro.ricequant.com:16011'
  python scripts/data/download.py [step]
  # step: metadata | stock_price | stock_finance | ... | all
  ```

## Quota Management

**Flow Control:**
- Daily quota: 1GB (1024MB)
- Safety margin: 100MB reserved
- Check function: `rqdatac.user.get_quota()`
- Returns: `{"bytes_limit": ..., "bytes_used": ...}`

**Usage Pattern:**
```python
quota = rqdatac.user.get_quota()
remaining_mb = (quota["bytes_limit"] - quota["bytes_used"]) / 1024 / 1024
if remaining_mb < QUOTA_MARGIN_MB:
    # Stop downloading, wait for quota reset
```

---

*Integration audit: 2026-04-23*
