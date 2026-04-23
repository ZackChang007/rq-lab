# Technology Stack

**Analysis Date:** 2026-04-23

## Languages

**Primary:**
- Python 3.12.13 - Core language for all development, using CPython implementation

**Secondary:**
- Not applicable - Single language project

## Runtime

**Environment:**
- Conda environment: `rq-lab`
- Path: `C:\ProgramData\Anaconda3\envs\rq-lab`
- Managed via Poetry within Conda environment

**Package Manager:**
- Poetry 2.0.0+ (build backend: `poetry-core>=2.0.0,<3.0.0`)
- Lockfile: `poetry.lock` present (173KB)
- PyPI mirror: Tsinghua (`https://pypi.tuna.tsinghua.edu.cn/simple/`) - primary source

## Frameworks

**Core:**
- RQSDK 1.7.1 - Ricequant SDK umbrella package, manages license and component installation
- RQData 3.4.7.8 - Financial data API (market quotes, fundamentals, factors)
- RQData Fund Extension 1.0.40 - Mutual fund data extension

**Testing:**
- Not configured yet - No pytest or other testing framework in dependencies

**Build/Dev:**
- Poetry - Dependency management and build system
- Conda - Python environment isolation

## Key Dependencies

**Critical:**
- pandas 2.3.3 - Data manipulation, core data structure for all financial data
- numpy 2.4.4 - Array computing foundation
- scipy 1.17.1 - Scientific computing, statistical functions
- statsmodels 0.14.6 - Statistical modeling, factor analysis support

**Infrastructure:**
- requests 2.33.1 - HTTP client for API calls
- pyarrow (via pandas) - Parquet file storage engine
- orjson 3.11.8 - Fast JSON serialization for data logs
- python-rapidjson 1.23 - Alternative JSON library
- msgpack 1.1.2 - Binary serialization

**Security/Auth:**
- pyjwt 1.7.1 - JWT token handling for RQSDK authentication
- cryptography 46.0.7 - SSL/TLS support
- pyOpenSSL 26.0.0 - OpenSSL wrapper

## Configuration

**Environment:**
- Credentials stored in `config/credentials.py` (gitignored)
- Template: `config/credentials.example.py`
- License key imported via: `from config.credentials import RQSDK_LICENSE_KEY`

**Build:**
- `pyproject.toml` - Poetry configuration, project metadata
- Tsinghua PyPI mirror configured for faster downloads in China

## Platform Requirements

**Development:**
- Windows 11 Pro (win32)
- Python 3.12+ required (`requires-python = "^3.12"`)
- Conda environment management

**Production:**
- Not applicable - Research/analysis project, no production deployment
- Data cached locally in `data/` directory (Parquet format)

## Data Storage

**Local Storage:**
- Format: Parquet (Snappy compression, PyArrow engine)
- Location: `C:\gh\rq-lab\data\`
- Structure: Organized by asset type (stock/, index/, futures/, options/, fund/, etc.)
- Log: `data/download_log.json` tracks download progress

**External Data Sources:**
- RQData API - Primary financial data source
- Trial license: 1GB/day quota, sample data doesn't count

---

*Stack analysis: 2026-04-23*
