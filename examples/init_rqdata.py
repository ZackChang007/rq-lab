"""
RQData 初始化示例

运行前确保：
1. pip install rqsdk
2. config/credentials.py 已配置好许可证密钥
"""

from config.credentials import RQSDK_LICENSE_KEY


def init_rqdata():
    """初始化 RQData"""
    import rqdatac

    # 方式一：直接传入许可证密钥
    rqdatac.init(RQSDK_LICENSE_KEY)

    # 验证连接
    info = rqdatac.info()
    print(f"RQData 版本: {info.get('version', 'N/A')}")
    print(f"服务器: {info.get('server', 'N/A')}")

    return rqdatac


def check_quota():
    """检查流量配额"""
    import rqdatac

    quota = rqdatac.user.get_quota()
    print(f"流量限额: {quota['bytes_limit'] / 1024 / 1024:.2f} MB")
    print(f"已用流量: {quota['bytes_used'] / 1024 / 1024:.2f} MB")
    print(f"剩余天数: {quota['remaining_days']} 天")
    print(f"授权类型: {quota['license_type']}")


if __name__ == "__main__":
    rqdatac = init_rqdata()
    check_quota()

    # 测试数据获取
    print("\n测试获取平安银行行情...")
    df = rqdatac.get_price("000001.XSHE", "2024-01-01", "2024-01-10")
    print(df.head())
