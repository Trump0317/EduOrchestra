# server/tests/unit/test_graph_structure.py
# 测试行为：
# - test_assistant_creates_plan: mock LLM 返回步骤 + action
# - test_assistant_analyzes_answers: mock LLM 分析答题 + 返回反馈
# - test_resource_returns_resources: Resource 返回非空列表
# - test_practice_returns_questions: Practice 返回题目 + waiting=True
# - test_check_answer_correct: 相同答案判对
# - test_check_answer_wrong: 不同答案判错
# - test_graph_has_all_nodes: 图包含 assistant/resource/practice 3 个节点
# - test_graph_edge_chain: resource→practice 链路存在
# - test_graph_interrupts_before_practice: practice 在 interrupt_after 中

from unittest.mock import patch

from orchestrator.agents.assistant import assistant_node
from orchestrator.agents.resource import resource_node
from orchestrator.agents.practice import practice_node, check_answer, Question
from orchestrator.graph import build_graph


def make_base_state(**overrides) -> dict:
    state = {
        "task_id": "test-task",
        "task_goal": "掌握二次函数",
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


# ── Assistant 单元测试 ──

def test_assistant_creates_plan():
    """首次调用：mock LLM 返回 plan + action=next"""
    mock = {
        "plan": [
            {"title": "理解概念", "desc": "学习基本定义"},
            {"title": "掌握图像", "desc": "学习图像性质"},
        ],
        "feedback": {},
        "action": "next",
    }
    state = make_base_state(plan=[], answers=[], step_history=[])
    with patch("orchestrator.agents.assistant.llm_invoke_json", return_value=mock):
        result = assistant_node(state)
    assert len(result["plan"]) == 2
    assert result["plan"][0]["title"] == "理解概念"
    assert result["next_action"] == "next"
    # 首次无答案，current_step 不变
    assert "current_step" not in result


def test_assistant_analyzes_answers():
    """答题后：mock LLM 返回 feedback + action"""
    mock = {
        "plan": [],  # 不更新 plan
        "feedback": {"summary": "很好", "suggestion": "继续"},
        "action": "next",
    }
    state = make_base_state(
        plan=[{"title": "理解概念", "desc": "学习定义"}],
        current_step=0,
        answers=[
            {"question_id": "q1", "student_answer": "A",
             "is_correct": True, "correct_answer": "A"},
        ],
        step_history=[
            {"step_index": 0, "rounds": 1, "best_accuracy": 1.0,
             "latest_accuracy": 1.0},
        ],
    )
    with patch("orchestrator.agents.assistant.llm_invoke_json", return_value=mock):
        result = assistant_node(state)
    assert result["next_action"] == "next"
    assert result["feedback"]["summary"] == "很好"
    # 有答案 + action=next → current_step 递增
    assert result["current_step"] == 1


# ── Resource 单元测试 ──

@patch("orchestrator.agents.resource.llm_invoke_json")
def test_resource_returns_resources(mock_llm):
    mock_llm.return_value = {
        "resources": [
            {"type": "video", "title": "教学视频", "url": "https://a.com"},
        ]
    }
    state = make_base_state(
        plan=[{"title": "概念", "desc": "学习概念"}],
        current_step=0,
    )
    result = resource_node(state)
    assert len(result["resources"]) > 0
    assert result["resources"][0]["type"] in ("video", "article")


# ── Practice 单元测试 ──

def test_practice_returns_questions():
    result = practice_node(make_base_state())
    assert len(result["questions"]) > 0
    assert result["waiting_for_answer"] is True


def test_check_answer_correct():
    q: Question = {"id": "q1", "content": "", "options": [],
                   "answer": "B", "kp": ""}
    assert check_answer(q, "B") is True


def test_check_answer_wrong():
    q: Question = {"id": "q1", "content": "", "options": [],
                   "answer": "B", "kp": ""}
    assert check_answer(q, "A") is False


# ── 图结构测试 ──

def test_graph_has_all_nodes():
    graph = build_graph()
    nodes = list(graph.get_graph().nodes.keys())
    for name in ("assistant", "resource", "practice"):
        assert name in nodes


def test_graph_edge_chain():
    graph = build_graph()
    edges = list(graph.get_graph().edges)
    assert ("resource", "practice") in edges or any(
        src == "resource" and dst == "practice" for src, dst, *_ in edges
    )


def test_graph_interrupts_before_practice():
    graph = build_graph()
    assert "practice" in (graph.interrupt_after_nodes or [])
