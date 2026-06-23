# server/tests/unit/test_llm.py
# 测试行为：
# - test_get_llm_raises_on_missing_key: 无 API Key 时抛出 ValueError
# - test_get_llm_returns_chatopenai: 有 API Key 时返回 ChatOpenAI 实例
# - test_llm_invoke_returns_string: mock invoke 返回 str
# - test_llm_invoke_json_parses_valid: mock 返回 JSON 文本，正确解析
# - test_llm_invoke_json_handles_code_block: mock 返回 ```json 块，正确解析
# - test_llm_invoke_json_raises_on_invalid: mock 返回无 JSON 文本，抛出 ValueError

import os
from importlib import reload
from unittest.mock import patch, MagicMock

import pytest


class TestGetLLM:
    def test_raises_on_missing_key(self):
        """缺 API Key 时抛出 ValueError"""
        with patch.dict(os.environ, {"LLM_API_KEY": ""}, clear=True):
            import config
            reload(config)
            import orchestrator.llm as llm_mod
            reload(llm_mod)
            with pytest.raises(ValueError, match="LLM_API_KEY"):
                llm_mod.get_llm()

    def test_returns_chatopenai_with_valid_config(self):
        """有 API Key 时返回 ChatOpenAI 实例"""
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": "sk-test",
        }, clear=True):
            import config
            reload(config)
            import orchestrator.llm as llm_mod
            reload(llm_mod)
            llm = llm_mod.get_llm()
            from langchain_openai import ChatOpenAI
            assert isinstance(llm, ChatOpenAI)


class TestLLMInvoke:
    def test_invoke_returns_string(self):
        """llm_invoke 返回 LLM 输出的字符串，并正确传递 prompt"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="hello world")

        import orchestrator.llm as llm_mod
        with patch.object(llm_mod, "get_llm", return_value=mock_llm):
            result = llm_mod.llm_invoke("test prompt")
        assert result == "hello world"
        mock_llm.invoke.assert_called_once_with("test prompt")

    def test_invoke_json_parses_valid_json(self):
        """llm_invoke_json 正确解析 JSON 文本"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"steps": [{"title": "理解概念"}]}'
        )

        import orchestrator.llm as llm_mod
        with patch.object(llm_mod, "get_llm", return_value=mock_llm):
            result = llm_mod.llm_invoke_json("test prompt")
        assert result == {"steps": [{"title": "理解概念"}]}

    def test_invoke_json_handles_code_block(self):
        """llm_invoke_json 正确解析 ```json 代码块中的 JSON"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='```json\n{"key": "value"}\n```'
        )

        import orchestrator.llm as llm_mod
        with patch.object(llm_mod, "get_llm", return_value=mock_llm):
            result = llm_mod.llm_invoke_json("test prompt")
        assert result == {"key": "value"}

    def test_invoke_json_raises_on_invalid(self):
        """LLM 返回无 JSON 文本时抛出 ValueError"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="just some text")

        import orchestrator.llm as llm_mod
        with patch.object(llm_mod, "get_llm", return_value=mock_llm):
            with pytest.raises(ValueError, match="JSON"):
                llm_mod.llm_invoke_json("test prompt")
