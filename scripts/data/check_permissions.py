"""检查 RQData 账户权限和可用 API"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.common import setup_license
import rqdatac

# 初始化许可证
setup_license()
rqdatac.init()

print("=" * 60)
print("RQData 账户权限检查")
print("=" * 60)

# 1. 检查可用模块
print("\n1. 可用模块:")
modules = [m for m in dir(rqdatac) if not m.startswith('_') and not m.isupper()]
for m in sorted(modules):
    obj = getattr(rqdatac, m)
    if hasattr(obj, '__module__') and 'rqdatac' in str(obj.__module__):
        print(f"   - {m} (模块)")
    elif callable(obj):
        print(f"   - {m}()")

# 2. 检查子模块
print("\n2. 子模块详情:")
submodules = ['futures', 'options', 'bond', 'fund', 'econ', 'consensus', 'news']
for sm in submodules:
    if hasattr(rqdatac, sm):
        obj = getattr(rqdatac, sm)
        methods = [m for m in dir(obj) if not m.startswith('_') and callable(getattr(obj, m, None))]
        print(f"   - rqdatac.{sm}: {len(methods)} 个方法")
        for method in methods[:5]:  # 只显示前5个
            print(f"       .{method}()")
        if len(methods) > 5:
            print(f"       ... 还有 {len(methods) - 5} 个")

# 3. 测试核心 API 可用性
print("\n3. 核心 API 测试:")
test_apis = [
    ('get_price', lambda: rqdatac.get_price('000001.XSHE', start_date='2024-01-01', end_date='2024-01-05')),
    ('get_factor', lambda: rqdatac.get_factor('000001.XSHE', 'pe_ratio', start_date='2024-01-01', end_date='2024-01-05')),
    ('index_weights', lambda: rqdatac.index_weights('000300.XSHG', '2024-01-01')),
    ('get_trading_dates', lambda: rqdatac.get_trading_dates(start_date='2024-01-01', end_date='2024-01-05')),
]

for api_name, api_func in test_apis:
    try:
        result = api_func()
        if result is not None and len(result) > 0:
            print(f"   ✅ {api_name}: 可用 (返回 {len(result)} 行)")
        else:
            print(f"   ⚠️ {api_name}: 返回空数据")
    except Exception as e:
        print(f"   ❌ {api_name}: {str(e)[:50]}")

# 4. 检查特殊模块
print("\n4. 特殊模块检查:")
special_checks = [
    ('esg', 'ESG评级'),
    ('news', '新闻舆情'),
    ('social', '社交数据'),
]

for module_name, desc in special_checks:
    if hasattr(rqdatac, module_name):
        print(f"   ✅ {desc}: 存在")
    else:
        print(f"   ❌ {desc}: 不存在")

# 5. 检查可下载的数据类型
print("\n5. all_instruments 类型测试:")
try:
    all_inst = rqdatac.all_instruments()
    types = all_inst['order_book_id'].str.split('.').str[1].unique()
    print(f"   可用品种: {list(types)}")
except Exception as e:
    print(f"   ❌ 获取失败: {str(e)[:50]}")

print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)
