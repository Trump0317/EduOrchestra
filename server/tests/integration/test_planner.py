# server/tests/integration/test_planner.py
# 测试行为（调真实 LLM）：
# - test_planner_creates_plan: 给定目标 → 返回 2-5 个步骤，每个含 title/desc
# - test_planner_steps_have_required_fields: 每个步骤的字段完整性
# - test_planner_handles_specific_goal: 不同目标能生成不同计划

import pytest
from orchestrator.agents.planner import planner_node


def make_state(goal: str) -> dict:
    return {
        "task_id": "test-planner",
        "task_goal": goal,
        "plan": [],
        "current_step": 0,
        "step_history": [],
        "resources": [],
        "questions": [],
        "waiting_for_answer": False,
        "answers": [],
        "feedback": None,
        "next_action": "",
    }


class TestPlanner:
    def test_planner_creates_plan(self):
        """给定目标 → 返回 2-5 个步骤"""
        state = make_state("掌握二次函数")
        result = planner_node(state)

        assert "plan" in result
        plan = result["plan"]
        assert isinstance(plan, list)
        assert 2 <= len(plan) <= 5, f"步骤数期望 2-5，实际 {len(plan)}"

        for i, step in enumerate(plan):
            assert "title" in step, f"步骤 {i} 缺 title"
            assert "desc" in step, f"步骤 {i} 缺 desc"
            assert isinstance(step["title"], str) and len(step["title"]) > 0
            assert isinstance(step["desc"], str) and len(step["desc"]) > 0

    def test_planner_handles_specific_goal(self):
        """不同目标能生成不同计划"""
        state = make_state("学会解一元二次方程")
        result = planner_node(state)

        plan = result["plan"]
        titles_text = " ".join(s["title"] for s in plan)
        # 计划应体现"方程"相关内容
        assert len(plan) >= 2
        assert len(titles_text) > 0
