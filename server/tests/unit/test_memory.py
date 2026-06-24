# server/tests/unit/test_memory.py
# 测试行为：
# - test_raw_save_and_read: 写入 → 读取验证
# - test_raw_prefix_filter: 前缀过滤
# - test_raw_empty_returns_all: 空前缀返回全部
# - test_raw_no_match: 无匹配时返回提示
# - test_tools_are_langchain_tools: ASSISTANT_TOOLS 中的工具是 BaseTool
# - test_assistant_tools_count: ASSISTANT_TOOLS 含 4 个工具

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def temp_data_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        import server.memory as memory_module
        monkeypatch.setattr(memory_module, "DATA_DIR", Path(tmpdir))
        monkeypatch.setattr(memory_module, "TASKS_DIR", Path(tmpdir) / "tasks")
        monkeypatch.setattr(memory_module, "PROFILE_PATH", Path(tmpdir) / "profile.json")
        monkeypatch.setattr(memory_module, "MEMORIES_PATH", Path(tmpdir) / "memories.json")
        yield tmpdir


class TestRawMemory:
    def test_save_and_read(self, temp_data_dir):
        from memory import raw_save_memory, raw_read_memory
        raw_save_memory("weakness:顶点", "公式出错")
        mem = raw_read_memory("")
        assert "weakness:顶点" in mem
        assert "公式出错" in mem

    def test_prefix_filter(self, temp_data_dir):
        from memory import raw_save_memory, raw_read_memory
        raw_save_memory("weakness:计算", "易错")
        raw_save_memory("strength:概念", "扎实")
        weak = raw_read_memory("weakness:")
        assert "weakness:计算" in weak
        assert "strength:概念" not in weak

    def test_empty_prefix(self, temp_data_dir):
        from memory import raw_save_memory, raw_read_memory
        raw_save_memory("x", "1")
        raw_save_memory("y", "2")
        assert "x: 1" in raw_read_memory("")
        assert "y: 2" in raw_read_memory("")

    def test_no_match(self, temp_data_dir):
        from memory import raw_read_memory
        assert "暂无" in raw_read_memory("nonexistent:")


class TestTools:
    def test_are_langchain_tools(self):
        from orchestrator.tools import ASSISTANT_TOOLS
        from langchain_core.tools import BaseTool
        for t in ASSISTANT_TOOLS:
            assert isinstance(t, BaseTool), f"{t.name} 不是 BaseTool"

    def test_count(self):
        from orchestrator.tools import ASSISTANT_TOOLS
        assert len(ASSISTANT_TOOLS) == 4
