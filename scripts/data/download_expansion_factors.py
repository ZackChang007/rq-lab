"""
财务膨胀因子下载脚本

下载 _lyr_1~8, _mrq_1~11, _ttm_1~8, _ttm1_1~8 历史膨胀因子。

用法:
    python scripts/data/download_expansion_factors.py --suffix lyr_1
    python scripts/data/download_expansion_factors.py --suffix ttm_3
    python scripts/data/download_expansion_factors.py --all
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

import rqdatac
from utils.common import setup_license

setup_license()
rqdatac.init()

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"
LOG_PATH = DATA_ROOT / "download_log.json"
QUOTA_MARGIN_MB = 50

_session_used_mb = 0.0


def get_quota_info():
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
    global _session_used_mb
    info = get_quota_info()
    actual = info["used_mb"] - before_mb
    if actual > 0:
        _session_used_mb += actual
    return actual


def load_log():
    if LOG_PATH.exists():
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    return {}


def save_log(log):
    LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


def is_done(key):
    log = load_log()
    for day_data in log.values():
        if key in day_data and day_data[key]["status"] == "done":
            return True
    return False


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


def mark_failed(key, err_msg):
    log = load_log()
    today = datetime.now().strftime("%Y-%m-%d")
    log.setdefault(today, {})[key] = {
        "status": "failed",
        "error": err_msg[:200],
        "ts": datetime.now().isoformat(),
    }
    save_log(log)


def get_factor_list(suffix):
    """获取指定后缀的因子列表"""
    factor_names_path = DATA_ROOT / "stock" / "factor_names.json"
    if not factor_names_path.exists():
        print("[错误] factor_names.json 不存在，请先运行 metadata 下载")
        return []

    factor_names = json.loads(factor_names_path.read_text(encoding="utf-8"))
    return [f for f in factor_names if f"_{suffix}" in f]


def download_batch(suffix, start_date="2010-01-01"):
    """下载指定后缀的膨胀因子"""
    factor_list = get_factor_list(suffix)
    if not factor_list:
        print(f"[跳过] 无 _{suffix} 因子")
        return

    # 检查已下载
    factor_dir = DATA_ROOT / "factor"
    factor_dir.mkdir(parents=True, exist_ok=True)
    downloaded = {f.stem for f in factor_dir.glob("*.parquet")}
    todo = [f for f in factor_list if f not in downloaded and not is_done(f"factor/{f}")]

    print(f"\n=== 下载 _{suffix} 因子 ===")
    print(f"总计: {len(factor_list)}, 已下载: {len(factor_list) - len(todo)}, 待下载: {len(todo)}")

    if not todo:
        print("[完成] 全部已下载")
        return

    cs = rqdatac.all_instruments(type="CS")
    stock_ids = cs["order_book_id"].tolist()
    end_date = datetime.now().strftime("%Y-%m-%d")

    success = 0
    failed = 0
    for i, factor_name in enumerate(todo):
        if not check_quota(5):
            print(f"\n[停止] 流量不足，已完成 {success}/{len(todo)}")
            break

        try:
            info_before = get_quota_info()
            before_mb = info_before["used_mb"]

            print(f"  [{i+1}/{len(todo)}] {factor_name} ...", end=" ", flush=True)
            df = rqdatac.get_factor(stock_ids, factor_name, start_date, end_date, expect_df=True)

            actual_used = track_usage(before_mb)

            if df is not None and not df.empty:
                out_path = factor_dir / f"{factor_name}.parquet"
                df.to_parquet(str(out_path), engine="pyarrow", compression="snappy")
                print(f"完成 ({len(df)} 行, {actual_used:.2f} MB)", flush=True)
                mark_done(f"factor/{factor_name}", rows=len(df), bytes_est=int(actual_used * 1024 * 1024))
                success += 1
            else:
                print(f"空数据 ({actual_used:.2f} MB)", flush=True)
                mark_done(f"factor/{factor_name}", rows=0, bytes_est=int(actual_used * 1024 * 1024))
                success += 1
        except Exception as e:
            err_msg = str(e)
            if "Quota exceeded" in err_msg:
                print("流量超限")
                mark_failed(f"factor/{factor_name}", "Quota exceeded")
                break
            print(f"失败: {err_msg[:60]}", flush=True)
            mark_failed(f"factor/{factor_name}", err_msg)
            failed += 1

    print(f"\n[_{suffix}] 完成: {success}, 失败: {failed}, 剩余配额: {get_quota_info()['remaining_mb']:.1f} MB")


def main():
    parser = argparse.ArgumentParser(description="下载财务膨胀因子")
    parser.add_argument("--suffix", type=str, help="后缀，如 lyr_1, mrq_3, ttm_5, ttm1_2")
    parser.add_argument("--all", action="store_true", help="下载全部膨胀因子")
    parser.add_argument("--start", type=str, default="2010-01-01", help="起始日期")
    args = parser.parse_args()

    info = get_quota_info()
    print(f"膨胀因子下载 | 剩余流量: {info['remaining_mb']:.1f} MB")

    # 所有膨胀因子后缀
    all_suffixes = (
        [f"lyr_{i}" for i in range(1, 9)]
        + [f"ttm_{i}" for i in range(1, 9)]
        + [f"mrq_{i}" for i in range(1, 12)]
        + [f"ttm1_{i}" for i in range(1, 9)]
    )

    if args.all:
        for suffix in all_suffixes:
            if not check_quota(100):
                print(f"\n[停止] 流量不足，明日继续")
                break
            download_batch(suffix, start_date=args.start)
    elif args.suffix:
        download_batch(args.suffix, start_date=args.start)
    else:
        print("请指定 --suffix 或 --all")
        print(f"可用后缀: {', '.join(all_suffixes)}")

    # 摘要
    info = get_quota_info()
    print(f"\n=== 流量使用摘要 ===")
    print(f"本次会话消耗: {_session_used_mb:.1f} MB")
    print(f"当前剩余: {info['remaining_mb']:.1f} MB")


if __name__ == "__main__":
    main()
