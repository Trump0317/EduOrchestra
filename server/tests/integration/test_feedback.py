# server/tests/integration/test_feedback.py
# 测试行为（调真实 LLM）：
# - test_feedback_low_accuracy_repeat: accuracy=0.3 → action=repeat_step, current_step 不变
# - test_feedback_high_accuracy_next: accuracy=0.8 → action=next_step, current_step +1
# - test_feedback_returns_summary: summary 和 suggestion 非空
# - test_feedback_all_correct: accuracy=1.0 → action=next_step

import pytest
from orchestrator.agents.feedback import feedback_node


def make_state(
    accuracy: float,
    weak_points: list[str] | None = None,
    current_step: int = 0,
    total: int = 2,
    correct: int | None = None,
) -> dict:
    """构造已跑完 analytics 的 AgentState"""
    if correct is None:
        correct = int(total * accuracy)
    return {
        "task_id": "test-feedback",
        "task_goal": "掌握二次函数",
        "plan": [
            {"title": "理解概念", "desc": "学习基本定义"},
            {"title": "掌握图像", "desc": "学习图像性质"},
        ],
        "current_step": current_step,
        "resources": [],
        "questions": [],
        "waiting_for_answer": False,
        "answers": [],
        "analytics": {
            "total_questions": total,
            "correct_count": correct,
            "accuracy": accuracy,
            "weak_points": weak_points or [],
            "summary": "",
        },
        "feedback": None,
        "next_action": "",
    }


class TestFeedbackIntegration:
    def test_feedback_low_accuracy_repeat(self):
        """accuracy=0.3 → action=repeat_step, current_step 不变"""
        state = make_state(accuracy=0.3, current_step=1)
        result = feedback_node(state)

        assert result["next_action"] == "repeat_step"
        assert "current_step" not in result, "repeat 时不应修改 current_step"
        assert "feedback" in result

    def test_feedback_high_accuracy_next(self):
        """accuracy=0.8 → action=next_step, current_step +1"""
        state = make_state(accuracy=0.8, current_step=0)
        result = feedback_node(state)

        assert result["next_action"] == "next_step"
        assert result["current_step"] == 1, "next_step 应递增 current_step"
        assert "feedback" in result

    def test_feedback_all_correct(self):
        """accuracy=1.0 → action=next_step"""
        state = make_state(accuracy=1.0, current_step=0)
        result = feedback_node(state)

        assert result["next_action"] == "next_step"
        assert result["current_step"] == 1
        assert "feedback" in result

    def test_feedback_returns_summary(self):
        """summary 和 suggestion 非空"""
        state = make_state(accuracy=0.5, current_step=0,
                           weak_points=["二次函数顶点"], total=4, correct=2)
        result = feedback_node(state)

        feedback = result["feedback"]
        assert isinstance(feedback.get("summary"), str) and len(feedback["summary"]) > 0
        assert isinstance(feedback.get("suggestion"), str) and len(feedback["suggestion"]) > 0
