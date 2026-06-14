"""
检查 progress.md 中提到的所有数据下载任务是否已完成

输出:
- 检查每个计划中的待下载任务
- 验证本地文件是否存在
- 生成完整性检查报告
"""
import re
from pathlib import Path

PROGRESS_FILE = Path("docs/progress.md")
DATA_ROOT = Path("data")

# 关键数据路径映射
DATA_PATHS = {
    # 股票数据
    "stock_prices": DATA_ROOT / "stock" / "prices.parquet",
    "stock_info": DATA_ROOT / "stock" / "info.parquet",
    "stock_suspend": DATA_ROOT / "stock" / "suspend.parquet",
    "stock_st": DATA_ROOT / "stock" / "st.parquet",

    # 财务数据
    "pit_financials": DATA_ROOT / "stock" / "pit_financials",

    # 因子数据
    "factor": DATA_ROOT / "factor",
    "factor_early": DATA_ROOT / "factor_early",

    # 期货数据
    "futures_contracts": DATA_ROOT / "futures" / "contracts.json",
    "futures_prices": DATA_ROOT / "futures" / "prices.parquet",

    # 期权数据
    "options_dominant_month": DATA_ROOT / "options" / "dominant_month.parquet",

    # 宏观数据
    "macro_reserve_ratio": DATA_ROOT / "macro" / "reserve_ratio.parquet",

    # 概念数据
    "concept_5g": DATA_ROOT / "stock" / "concept_5G.json",
    "concept_ai": DATA_ROOT / "stock" / "concept_人工智能.json",
    "concept_medical": DATA_ROOT / "stock" / "concept_医药.json",
    "concept_energy": DATA_ROOT / "stock" / "concept_新能源.json",
}

def check_file_exists(path: Path) -> dict:
    """检查文件或目录是否存在及大小"""
    result = {
        "path": str(path),
        "exists": path.exists(),
        "size_mb": 0,
        "rows": 0,
    }

    if path.exists():
        if path.is_file():
            result["size_mb"] = round(path.stat().st_size / 1024 / 1024, 2)
        elif path.is_dir():
            # 统计目录下所有文件
            files = list(path.glob("*.parquet")) + list(path.glob("*.json"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            result["size_mb"] = round(total_size / 1024 / 1024, 2)
            result["file_count"] = len(files)

    return result

def extract_download_tasks(progress_content: str) -> dict:
    """从 progress.md 中提取下载任务清单"""
    tasks = {}

    # 提取各计划的章节标题
    plan_pattern = r"# 数据补充计划\s+([IVX]+).*?\n"
    plans = re.findall(plan_pattern, progress_content)

    # 提取待下载任务
    for plan_num in plans:
        # 找到该计划的章节内容
        plan_start = progress_content.find(f"# 数据补充计划 {plan_num}")
        if plan_start == -1:
            continue

        # 找下一个计划的开始位置
        next_plan_match = re.search(r"# 数据补充计划", progress_content[plan_start + 50:])
        if next_plan_match:
            plan_end = plan_start + 50 + next_plan_match.start()
        else:
            plan_end = len(progress_content)

        plan_content = progress_content[plan_start:plan_end]

        # 检查是否标记为已完成
        if "✅ 已完成" in plan_content or "**已完成**" in plan_content:
            tasks[plan_num] = {"status": "completed", "details": []}
        else:
            # 提取具体的待下载项目
            tasks[plan_num] = {"status": "pending", "details": []}

            # 匹配待下载清单中的项目
            download_items = re.findall(r"-\s+(.+?)\n", plan_content)
            for item in download_items[:10]:  # 只取前10个避免过多噪音
                if "下载" in item or "因子" in item or "数据" in item:
                    tasks[plan_num]["details"].append(item.strip())

    return tasks

def check_data_completeness():
    """检查数据完整性"""
    print("=" * 80)
    print("数据下载完整性检查")
    print("=" * 80)

    # 读取 progress.md
    progress_content = PROGRESS_FILE.read_text(encoding="utf-8")

    # 提取下载任务
    tasks = extract_download_tasks(progress_content)

    # 检查关键数据文件
    print("\n关键数据文件检查:")
    print("-" * 80)

    results = {}
    for name, path in DATA_PATHS.items():
        result = check_file_exists(path)
        results[name] = result

        status = "✅" if result["exists"] else "❌"
        size_info = f"{result['size_mb']:.2f} MB" if result["exists"] else "不存在"

        print(f"{status} {name}: {size_info}")

    # 汇总统计
    print("\n" + "=" * 80)
    print("汇总统计:")
    print("-" * 80)

    exists_count = sum(1 for r in results.values() if r["exists"])
    total_count = len(results)

    print(f"✅ 存在: {exists_count}/{total_count} ({exists_count/total_count*100:.1f}%)")
    print(f"❌ 缺失: {total_count - exists_count}/{total_count}")

    # 总数据量
    total_size = sum(r["size_mb"] for r in results.values() if r["exists"])
    print(f"📊 总数据量: {total_size:.2f} MB ({total_size/1024:.2f} GB)")

    # 检查因子数据详情
    print("\n" + "=" * 80)
    print("因子数据详细检查:")
    print("-" * 80)

    factor_dir = DATA_ROOT / "factor"
    if factor_dir.exists():
        factor_files = list(factor_dir.glob("*.parquet"))
        print(f"✅ 因子文件数: {len(factor_files)} 个")

        # 统计因子类别
        lyr_count = sum(1 for f in factor_files if "_lyr_" in f.name)
        mrq_count = sum(1 for f in factor_files if "_mrq_" in f.name)
        ttm_count = sum(1 for f in factor_files if "_ttm_" in f.name and "_ttm1_" not in f.name)
        ttm1_count = sum(1 for f in factor_files if "_ttm1_" in f.name)
        other_count = len(factor_files) - lyr_count - mrq_count - ttm_count - ttm1_count

        print(f"  - LYR因子: {lyr_count} 个")
        print(f"  - MRQ因子: {mrq_count} 个")
        print(f"  - TTM因子: {ttm_count} 个")
        print(f"  - TTM1因子: {ttm1_count} 个")
        print(f"  - 其他因子: {other_count} 个")

        # 总大小
        total_factor_size = sum(f.stat().st_size for f in factor_files) / 1024 / 1024
        print(f"  📊 总大小: {total_factor_size:.2f} MB ({total_factor_size/1024:.2f} GB)")

    # 检查 PIT 财务数据
    print("\n" + "=" * 80)
    print("PIT 财务数据检查:")
    print("-" * 80)

    pit_dir = DATA_ROOT / "stock" / "pit_financials"
    if pit_dir.exists():
        pit_files = list(pit_dir.glob("*.parquet"))
        print(f"✅ PIT文件数: {len(pit_files)} 个")

        # 统计 PIT 表类型
        tables = {}
        for f in pit_files:
            # 提取表名（文件名格式：表名_年份.parquet）
            table_name = f.name.split("_")[0]
            tables[table_name] = tables.get(table_name, 0) + 1

        print(f"  📊 财务表类型: {len(tables)} 种")
        for table, count in sorted(tables.items())[:10]:
            print(f"    - {table}: {count} 个文件")

        # 总大小
        total_pit_size = sum(f.stat().st_size for f in pit_files) / 1024 / 1024
        print(f"  📊 总大小: {total_pit_size:.2f} MB ({total_pit_size/1024:.2f} GB)")

    # 各计划完成情况
    print("\n" + "=" * 80)
    print("各数据补充计划完成情况:")
    print("-" * 80)

    for plan_num, task_info in sorted(tasks.items(), key=lambda x: x[0]):
        status_symbol = "✅" if task_info["status"] == "completed" else "⏳"
        print(f"{status_symbol} 计划 {plan_num}: {task_info['status']}")

    # 缺失数据清单
    print("\n" + "=" * 80)
    print("缺失数据清单:")
    print("-" * 80)

    missing_items = [(name, r) for name, r in results.items() if not r["exists"]]

    if missing_items:
        for name, result in missing_items:
            print(f"❌ {name}: {result['path']}")
    else:
        print("✅ 所有关键数据文件都存在！")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_data_completeness()