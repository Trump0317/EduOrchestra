# server/tests/integration/test_resource.py
# 测试行为（调真实 LLM）：
# - test_resource_returns_materials: 给定步骤 → 返回 2-5 条资料，含 type/title/url
# - test_resource_types_are_valid: type 只能是 "video" 或 "article"
# - test_resource_relevant_to_step: 资料标题与步骤描述相关

import pytest
from orchestrator.agents.resource import resource_node


def make_state(step_title: str, step_desc: str, goal: str = "掌握二次函数") -> dict:
    """构造一个已到 current_step 的 AgentState"""
    return {
        "task_id": "test-resource",
        "task_goal": goal,
        "plan": [{"title": step_title, "desc": step_desc}],
        "current_step": 0,
        "resources": [],
        "questions": [],
        "waiting_for_answer": False,
        "answers": [],
        "analytics": None,
        "feedback": None,
        "next_action": "",
    }


class TestResourceIntegration:
    def test_resource_returns_materials(self):
        """给定步骤 → 返回 2-5 条资料，每条含 type/title/url"""
        state = make_state(
            step_title="理解二次函数定义",
            step_desc="学习二次函数的标准形式和基本定义",
        )
        result = resource_node(state)

        assert "resources" in result
        resources = result["resources"]
        assert 2 <= len(resources) <= 5, f"资料数期望 2-5，实际 {len(resources)}"

        for i, r in enumerate(resources):
            assert "type" in r, f"资源 {i} 缺 type"
            assert "title" in r, f"资源 {i} 缺 title"
            assert "url" in r, f"资源 {i} 缺 url"
            assert isinstance(r["title"], str) and len(r["title"]) > 0
            assert isinstance(r["url"], str) and len(r["url"]) > 0
            assert r["url"].startswith("http"), f"资源 {i} URL 不以 http 开头"

    def test_resource_types_are_valid(self):
        """type 只能是 video 或 article"""
        state = make_state(
            step_title="图像性质",
            step_desc="学习二次函数的图像、顶点和对称轴",
        )
        result = resource_node(state)

        for i, r in enumerate(result["resources"]):
            assert r["type"] in ("video", "article"), (
                f"资源 {i} type='{r['type']}' 不是 video/article"
            )

    def test_resource_relevant_to_step(self):
        """资料标题与步骤描述相关"""
        state = make_state(
            step_title="顶点与对称轴",
            step_desc="学习如何计算二次函数的顶点坐标和对称轴方程",
        )
        result = resource_node(state)

        titles_text = " ".join(r["title"] for r in result["resources"])
        keywords = ["顶点", "对称轴", "二次函数", "公式"]
        assert any(kw in titles_text for kw in keywords), (
            f"资料标题与当前步骤不相关: {titles_text[:200]}"
        )
