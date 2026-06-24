# server/tests/unit/test_graph_structure.py
# 测试行为：
# - test_assistant_routes_first_call: Mock LLM 返回 action=next（首次）
# - test_assistant_routes_with_feedback: Mock LLM 读取 feedback 做路由
# - test_resource_returns_resources: Resource 返回非空列表
# - test_practice_returns_questions: Practice 返回题目 + waiting=True
# - test_check_answer_correct: 相同答案判对
# - test_check_answer_wrong: 不同答案判错
# - test_graph_has_all_nodes: 图包含 5 个节点
# - test_graph_edge_chain: 核心边存在
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


# ── Assistant 单元测试（v0.7: 纯路由） ──

def test_assistant_routes_first_call():
    """首次调用（无 feedback）：mock LLM 返回 action=next"""
    mock = {"action": "next", "reason": "开始学习第一步"}
    state = make_base_state(
        plan=[{"title": "理解概念", "desc": "学习基本定义"}],
        current_step=0,
        answers=[],
        feedback=None,
    )
    with patch("orchestrator.agents.assistant.llm_invoke_json", return_value=mock):
        result = assistant_node(state)
    assert result["next_action"] == "next"
    # 首次无答案，current_step 不变
    assert "current_step" not in result


def test_assistant_routes_with_feedback():
    """答题后（有 feedback）：mock LLM 做路由决策"""
    mock = {"action": "next", "reason": "掌握良好，进入下一步"}
    state = make_base_state(
        plan=[{"title": "理解概念", "desc": "学习定义"}],
        current_step=0,
        answers=[
            {"question_id": "q1", "student_answer": "A",
             "is_correct": True, "correct_answer": "A"},
        ],
        feedback={"summary": "不错", "strengths": ["概念清晰"],
                  "weaknesses": [], "suggestion": "继续"},
        step_history=[],
    )
    with patch("orchestrator.agents.assistant.llm_invoke_json", return_value=mock):
        result = assistant_node(state)
    assert result["next_action"] == "next"
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
    for name in ("planner", "assistant", "resource", "practice", "diagnose"):
        assert name in nodes, f"图缺少节点: {name}"


def test_graph_edge_chain():
    graph = build_graph()
    edges = list(graph.get_graph().edges)
    # 核心边存在性检查
    edge_pairs = [
        ("resource", "practice"),
        ("practice", "diagnose"),
        ("diagnose", "assistant"),
    ]
    for src, dst in edge_pairs:
        found = (src, dst) in edges or any(
            e[0] == src and e[1] == dst for e in edges
        )
        assert found, f"图缺少边: {src} → {dst}"


def test_graph_interrupts_before_practice():
    graph = build_graph()
    assert "practice" in (graph.interrupt_after_nodes or [])
