"""检查已下载数据的时间范围"""
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_ROOT = Path('C:/gh/rq-lab/data')

def get_date_range(file_path):
    """获取 Parquet 文件的日期范围"""
    try:
        df = pd.read_parquet(file_path)
        if df.empty:
            return None, None

        dates = None

        # 处理 MultiIndex
        if isinstance(df.index, pd.MultiIndex):
            # 查找 date 或 datetime 或 trading_date 层级
            for name in df.index.names:
                if name in ['date', 'datetime', 'trading_date']:
                    dates = df.index.get_level_values(name)
                    break
            # 如果没找到，检查第二层（通常是日期）
            if dates is None and len(df.index.names) >= 2:
                level1 = df.index.get_level_values(1)
                try:
                    dates = pd.to_datetime(level1, errors='coerce')
                except:
                    pass
        elif isinstance(df.index, pd.DatetimeIndex):
            dates = df.index
        else:
            # 尝试从索引或列中找日期
            if 'date' in df.columns:
                dates = pd.to_datetime(df['date'], errors='coerce')
            elif 'trading_date' in df.columns:
                dates = pd.to_datetime(df['trading_date'], errors='coerce')
            elif 'datetime' in df.columns:
                dates = pd.to_datetime(df['datetime'], errors='coerce')
            elif 'info_date' in df.columns:
                dates = pd.to_datetime(df['info_date'], errors='coerce')
            else:
                try:
                    dates = pd.to_datetime(df.index, errors='coerce')
                except:
                    pass

        if dates is not None:
            dates = pd.to_datetime(dates, errors='coerce')
            dates = dates.dropna()
            if not dates.empty:
                min_date = dates.min()
                max_date = dates.max()
                if pd.notna(min_date) and pd.notna(max_date):
                    return min_date.strftime('%Y-%m-%d'), max_date.strftime('%Y-%m-%d')

        return None, None
    except Exception as e:
        return None, None

results = []

# 1. A股日线行情
p = DATA_ROOT / 'stock/price_1d.parquet'
if p.exists():
    start, end = get_date_range(p)
    results.append(('A股日线行情', p.name, start, end))

# 2. A股PIT财务数据
pit_dir = DATA_ROOT / 'stock/pit_financials'
if pit_dir.exists():
    all_dates = []
    for f in sorted(pit_dir.glob('*.parquet')):
        df = pd.read_parquet(f)
        if 'info_date' in df.columns:
            dates = pd.to_datetime(df['info_date'], errors='coerce').dropna()
            all_dates.extend(dates.tolist())
    if all_dates:
        min_date = pd.to_datetime(all_dates).min()
        max_date = pd.to_datetime(all_dates).max()
        results.append(('A股PIT财务数据', '22个年度文件', min_date.strftime('%Y-%m-%d'), max_date.strftime('%Y-%m-%d')))

# 3. 因子数据
factor_dir = DATA_ROOT / 'factor'
if factor_dir.exists():
    sample_files = list(factor_dir.glob('*.parquet'))[:20]
    all_dates = []
    for f in sample_files:
        df = pd.read_parquet(f)
        if isinstance(df.index, pd.MultiIndex):
            for name in df.index.names:
                if name == 'date':
                    dates = pd.to_datetime(df.index.get_level_values(name), errors='coerce').dropna()
                    all_dates.extend(dates.tolist())
        elif isinstance(df.index, pd.DatetimeIndex):
            all_dates.extend(df.index.tolist())
    if all_dates:
        total = len(list(factor_dir.glob('*.parquet')))
        min_date = pd.to_datetime(all_dates).min()
        max_date = pd.to_datetime(all_dates).max()
        results.append(('因子数据', f'{total}个因子', min_date.strftime('%Y-%m-%d'), max_date.strftime('%Y-%m-%d')))

# 4. 指数日线行情
p = DATA_ROOT / 'index/price_1d.parquet'
if p.exists():
    start, end = get_date_range(p)
    results.append(('指数日线行情', p.name, start, end))

# 5. 指数权重
weights_dir = DATA_ROOT / 'index/weights'
if weights_dir.exists():
    sample_files = list(weights_dir.glob('*.parquet'))
    all_dates = []
    for f in sample_files:
        df = pd.read_parquet(f)
        if isinstance(df.index, pd.DatetimeIndex):
            all_dates.extend(df.index.tolist())
        elif isinstance(df.index, pd.MultiIndex):
            dates = df.index.get_level_values(0)
            all_dates.extend(pd.to_datetime(dates, errors='coerce').dropna().tolist())
    if all_dates:
        min_date = pd.to_datetime(all_dates).min()
        max_date = pd.to_datetime(all_dates).max()
        results.append(('指数权重', f'{len(sample_files)}个指数', min_date.strftime('%Y-%m-%d'), max_date.strftime('%Y-%m-%d')))

# 6. 期货日线行情
p = DATA_ROOT / 'futures/price_1d.parquet'
if p.exists():
    start, end = get_date_range(p)
    results.append(('期货日线行情', p.name, start, end))

# 7. 期货主力合约
futures_dir = DATA_ROOT / 'futures'
dominant_files = list(futures_dir.glob('dominant_*.parquet'))
if dominant_files:
    all_dates = []
    for f in dominant_files:
        df = pd.read_parquet(f)
        if isinstance(df.index, pd.DatetimeIndex):
            all_dates.extend(df.index.tolist())
    if all_dates:
        min_date = pd.to_datetime(all_dates).min()
        max_date = pd.to_datetime(all_dates).max()
        results.append(('期货主力合约', f'{len(dominant_files)}品种', min_date.strftime('%Y-%m-%d'), max_date.strftime('%Y-%m-%d')))

# 8. 期货展期收益
p = DATA_ROOT / 'futures/roll_yield.parquet'
if p.exists():
    start, end = get_date_range(p)
    results.append(('期货展期收益', p.name, start, end))

# 9. 可转债日线行情
cb_dir = DATA_ROOT / 'convertible'
cb_files = list(cb_dir.glob('price_1d_*.parquet'))
if cb_files:
    start, end = get_date_range(cb_dir / cb_files[0])
    results.append(('可转债日线行情', f'{len(cb_files)}个文件', start, end))

# 10. 可转债指标
p = DATA_ROOT / 'convertible/indicators.parquet'
if p.exists():
    start, end = get_date_range(p)
    results.append(('可转债估值指标', p.name, start, end))

# 11. 基金净值
p = DATA_ROOT / 'fund/nav.parquet'
if p.exists():
    start, end = get_date_range(p)
    results.append(('基金净值数据', p.name, start, end))

# 12. 风险因子暴露
p = DATA_ROOT / 'risk_factor/factor_exposure_v1.parquet'
if p.exists():
    start, end = get_date_range(p)
    results.append(('风险因子暴露v1', p.name, start, end))

p = DATA_ROOT / 'risk_factor/factor_exposure_v2.parquet'
if p.exists():
    start, end = get_date_range(p)
    results.append(('风险因子暴露v2', p.name, start, end))

# 13. 风险因子收益
p = DATA_ROOT / 'risk_factor/factor_return.parquet'
if p.exists():
    start, end = get_date_range(p)
    results.append(('风险因子收益', p.name, start, end))

# 14. 风险因子协方差
cov_dir = DATA_ROOT / 'risk_factor/factor_covariance'
if cov_dir.exists():
    cov_files = sorted(cov_dir.glob('*.parquet'))
    if cov_files:
        first_date = cov_files[0].stem.replace('factor_covariance_', '')
        last_date = cov_files[-1].stem.replace('factor_covariance_', '')
        results.append(('风险因子协方差', f'{len(cov_files)}个月度文件', first_date, last_date))

# 15. 宏观因子
p = DATA_ROOT / 'macro/factors/all_factors.parquet'
if p.exists():
    start, end = get_date_range(p)
    results.append(('宏观因子数据', p.name, start, end))

# 16. 一致预期
p = DATA_ROOT / 'alternative/consensus/comp_indicators.parquet'
if p.exists():
    start, end = get_date_range(p)
    results.append(('一致预期综合指标', p.name, start, end))

# 17. 资金流向
p = DATA_ROOT / 'stock/capital_flow.parquet'
if p.exists():
    start, end = get_date_range(p)
    results.append(('A股资金流向', p.name, start, end))

# 18. 融资融券
p = DATA_ROOT / 'stock/securities_margin.parquet'
if p.exists():
    start, end = get_date_range(p)
    results.append(('A股融资融券', p.name, start, end))

# 19. 收益率曲线
p = DATA_ROOT / 'yield_curve/yield_curve.parquet'
if p.exists():
    start, end = get_date_range(p)
    results.append(('收益率曲线', p.name, start, end))

# 20. ETF行情
etf_dir = DATA_ROOT / 'etf'
etf_files = list(etf_dir.glob('price_1d_*.parquet'))
if etf_files:
    start, end = get_date_range(etf_dir / etf_files[0])
    results.append(('ETF日线行情', f'{len(etf_files)}个文件', start, end))

# 21. LOF行情
lof_dir = DATA_ROOT / 'lof'
lof_files = list(lof_dir.glob('price_1d_*.parquet'))
if lof_files:
    start, end = get_date_range(lof_dir / lof_files[0])
    results.append(('LOF日线行情', f'{len(lof_files)}个文件', start, end))

# 输出结果
print('=' * 88)
print('本地已下载数据时间范围汇总（排除分钟级数据）')
print('=' * 88)
print(f'{"数据类别":<20} {"文件说明":<25} {"开始日期":<12} {"结束日期":<12}')
print('-' * 88)
for name, file, start, end in results:
    start_str = start if start else 'N/A'
    end_str = end if end else 'N/A'
    print(f'{name:<20} {file:<25} {start_str:<12} {end_str:<12}')
print('=' * 88)