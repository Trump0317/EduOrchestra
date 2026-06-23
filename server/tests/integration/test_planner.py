# server/tests/integration/test_planner.py
# 测试行为（调真实 LLM）：
# - test_planner_returns_steps: 输入"掌握二次函数"→ 返回 2-5 个步骤，每步含 title/desc
# - test_planner_steps_relevant_to_goal: 步骤内容与输入目标相关（含"二次函数"关键词）
# - test_planner_handles_specific_goal: 输入"理解集合的基本概念"→ 返回相关步骤

import pytest

from orchestrator.agents.planner import planner_node


def make_state(task_goal: str) -> dict:
    """构造最小 AgentState"""
    return {
        "task_id": "test-planner",
        "task_goal": task_goal,
        "plan": [],
        "current_step": 0,
        "resources": [],
        "questions": [],
        "waiting_for_answer": False,
        "answers": [],
        "analytics": None,
        "feedback": None,
        "next_action": "",
    }


class TestPlannerIntegration:
    def test_planner_returns_steps(self):
        """输入目标 → 返回 2-5 个步骤，每步含 title/desc"""
        state = make_state("掌握二次函数")
        result = planner_node(state)

        assert "plan" in result
        plan = result["plan"]
        assert 2 <= len(plan) <= 5, f"步骤数期望 2-5，实际 {len(plan)}"

        for i, step in enumerate(plan):
            assert "title" in step, f"步骤 {i} 缺 title"
            assert "desc" in step, f"步骤 {i} 缺 desc"
            assert isinstance(step["title"], str) and len(step["title"]) > 0
            assert isinstance(step["desc"], str) and len(step["desc"]) > 0

    def test_planner_steps_relevant_to_goal(self):
        """步骤内容与输入目标相关（含"二次函数"关键词）"""
        state = make_state("掌握二次函数")
        result = planner_node(state)

        plan_text = " ".join(
            f"{s['title']} {s['desc']}" for s in result["plan"]
        )
        # 至少一个步骤提到"二次函数"或相关术语
        keywords = ["二次函数", "函数", "图像", "顶点", "对称轴", "标准形式"]
        assert any(kw in plan_text for kw in keywords), (
            f"步骤内容与目标不相关: {plan_text[:200]}"
        )

    def test_planner_handles_specific_goal(self):
        """输入具体的知识点目标 → 返回对应步骤"""
        state = make_state("理解集合的基本概念：子集、交集、并集")
        result = planner_node(state)

        plan_text = " ".join(
            f"{s['title']} {s['desc']}" for s in result["plan"]
        )
        keywords = ["集合", "子集", "交集", "并集", "集合运算"]
        assert any(kw in plan_text for kw in keywords), (
            f"步骤内容与集合目标不相关: {plan_text[:200]}"
        )
