# server/tests/integration/test_feedback.py
# 测试行为（调真实 LLM）：
# - test_feedback_returns_diagnosis: 有答题记录 → 返回 feedback 含必要字段
# - test_feedback_strengths_weaknesses: strengths 和 weaknesses 为 list[str]

import pytest
from orchestrator.agents.feedback import feedback_node


def make_state(goal: str = "掌握二次函数", answers: list[dict] | None = None) -> dict:
    return {
        "task_id": "test-fb",
        "task_goal": goal,
        "plan": [
            {"title": "二次函数定义", "desc": "理解标准形式和基本概念"},
        ],
        "current_step": 0,
        "step_history": [],
        "resources": [],
        "questions": [],
        "waiting_for_answer": False,
        "answers": answers or [
            {"question_id": "q1", "student_answer": "A", "is_correct": True, "correct_answer": "A"},
            {"question_id": "q2", "student_answer": "C", "is_correct": False, "correct_answer": "B"},
        ],
        "feedback": None,
        "next_action": "",
    }


class TestFeedback:
    def test_feedback_returns_diagnosis(self):
        """有答题记录 → 返回 feedback 含 summary/suggestion"""
        state = make_state()
        result = feedback_node(state)

        assert "feedback" in result
        fb = result["feedback"]
        assert isinstance(fb, dict)
        assert "summary" in fb, "feedback 缺 summary"
        assert isinstance(fb["summary"], str) and len(fb["summary"]) > 0
        assert "suggestion" in fb, "feedback 缺 suggestion"
        assert isinstance(fb["suggestion"], str) and len(fb["suggestion"]) > 0

    def test_feedback_strengths_weaknesses(self):
        """strengths 和 weaknesses 为 list[str]"""
        state = make_state()
        result = feedback_node(state)

        fb = result["feedback"]
        assert "strengths" in fb, "feedback 缺 strengths"
        assert "weaknesses" in fb, "feedback 缺 weaknesses"
        assert isinstance(fb["strengths"], list)
        assert isinstance(fb["weaknesses"], list)
