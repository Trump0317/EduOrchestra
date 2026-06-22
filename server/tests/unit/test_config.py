# 测试行为：
# - test_config_defaults: 无环境变量时使用默认值（provider=deepseek, model=deepseek-chat）
# - test_config_validates_missing_key: 缺 API Key 时 validate() 返回缺失列表
# - test_config_dict: dict() 返回 provider/model/has_api_key，不暴露 api_key
import os
import pytest
from unittest.mock import patch


# load_dotenv 在模块加载时会重置环境变量，影响 env 测试，全部 mock 掉
@pytest.fixture(autouse=True)
def mock_load_dotenv():
    with patch("config.load_dotenv"):
        yield


class TestConfig:
    def test_config_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            from importlib import reload
            import config

            reload(config)
            assert config.config.LLM_PROVIDER == "deepseek"
            assert config.config.LLM_MODEL == "deepseek-chat"

    def test_config_validates_missing_key(self):
        with patch.dict(os.environ, {"LLM_API_KEY": ""}, clear=True):
            from importlib import reload
            import config

            reload(config)
            missing = config.config.validate()
            assert "LLM_API_KEY" in missing

    def test_config_dict(self):
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "openai",
                "LLM_API_KEY": "sk-test",
                "LLM_MODEL": "gpt-4o",
            },
            clear=True,
        ):
            from importlib import reload
            import config

            reload(config)
            d = config.config.dict()
            assert d["provider"] == "openai"
            assert d["has_api_key"] is True
            assert d["model"] == "gpt-4o"
            # API Key 不应暴露在 dict 中
            assert "api_key" not in d
