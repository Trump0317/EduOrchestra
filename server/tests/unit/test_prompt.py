# server/tests/unit/test_prompt.py
# 测试行为：
# - test_load_prompt_returns_content: 模板文件存在时返回内容
# - test_load_prompt_raises_on_missing: 模板文件不存在时抛出 FileNotFoundError
# - test_render_prompt_fills_vars: {task_goal} 正确替换为传入值
# - test_render_prompt_raises_on_missing_var: 模板含未传入变量时抛出 KeyError

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestLoadPrompt:
    def test_returns_content(self):
        """模板文件存在时返回文件内容"""
        import orchestrator.prompt as prompt_mod
        content = prompt_mod.load_prompt("assistant")
        assert len(content) > 0
        assert isinstance(content, str)

    def test_raises_on_missing(self):
        """模板文件不存在时抛出 FileNotFoundError"""
        import orchestrator.prompt as prompt_mod
        with pytest.raises(FileNotFoundError):
            prompt_mod.load_prompt("nonexistent_template_xyz")


class TestRenderPrompt:
    def test_fills_vars(self):
        """{task_goal} 正确替换为传入值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpl_path = Path(tmpdir) / "test_tmpl.md"
            tmpl_path.write_text("目标是：{task_goal}，学科：{subject}", encoding="utf-8")

            import orchestrator.prompt as prompt_mod
            with patch.object(prompt_mod, "PROMPT_DIR", Path(tmpdir)):
                result = prompt_mod.render_prompt(
                    "test_tmpl", task_goal="二次函数", subject="数学"
                )
            assert "二次函数" in result
            assert "数学" in result
            assert "{" not in result  # 全部变量已替换

    def test_raises_on_missing_var(self):
        """模板含未传入变量时抛出 KeyError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpl_path = Path(tmpdir) / "test_tmpl.md"
            tmpl_path.write_text("目标：{task_goal}", encoding="utf-8")

            import orchestrator.prompt as prompt_mod
            with patch.object(prompt_mod, "PROMPT_DIR", Path(tmpdir)):
                with pytest.raises(KeyError):
                    prompt_mod.render_prompt("test_tmpl")  # 缺少 task_goal
