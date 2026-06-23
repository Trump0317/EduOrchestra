import sys
from pathlib import Path

# 确保 server/ 在 Python 路径中，以便 from main import app 生效
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import pytest


@pytest.fixture(autouse=True)
def _reset_config_after_test():
    """自动备份并恢复全局 config，防止测试间通过 PUT /api/config 污染。

    test_update_config 等测试会修改 config.LLM_MODEL 等字段，
    如果不恢复，后续测试会看到被污染的配置。
    """
    from config import config as app_config

    backup = {
        "provider": app_config.LLM_PROVIDER,
        "api_key": app_config.LLM_API_KEY,
        "model": app_config.LLM_MODEL,
    }
    yield
    app_config.LLM_PROVIDER = backup["provider"]
    app_config.LLM_API_KEY = backup["api_key"]
    app_config.LLM_MODEL = backup["model"]
