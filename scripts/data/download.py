"""
RQData 全量数据下载工具

用法:
    export RQDATAC2_CONF='tcp://license:...@rqdatad-pro.ricequant.com:16011'
    python scripts/download.py [step]

    step: metadata | stock_price | stock_finance | stock_factor | stock_events |
          index | futures | options | convertible | fund | risk_factor |
          macro_alt_spot | all

    不指定 step 则按顺序执行所有步骤。
"""
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd
import rqdatac

# ── 配置 ──────────────────────────────────────────────────────────────────
DATA_ROOT = Path(__file__).resolve().parent.parent / "data"
LOG_PATH = DATA_ROOT / "download_log.json"
DAILY_QUOTA_MB = 1024
QUOTA_MARGIN_MB = 100  # 保留余量
PYTHON = sys.executable

# 启动时初始化连接
rqdatac.init()


# ── 日志系统 ──────────────────────────────────────────────────────────────
def load_log():
    if LOG_PATH.exists():
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    return {}


def save_log(log):
    LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


def mark_done(key, rows=0, bytes_est=0):
    log = load_log()
    today = datetime.now().strftime("%Y-%m-%d")
    log.setdefault(today, {})[key] = {
        "status": "done",
        "rows": rows,
        "bytes_est": bytes_est,
        "ts": datetime.now().isoformat(),
    }
    save_log(log)


def is_done(key):
    log = load_log()
    for day_data in log.values():
        if key in day_data and day_data[key]["status"] == "done":
            return True
    return False


def mark_failed(key, err_msg):
    log = load_log()
    today = datetime.now().strftime("%Y-%m-%d")
    log.setdefault(today, {})[key] = {
        "status": "failed",
        "error": err_msg[:200],
        "ts": datetime.now().isoformat(),
    }
    save_log(log)


# ── 流量控制 ──────────────────────────────────────────────────────────────
def remaining_quota_mb():
    quota = rqdatac.user.get_quota()
    return (quota["bytes_limit"] - quota["bytes_used"]) / 1024 / 1024


def check_quota(need_mb=50):
    rem = remaining_quota_mb()
    if rem < QUOTA_MARGIN_MB:
        print(f"  [流量不足] 剩余 {rem:.1f}MB，低于安全余量，停止下载")
        return False
    if rem < need_mb:
        print(f"  [流量紧张] 剩余 {rem:.1f}MB，需要 {need_mb}MB，跳过")
        return False
    return True


# ── 通用下载函数 ──────────────────────────────────────────────────────────
def safe_download(key, func, path, need_mb=50, **to_parquet_kwargs):
    """安全下载：断点续传 + 流量检查 + 错误重试"""
    if is_done(key):
        print(f"  [跳过] {key} 已下载")
        return True

    if not check_quota(need_mb):
        return False

    parquet_kwargs = {"engine": "pyarrow", "compression": "snappy", "index": True}
    parquet_kwargs.update(to_parquet_kwargs)

    last_error = None
    for attempt in range(3):
        try:
            print(f"  [下载] {key} ...", end=" ", flush=True)
            df = func()
            if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                print("数据为空，标记完成")
                mark_done(key, rows=0, bytes_est=0)
                return True
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(df, pd.DataFrame):
                df.to_parquet(str(path), **parquet_kwargs)
                rows = len(df)
            else:
                # 非DataFrame结果存为JSON
                path = path.with_suffix(".json")
                path.write_text(json.dumps(df, ensure_ascii=False, default=str), encoding="utf-8")
                rows = len(df) if hasattr(df, "__len__") else 1
            print(f"完成 ({rows} 行)")
            mark_done(key, rows=rows, bytes_est=need_mb * 1024 * 1024)
            return True
        except Exception as e:
            last_error = e
            print(f"失败 (尝试 {attempt+1}/3): {e}")
            traceback.print_exc()
            time.sleep(5)
    mark_failed(key, str(last_error))
    return False


# ── Step 1: 元数据 ────────────────────────────────────────────────────────
def download_metadata():
    print("\n=== Step 1: 元数据 ===")
    types = ["CS", "ETF", "LOF", "INDX", "Future", "Spot", "Option", "Convertible", "Repo", "REITs", "FUND"]

    for t in types:
        safe_download(
            f"instruments/all_instruments_{t}",
            lambda t=t: rqdatac.all_instruments(type=t),
            DATA_ROOT / f"instruments/all_instruments_{t}.parquet",
            need_mb=5,
        )

    # 交易日历
    safe_download(
        "calendar/trading_dates",
        lambda: rqdatac.get_trading_dates("2005-01-01", "2026-12-31"),
        DATA_ROOT / "calendar/trading_dates.parquet",
        need_mb=1,
    )

    # 收益率曲线
    safe_download(
        "yield_curve",
        lambda: rqdatac.get_yield_curve("2002-01-01", "2026-12-31"),
        DATA_ROOT / "yield_curve/yield_curve.parquet",
        need_mb=5,
    )

    # 因子名称
    safe_download(
        "factor_names",
        lambda: rqdatac.get_all_factor_names(),
        DATA_ROOT / "stock/factor_names.json",
        need_mb=1,
    )


# ── Step 2: A 股行情 ─────────────────────────────────────────────────────
def download_stock_price():
    print("\n=== Step 2: A 股日线行情 ===")
    if not check_quota(300):
        return

    # 获取全部 A 股列表
    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()
    print(f"  A 股总数: {len(stock_ids)}")

    # 分批下载日线行情（按时间分段，减少单次请求量）
    date_ranges = [
        ("2005-01-01", "2009-12-31"),
        ("2010-01-01", "2014-12-31"),
        ("2015-01-01", "2019-12-31"),
        ("2020-01-01", "2026-12-31"),
    ]

    all_frames = []
    for start, end in date_ranges:
        key = f"stock/price_1d_{start}_{end}"
        if is_done(key):
            print(f"  [跳过] {key} 已下载")
            continue
        if not check_quota(200):
            break
        try:
            print(f"  [下载] {key} ...", end=" ", flush=True)
            df = rqdatac.get_price(
                stock_ids, start_date=start, end_date=end,
                frequency="1d", fields=["open", "close", "high", "low", "total_turnover", "volume", "num_trades", "prev_close", "limit_up", "limit_down"],
                adjust_type="pre", expect_df=True,
            )
            if df is not None and not df.empty:
                all_frames.append(df)
                rows = len(df)
                print(f"完成 ({rows} 行)")
                mark_done(key, rows=rows, bytes_est=200 * 1024 * 1024)
            else:
                print("数据为空")
                mark_done(key, rows=0, bytes_est=0)
        except Exception as e:
            print(f"失败: {e}")
            mark_failed(key, str(e))

    if all_frames:
        merged = pd.concat(all_frames)
        out_path = DATA_ROOT / "stock/price_1d.parquet"
        merged.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
        print(f"  [合并] A股日线行情 -> {out_path} ({len(merged)} 行)")

    # 价格变化率
    safe_download(
        "stock/price_change_rate",
        lambda: rqdatac.get_price_change_rate(stock_ids, "2005-01-01", "2026-12-31", expect_df=True),
        DATA_ROOT / "stock/price_change_rate.parquet",
        need_mb=100,
    )


# ── Step 3: A 股财务 ─────────────────────────────────────────────────────
def download_stock_finance():
    print("\n=== Step 3: A 股财务数据 ===")
    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()

    # 财务字段（使用 API 实际接受的字段名）
    income_fields = ["revenue", "operating_revenue", "total_operating_revenueTTM", "operating_costTTM",
                     "gross_profitTTM", "total_profitTTM", "net_profitTTM", "np_parent_company_ownersTTM",
                     "ebitTTM", "basic_earnings_per_share", "other_income"]
    balance_fields = ["total_assets", "total_liabilities", "total_equity", "equity_parent_company",
                      "cash_equivalent", "net_accts_receivable", "inventory", "net_fixed_assets",
                      "short_term_loans", "long_term_loans", "accts_payable"]
    cashflow_fields = ["cash_flow_from_operating_activities", "cash_flow_from_investing_activities",
                       "cash_flow_from_financing_activities", "net_operate_cashflowTTM"]
    all_fields = income_fields + balance_fields + cashflow_fields

    # 按年度分批下载 PIT 财务数据
    for year in range(2005, 2027):
        sq = f"{year}q1"
        eq = f"{year}q4"
        key = f"stock/pit_financials_{year}"
        if is_done(key):
            print(f"  [跳过] {key} 已下载")
            continue
        if not check_quota(30):
            break
        try:
            print(f"  [下载] {key} ...", end=" ", flush=True)
            df = rqdatac.get_pit_financials_ex(
                stock_ids, all_fields, start_quarter=sq, end_quarter=eq,
                statements="all",
            )
            if df is not None and not df.empty:
                out_path = DATA_ROOT / f"stock/pit_financials/pit_financials_{year}.parquet"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
                print(f"完成 ({len(df)} 行)")
                mark_done(key, rows=len(df), bytes_est=30 * 1024 * 1024)
            else:
                print("数据为空")
                mark_done(key, rows=0, bytes_est=0)
        except Exception as e:
            print(f"失败: {e}")
            mark_failed(key, str(e))

    # 财务快报
    safe_download(
        "stock/current_performance",
        lambda: rqdatac.current_performance(stock_ids, interval="1q"),
        DATA_ROOT / "stock/current_performance.parquet",
        need_mb=50,
    )

    # 业绩预告
    safe_download(
        "stock/performance_forecast",
        lambda: rqdatac.performance_forecast(stock_ids),
        DATA_ROOT / "stock/performance_forecast.parquet",
        need_mb=20,
    )


# ── Step 4: A 股因子 ─────────────────────────────────────────────────────
def download_stock_factor():
    print("\n=== Step 4: A 股因子数据 ===")
    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()

    # 获取所有因子名
    try:
        all_factors = rqdatac.get_all_factor_names()
    except Exception:
        all_factors = None

    if all_factors:
        (DATA_ROOT / "stock").mkdir(parents=True, exist_ok=True)
        (DATA_ROOT / "stock" / "factor_names.json").write_text(
            json.dumps(all_factors, ensure_ascii=False), encoding="utf-8"
        )
        print(f"  因子总数: {len(all_factors)}")

    # 批量下载因子（按批次，每次50个因子）
    batch_size = 50
    factor_list = all_factors if all_factors else []
    for i in range(0, len(factor_list), batch_size):
        batch = factor_list[i:i + batch_size]
        key = f"factor/batch_{i//batch_size}"
        if is_done(key):
            print(f"  [跳过] {key} 已下载")
            continue
        if not check_quota(30):
            break
        try:
            print(f"  [下载] 因子批次 {i//batch_size} ({len(batch)} 个因子) ...", end=" ", flush=True)
            df = rqdatac.get_factor(stock_ids, batch, "2020-01-01", "2026-12-31", expect_df=True)
            if df is not None and not df.empty:
                out_path = DATA_ROOT / f"factor/batch_{i//batch_size}.parquet"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
                print(f"完成 ({len(df)} 行)")
                mark_done(key, rows=len(df), bytes_est=30 * 1024 * 1024)
            else:
                print("数据为空")
                mark_done(key, rows=0, bytes_est=0)
        except Exception as e:
            print(f"失败: {e}")
            mark_failed(key, str(e))


# ── Step 5: A 股公司事件 ─────────────────────────────────────────────────
def download_stock_events():
    print("\n=== Step 5: A 股公司事件 ===")
    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()

    apis = [
        ("stock/dividend", lambda: rqdatac.get_dividend(stock_ids), 10),
        ("stock/split", lambda: rqdatac.get_split(stock_ids), 5),
        ("stock/shares", lambda: rqdatac.get_shares(stock_ids, fields=None), 10),
        ("stock/turnover_rate", lambda: rqdatac.get_turnover_rate(stock_ids, fields=None), 10),
        ("stock/suspended", lambda: rqdatac.is_suspended(stock_ids), 5),
        ("stock/st_stock", lambda: rqdatac.is_st_stock(stock_ids), 5),
        ("stock/securities_margin", lambda: rqdatac.get_securities_margin(stock_ids), 10),
        ("stock/margin_stocks", lambda: rqdatac.get_margin_stocks(), 5),
        ("stock/stock_connect", lambda: rqdatac.get_stock_connect(stock_ids), 10),
        ("stock/industry_citics", lambda: rqdatac.get_industry("citics"), 5),
        ("stock/instrument_industry", lambda: rqdatac.get_instrument_industry(stock_ids), 5),
    ]

    # concept 需要特殊处理
    try:
        concept_names = ["新能源", "人工智能", "芯片", "5G", "医药", "消费", "金融"]
        for name in concept_names:
            apis.append((f"stock/concept_{name}", lambda n=name: rqdatac.concept(n), 1))
    except Exception:
        pass

    for key, func, need_mb in apis:
        safe_download(key, func, DATA_ROOT / f"{key}.parquet", need_mb=need_mb)


# ── Step 6: 指数数据 ─────────────────────────────────────────────────────
def download_index():
    print("\n=== Step 6: 指数数据 ===")
    # 主要指数列表
    major_indices = [
        "000001.XSHG",  # 上证综指
        "000300.XSHG",  # 沪深300
        "000905.XSHG",  # 中证500
        "000906.XSHG",  # 中证800
        "000852.XSHG",  # 中证1000
        "000016.XSHG",  # 上证50
        "399001.XSHE",  # 深证成指
        "399006.XSHE",  # 创业板指
        "399005.XSHE",  # 中小板指
    ]

    # 获取所有指数
    indx = rqdatac.all_instruments(type="INDX")
    all_index_ids = indx["order_book_id"].tolist()
    print(f"  指数总数: {len(all_index_ids)}")

    # 指数日线行情
    safe_download(
        "index/price_1d",
        lambda: rqdatac.get_price(all_index_ids, "2005-01-01", "2026-12-31", frequency="1d",
                                  fields=["open", "close", "high", "low", "total_turnover", "volume"],
                                  adjust_type="none", expect_df=True),
        DATA_ROOT / "index/price_1d.parquet",
        need_mb=100,
    )

    # 成分股 + 权重（主要指数逐个下载）
    for idx_id in major_indices:
        for api_name, func in [
            (f"index/components/{idx_id}", lambda i=idx_id: rqdatac.index_components(i, start_date="2010-01-01", end_date="2026-12-31")),
            (f"index/weights/{idx_id}", lambda i=idx_id: rqdatac.index_weights(i, start_date="2010-01-01", end_date="2026-12-31")),
        ]:
            safe_download(api_name, func, DATA_ROOT / f"{api_name}.parquet", need_mb=20)


# ── Step 7: 期货数据 ─────────────────────────────────────────────────────
def download_futures():
    print("\n=== Step 7: 期货数据 ===")
    future_types = ['IF', 'IH', 'IC', 'IM', 'TF', 'T', 'TS', 'TL', 'CU', 'AL', 'ZN', 'PB', 'NI', 'SN',
                    'AU', 'AG', 'RB', 'HC', 'SS', 'I', 'J', 'JM', 'ZC', 'FG', 'SA', 'MA', 'TA', 'CF',
                    'SR', 'OI', 'AP', 'CJ', 'CY', 'ER', 'WH', 'PM', 'RI', 'RS', 'JR', 'LR', 'A', 'B',
                    'C', 'CS', 'JD', 'L', 'M', 'P', 'V', 'Y', 'PP', 'EG', 'EB', 'PG', 'FU', 'LU', 'SC',
                    'NR', 'SI', 'LC', 'BR', 'AO', 'EC']

    apis = [
        ("futures/dominant", lambda: rqdatac.futures.get_dominant(future_types, "2010-01-01", "2026-12-31"), 20),
        ("futures/contracts", lambda: rqdatac.futures.get_contracts(future_types[0]), 1),
        ("futures/exchange_daily", lambda: rqdatac.futures.get_exchange_daily(future_types, "2010-01-01", "2026-12-31"), 50),
        ("futures/member_rank", lambda: rqdatac.futures.get_member_rank(future_types[0], start_date="2020-01-01", end_date="2026-12-31"), 10),
        ("futures/warehouse_stocks", lambda: rqdatac.futures.get_warehouse_stocks(future_types, "2010-01-01", "2026-12-31"), 10),
        ("futures/basis", lambda: rqdatac.futures.get_basis(future_types, "2010-01-01", "2026-12-31"), 10),
        ("futures/roll_yield", lambda: rqdatac.futures.get_roll_yield(future_types, "2010-01-01", "2026-12-31"), 10),
    ]

    for key, func, need_mb in apis:
        safe_download(key, func, DATA_ROOT / f"{key}.parquet", need_mb=need_mb)


# ── Step 8: 期权数据 ─────────────────────────────────────────────────────
def download_options():
    print("\n=== Step 8: 期权数据 ===")
    underlying_symbols = ["510050.XSHG", "510300.XSHG", "159919.XSHE", "000300.XSHG"]

    apis = [
        ("options/greeks", lambda: rqdatac.options.get_greeks("10003720.XSHG", "2020-01-01", "2026-12-31"), 30),
        ("options/contract_property", lambda: rqdatac.options.get_contract_property("10003720.XSHG", "2020-01-01", "2026-12-31"), 5),
        ("options/dominant_month", lambda: rqdatac.options.get_dominant_month(underlying_symbols, "2020-01-01", "2026-12-31"), 5),
        ("options/indicators", lambda: rqdatac.options.get_indicators(underlying_symbols, "2020-01-01", "2020-12-31"), 10),
    ]

    for key, func, need_mb in apis:
        safe_download(key, func, DATA_ROOT / f"{key}.parquet", need_mb=need_mb)

    # 合约查询按标的逐个
    for sym in underlying_symbols[:2]:
        for opt_type in ["C", "P"]:
            key = f"options/contracts_{sym}_{opt_type}"
            safe_download(
                key,
                lambda s=sym, t=opt_type: rqdatac.options.get_contracts(s, option_type=t),
                DATA_ROOT / f"options/contracts_{sym}_{opt_type}.parquet",
                need_mb=5,
            )


# ── Step 9: 可转债数据 ───────────────────────────────────────────────────
def download_convertible():
    print("\n=== Step 9: 可转债数据 ===")
    # 获取可转债列表
    cb = rqdatac.all_instruments(type="Convertible")
    cb_ids = cb["order_book_id"].tolist() if cb is not None and not cb.empty else []
    print(f"  可转债总数: {len(cb_ids)}")

    apis = [
        ("convertible/all_instruments", lambda: rqdatac.convertible.all_instruments(), 5),
        ("convertible/conversion_price", lambda: rqdatac.convertible.get_conversion_price(cb_ids, "2015-01-01", "2026-12-31") if cb_ids else pd.DataFrame(), 10),
        ("convertible/conversion_info", lambda: rqdatac.convertible.get_conversion_info(cb_ids, "2015-01-01", "2026-12-31") if cb_ids else pd.DataFrame(), 10),
        ("convertible/call_info", lambda: rqdatac.convertible.get_call_info(cb_ids, "2015-01-01", "2026-12-31") if cb_ids else pd.DataFrame(), 5),
        ("convertible/put_info", lambda: rqdatac.convertible.get_put_info(cb_ids, "2015-01-01", "2026-12-31") if cb_ids else pd.DataFrame(), 5),
        ("convertible/cash_flow", lambda: rqdatac.convertible.get_cash_flow(cb_ids, "2015-01-01", "2026-12-31") if cb_ids else pd.DataFrame(), 5),
        ("convertible/indicators", lambda: rqdatac.convertible.get_indicators(cb_ids, "2018-01-01", "2026-12-31") if cb_ids else pd.DataFrame(), 20),
        ("convertible/credit_rating", lambda: rqdatac.convertible.get_credit_rating(cb_ids, "2015-01-01", "2026-12-31") if cb_ids else pd.DataFrame(), 5),
        ("convertible/close_price", lambda: rqdatac.convertible.get_close_price(cb_ids, "2018-01-01", "2026-12-31") if cb_ids else pd.DataFrame(), 10),
        ("convertible/std_discount", lambda: rqdatac.convertible.get_std_discount(cb_ids, "2015-01-01", "2026-12-31") if cb_ids else pd.DataFrame(), 5),
        ("convertible/call_announcement", lambda: rqdatac.convertible.get_call_announcement(cb_ids, "2015-01-01", "2026-12-31") if cb_ids else pd.DataFrame(), 5),
    ]

    for key, func, need_mb in apis:
        safe_download(key, func, DATA_ROOT / f"{key}.parquet", need_mb=need_mb)


# ── Step 10: 公募基金数据 ────────────────────────────────────────────────
def download_fund():
    print("\n=== Step 10: 公募基金数据 ===")
    fund_list = rqdatac.fund.all_instruments()
    fund_ids = fund_list["order_book_id"].tolist() if fund_list is not None and not fund_list.empty else []
    print(f"  基金总数: {len(fund_ids)}")

    apis = [
        ("fund/all_instruments", lambda: rqdatac.fund.all_instruments(), 5),
        ("fund/nav", lambda: rqdatac.fund.get_nav(fund_ids[:500], "2010-01-01", "2026-12-31") if fund_ids else pd.DataFrame(), 30),
        ("fund/dividend", lambda: rqdatac.fund.get_dividend(fund_ids), 5),
        ("fund/split", lambda: rqdatac.fund.get_split(fund_ids), 2),
        ("fund/fee", lambda: rqdatac.fund.get_fee(fund_ids[:100]), 5),
        ("fund/ratings", lambda: rqdatac.fund.get_ratings(fund_ids[:200]), 5),
        ("fund/holder_structure", lambda: rqdatac.fund.get_holder_structure(fund_ids[:200], "2020-01-01", "2026-12-31") if fund_ids else pd.DataFrame(), 10),
        ("fund/units_change", lambda: rqdatac.fund.get_units_change(fund_ids[:200]) if fund_ids else pd.DataFrame(), 5),
        ("fund/benchmark", lambda: rqdatac.fund.get_benchmark(fund_ids), 5),
        ("fund/instrument_category", lambda: rqdatac.fund.get_instrument_category(fund_ids[:200]), 5),
        ("fund/category_mapping", lambda: rqdatac.fund.get_category_mapping(), 1),
        ("fund/manager", lambda: rqdatac.fund.get_manager(fund_ids[:200]), 5),
        ("fund/transition_info", lambda: rqdatac.fund.get_transition_info(fund_ids), 5),
    ]

    for key, func, need_mb in apis:
        safe_download(key, func, DATA_ROOT / f"{key}.parquet", need_mb=need_mb)

    # 基金持仓/资产配置/行业配置按季度下载
    for year in range(2015, 2027):
        for q in ["0331", "0630", "0930", "1231"]:
            date_str = f"{year}{q}"
            for api_short, api_func in [
                ("holdings", lambda d=date_str: rqdatac.fund.get_holdings(fund_ids[:100], date=d)),
                ("asset_allocation", lambda d=date_str: rqdatac.fund.get_asset_allocation(fund_ids[:100], date=d)),
                ("industry_allocation", lambda d=date_str: rqdatac.fund.get_industry_allocation(fund_ids[:100], date=d)),
            ]:
                key = f"fund/{api_short}_{date_str}"
                safe_download(key, api_func, DATA_ROOT / f"fund/{api_short}_{date_str}.parquet", need_mb=5)


# ── Step 11: 风险因子 ─────────────────────────────────────────────────────
def download_risk_factor():
    print("\n=== Step 11: 风险因子 ===")
    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()[:500]  # 限制数量避免超时

    apis = [
        ("risk_factor/factor_exposure_v1",
         lambda: rqdatac.get_factor_exposure(stock_ids, "2020-01-01", "2026-12-31", model="v1"), 30),
        ("risk_factor/factor_exposure_v2",
         lambda: rqdatac.get_factor_exposure(stock_ids, "2020-01-01", "2026-12-31", model="v2"), 30),
        ("risk_factor/stock_beta",
         lambda: rqdatac.get_stock_beta(stock_ids, "2020-01-01", "2026-12-31"), 20),
        ("risk_factor/factor_return",
         lambda: rqdatac.get_factor_return("2020-01-01", "2026-12-31"), 10),
        ("risk_factor/specific_return",
         lambda: rqdatac.get_specific_return(stock_ids, "2020-01-01", "2026-12-31"), 20),
        ("risk_factor/specific_risk",
         lambda: rqdatac.get_specific_risk(stock_ids, "2020-01-01", "2026-12-31"), 20),
    ]

    for key, func, need_mb in apis:
        safe_download(key, func, DATA_ROOT / f"{key}.parquet", need_mb=need_mb)

    # 因子协方差按月下载
    for year in range(2020, 2027):
        for month in range(1, 13):
            date_str = f"{year}-{month:02d}-01"
            key = f"risk_factor/factor_covariance_{date_str}"
            safe_download(
                key,
                lambda d=date_str: rqdatac.get_factor_covariance(d),
                DATA_ROOT / f"risk_factor/factor_covariance/factor_covariance_{date_str}.parquet",
                need_mb=1,
            )


# ── Step 12: 宏观 + 另类 + 现货 ─────────────────────────────────────────
def download_macro_alt_spot():
    print("\n=== Step 12: 宏观 + 另类 + 现货 ===")
    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()[:500]

    # 宏观
    apis = [
        ("macro/reserve_ratio", lambda: rqdatac.econ.get_reserve_ratio(start_date="2005-01-01", end_date="2026-12-31"), 2),
        ("macro/money_supply", lambda: rqdatac.econ.get_money_supply(start_date="2005-01-01", end_date="2026-12-31"), 2),
        ("macro/interbank_offered_rate", lambda: rqdatac.get_interbank_offered_rate(start_date="2005-01-01", end_date="2026-12-31"), 2),
    ]

    # 另类 - 一致预期
    alt_apis = [
        ("alternative/consensus/comp_indicators",
         lambda: rqdatac.consensus.get_comp_indicators(stock_ids[:200], "2020-01-01", "2026-12-31"), 20),
        ("alternative/consensus/indicator",
         lambda: rqdatac.consensus.get_indicator(stock_ids[:200], "2024"), 10),
        ("alternative/consensus/industry_rating",
         lambda: rqdatac.consensus.get_industry_rating(start_date="2020-01-01", end_date="2026-12-31"), 5),
        ("alternative/news/stock_news",
         lambda: rqdatac.news.get_stock_news(stock_ids[:100], "2024-01-01", "2026-04-23"), 10),
        ("alternative/esg/rating",
         lambda: rqdatac.esg.get_rating(stock_ids[:200], "2020-01-01", "2026-12-31"), 10),
    ]

    # 现货
    spot_apis = [
        ("spot/spot_benchmark_price",
         lambda: rqdatac.get_spot_benchmark_price("AU9999.SGEX", "2020-01-01", "2026-12-31"), 2),
    ]

    for key, func, need_mb in apis + alt_apis + spot_apis:
        safe_download(key, func, DATA_ROOT / f"{key}.parquet", need_mb=need_mb)


# ── 主入口 ────────────────────────────────────────────────────────────────
STEPS = {
    "metadata": download_metadata,
    "stock_price": download_stock_price,
    "stock_finance": download_stock_finance,
    "stock_factor": download_stock_factor,
    "stock_events": download_stock_events,
    "index": download_index,
    "futures": download_futures,
    "options": download_options,
    "convertible": download_convertible,
    "fund": download_fund,
    "risk_factor": download_risk_factor,
    "macro_alt_spot": download_macro_alt_spot,
}

STEP_ORDER = [
    "metadata", "stock_price", "stock_finance", "stock_factor",
    "stock_events", "index", "futures", "options",
    "convertible", "fund", "risk_factor", "macro_alt_spot",
]


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "all"

    print(f"RQData 全量下载工具 | 剩余流量: {remaining_quota_mb():.1f} MB")
    print(f"数据目录: {DATA_ROOT}")

    if step == "all":
        for s in STEP_ORDER:
            if remaining_quota_mb() < QUOTA_MARGIN_MB + 50:
                print(f"\n[停止] 流量不足 ({remaining_quota_mb():.1f} MB)，请明日继续")
                break
            STEPS[s]()
    elif step in STEPS:
        STEPS[step]()
    else:
        print(f"未知步骤: {step}")
        print(f"可用步骤: {', '.join(STEP_ORDER)} | all")
        sys.exit(1)

    print(f"\n完成! 剩余流量: {remaining_quota_mb():.1f} MB")


if __name__ == "__main__":
    main()
