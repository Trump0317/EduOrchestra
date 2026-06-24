# server/tests/integration/test_planner.py
# 测试行为（调真实 LLM）：
# - test_planner_creates_plan: 给定目标 → 返回 2-5 个步骤，每个含 title/desc
# - test_planner_steps_have_required_fields: 每个步骤的字段完整性
# - test_planner_handles_specific_goal: 不同目标能生成不同计划

import pytest
from orchestrator.agents.planner import planner_node


def make_state(goal: str = "掌握二次函数", **overrides) -> dict:
    state = {
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
    state.update(overrides)
    return state


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

    def test_planner_replan_when_stuck(self):
        """卡住场景：replan 应拆分或调整当前步骤"""
        state = make_state(
            plan=[
                {"title": "理解概念", "desc": "学习基本定义"},
                {"title": "综合应用", "desc": "解决复杂二次函数问题"},
            ],
            current_step=1,  # 卡在第二步
            step_history=[
                {"step_index": 0, "rounds": 1, "best_accuracy": 1.0, "latest_accuracy": 1.0},
                {"step_index": 1, "rounds": 1, "best_accuracy": 0.2, "latest_accuracy": 0.2},
                {"step_index": 1, "rounds": 2, "best_accuracy": 0.3, "latest_accuracy": 0.3},
            ],
            feedback={
                "summary": "综合应用困难",
                "strengths": [],
                "weaknesses": ["缺乏中间步骤训练", "从概念直接跳到应用跨度太大"],
                "suggestion": "增加中间难度过渡",
            },
        )
        result = planner_node(state)

        assert "plan" in result
        new_plan = result["plan"]
        # 已完成步骤（index 0）应保留
        assert new_plan[0]["title"] == "理解概念"
        # 新计划应有合理步骤数
        assert 2 <= len(new_plan) <= 6
