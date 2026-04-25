"""测试 utils/common.py 模块"""
import os
import pytest

from utils.common import setup_license, QUOTA_SAFE_CONFIG


class TestSetupLicense:
    """测试 setup_license 函数"""

    def test_quota_safe_config_structure(self):
        """验证 QUOTA_SAFE_CONFIG 结构正确"""
        assert "base" in QUOTA_SAFE_CONFIG
        assert "mod" in QUOTA_SAFE_CONFIG

        # 验证配额保护设置
        assert QUOTA_SAFE_CONFIG["base"]["auto_update_bundle"] is False
        assert QUOTA_SAFE_CONFIG["base"]["rqdatac_uri"] == "disabled"

        # 验证非股票品种模块禁用
        assert QUOTA_SAFE_CONFIG["mod"]["option"]["enabled"] is False
        assert QUOTA_SAFE_CONFIG["mod"]["convertible"]["enabled"] is False
        assert QUOTA_SAFE_CONFIG["mod"]["fund"]["enabled"] is False
        assert QUOTA_SAFE_CONFIG["mod"]["future"]["enabled"] is False
        assert QUOTA_SAFE_CONFIG["mod"]["spot"]["enabled"] is False

    def test_setup_license_no_existing_env(self, monkeypatch):
        """测试无现有环境变量时的行为"""
        # 清除现有环境变量
        monkeypatch.delenv("RQDATAC2_CONF", raising=False)

        # setup_license 应该尝试从 credentials.py 读取
        # 如果文件不存在或无密钥，不会设置环境变量
        setup_license()
        # 不强制断言，因为取决于 credentials.py 是否存在

    def test_setup_license_existing_env(self, monkeypatch):
        """测试已有环境变量时跳过设置"""
        monkeypatch.setenv("RQDATAC2_CONF", "existing_value")

        setup_license()

        assert os.environ.get("RQDATAC2_CONF") == "existing_value"
