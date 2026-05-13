"""
RQData 数据补充脚本

目标：将指定数据从 2010 年开始补充，并更新到当前最新

用法:
    python scripts/data/supplement_data.py [task_id]

    task_id: 1-13，对应 progress.md 中的任务编号
    不指定则执行所有任务
"""
import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd
import rqdatac
from utils.common import setup_license

setup_license()

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"
LOG_PATH = DATA_ROOT / "download_log.json"
PROGRESS_PATH = DATA_ROOT.parent / "docs" / "progress.md"
QUOTA_MARGIN_MB = 50  # 保留余量

rqdatac.init()

_session_used_mb = 0.0
TOTAL_QUOTA_MB = 1024


def get_quota_info():
    """获取配额信息"""
    try:
        quota = rqdatac.user.get_quota()
        return {
            "limit_mb": quota["bytes_limit"] / 1024 / 1024,
            "used_mb": quota["bytes_used"] / 1024 / 1024,
            "remaining_mb": (quota["bytes_limit"] - quota["bytes_used"]) / 1024 / 1024,
        }
    except Exception as e:
        print(f"[警告] 获取配额失败: {e}")
        return {"limit_mb": 1024, "used_mb": 1024, "remaining_mb": 0}


def check_quota(need_mb=50):
    """检查流量是否充足"""
    info = get_quota_info()
    rem = info["remaining_mb"]
    if rem < QUOTA_MARGIN_MB:
        print(f"[流量不足] 剩余 {rem:.1f} MB，低于安全余量 {QUOTA_MARGIN_MB} MB")
        return False
    if rem < need_mb:
        print(f"[流量紧张] 剩余 {rem:.1f} MB，需要 {need_mb} MB")
        return False
    return True


def track_usage(before_mb):
    """追踪实际流量消耗"""
    global _session_used_mb
    info = get_quota_info()
    actual = info["used_mb"] - before_mb
    if actual > 0:
        _session_used_mb += actual
    return actual, info["remaining_mb"]


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


def update_progress_md(task_id, status, new_range=None, notes=None):
    """更新 progress.md 中的任务状态"""
    if not PROGRESS_PATH.exists():
        print(f"[警告] {PROGRESS_PATH} 不存在")
        return

    content = PROGRESS_PATH.read_text(encoding="utf-8")
    lines = content.split("\n")

    status_map = {
        "pending": "⏳ 待执行",
        "running": "🔄 执行中",
        "done": "✅ 已完成",
        "failed": "❌ 失败",
        "paused": "⏸️ 暂停",
    }

    for i, line in enumerate(lines):
        # 查找任务行 (格式: | 1 | A股日线行情 | ...)
        if line.startswith(f"| {task_id} |"):
            parts = line.split("|")
            if len(parts) >= 7:
                # 更新状态
                parts[6] = f" {status_map.get(status, status)} "
                # 如果有新的范围，更新当前范围
                if new_range:
                    parts[3] = f" {new_range} "
                # 更新完成时间
                if status == "done":
                    parts[7] = f" {datetime.now().strftime('%Y-%m-%d %H:%M')} |\n"
                else:
                    parts[7] = " - |\n"
                lines[i] = "|".join(parts)
                break

    PROGRESS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[进度] 任务 {task_id} 状态更新为: {status_map.get(status, status)}")


def safe_download(key, func, path, need_mb=50):
    """安全下载：流量检查 + 实际消耗追踪"""
    if is_done(key):
        print(f"[跳过] {key} 已下载")
        return True, 0, 0

    if not check_quota(need_mb):
        return False, 0, 0

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        info_before = get_quota_info()
        before_mb = info_before["used_mb"]

        print(f"[下载] {key} ...", end=" ", flush=True)
        df = func()

        actual_used, remaining = track_usage(before_mb)

        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            print(f"数据为空 (消耗 {actual_used:.2f} MB, 剩余 {remaining:.1f} MB)")
            mark_done(key, rows=0, bytes_est=int(actual_used * 1024 * 1024))
            return True, 0, actual_used

        if isinstance(df, pd.DataFrame):
            df.to_parquet(str(path), engine="pyarrow", compression="snappy", index=True)
            rows = len(df)
        elif isinstance(df, pd.Series):
            df = df.to_frame(name="value")
            df.to_parquet(str(path), engine="pyarrow", compression="snappy", index=True)
            rows = len(df)
        else:
            path = path.with_suffix(".json")
            path.write_text(json.dumps(df, ensure_ascii=False), encoding="utf-8")
            rows = 1

        print(f"完成 ({rows} 行, 消耗 {actual_used:.2f} MB, 剩余 {remaining:.1f} MB)")
        mark_done(key, rows=rows, bytes_est=int(actual_used * 1024 * 1024))
        return True, rows, actual_used

    except Exception as e:
        err_msg = str(e)
        if "Quota exceeded" in err_msg:
            print(f"流量超限")
            return False, 0, 0
        print(f"失败: {e}")
        traceback.print_exc()
        return False, 0, 0


# ═══════════════════════════════════════════════════════════════════════════
# 任务 1: A股日线行情
# ═══════════════════════════════════════════════════════════════════════════
def task1_stock_price():
    """补充 A股日线行情 (2010-01-01 ~ 当前)"""
    print("\n" + "=" * 60)
    print("任务 1: A股日线行情")
    print("=" * 60)

    update_progress_md(1, "running")

    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()
    print(f"A股总数: {len(stock_ids)}")

    # 下载 2010-2013 年的数据（补充早期数据）
    date_ranges = [
        ("2010-01-01", "2011-12-31"),
        ("2012-01-01", "2013-12-31"),
        # 2014+ 已有数据，检查是否需要更新到最新
        ("2026-05-01", datetime.now().strftime("%Y-%m-%d")),  # 更新最新数据
    ]

    all_frames = []
    total_used = 0

    for start, end in date_ranges:
        key = f"stock/price_1d_{start}_{end}"
        if is_done(key):
            print(f"[跳过] {key} 已下载")
            continue
        if not check_quota(50):
            update_progress_md(1, "paused")
            return False

        try:
            info_before = get_quota_info()
            before_mb = info_before["used_mb"]

            print(f"[下载] {key} ...", end=" ", flush=True)
            df = rqdatac.get_price(
                stock_ids, start_date=start, end_date=end,
                frequency="1d",
                fields=["open", "close", "high", "low", "total_turnover", "volume", "num_trades", "prev_close", "limit_up", "limit_down"],
                adjust_type="pre", expect_df=True,
            )

            actual_used, remaining = track_usage(before_mb)
            total_used += actual_used

            if df is not None and not df.empty:
                all_frames.append(df)
                rows = len(df)
                print(f"完成 ({rows} 行, 消耗 {actual_used:.2f} MB)")
                mark_done(key, rows=rows, bytes_est=int(actual_used * 1024 * 1024))
            else:
                print(f"数据为空 (消耗 {actual_used:.2f} MB)")
                mark_done(key, rows=0, bytes_est=int(actual_used * 1024 * 1024))

        except Exception as e:
            print(f"失败: {e}")

    # 合并所有数据到主文件
    if all_frames:
        # 读取现有数据
        existing_path = DATA_ROOT / "stock/price_1d.parquet"
        if existing_path.exists():
            existing_df = pd.read_parquet(existing_path)
            all_frames.insert(0, existing_df)

        merged = pd.concat(all_frames)
        # 去重（按 order_book_id 和 date）
        if isinstance(merged.index, pd.MultiIndex):
            merged = merged[~merged.index.duplicated(keep='last')]
        merged = merged.sort_index()

        merged.to_parquet(str(existing_path), engine="pyarrow", compression="snappy")
        print(f"[合并] A股日线行情 -> {existing_path} ({len(merged)} 行)")

        # 获取实际日期范围
        if isinstance(merged.index, pd.MultiIndex):
            dates = merged.index.get_level_values(1)
            min_date = pd.to_datetime(dates).min().strftime('%Y-%m-%d')
            max_date = pd.to_datetime(dates).max().strftime('%Y-%m-%d')
        else:
            min_date = merged.index.min().strftime('%Y-%m-%d')
            max_date = merged.index.max().strftime('%Y-%m-%d')

        new_range = f"{min_date} ~ {max_date}"
        update_progress_md(1, "done", new_range)
        return True

    update_progress_md(1, "done")
    return True


# ═══════════════════════════════════════════════════════════════════════════
# 任务 2: 指数日线行情
# ═══════════════════════════════════════════════════════════════════════════
def task2_index_price():
    """补充指数日线行情 (2010-01-01 ~ 当前)"""
    print("\n" + "=" * 60)
    print("任务 2: 指数日线行情")
    print("=" * 60)

    update_progress_md(2, "running")

    indx = rqdatac.all_instruments(type="INDX")
    index_ids = indx["order_book_id"].tolist()
    print(f"指数总数: {len(index_ids)}")

    date_ranges = [
        ("2010-01-01", "2013-12-31"),
        ("2026-05-01", datetime.now().strftime("%Y-%m-%d")),
    ]

    all_frames = []

    for start, end in date_ranges:
        success, rows, used = safe_download(
            f"index/price_1d_{start}_{end}",
            lambda s=start, e=end: rqdatac.get_price(
                index_ids, start_date=s, end_date=e,
                frequency="1d",
                fields=["open", "close", "high", "low", "total_turnover", "volume"],
                adjust_type="none", expect_df=True,
            ),
            DATA_ROOT / f"index/price_1d_{start}_{end}.parquet",
            need_mb=30,
        )
        if success and rows > 0:
            all_frames.append(pd.read_parquet(DATA_ROOT / f"index/price_1d_{start}_{end}.parquet"))
        if not success:
            update_progress_md(2, "paused")
            return False

    if all_frames:
        existing_path = DATA_ROOT / "index/price_1d.parquet"
        if existing_path.exists():
            existing_df = pd.read_parquet(existing_path)
            all_frames.insert(0, existing_df)

        merged = pd.concat(all_frames)
        if isinstance(merged.index, pd.MultiIndex):
            merged = merged[~merged.index.duplicated(keep='last')]
        merged = merged.sort_index()
        merged.to_parquet(str(existing_path), engine="pyarrow", compression="snappy")
        print(f"[合并] 指数日线行情 -> {existing_path} ({len(merged)} 行)")

        if isinstance(merged.index, pd.MultiIndex):
            dates = merged.index.get_level_values(1)
            min_date = pd.to_datetime(dates).min().strftime('%Y-%m-%d')
            max_date = pd.to_datetime(dates).max().strftime('%Y-%m-%d')
        else:
            min_date = merged.index.min().strftime('%Y-%m-%d')
            max_date = merged.index.max().strftime('%Y-%m-%d')

        update_progress_md(2, "done", f"{min_date} ~ {max_date}")
        return True

    update_progress_md(2, "done")
    return True


# ═══════════════════════════════════════════════════════════════════════════
# 任务 3: 指数权重
# ═══════════════════════════════════════════════════════════════════════════
def task3_index_weights():
    """补充指数权重 (2010-01-01 ~ 当前)"""
    print("\n" + "=" * 60)
    print("任务 3: 指数权重")
    print("=" * 60)

    update_progress_md(3, "running")

    major_indices = [
        "000001.XSHG", "000300.XSHG", "000905.XSHG", "000906.XSHG",
        "000852.XSHG", "000016.XSHG", "399001.XSHE", "399006.XSHE", "399005.XSHE",
    ]

    today = datetime.now().strftime("%Y-%m-%d")

    for idx_id in major_indices:
        success, rows, used = safe_download(
            f"index/weights/{idx_id}_2010",
            lambda i=idx_id: rqdatac.index_weights(i, start_date="2010-01-01", end_date=today),
            DATA_ROOT / f"index/weights/{idx_id}.parquet",
            need_mb=10,
        )
        if not success:
            update_progress_md(3, "paused")
            return False

    update_progress_md(3, "done", f"2010-01-01 ~ {today}")
    return True


# ═══════════════════════════════════════════════════════════════════════════
# 任务 5-6: 风险因子暴露
# ═══════════════════════════════════════════════════════════════════════════
def task5_6_factor_exposure():
    """补充风险因子暴露 v1/v2 (尝试从2010开始，可能最早2014)"""
    print("\n" + "=" * 60)
    print("任务 5-6: 风险因子暴露")
    print("=" * 60)

    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()[:500]  # 限制数量

    today = datetime.now().strftime("%Y-%m-%d")

    for task_id, model in [(5, "v1"), (6, "v2")]:
        update_progress_md(task_id, "running")

        success, rows, used = safe_download(
            f"risk_factor/factor_exposure_{model}_2010",
            lambda m=model: rqdatac.get_factor_exposure(
                stock_ids, "2010-01-01", today, model=m
            ),
            DATA_ROOT / f"risk_factor/factor_exposure_{model}.parquet",
            need_mb=30,
        )

        if success:
            # 检查实际日期范围
            df = pd.read_parquet(DATA_ROOT / f"risk_factor/factor_exposure_{model}.parquet")
            if isinstance(df.index, pd.MultiIndex):
                dates = df.index.get_level_values(0)
                min_date = pd.to_datetime(dates).min().strftime('%Y-%m-%d')
                max_date = pd.to_datetime(dates).max().strftime('%Y-%m-%d')
            else:
                min_date = "2010-01-01"
                max_date = today
            update_progress_md(task_id, "done", f"{min_date} ~ {max_date}")
        else:
            update_progress_md(task_id, "paused")
            return False

    return True


# ═══════════════════════════════════════════════════════════════════════════
# 任务 7: 风险因子收益
# ═══════════════════════════════════════════════════════════════════════════
def task7_factor_return():
    """补充风险因子收益 (2010-01-01 ~ 当前)"""
    print("\n" + "=" * 60)
    print("任务 7: 风险因子收益")
    print("=" * 60)

    update_progress_md(7, "running")

    today = datetime.now().strftime("%Y-%m-%d")

    success, rows, used = safe_download(
        "risk_factor/factor_return_2010",
        lambda: rqdatac.get_factor_return("2010-01-01", today),
        DATA_ROOT / "risk_factor/factor_return.parquet",
        need_mb=10,
    )

    if success:
        df = pd.read_parquet(DATA_ROOT / "risk_factor/factor_return.parquet")
        if isinstance(df.index, pd.DatetimeIndex):
            min_date = df.index.min().strftime('%Y-%m-%d')
            max_date = df.index.max().strftime('%Y-%m-%d')
        else:
            min_date = "2010-01-01"
            max_date = today
        update_progress_md(7, "done", f"{min_date} ~ {max_date}")
    else:
        update_progress_md(7, "paused")
        return False

    return True


# ═══════════════════════════════════════════════════════════════════════════
# 任务 8: 风险因子协方差
# ═══════════════════════════════════════════════════════════════════════════
def task8_factor_covariance():
    """补充风险因子协方差 (2010-01-01 ~ 当前)"""
    print("\n" + "=" * 60)
    print("任务 8: 风险因子协方差")
    print("=" * 60)

    update_progress_md(8, "running")

    # 按月下载
    cov_dir = DATA_ROOT / "risk_factor/factor_covariance"
    cov_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now()

    for year in range(2010, today.year + 1):
        for month in range(1, 13):
            # 跳过未来的月份
            if year == today.year and month > today.month:
                break

            date_str = f"{year}-{month:02d}-01"
            key = f"risk_factor/factor_covariance_{date_str}"

            if is_done(key):
                continue
            if not check_quota(1):
                update_progress_md(8, "paused")
                return False

            success, rows, used = safe_download(
                key,
                lambda d=date_str: rqdatac.get_factor_covariance(d),
                cov_dir / f"factor_covariance_{date_str}.parquet",
                need_mb=1,
            )

    # 更新范围
    update_progress_md(8, "done", f"2010-01-01 ~ {today.strftime('%Y-%m-%d')}")
    return True


# ═══════════════════════════════════════════════════════════════════════════
# 任务 9: 一致预期综合指标
# ═══════════════════════════════════════════════════════════════════════════
def task9_consensus():
    """补充一致预期综合指标 (2010-01-01 ~ 当前)"""
    print("\n" + "=" * 60)
    print("任务 9: 一致预期综合指标")
    print("=" * 60)

    update_progress_md(9, "running")

    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()[:300]

    today = datetime.now().strftime("%Y-%m-%d")

    success, rows, used = safe_download(
        "alternative/consensus/comp_indicators_2010",
        lambda: rqdatac.consensus.get_comp_indicators(stock_ids, "2010-01-01", today),
        DATA_ROOT / "alternative/consensus/comp_indicators.parquet",
        need_mb=20,
    )

    if success:
        update_progress_md(9, "done", f"2010-01-01 ~ {today}")
    else:
        update_progress_md(9, "paused")
        return False

    return True


# ═══════════════════════════════════════════════════════════════════════════
# 任务 10: A股资金流向
# ═══════════════════════════════════════════════════════════════════════════
def task10_capital_flow():
    """补充A股资金流向 (2010-01-01 ~ 当前)"""
    print("\n" + "=" * 60)
    print("任务 10: A股资金流向")
    print("=" * 60)

    update_progress_md(10, "running")

    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()

    today = datetime.now().strftime("%Y-%m-%d")

    # 尝试从 2010 开始，但资金流向数据可能只从 2020 开始
    success, rows, used = safe_download(
        "stock/capital_flow_2010",
        lambda: rqdatac.get_capital_flow(stock_ids, "2010-01-01", today),
        DATA_ROOT / "stock/capital_flow.parquet",
        need_mb=100,
    )

    if success:
        # 检查实际日期范围
        df = pd.read_parquet(DATA_ROOT / "stock/capital_flow.parquet")
        if isinstance(df.index, pd.MultiIndex):
            dates = df.index.get_level_values(1)
            min_date = pd.to_datetime(dates).min().strftime('%Y-%m-%d')
            max_date = pd.to_datetime(dates).max().strftime('%Y-%m-%d')
        else:
            min_date = "2010-01-01"
            max_date = today
        update_progress_md(10, "done", f"{min_date} ~ {max_date}")
    else:
        update_progress_md(10, "paused")
        return False

    return True


# ═══════════════════════════════════════════════════════════════════════════
# 任务 11: A股融资融券
# ═══════════════════════════════════════════════════════════════════════════
def task11_securities_margin():
    """补充A股融资融券 (2010-01-01 ~ 当前)"""
    print("\n" + "=" * 60)
    print("任务 11: A股融资融券")
    print("=" * 60)

    update_progress_md(11, "running")

    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()

    today = datetime.now().strftime("%Y-%m-%d")

    success, rows, used = safe_download(
        "stock/securities_margin_2010",
        lambda: rqdatac.get_securities_margin(stock_ids, "2010-01-01", today),
        DATA_ROOT / "stock/securities_margin.parquet",
        need_mb=50,
    )

    if success:
        update_progress_md(11, "done", f"2010-01-01 ~ {today}")
    else:
        update_progress_md(11, "paused")
        return False

    return True


# ═══════════════════════════════════════════════════════════════════════════
# 任务 12-13: ETF/LOF 日线行情
# ═══════════════════════════════════════════════════════════════════════════
def task12_13_etf_lof():
    """补充ETF/LOF日线行情 (2010-01-01 ~ 当前)"""
    print("\n" + "=" * 60)
    print("任务 12-13: ETF/LOF日线行情")
    print("=" * 60)

    today = datetime.now().strftime("%Y-%m-%d")

    for task_id, inst_type, name in [(12, "ETF", "ETF"), (13, "LOF", "LOF")]:
        update_progress_md(task_id, "running")

        inst = rqdatac.all_instruments(type=inst_type)
        ids = inst["order_book_id"].tolist()
        print(f"{name}总数: {len(ids)}")

        date_ranges = [
            ("2010-01-01", "2013-12-31"),
            ("2026-05-01", today),
        ]

        all_frames = []
        for start, end in date_ranges:
            success, rows, used = safe_download(
                f"{inst_type.lower()}/price_1d_{start}_{end}",
                lambda i=ids, s=start, e=end: rqdatac.get_price(
                    i, start_date=s, end_date=e,
                    frequency="1d",
                    fields=["open", "close", "high", "low", "total_turnover", "volume"],
                    adjust_type="none", expect_df=True,
                ),
                DATA_ROOT / f"{inst_type.lower()}/price_1d_{start}_{end}.parquet",
                need_mb=20,
            )
            if success and rows > 0:
                all_frames.append(pd.read_parquet(DATA_ROOT / f"{inst_type.lower()}/price_1d_{start}_{end}.parquet"))
            if not success:
                update_progress_md(task_id, "paused")
                return False

        if all_frames:
            # 合并到现有文件
            existing_dir = DATA_ROOT / inst_type.lower()
            existing_files = list(existing_dir.glob("price_1d_*.parquet"))
            for ef in existing_files:
                if f"{start}_{end}" not in ef.name:  # 不要重复读取刚下载的
                    all_frames.insert(0, pd.read_parquet(ef))

            merged = pd.concat(all_frames)
            if isinstance(merged.index, pd.MultiIndex):
                merged = merged[~merged.index.duplicated(keep='last')]
            merged = merged.sort_index()

            out_path = DATA_ROOT / f"{inst_type.lower()}/price_1d_merged.parquet"
            merged.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
            print(f"[合并] {name}日线行情 -> {out_path} ({len(merged)} 行)")

            if isinstance(merged.index, pd.MultiIndex):
                dates = merged.index.get_level_values(1)
                min_date = pd.to_datetime(dates).min().strftime('%Y-%m-%d')
                max_date = pd.to_datetime(dates).max().strftime('%Y-%m-%d')
            else:
                min_date = "2010-01-01"
                max_date = today

            update_progress_md(task_id, "done", f"{min_date} ~ {max_date}")

    return True


# ═══════════════════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════════════════
TASKS = {
    1: task1_stock_price,
    2: task2_index_price,
    3: task3_index_weights,
    5: task5_6_factor_exposure,
    7: task7_factor_return,
    8: task8_factor_covariance,
    9: task9_consensus,
    10: task10_capital_flow,
    11: task11_securities_margin,
    12: task12_13_etf_lof,
}

TASK_ORDER = [1, 2, 3, 5, 7, 8, 9, 10, 11, 12]


def main():
    info = get_quota_info()
    print(f"RQData 数据补充 | 剩余流量: {info['remaining_mb']:.1f} MB")
    print(f"目标: 从 2010 年开始补充数据，并更新到当前最新")
    print(f"数据目录: {DATA_ROOT}")
    print(f"进度文件: {PROGRESS_PATH}")

    task_id = int(sys.argv[1]) if len(sys.argv) > 1 else None

    if task_id:
        if task_id in TASKS:
            TASKS[task_id]()
        else:
            print(f"未知任务: {task_id}")
            print(f"可用任务: {list(TASKS.keys())}")
    else:
        for tid in TASK_ORDER:
            if not check_quota(QUOTA_MARGIN_MB + 20):
                print(f"\n[停止] 流量不足，请明日继续")
                break
            if tid in TASKS:
                TASKS[tid]()

    info = get_quota_info()
    print(f"\n=== 流量使用摘要 ===")
    print(f"本次会话消耗: {_session_used_mb:.1f} MB")
    print(f"当前剩余: {info['remaining_mb']:.1f} MB")


if __name__ == "__main__":
    main()
