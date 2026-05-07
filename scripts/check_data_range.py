"""检查本地已下载数据的时间范围"""
import pandas as pd
import os
import json
from pathlib import Path

def format_date(date_val):
    """格式化日期值，处理多种类型"""
    if isinstance(date_val, pd.Timestamp):
        return date_val.strftime('%Y-%m-%d')
    elif isinstance(date_val, str):
        # 字符串格式如 '20140102' -> '2014-01-02'
        if len(date_val) == 8 and date_val.isdigit():
            return f'{date_val[:4]}-{date_val[4:6]}-{date_val[6:8]}'
        return date_val
    elif hasattr(date_val, 'strftime'):
        return date_val.strftime('%Y-%m-%d')
    return str(date_val)

def get_date_range_from_parquet(filepath):
    """从 Parquet 文件获取日期范围（处理 MultiIndex 情况）"""
    df = pd.read_parquet(filepath)

    # 检查是否是 MultiIndex
    if isinstance(df.index, pd.MultiIndex):
        # 找到日期级别的索引
        for name in ['date', 'trade_date', 'trading_date', 'ex_dividend_date',
                     'declaration_announcement_date', 'info_date']:
            if name in df.index.names:
                idx = df.index.get_level_values(name)
                return format_date(idx.min()), format_date(idx.max())
        # 如果没找到，使用最后一个级别（通常是日期）
        idx = df.index.get_level_values(-1)
        return format_date(idx.min()), format_date(idx.max())
    elif isinstance(df.index, pd.DatetimeIndex):
        return format_date(df.index.min()), format_date(df.index.max())

    return None, None

results = []

# ============ 股票数据 ============
# 1. A股日线（分年文件）
price_files = list(Path('data/stock').glob('price_1d_*.parquet'))
if price_files:
    all_dates = []
    for f in price_files:
        min_d, max_d = get_date_range_from_parquet(f)
        if min_d:
            all_dates.append(min_d)
            all_dates.append(max_d)
    if all_dates:
        results.append(['A股日线行情', '上市以来', f'{min(all_dates)} ~ {max(all_dates)}', '完整'])

# 2. PIT财务（分年文件）
pit_files = sorted(Path('data/stock/pit_financials').glob('*.parquet'))
if pit_files:
    years = [f.stem.split('_')[-1] for f in pit_files]
    results.append(['PIT财务数据', '上市以来(2005+)', f'{min(years)} ~ {max(years)}', '完整'])

# 3. 资金流向
if os.path.exists('data/stock/capital_flow.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/stock/capital_flow.parquet')
    if min_d:
        results.append(['资金流向', '2020年初至今', f'{min_d} ~ {max_d}', '完整'])

# 4. 分红数据
if os.path.exists('data/stock/dividend.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/stock/dividend.parquet')
    if min_d:
        results.append(['分红数据', '上市以来', f'{min_d} ~ {max_d}', '完整'])

# 5. 拆股数据
if os.path.exists('data/stock/split.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/stock/split.parquet')
    if min_d:
        results.append(['拆股数据', '上市以来', f'{min_d} ~ {max_d}', '完整'])

# 6. 股本数据
if os.path.exists('data/stock/shares.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/stock/shares.parquet')
    if min_d:
        results.append(['股本数据', '上市以来', f'{min_d} ~ {max_d}', '完整'])

# 7. 换手率
if os.path.exists('data/stock/turnover_rate.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/stock/turnover_rate.parquet')
    if min_d:
        results.append(['换手率', '上市以来', f'{min_d} ~ {max_d}', '完整'])

# 8. 停牌数据
if os.path.exists('data/stock/suspended.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/stock/suspended.parquet')
    if min_d:
        results.append(['停牌数据', '上市以来', f'{min_d} ~ {max_d}', '完整'])

# 9. ST股票
if os.path.exists('data/stock/st_stock.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/stock/st_stock.parquet')
    if min_d:
        results.append(['ST股票列表', '上市以来', f'{min_d} ~ {max_d}', '完整'])

# 10. 融资融券
if os.path.exists('data/stock/securities_margin.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/stock/securities_margin.parquet')
    if min_d:
        results.append(['融资融券', '2010-03-31至今', f'{min_d} ~ {max_d}', '完整'])

# 11. 行业分类
if os.path.exists('data/stock/instrument_industry.parquet'):
    df = pd.read_parquet('data/stock/instrument_industry.parquet')
    if 'date' in df.columns:
        dates = pd.to_datetime(df['date'])
        results.append(['行业分类', '上市以来', f'{dates.min().strftime("%Y-%m-%d")} ~ {dates.max().strftime("%Y-%m-%d")}', '完整'])
    else:
        results.append(['行业分类', '上市以来', '已下载(静态数据)', '完整'])

# ============ 指数数据 ============
# 12. 指数日线
if os.path.exists('data/index/price_1d.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/index/price_1d.parquet')
    if min_d:
        results.append(['指数日线', '10+年历史', f'{min_d} ~ {max_d}', '完整'])

# 13. 指数权重
weight_files = list(Path('data/index/weights').glob('*.parquet'))
if weight_files:
    all_dates = []
    for f in weight_files:
        min_d, max_d = get_date_range_from_parquet(f)
        if min_d:
            all_dates.extend([min_d, max_d])
    if all_dates:
        results.append(['指数成分股权重', '指数成立以来', f'{min(all_dates)} ~ {max(all_dates)}', '完整'])

# ============ 期货数据 ============
# 14. 期货主力合约
futures_files = list(Path('data/futures').glob('dominant_*.parquet'))
if futures_files:
    all_dates = []
    for f in futures_files:
        min_d, max_d = get_date_range_from_parquet(f)
        if min_d:
            all_dates.extend([min_d, max_d])
    if all_dates:
        results.append(['期货主力合约', '历史数据', f'{min(all_dates)} ~ {max(all_dates)}', '完整'])

# 15. 期货仓单
if os.path.exists('data/futures/warehouse_stocks.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/futures/warehouse_stocks.parquet')
    if min_d:
        results.append(['期货仓单数据', '历史数据', f'{min_d} ~ {max_d}', '完整'])

# 16. 期货会员排名
if os.path.exists('data/futures/member_rank.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/futures/member_rank.parquet')
    if min_d:
        results.append(['期货会员排名', '历史数据', f'{min_d} ~ {max_d}', '完整'])

# 17. 展期收益
if os.path.exists('data/futures/roll_yield.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/futures/roll_yield.parquet')
    if min_d:
        results.append(['期货展期收益', '历史数据', f'{min_d} ~ {max_d}', '完整'])

# ============ 可转债数据 ============
# 18. 可转债日线
conv_files = list(Path('data/convertible').glob('price_1d_*.parquet'))
if conv_files:
    all_dates = []
    for f in conv_files:
        min_d, max_d = get_date_range_from_parquet(f)
        if min_d:
            all_dates.extend([min_d, max_d])
    if all_dates:
        results.append(['可转债日线', '历史数据', f'{min(all_dates)} ~ {max(all_dates)}', '完整'])

# 19. 可转债估值指标
if os.path.exists('data/convertible/indicators.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/convertible/indicators.parquet')
    if min_d:
        results.append(['可转债估值指标', '历史数据', f'{min_d} ~ {max_d}', '完整'])

# ============ 基金数据 ============
# 20. 基金净值
if os.path.exists('data/fund/nav.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/fund/nav.parquet')
    if min_d:
        results.append(['基金净值', '历史数据', f'{min_d} ~ {max_d}', '完整'])

# ============ ETF/LOF数据 ============
# 21. ETF日线
etf_files = list(Path('data/etf').glob('price_1d_*.parquet'))
if etf_files:
    all_dates = []
    for f in etf_files:
        min_d, max_d = get_date_range_from_parquet(f)
        if min_d:
            all_dates.extend([min_d, max_d])
    if all_dates:
        results.append(['ETF日线', '10+年历史', f'{min(all_dates)} ~ {max(all_dates)}', '完整'])

# 22. LOF日线
lof_files = list(Path('data/lof').glob('price_1d_*.parquet'))
if lof_files:
    all_dates = []
    for f in lof_files:
        min_d, max_d = get_date_range_from_parquet(f)
        if min_d:
            all_dates.extend([min_d, max_d])
    if all_dates:
        results.append(['LOF日线', '10+年历史', f'{min(all_dates)} ~ {max(all_dates)}', '完整'])

# ============ 其他数据 ============
# 23. 国债收益率曲线
if os.path.exists('data/yield_curve/yield_curve.parquet'):
    min_d, max_d = get_date_range_from_parquet('data/yield_curve/yield_curve.parquet')
    if min_d:
        results.append(['国债收益率曲线', '2002年至今', f'{min_d} ~ {max_d}', '完整'])

# 24. 交易日历
with open('data/calendar/trading_dates.json', 'r') as f:
    dates = json.load(f)
results.append(['交易日历', '2005至今', f'{dates[0]} ~ {dates[-1]}', '完整'])

# ============ 因子数据 ============
factor_files = list(Path('data/factor').glob('*.parquet'))

# TTM因子
ttm_files = [f for f in factor_files if '_ttm_' in f.name.lower()]
if ttm_files:
    min_d, max_d = get_date_range_from_parquet(ttm_files[0])
    if min_d:
        results.append(['财务因子(TTM)', '2020年至今', f'{min_d} ~ {max_d}', '完整(359个)'])

# LYR因子
lyr_files = [f for f in factor_files if '_lyr_' in f.name.lower()]
if lyr_files:
    min_d, max_d = get_date_range_from_parquet(lyr_files[0])
    if min_d:
        results.append(['财务因子(LYR)', '2020年至今', f'{min_d} ~ {max_d}', '完整(359个)'])

# MRQ因子
mrq_files = [f for f in factor_files if '_mrq_' in f.name.lower()]
if mrq_files:
    min_d, max_d = get_date_range_from_parquet(mrq_files[0])
    if min_d:
        results.append(['财务因子(MRQ)', '2020年至今', f'{min_d} ~ {max_d}', '完整(359个)'])

# 估值因子
valuation_factors = ['pe_', 'pb_', 'ps_', 'pcf_']
val_files = [f for f in factor_files if any(f.name.startswith(x) for x in valuation_factors)]
if val_files:
    min_d, max_d = get_date_range_from_parquet(val_files[0])
    if min_d:
        results.append(['估值因子', '2020年至今', f'{min_d} ~ {max_d}', '完整(23个)'])

# 技术因子 - 统计数量
all_factor_names = set(f.stem.rsplit('_', 2)[0] for f in factor_files)
non_financial_factors = [f for f in factor_files
                         if not any(x in f.name.lower() for x in ['_ttm_', '_lyr_', '_mrq_'])
                         and not any(f.name.startswith(x) for x in valuation_factors)]
tech_count = len(set(f.stem for f in non_financial_factors))
if tech_count > 0:
    results.append(['技术因子', '历史数据', f'已下载 {tech_count} 个常用因子', '部分'])

# ============ 不可用数据（试用限制）===============
unavailable = [
    ['新闻舆情数据', '需更高级权限', '模块不可用', '不可用'],
    ['ESG评级数据', '需更高级权限', '模块不可用', '不可用'],
    ['宏观全量数据', '需更高级权限', '模块不可用', '不可用'],
    ['期权希腊值', '试用返回空', '返回空数据', '不可用'],
    ['行业资金流向', '需更高级权限', '模块不可用', '不可用'],
]
results.extend(unavailable)

# 打印结果
print("=" * 110)
print(f"{'数据类型':<20} | {'API允许时间范围':<20} | {'本地已下载范围':<40} | {'状态':<10}")
print("=" * 110)
for row in results:
    print(f"{row[0]:<20} | {row[1]:<20} | {row[2]:<40} | {row[3]:<10}")
print("=" * 110)
