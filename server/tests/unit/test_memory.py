# server/tests/unit/test_memory.py
# 测试行为：
# - test_save_memory_writes_and_reads: 写入 → 读取验证
# - test_read_memory_prefix_filter: 前缀过滤
# - test_save_memory_is_langchain_tool: save_memory 是 LangChain Tool
# - test_read_memory_default_empty: 前缀无匹配时返回提示

import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

import pytest


# 在导入前设置 DATA_DIR 为临时目录，避免污染真实数据
@pytest.fixture(autouse=True)
def temp_data_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch memory module's DATA_DIR before import
        import server.memory as memory_module
        monkeypatch.setattr(memory_module, "DATA_DIR", Path(tmpdir))
        monkeypatch.setattr(memory_module, "TASKS_DIR", Path(tmpdir) / "tasks")
        monkeypatch.setattr(memory_module, "PROFILE_PATH", Path(tmpdir) / "profile.json")
        monkeypatch.setattr(memory_module, "MEMORIES_PATH", Path(tmpdir) / "memories.json")
        yield tmpdir


class TestSaveMemory:
    def test_save_and_read(self, temp_data_dir):
        """写入 → 读取验证"""
        from memory import save_memory, read_memory

        result = save_memory.invoke({"key": "weakness:顶点", "value": "公式出错"})
        assert "已保存" in result

        memories = read_memory.invoke({"prefix": ""})
        assert "weakness:顶点" in memories
        assert "公式出错" in memories

    def test_write_multiple(self, temp_data_dir):
        """多次写入不覆盖"""
        from memory import save_memory, read_memory

        save_memory.invoke({"key": "a", "value": "1"})
        save_memory.invoke({"key": "b", "value": "2"})

        memories = read_memory.invoke({"prefix": ""})
        assert "a: 1" in memories
        assert "b: 2" in memories


class TestReadMemory:
    def test_prefix_filter(self, temp_data_dir):
        """前缀过滤"""
        from memory import save_memory, read_memory

        save_memory.invoke({"key": "weakness:计算", "value": "易错"})
        save_memory.invoke({"key": "strength:概念", "value": "扎实"})

        weak = read_memory.invoke({"prefix": "weakness:"})
        assert "weakness:计算" in weak
        assert "strength:概念" not in weak

        strong = read_memory.invoke({"prefix": "strength:"})
        assert "strength:概念" in strong

    def test_empty_prefix_returns_all(self, temp_data_dir):
        """空前缀返回全部"""
        from memory import save_memory, read_memory

        save_memory.invoke({"key": "x", "value": "1"})
        save_memory.invoke({"key": "y", "value": "2"})

        all_mem = read_memory.invoke({"prefix": ""})
        assert "x: 1" in all_mem
        assert "y: 2" in all_mem

    def test_no_match(self, temp_data_dir):
        """无匹配时返回提示"""
        from memory import read_memory

        result = read_memory.invoke({"prefix": "nonexistent:"})
        assert "暂无" in result


class TestToolType:
    def test_is_langchain_tool(self):
        """验证是 LangChain Tool 类型"""
        from memory import save_memory, read_memory
        from langchain_core.tools import BaseTool

        assert isinstance(save_memory, BaseTool)
        assert isinstance(read_memory, BaseTool)

    def test_tools_list(self):
        """MEMORY_TOOLS 包含两个工具"""
        from memory import MEMORY_TOOLS
        assert len(MEMORY_TOOLS) == 2
