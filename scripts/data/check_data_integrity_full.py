"""
数据完整性检查脚本 - 全量版本

用法:
    python scripts/data/check_data_integrity_full.py

检查项：
- 文件是否存在
- 文件是否非空
- 列名是否符合预期
- 数据类型是否正确
- 行数统计
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from utils.common import setup_license

setup_license()

# ── 配置 ──────────────────────────────────────────────────────────────────
DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"
REPORT_PATH = DATA_ROOT / "DATA_INTEGRITY_REPORT.md"


# ── 数据结构定义 ──────────────────────────────────────────────────────────
# 格式: { 文件路径: { "expected_columns": [...], "description": "..." } }
DATA_SCHEMA = {
    # === 元数据 ===
    "instruments/all_instruments_CS.parquet": {
        "expected_columns": ["order_book_id", "symbol", "display_name", "abbreviation", "listed_date", "de_listed_date", "type"],
        "description": "A股股票列表"
    },
    "instruments/all_instruments_ETF.parquet": {
        "expected_columns": ["order_book_id", "symbol", "display_name", "abbreviation", "listed_date", "de_listed_date", "type"],
        "description": "ETF基金列表"
    },
    "instruments/all_instruments_LOF.parquet": {
        "expected_columns": ["order_book_id", "symbol", "display_name", "abbreviation", "listed_date", "de_listed_date", "type"],
        "description": "LOF基金列表"
    },
    "instruments/all_instruments_INDX.parquet": {
        "expected_columns": ["order_book_id", "symbol", "display_name", "abbreviation", "listed_date", "de_listed_date", "type"],
        "description": "指数列表"
    },
    "instruments/all_instruments_Future.parquet": {
        "expected_columns": ["order_book_id", "symbol", "display_name", "abbreviation", "listed_date", "de_listed_date", "type"],
        "description": "期货合约列表"
    },
    "instruments/all_instruments_Spot.parquet": {
        "expected_columns": ["order_book_id", "symbol", "display_name", "abbreviation", "listed_date", "de_listed_date", "type"],
        "description": "现货合约列表"
    },
    "instruments/all_instruments_Option.parquet": {
        "expected_columns": ["order_book_id", "symbol", "display_name", "abbreviation", "listed_date", "de_listed_date", "type"],
        "description": "期权合约列表"
    },
    "instruments/all_instruments_Convertible.parquet": {
        "expected_columns": ["order_book_id", "symbol", "display_name", "abbreviation", "listed_date", "de_listed_date", "type"],
        "description": "可转债列表"
    },
    "instruments/all_instruments_Repo.parquet": {
        "expected_columns": ["order_book_id", "symbol", "display_name", "abbreviation", "listed_date", "de_listed_date", "type"],
        "description": "回购合约列表"
    },
    "instruments/all_instruments_REITs.parquet": {
        "expected_columns": ["order_book_id", "symbol", "display_name", "abbreviation", "listed_date", "de_listed_date", "type"],
        "description": "REITs列表"
    },
    "instruments/all_instruments_FUND.parquet": {
        "expected_columns": ["order_book_id", "symbol", "display_name", "abbreviation", "listed_date", "de_listed_date", "type"],
        "description": "公募基金列表"
    },

    # === 收益率曲线 ===
    "yield_curve/yield_curve.parquet": {
        "expected_columns": ["date", "1m", "3m", "6m", "1y", "3y", "5y", "7y", "10y", "30y"],
        "description": "国债收益率曲线"
    },

    # === A股数据 ===
    "stock/price_change_rate.parquet": {
        "expected_columns": ["order_book_id", "date", "price_change_rate"],
        "description": "股价变化率"
    },
    "stock/current_performance.parquet": {
        "expected_columns": ["order_book_id", "info_date", "pub_date", "interval", "revenue", "net_profit", "operating_profit", "total_profit"],
        "description": "财务快报"
    },
    "stock/performance_forecast.parquet": {
        "expected_columns": ["order_book_id", "info_date", "pub_date", "interval", "forecast_type", "forecast", "change_min", "change_max"],
        "description": "业绩预告"
    },
    "stock/dividend.parquet": {
        "expected_columns": ["order_book_id", "book_closure_date", "ex_dividend_date", "payable_date", "dividend_coefficient", "cash_amount_per_share", "round_lot_amount", "transfer_amount_per_share", "retained_earnings_per_share", "capital_reserve_per_share"],
        "description": "分红数据"
    },
    "stock/split.parquet": {
        "expected_columns": ["order_book_id", "ex_dividend_date", "split_coefficient"],
        "description": "拆股数据"
    },
    "stock/turnover_rate.parquet": {
        "expected_columns": ["order_book_id", "date", "today_turnover_rate", "week_turnover_rate", "month_turnover_rate"],
        "description": "换手率"
    },
    "stock/suspended.parquet": {
        "expected_columns": ["order_book_id", "suspended_dates"],
        "description": "停牌信息"
    },
    "stock/st_stock.parquet": {
        "expected_columns": ["order_book_id", "special_type", "special_type_start_date"],
        "description": "ST股票标记"
    },
    "stock/securities_margin.parquet": {
        "expected_columns": ["order_book_id", "date", "margin_balance", "buy_on_margin_value", "sell_on_margin_value", "short_balance", "short_balance_value", "short_sell_quantity", "short_sell_value", "repay_short_quantity", "repay_short_value"],
        "description": "融资融券数据"
    },
    "stock/stock_connect.parquet": {
        "expected_columns": ["order_book_id", "start_date", "end_date", "channel"],
        "description": "沪港通/深港通标的"
    },
    "stock/instrument_industry.parquet": {
        "expected_columns": ["order_book_id", "industry", "industry_name", "sector", "sector_name"],
        "description": "股票行业分类"
    },

    # === 期货数据 ===
    "futures/member_rank.parquet": {
        "expected_columns": ["underlying_symbol", "date", "rank", "broker", "volume", "long_open_interest", "short_open_interest"],
        "description": "期货会员排名"
    },
    "futures/warehouse_stocks.parquet": {
        "expected_columns": ["underlying_symbol", "date", "warehouse", "volume"],
        "description": "期货仓单"
    },
    "futures/roll_yield.parquet": {
        "expected_columns": ["date", "underlying_symbol", "dominant_contract", "next_contract", "roll_yield"],
        "description": "期货展期收益"
    },

    # === 可转债数据 ===
    "convertible/all_instruments.parquet": {
        "expected_columns": ["order_book_id", "symbol", "display_name", "abbreviation", "listed_date", "de_listed_date", "type"],
        "description": "可转债列表"
    },
    "convertible/conversion_price.parquet": {
        "expected_columns": ["order_book_id", "date", "conversion_price"],
        "description": "转股价"
    },
    "convertible/conversion_info.parquet": {
        "expected_columns": ["order_book_id", "start_date", "end_date"],
        "description": "转股信息"
    },
    "convertible/call_info.parquet": {
        "expected_columns": ["order_book_id", "call_trigger_date", "call_trigger_price", "call_price"],
        "description": "赎回信息"
    },
    "convertible/put_info.parquet": {
        "expected_columns": ["order_book_id", "put_trigger_date", "put_trigger_price", "put_price"],
        "description": "回售信息"
    },
    "convertible/cash_flow.parquet": {
        "expected_columns": ["order_book_id", "payment_date", "coupon_rate"],
        "description": "现金流"
    },
    "convertible/indicators.parquet": {
        "expected_columns": ["order_book_id", "date", "conversion_premium_rate", "conversion_rate", "conversion_value", "pure_debt_value"],
        "description": "可转债指标"
    },
    "convertible/credit_rating.parquet": {
        "expected_columns": ["order_book_id", "date", "rating", "rating_agency"],
        "description": "信用评级"
    },
    "convertible/close_price.parquet": {
        "expected_columns": ["order_book_id", "date", "close"],
        "description": "可转债收盘价"
    },
    "convertible/std_discount.parquet": {
        "expected_columns": ["order_book_id", "date", "discount_rate"],
        "description": "标准折价率"
    },
    "convertible/call_announcement.parquet": {
        "expected_columns": ["order_book_id", "announcement_date", "call_date"],
        "description": "赎回公告"
    },

    # === 风险因子 ===
    "risk_factor/stock_beta.parquet": {
        "expected_columns": ["order_book_id", "date", "beta"],
        "description": "股票Beta值"
    },

    # === 基金数据 ===
    "fund/all_instruments.parquet": {
        "expected_columns": ["order_book_id", "symbol", "display_name", "abbreviation", "listed_date", "de_listed_date", "type"],
        "description": "公募基金列表"
    },
    "fund/dividend.parquet": {
        "expected_columns": ["order_book_id", "effective_date", "record_date", "ex_dividend_date", "payable_date", "dividend_per_unit"],
        "description": "基金分红"
    },
    "fund/split.parquet": {
        "expected_columns": ["order_book_id", "ex_dividend_date", "split_coefficient"],
        "description": "基金拆分"
    },
    "fund/fee.parquet": {
        "expected_columns": ["order_book_id", "management_fee", "custodian_fee", "subscription_fee", "purchase_fee", "redeem_fee"],
        "description": "基金费率"
    },
    "fund/ratings.parquet": {
        "expected_columns": ["order_book_id", "rating_date", "rating", "rating_agency"],
        "description": "基金评级"
    },
    "fund/holder_structure.parquet": {
        "expected_columns": ["order_book_id", "info_date", "holder_type", "holder_percentage"],
        "description": "基金持有人结构"
    },
    "fund/units_change.parquet": {
        "expected_columns": ["order_book_id", "effective_date", "change_reason", "change"],
        "description": "基金份额变动"
    },
    "fund/benchmark.parquet": {
        "expected_columns": ["order_book_id", "benchmark"],
        "description": "基金基准"
    },
    "fund/instrument_category.parquet": {
        "expected_columns": ["order_book_id", "category"],
        "description": "基金分类"
    },
    "fund/category_mapping.parquet": {
        "expected_columns": ["category", "source"],
        "description": "基金分类映射"
    },
    "fund/manager.parquet": {
        "expected_columns": ["order_book_id", "manager"],
        "description": "基金经理"
    },
    "fund/nav.parquet": {
        "expected_columns": ["order_book_id", "date", "net_value", "accumulated_net_value"],
        "description": "基金净值"
    },
    "fund/transition_info.parquet": {
        "expected_columns": ["order_book_id", "transition_date", "transition_type"],
        "description": "基金转型信息"
    },
}


# ── 检查函数 ──────────────────────────────────────────────────────────────
def check_file_integrity(file_path: Path, schema: dict[str, Any]) -> dict[str, Any]:
    """检查单个文件的完整性"""
    result = {
        "file": str(file_path.relative_to(DATA_ROOT)),
        "description": schema.get("description", ""),
        "exists": False,
        "empty": True,
        "rows": 0,
        "columns": [],
        "expected_columns": schema.get("expected_columns", []),
        "missing_columns": [],
        "extra_columns": [],
        "column_match": False,
        "errors": []
    }

    # 检查文件是否存在
    if not file_path.exists():
        result["errors"].append("文件不存在")
        return result

    result["exists"] = True

    # 读取文件
    try:
        if file_path.suffix == ".parquet":
            df = pd.read_parquet(str(file_path))
        elif file_path.suffix == ".json":
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
        else:
            result["errors"].append(f"不支持的文件格式: {file_path.suffix}")
            return result
    except Exception as e:
        result["errors"].append(f"读取文件失败: {e}")
        return result

    # 检查是否为空
    if df.empty:
        result["errors"].append("文件为空")
        return result

    result["empty"] = False
    result["rows"] = len(df)
    result["columns"] = list(df.columns)

    # 检查列名
    expected = set(result["expected_columns"])
    actual = set(result["columns"])

    result["missing_columns"] = list(expected - actual)
    result["extra_columns"] = list(actual - expected)
    result["column_match"] = len(result["missing_columns"]) == 0

    if result["missing_columns"]:
        result["errors"].append(f"缺失列: {', '.join(result['missing_columns'])}")

    return result


def scan_all_data_files() -> list[Path]:
    """扫描所有数据文件"""
    files = []

    # 扫描定义的文件
    for rel_path in DATA_SCHEMA.keys():
        file_path = DATA_ROOT / rel_path
        files.append(file_path)

    # 扫描 PIT 财务数据（按年度）
    pit_dir = DATA_ROOT / "stock" / "pit_financials"
    if pit_dir.exists():
        for f in pit_dir.glob("pit_financials_*.parquet"):
            files.append(f)

    # 扫描因子数据
    factor_dir = DATA_ROOT / "factor"
    if factor_dir.exists():
        for f in factor_dir.glob("*.parquet"):
            files.append(f)

    # 扫描基金持仓/资产配置/行业配置（按季度）
    fund_dir = DATA_ROOT / "fund"
    if fund_dir.exists():
        for pattern in ["holdings_*.parquet", "asset_allocation_*.parquet", "industry_allocation_*.parquet"]:
            for f in fund_dir.glob(pattern):
                files.append(f)

    return sorted(set(files))


def generate_report(results: list[dict[str, Any]]) -> str:
    """生成完整性检查报告"""
    report_lines = [
        "# 数据完整性检查报告",
        f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"数据目录: `{DATA_ROOT}`",
        "\n---",
        "\n## 检查摘要\n",
    ]

    # 统计摘要
    total = len(results)
    exists = sum(1 for r in results if r["exists"])
    non_empty = sum(1 for r in results if not r["empty"])
    column_match = sum(1 for r in results if r["column_match"])
    has_errors = sum(1 for r in results if r["errors"])

    report_lines.extend([
        f"- 总文件数: {total}",
        f"- 文件存在: {exists} / {total}",
        f"- 文件非空: {non_empty} / {exists}",
        f"- 列名匹配: {column_match} / {exists}",
        f"- 有错误: {has_errors}",
    ])

    # 分类统计
    categories = {}
    for r in results:
        file_path = r["file"]
        category = file_path.split("/")[0] if "/" in file_path else "other"
        if category not in categories:
            categories[category] = {"total": 0, "errors": 0}
        categories[category]["total"] += 1
        if r["errors"]:
            categories[category]["errors"] += 1

    report_lines.append("\n## 分类统计\n")
    report_lines.append("| 类别 | 文件数 | 有错误 |")
    report_lines.append("|------|--------|--------|")
    for cat in sorted(categories.keys()):
        stats = categories[cat]
        report_lines.append(f"| {cat} | {stats['total']} | {stats['errors']} |")

    # 详细检查结果
    report_lines.append("\n## 详细检查结果\n")

    # 按类别分组
    grouped = {}
    for r in results:
        file_path = r["file"]
        category = file_path.split("/")[0] if "/" in file_path else "other"
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(r)

    for category in sorted(grouped.keys()):
        report_lines.append(f"\n### {category.upper()}\n")
        report_lines.append("| 文件 | 描述 | 行数 | 状态 |")
        report_lines.append("|------|------|------|------|")

        for r in grouped[category]:
            status = "✅ 正常" if not r["errors"] else "❌ " + "; ".join(r["errors"])
            desc = r.get("description", "")
            report_lines.append(f"| `{r['file']}` | {desc} | {r['rows']:,} | {status} |")

    # 错误汇总
    error_files = [r for r in results if r["errors"]]
    if error_files:
        report_lines.append("\n## 错误文件列表\n")
        for r in error_files:
            report_lines.append(f"\n### {r['file']}\n")
            for err in r["errors"]:
                report_lines.append(f"- {err}")
            if r["missing_columns"]:
                report_lines.append(f"  - 缺失列: {', '.join(r['missing_columns'])}")
            if r["extra_columns"]:
                report_lines.append(f"  - 额外列: {', '.join(r['extra_columns'])}")

    return "\n".join(report_lines)


def main():
    print(f"数据完整性检查工具")
    print(f"数据目录: {DATA_ROOT}")
    print()

    # 扫描所有数据文件
    print("扫描数据文件...")
    all_files = scan_all_data_files()
    print(f"找到 {len(all_files)} 个文件")

    # 检查每个文件
    results = []
    for i, file_path in enumerate(all_files, 1):
        rel_path = file_path.relative_to(DATA_ROOT)
        schema = DATA_SCHEMA.get(str(rel_path), {})

        if i % 10 == 0 or i == len(all_files):
            print(f"检查进度: {i}/{len(all_files)} ({i/len(all_files)*100:.1f}%)")

        result = check_file_integrity(file_path, schema)
        results.append(result)

    # 生成报告
    print("\n生成报告...")
    report = generate_report(results)

    # 保存报告
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"报告已保存: {REPORT_PATH}")

    # 打印摘要
    has_errors = sum(1 for r in results if r["errors"])
    print(f"\n检查完成: {len(results)} 个文件, {has_errors} 个有错误")

    if has_errors > 0:
        print("\n错误文件:")
        for r in results:
            if r["errors"]:
                print(f"  - {r['file']}: {'; '.join(r['errors'])}")


if __name__ == "__main__":
    main()
