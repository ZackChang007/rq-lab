"""数据完整性详细检查脚本"""

import pandas as pd
from pathlib import Path
import json
from datetime import datetime
from collections import defaultdict

DATA_DIR = Path("data")

def check_file_time_range(file_path, date_cols=None):
    """检查文件的时间范围"""
    try:
        df = pd.read_parquet(file_path)

        # 尝试找到时间列
        time_range = None
        time_col_found = None

        # 1. 检查指定的时间列
        if date_cols:
            for col in date_cols:
                if col in df.columns:
                    try:
                        if df[col].dtype == 'datetime64[ns]' or 'datetime' in str(df[col].dtype):
                            time_range = (str(df[col].min())[:10], str(df[col].max())[:10])
                            time_col_found = col
                            break
                    except:
                        pass

        # 2. 检查索引
        if time_range is None and hasattr(df.index, 'name') and df.index.name:
            idx_name = str(df.index.name).lower()
            if 'date' in idx_name or 'time' in idx_name:
                try:
                    time_range = (str(df.index.min())[:10], str(df.index.max())[:10])
                    time_col_found = f"index:{df.index.name}"
                except:
                    pass

        # 3. 自动检测时间列
        if time_range is None:
            for col in df.columns:
                col_lower = str(col).lower()
                if 'date' in col_lower or 'time' in col_lower:
                    try:
                        if df[col].dtype == 'datetime64[ns]' or 'datetime' in str(df[col].dtype):
                            time_range = (str(df[col].min())[:10], str(df[col].max())[:10])
                            time_col_found = col
                            break
                    except:
                        pass

        return {
            'rows': len(df),
            'cols': len(df.columns),
            'time_col': time_col_found,
            'start': time_range[0] if time_range else None,
            'end': time_range[1] if time_range else None,
        }
    except Exception as e:
        return {'error': str(e)[:50]}

def check_category(category_path, expected_files=None, date_cols=None):
    """检查一个数据类别的完整性"""
    p = Path(category_path)
    if not p.exists():
        return {'status': 'NOT_EXISTS', 'path': str(p)}

    files = list(p.glob('*.parquet')) + list(p.glob('*.json'))

    results = {
        'path': str(p),
        'file_count': len(files),
        'total_size_mb': sum(f.stat().st_size for f in files) / 1024 / 1024,
        'files': {}
    }

    for f in sorted(files)[:10]:  # 只检查前10个文件的详细信息
        info = check_file_time_range(f, date_cols)
        info['size_mb'] = round(f.stat().st_size / 1024 / 1024, 2)
        results['files'][f.name] = info

    # 如果有预期文件列表，检查缺失
    if expected_files:
        existing = set(f.name for f in files)
        missing = set(expected_files) - existing
        results['missing'] = list(missing)

    return results

def main():
    print("=" * 80)
    print("数据完整性详细检查报告")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 定义检查配置
    checks = [
        # (类别名, 路径, 预期文件列表, 时间列名)
        ("合约基本信息", "data/instruments", None, None),
        ("交易日历", "data/calendar", ["trading_dates.json"], None),
        ("收益率曲线", "data/yield_curve", None, None),

        # A股数据
        ("A股-分红", "data/stock", None, None),
        ("A股-PIT财务", "data/stock/pit_financials", None, "info_date"),

        # 因子数据
        ("因子-膨胀因子", "data/factor", None, None),
        ("因子-早期因子", "data/factor_early", None, None),

        # 指数数据
        ("指数-成分股", "data/index/components", None, None),
        ("指数-权重", "data/index/weights", None, None),

        # 期货数据
        ("期货数据", "data/futures", None, None),

        # 期权数据
        ("期权数据", "data/options", None, None),

        # 可转债数据
        ("可转债数据", "data/convertible", None, None),

        # 基金数据
        ("公募基金", "data/fund", None, None),

        # 风险因子
        ("风险因子", "data/risk_factor", None, None),

        # 宏观数据
        ("宏观数据", "data/macro", None, None),

        # 另类数据
        ("另类数据", "data/alternative", None, None),
    ]

    all_results = {}

    for name, path, expected, date_cols in checks:
        print(f"\n【{name}】")
        result = check_category(path, expected, date_cols)
        all_results[name] = result

        print(f"  路径: {result['path']}")
        print(f"  文件数: {result['file_count']}")
        print(f"  总大小: {result['total_size_mb']:.1f} MB")

        if result['files']:
            print(f"  文件详情:")
            for fname, info in list(result['files'].items())[:5]:
                if 'error' in info:
                    print(f"    - {fname}: ERROR {info['error']}")
                else:
                    time_info = f" [{info['start']} ~ {info['end']}]" if info.get('start') else ""
                    print(f"    - {fname}: {info['rows']} 行{time_info}")

        if result.get('missing'):
            print(f"  ⚠️ 缺失文件: {result['missing'][:5]}")

    # 特别检查：因子数据完整性
    print("\n" + "=" * 80)
    print("【因子数据完整性专项检查】")
    print("=" * 80)

    factor_dir = Path("data/factor")
    factor_files = list(factor_dir.glob("*.parquet"))

    # 统计各类因子
    suffix_stats = defaultdict(int)
    base_factors = set()

    import re
    for f in factor_files:
        name = f.stem
        # 提取基础因子名
        match = re.match(r'^(.+?)_(lyr|mrq|ttm|ttm1)_\d+$', name)
        if match:
            base = match.group(1)
            base_factors.add(base)
            suffix_stats[re.search(r'_(lyr|mrq|ttm|ttm1)_\d+$', name).group()] += 1
        elif not re.search(r'_(lyr|mrq|ttm|ttm1)_\d+$', name):
            # 非膨胀因子
            suffix_stats['[无后缀]'] += 1

    print(f"\n因子文件总数: {len(factor_files)}")
    print(f"基础因子数: {len(base_factors)}")
    print(f"\n膨胀因子后缀统计:")
    for suffix, count in sorted(suffix_stats.items()):
        print(f"  {suffix}: {count} 个文件")

    # 检查膨胀因子完整性 (预期: 每种后缀359个基础因子 × 9个年份 = 若干文件)
    print(f"\n膨胀因子预期数量:")
    print(f"  _lyr_0 ~ _lyr_8: 预期 359 × 9 = 3,231")
    print(f"  _mrq_0 ~ _mrq_11: 预期 359 × 12 = 4,308")
    print(f"  _ttm_0 ~ _ttm_8: 预期 359 × 9 = 3,231")
    print(f"  _ttm1_0 ~ _ttm1_8: 预期 170 × 9 = 1,530")

    # 检查时间范围
    print(f"\n抽样检查因子时间范围:")
    sample_files = ['pe_ratio_lyr_0.parquet', 'pe_ratio_mrq_0.parquet', 'pe_ratio_ttm_0.parquet']
    for fname in sample_files:
        fp = factor_dir / fname
        if fp.exists():
            try:
                df = pd.read_parquet(fp)
                # 尝试获取时间
                if df.index.name and 'date' in str(df.index.name).lower():
                    print(f"  {fname}: {df.index.min()} ~ {df.index.max()}")
                elif 'date' in df.columns:
                    print(f"  {fname}: {df['date'].min()} ~ {df['date'].max()}")
                else:
                    print(f"  {fname}: {len(df)} 行, 列: {list(df.columns)[:3]}")
            except Exception as e:
                print(f"  {fname}: ERROR {e}")
        else:
            print(f"  {fname}: 不存在")

    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)

if __name__ == "__main__":
    main()
