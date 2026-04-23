"""测试 RQData 连接"""
import rqdatac

rqdatac.init()
print('连接成功!')

quota = rqdatac.user.get_quota()
print()
print('流量限额: {:.0f} MB'.format(quota['bytes_limit']/1024/1024))
print('已用流量: {:.2f} MB'.format(quota['bytes_used']/1024/1024))
print('剩余流量: {:.2f} MB'.format((quota['bytes_limit']-quota['bytes_used'])/1024/1024))
print('剩余天数:', quota['remaining_days'])
print('授权类型:', quota['license_type'])
