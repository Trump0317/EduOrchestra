# server/tests/integration/test_analytics.py
# 测试行为（调真实 LLM）：
# - test_analytics_with_wrong_answers: 有答错时 → weak_points 非空 + summary 非空
# - test_analytics_all_correct: 全对时 → weak_points 为空 + summary 非空
# - test_analytics_accuracy_correct: accuracy 计算正确（统计部分）

import pytest
from orchestrator.agents.analytics import analytics_node


def make_state(answers: list[dict], task_goal: str = "掌握二次函数") -> dict:
    """构造已答题的 AgentState"""
    return {
        "task_id": "test-analytics",
        "task_goal": task_goal,
        "plan": [{"title": "理解概念", "desc": "学习基本定义"}],
        "current_step": 0,
        "resources": [],
        "questions": [],
        "waiting_for_answer": False,
        "answers": answers,
        "analytics": None,
        "feedback": None,
        "next_action": "",
    }


class TestAnalyticsIntegration:
    def test_analytics_with_wrong_answers(self):
        """有答错时 → weak_points 非空 + summary 非空"""
        state = make_state([
            {"question_id": "q1", "student_answer": "A", "is_correct": True, "correct_answer": "A"},
            {"question_id": "q2", "student_answer": "B", "is_correct": False, "correct_answer": "A"},
            {"question_id": "q3", "student_answer": "C", "is_correct": False, "correct_answer": "D"},
        ])
        result = analytics_node(state)

        analytics = result["analytics"]
        assert analytics["total_questions"] == 3
        assert analytics["correct_count"] == 1
        assert analytics["accuracy"] == pytest.approx(1 / 3)
        assert len(analytics.get("weak_points", [])) > 0, "有答错时应返回薄弱点"
        assert analytics.get("summary", ""), "summary 不应为空"

    def test_analytics_all_correct(self):
        """全对时 → weak_points 为空 + summary 非空"""
        state = make_state([
            {"question_id": "q1", "student_answer": "A", "is_correct": True, "correct_answer": "A"},
            {"question_id": "q2", "student_answer": "B", "is_correct": True, "correct_answer": "B"},
        ])
        result = analytics_node(state)

        analytics = result["analytics"]
        assert analytics["total_questions"] == 2
        assert analytics["correct_count"] == 2
        assert analytics["accuracy"] == 1.0
        assert analytics.get("weak_points") == []
        assert analytics.get("summary", ""), "summary 不应为空"

    def test_analytics_accuracy_correct(self):
        """accuracy 计算正确（统计部分，不调 LLM）"""
        state = make_state([
            {"question_id": "q1", "student_answer": "A", "is_correct": True, "correct_answer": "A"},
            {"question_id": "q2", "student_answer": "B", "is_correct": False, "correct_answer": "C"},
        ])
        result = analytics_node(state)

        analytics = result["analytics"]
        assert analytics["total_questions"] == 2
        assert analytics["correct_count"] == 1
        assert analytics["accuracy"] == 0.5
