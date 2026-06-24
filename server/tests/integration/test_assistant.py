# server/tests/integration/test_planner.py
# 测试行为（调真实 LLM）：
# - test_planner_creates_plan: 首次调用 → 返回 plan + action=next
# - test_planner_returns_feedback: 答题后调用 → 返回 feedback + action
# - test_planner_handles_specific_goal: 不同目标 → 返回对应步骤

import pytest
from orchestrator.agents.assistant import assistant_node


def make_state(plan=None, answers=None, step=0):
    if plan is None:
        plan = []
    if answers is None:
        answers = []
    return {
        "task_id": "test-planner",
        "task_goal": "掌握二次函数",
        "plan": plan,
        "current_step": step,
        "step_history": [],
        "resources": [],
        "questions": [],
        "waiting_for_answer": False,
        "answers": answers,
        "feedback": None,
        "next_action": "",
    }


class TestPlanner:
    def test_planner_creates_plan(self):
        """首次调用：创建计划，action=next"""
        state = make_state()
        result = assistant_node(state)

        assert "plan" in result
        assert 2 <= len(result["plan"]) <= 5
        assert result["next_action"] == "next"
        # 首次不应递增 current_step
        assert "current_step" not in result

    def test_planner_returns_feedback(self):
        """答题后：返回 feedback + action"""
        state = make_state(
            plan=[{"title": "概念", "desc": "学习定义"}],
            answers=[
                {"question_id": "q1", "student_answer": "A",
                 "is_correct": True, "correct_answer": "A"},
                {"question_id": "q2", "student_answer": "B",
                 "is_correct": False, "correct_answer": "A"},
            ],
            step=0,
        )
        result = assistant_node(state)

        assert result["feedback"] is not None
        assert result["feedback"].get("summary"), "summary 不应为空"
        assert result["next_action"] in ("repeat", "next", "done")
        # 正确率 50%，应 repeat
        assert result["next_action"] == "repeat"

    def test_planner_handles_specific_goal(self):
        """不同目标 → 对应步骤"""
        state = make_state()
        state["task_goal"] = "理解集合的基本概念：子集、交集、并集"
        result = assistant_node(state)

        plan_text = " ".join(s["title"] for s in result["plan"])
        assert any(kw in plan_text for kw in ["集合", "子集", "交集", "并集"]), (
            f"计划与目标不相关: {plan_text}"
        )
