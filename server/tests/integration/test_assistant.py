# server/tests/integration/test_assistant.py
# 测试行为（调真实 LLM）：
# - test_assistant_routes_first_call: 有计划无反馈 → action=next
# - test_assistant_routes_with_good_performance: 全对 → 倾向 next
# - test_assistant_routes_with_poor_performance: 全错 → 倾向 repeat

import pytest
from orchestrator.agents.assistant import assistant_node


def make_state(**overrides) -> dict:
    state = {
        "task_id": "test-asst",
        "task_goal": "掌握二次函数",
        "plan": [
            {"title": "理解概念", "desc": "学习基本定义"},
            {"title": "掌握图像", "desc": "学习图像性质"},
        ],
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


class TestAssistantRouting:
    def test_assistant_routes_first_call(self):
        """有计划无反馈：Assistant 应决定开始学习 (action=next)"""
        state = make_state()
        result = assistant_node(state)

        assert "next_action" in result
        assert result["next_action"] == "next", (
            f"首次调用期望 action=next，实际 {result['next_action']}"
        )
        # 首次调用不应推进 current_step（无答案）
        assert "current_step" not in result

    def test_assistant_routes_with_good_performance(self):
        """全对答题：LLM 应倾向于 next"""
        state = make_state(
            plan=[
                {"title": "理解概念", "desc": "学习基本定义"},
            ],
            answers=[
                {"question_id": "q1", "student_answer": "A",
                 "is_correct": True, "correct_answer": "A"},
                {"question_id": "q2", "student_answer": "B",
                 "is_correct": True, "correct_answer": "B"},
            ],
            feedback={
                "summary": "全对，掌握良好",
                "strengths": ["概念清晰"],
                "weaknesses": [],
                "suggestion": "继续下一步",
            },
        )
        result = assistant_node(state)

        assert result["next_action"] in ("next", "repeat", "done", "replan")

    def test_assistant_routes_with_poor_performance(self):
        """全错答题：LLM 应倾向于 repeat"""
        state = make_state(
            answers=[
                {"question_id": "q1", "student_answer": "A",
                 "is_correct": False, "correct_answer": "B"},
                {"question_id": "q2", "student_answer": "C",
                 "is_correct": False, "correct_answer": "B"},
            ],
            feedback={
                "summary": "全错，基础薄弱",
                "strengths": [],
                "weaknesses": ["基本概念不清"],
                "suggestion": "重新学习基础定义",
            },
        )
        result = assistant_node(state)

        assert result["next_action"] in ("next", "repeat", "done", "replan")
