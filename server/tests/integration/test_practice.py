# server/tests/integration/test_practice.py
# 测试行为（调真实 LLM）：
# - test_practice_generates_questions: 根据步骤生成 2-3 道题
# - test_practice_questions_have_required_fields: 每道题含必要字段
# - test_practice_caches_on_repeat: 已有题目时不再生成

import pytest
from unittest.mock import patch


def make_state(**overrides) -> dict:
    state = {
        "task_id": "test-prac",
        "task_goal": "掌握二次函数",
        "plan": [{"title": "理解定义", "desc": "学习二次函数的标准形式"}],
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


class TestPracticeGeneration:
    def test_generates_questions(self):
        """根据步骤生成 2-3 道题"""
        from orchestrator.agents.practice import practice_node

        state = make_state()
        result = practice_node(state)

        assert "questions" in result
        questions = result["questions"]
        assert 2 <= len(questions) <= 3, f"题目数期望 2-3，实际 {len(questions)}"
        assert result["waiting_for_answer"] is True

    def test_questions_have_required_fields(self):
        """每道题含 id/content/options/answer/kp"""
        from orchestrator.agents.practice import practice_node

        state = make_state()
        result = practice_node(state)

        for q in result["questions"]:
            assert "id" in q and q["id"].startswith("q"), f"id 格式错误: {q.get('id')}"
            assert "content" in q and len(q["content"]) > 0
            assert "options" in q and len(q["options"]) == 4
            assert "answer" in q and q["answer"] in "ABCD"
            assert "kp" in q and len(q["kp"]) > 0

    def test_caches_on_repeat(self):
        """已有题目时不再调用 LLM"""
        from orchestrator.agents.practice import practice_node

        existing = [
            {"id": "q1", "content": "test?", "options": ["A", "B", "C", "D"],
             "answer": "A", "kp": "测试"},
        ]
        state = make_state(questions=existing)

        with patch("orchestrator.agents.practice.llm_invoke_json") as mock_llm:
            result = practice_node(state)
            mock_llm.assert_not_called()

        assert result["questions"] == existing
