"""
数据完整性快速检查脚本

用法:
    python scripts/data/check_data_integrity_quick.py

只检查：
- 文件是否存在
- 文件大小是否合理
- 能否成功读取文件（不读取全部数据）
"""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"
REPORT_PATH = DATA_ROOT / "DATA_INTEGRITY_REPORT.md"


def check_parquet_file(file_path: Path) -> dict:
    """快速检查parquet文件"""
    result = {
        "file": str(file_path.relative_to(DATA_ROOT)),
        "exists": False,
        "size_mb": 0,
        "rows": 0,
        "columns": [],
        "errors": []
    }

    if not file_path.exists():
        result["errors"].append("文件不存在")
        return result

    result["exists"] = True
    result["size_mb"] = round(file_path.stat().st_size / 1024 / 1024, 2)

    if result["size_mb"] == 0:
        result["errors"].append("文件大小为0")
        return result

    try:
        # 只读取元数据，不读取全部数据
        pf = pq.ParquetFile(str(file_path))
        result["rows"] = pf.metadata.num_rows
        result["columns"] = [f.name for f in pf.schema_arrow]
    except Exception as e:
        result["errors"].append(f"读取失败: {str(e)[:100]}")

    return result


def check_json_file(file_path: Path) -> dict:
    """检查JSON文件"""
    result = {
        "file": str(file_path.relative_to(DATA_ROOT)),
        "exists": False,
        "size_mb": 0,
        "rows": 0,
        "errors": []
    }

    if not file_path.exists():
        result["errors"].append("文件不存在")
        return result

    result["exists"] = True
    result["size_mb"] = round(file_path.stat().st_size / 1024 / 1024, 2)

    if result["size_mb"] == 0:
        result["errors"].append("文件大小为0")
        return result

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            result["rows"] = len(data)
        elif isinstance(data, dict):
            result["rows"] = 1
    except Exception as e:
        result["errors"].append(f"读取失败: {str(e)[:100]}")

    return result


def scan_all_files() -> list[Path]:
    """扫描所有数据文件"""
    files = []

    # 扫描所有目录
    for pattern in ["**/*.parquet", "**/*.json"]:
        for f in DATA_ROOT.glob(pattern):
            # 跳过临时文件和报告文件
            if "download_log" in f.name or "INTEGRITY_REPORT" in f.name:
                continue
            files.append(f)

    return sorted(files)


def generate_report(results: list[dict]) -> str:
    """生成检查报告"""
    lines = [
        "# 数据完整性检查报告",
        f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"数据目录: `{DATA_ROOT}`",
        "\n---",
        "\n## 检查摘要\n",
    ]

    # 统计
    total = len(results)
    exists = sum(1 for r in results if r["exists"])
    has_data = sum(1 for r in results if r["rows"] > 0)
    has_errors = sum(1 for r in results if r["errors"])
    total_size_mb = sum(r.get("size_mb", 0) for r in results)
    total_rows = sum(r.get("rows", 0) for r in results)

    lines.extend([
        f"- 总文件数: {total}",
        f"- 文件存在: {exists} / {total}",
        f"- 有效数据文件: {has_data} / {exists}",
        f"- 有错误: {has_errors}",
        f"- 总数据量: {total_size_mb:.1f} MB",
        f"- 总记录数: {total_rows:,}",
    ])

    # 分类统计
    categories = {}
    for r in results:
        file_path = r["file"]
        category = file_path.split("/")[0] if "/" in file_path else "other"
        if category not in categories:
            categories[category] = {"total": 0, "errors": 0, "rows": 0, "size_mb": 0}
        categories[category]["total"] += 1
        categories[category]["rows"] += r.get("rows", 0)
        categories[category]["size_mb"] += r.get("size_mb", 0)
        if r["errors"]:
            categories[category]["errors"] += 1

    lines.append("\n## 分类统计\n")
    lines.append("| 类别 | 文件数 | 有错误 | 总行数 | 大小(MB) |")
    lines.append("|------|--------|--------|--------|----------|")
    for cat in sorted(categories.keys()):
        s = categories[cat]
        lines.append(f"| {cat} | {s['total']} | {s['errors']} | {s['rows']:,} | {s['size_mb']:.1f} |")

    # 详细结果（按类别分组）
    lines.append("\n## 详细检查结果\n")

    grouped = {}
    for r in results:
        file_path = r["file"]
        category = file_path.split("/")[0] if "/" in file_path else "other"
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(r)

    for category in sorted(grouped.keys()):
        lines.append(f"\n### {category.upper()}\n")
        lines.append("| 文件 | 大小(MB) | 行数 | 状态 |")
        lines.append("|------|----------|------|------|")

        for r in grouped[category]:
            status = "✅" if not r["errors"] else "❌ " + "; ".join(r["errors"])
            lines.append(f"| `{r['file']}` | {r.get('size_mb', 0):.1f} | {r.get('rows', 0):,} | {status} |")

    # 错误文件列表
    error_files = [r for r in results if r["errors"]]
    if error_files:
        lines.append("\n## 错误文件列表\n")
        for r in error_files:
            lines.append(f"\n### {r['file']}\n")
            for err in r["errors"]:
                lines.append(f"- {err}")

    return "\n".join(lines)


def main():
    print("数据完整性快速检查")
    print(f"数据目录: {DATA_ROOT}")
    print()

    # 扫描文件
    print("扫描数据文件...")
    all_files = scan_all_files()
    print(f"找到 {len(all_files)} 个文件")

    # 检查每个文件
    results = []
    for i, file_path in enumerate(all_files, 1):
        if i % 50 == 0 or i == len(all_files):
            print(f"进度: {i}/{len(all_files)} ({i/len(all_files)*100:.1f}%)")

        if file_path.suffix == ".parquet":
            result = check_parquet_file(file_path)
        elif file_path.suffix == ".json":
            result = check_json_file(file_path)
        else:
            continue

        results.append(result)

    # 生成报告
    print("\n生成报告...")
    report = generate_report(results)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"报告已保存: {REPORT_PATH}")

    # 打印摘要
    has_errors = sum(1 for r in results if r["errors"])
    total_size = sum(r.get("size_mb", 0) for r in results)
    print(f"\n检查完成: {len(results)} 个文件, {total_size:.1f} MB, {has_errors} 个错误")


if __name__ == "__main__":
    main()
