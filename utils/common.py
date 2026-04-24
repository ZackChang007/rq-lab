"""共享工具：许可证初始化 + 配额保护默认配置"""
import os
from pathlib import Path

_CREDENTIALS_FILE = Path(__file__).resolve().parent.parent / "config" / "credentials.py"


def setup_license() -> None:
    """设置 RQDATAC2_CONF 环境变量，从 config/credentials.py 读取密钥。"""
    if os.environ.get("RQDATAC2_CONF"):
        return
    if _CREDENTIALS_FILE.exists():
        import importlib.util

        spec = importlib.util.spec_from_file_location("credentials", str(_CREDENTIALS_FILE))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            key = getattr(mod, "RQSDK_LICENSE_KEY", "")
            if key:
                os.environ["RQDATAC2_CONF"] = f"tcp://license:{key}@rqdatad-pro.ricequant.com:16011"


# 配额保护默认配置（试用账号）
QUOTA_SAFE_CONFIG = {
    "base": {
        "auto_update_bundle": False,
        "rqdatac_uri": "disabled",
    },
    "mod": {
        "option": {"enabled": False},
        "convertible": {"enabled": False},
        "fund": {"enabled": False},
        "future": {"enabled": False},
        "spot": {"enabled": False},
    },
}
