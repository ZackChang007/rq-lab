"""详细检查 RQData 各品种数据权限"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.common import setup_license
import rqdatac

setup_license()
rqdatac.init()

print("=" * 70)
print("RQData 详细数据权限检查")
print("=" * 70)

# 1. 检查各品种 instruments
print("\n【1. 品种合约列表检查】")
instrument_types = ['CS', 'INDX', 'ETF', 'LOF', 'Fenji', 'FUND', 'Future', 'Option', 'Convertible', 'Bond']
for inst_type in instrument_types:
    try:
        df = rqdatac.all_instruments(type=inst_type)
        if df is not None and len(df) > 0:
            print(f"   ✅ {inst_type:12} - {len(df):5} 个合约")
        else:
            print(f"   ⚠️ {inst_type:12} - 返回空数据")
    except Exception as e:
        print(f"   ❌ {inst_type:12} - {str(e)[:40]}")

# 2. 检查核心数据 API
print("\n【2. 核心数据 API 检查】")
core_apis = [
    # 行情数据
    ('get_price (股票)', lambda: rqdatac.get_price('000001.XSHE', '2024-01-01', '2024-01-05', fields=['open', 'high', 'low', 'close', 'volume'])),
    ('get_price (指数)', lambda: rqdatac.get_price('000300.XSHG', '2024-01-01', '2024-01-05')),
    ('get_price (ETF)', lambda: rqdatac.get_price('510050.XSHG', '2024-01-01', '2024-01-05')),
    # 因子数据
    ('get_factor', lambda: rqdatac.get_factor('000001.XSHE', ['pe_ratio', 'pb_ratio', 'market_cap'], '2024-01-01', '2024-01-05')),
    ('get_factor_names', lambda: rqdatac.get_all_factor_names()),
    # 指数数据
    ('index_components', lambda: rqdatac.index_components('000300.XSHG', '2024-01-01')),
    ('index_weights', lambda: rqdatac.index_weights('000300.XSHG', '2024-01-01')),
    # 财务数据
    ('get_pit_financials', lambda: rqdatac.get_pit_financials_ex('000001.XSHE', 'income_statement', 'revenue', '2024-01-01', '2024-01-05')),
    # 风险因子
    ('get_factor_exposure', lambda: rqdatac.get_factor_exposure(['000001.XSHE'], '2024-01-01', '2024-01-05', model='risk_model_v1')),
    ('get_factor_return', lambda: rqdatac.get_factor_return('2024-01-01', '2024-01-05', model='risk_model_v1')),
]

for api_name, api_func in core_apis:
    try:
        result = api_func()
        if result is not None:
            if hasattr(result, '__len__'):
                print(f"   ✅ {api_name:25} - 返回 {len(result)} 行")
            else:
                print(f"   ✅ {api_name:25} - 可用")
        else:
            print(f"   ⚠️ {api_name:25} - 返回空")
    except Exception as e:
        err_msg = str(e)[:50]
        print(f"   ❌ {api_name:25} - {err_msg}")

# 3. 检查期货数据
print("\n【3. 期货数据检查】")
future_apis = [
    ('futures.get_contracts', lambda: rqdatac.futures.get_contracts('IF')),
    ('futures.get_dominant_contract', lambda: rqdatac.futures.get_dominant_contract('IF', '2024-01-01')),
    ('futures.get_basis', lambda: rqdatac.futures.get_basis('IF', '2024-01-01', '2024-01-05')),
]

for api_name, api_func in future_apis:
    try:
        result = api_func()
        if result is not None:
            if hasattr(result, '__len__'):
                print(f"   ✅ {api_name:30} - 返回 {len(result)} 行")
            else:
                print(f"   ✅ {api_name:30} - 可用")
        else:
            print(f"   ⚠️ {api_name:30} - 返回空")
    except Exception as e:
        err_msg = str(e)[:50]
        print(f"   ❌ {api_name:30} - {err_msg}")

# 4. 检查期权数据
print("\n【4. 期权数据检查】")
option_apis = [
    ('options.get_contracts', lambda: rqdatac.options.get_contracts('510050.XSHG')),
    ('options.get_greeks', lambda: rqdatac.options.get_greeks('510050.XSHG', '2024-01-01', '2024-01-05')),
]

for api_name, api_func in option_apis:
    try:
        result = api_func()
        if result is not None:
            if hasattr(result, '__len__'):
                print(f"   ✅ {api_name:30} - 返回 {len(result)} 行")
            else:
                print(f"   ✅ {api_name:30} - 可用")
        else:
            print(f"   ⚠️ {api_name:30} - 返回空")
    except Exception as e:
        err_msg = str(e)[:50]
        print(f"   ❌ {api_name:30} - {err_msg}")

# 5. 检查其他重要数据
print("\n【5. 其他重要数据检查】")
other_apis = [
    ('get_dividend', lambda: rqdatac.get_dividend('000001.XSHE', '2020-01-01', '2024-01-01')),
    ('get_split', lambda: rqdatac.get_split('000001.XSHE', '2020-01-01', '2024-01-01')),
    ('get_shares', lambda: rqdatac.get_shares('000001.XSHE', '2024-01-01', '2024-01-05')),
    ('get_securities_margin', lambda: rqdatac.get_securities_margin('000001.XSHE', '2024-01-01', '2024-01-05')),
    ('get_turnover_rate', lambda: rqdatac.get_turnover_rate('000001.XSHE', '2024-01-01', '2024-01-05')),
    ('get_stock_connect', lambda: rqdatac.get_stock_connect('000001.XSHE', '2024-01-01', '2024-01-05')),
    ('get_industry', lambda: rqdatac.get_industry('000001.XSHE', '2024-01-01')),
]

for api_name, api_func in other_apis:
    try:
        result = api_func()
        if result is not None:
            if hasattr(result, '__len__'):
                print(f"   ✅ {api_name:30} - 返回 {len(result)} 行")
            else:
                print(f"   ✅ {api_name:30} - 可用")
        else:
            print(f"   ⚠️ {api_name:30} - 返回空")
    except Exception as e:
        err_msg = str(e)[:50]
        print(f"   ❌ {api_name:30} - {err_msg}")

# 6. 检查新闻舆情
print("\n【6. 新闻舆情检查】")
try:
    news = rqdatac.news.get_stock_news('000001.XSHE', '2024-01-01', '2024-01-05')
    if news is not None and len(news) > 0:
        print(f"   ✅ news.get_stock_news - 返回 {len(news)} 条新闻")
    else:
        print("   ⚠️ news.get_stock_news - 返回空")
except Exception as e:
    print(f"   ❌ news.get_stock_news - {str(e)[:50]}")

# 7. 检查一致预期
print("\n【7. 一致预期数据检查】")
consensus_apis = [
    ('consensus.get_comp_indicators', lambda: rqdatac.consensus.get_comp_indicators(['000001.XSHE'], '2024-01-01', '2024-01-05')),
    ('consensus.get_indicator', lambda: rqdatac.consensus.get_indicator(['000001.XSHE'], fiscal_year=2024, date_rule='rpt_dt', start_date='2024-01-01', end_date='2024-01-05')),
]

for api_name, api_func in consensus_apis:
    try:
        result = api_func()
        if result is not None:
            if hasattr(result, '__len__'):
                print(f"   ✅ {api_name:35} - 返回 {len(result)} 行")
            else:
                print(f"   ✅ {api_name:35} - 可用")
        else:
            print(f"   ⚠️ {api_name:35} - 返回空")
    except Exception as e:
        err_msg = str(e)[:50]
        print(f"   ❌ {api_name:35} - {err_msg}")

print("\n" + "=" * 70)
print("检查完成")
print("=" * 70)
