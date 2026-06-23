# server/tests/unit/test_graph_structure.py
# 测试行为：
# - test_planner_returns_fixed_plan: Planner 返回固定两步计划，含 title/desc
# - test_resource_returns_resources: Resource 返回非空 ResourceEntry 列表
# - test_practice_returns_questions: Practice 返回题目并设置 waiting=True
# - test_check_answer_correct: 相同答案判对
# - test_check_answer_wrong: 不同答案判错
# - test_analytics_computes_accuracy: 1 对 1 错 → accuracy=0.5
# - test_feedback_repeat_on_low_accuracy: accuracy=0 → repeat_step, current_step 不变
# - test_feedback_next_on_high_accuracy: accuracy=1 → next_step, current_step += 1
# - test_feedback_repeat_on_mid_accuracy: accuracy=0.5 → repeat_step
# - test_graph_has_all_nodes: 图包含全部 5 个节点
# - test_graph_edge_chain: planner→resource→practice 链路存在
# - test_graph_interrupts_before_practice: practice 在 interrupt_before 中

from orchestrator.agents.planner import planner_node
from orchestrator.agents.resource import resource_node
from orchestrator.agents.practice import practice_node, check_answer, Question
from orchestrator.agents.analytics import analytics_node
from orchestrator.agents.feedback import feedback_node
from orchestrator.graph import build_graph


def make_base_state(**overrides) -> dict:
    """构造最小合法 AgentState，可通过 overrides 覆盖部分字段"""
    state = {
        "task_id": "test-task",
        "task_goal": "掌握二次函数",
        "plan": [],
        "current_step": 0,
        "resources": [],
        "questions": [],
        "waiting_for_answer": False,
        "answers": [],
        "analytics": None,
        "feedback": None,
        "next_action": "",
    }
    state.update(overrides)
    return state


# ---- Agent 单元测试 ----

def test_planner_returns_fixed_plan():
    result = planner_node(make_base_state())
    assert len(result["plan"]) == 2
    assert result["plan"][0]["title"]
    assert result["plan"][0]["desc"]
    # 不应修改 current_step
    assert "current_step" not in result


def test_resource_returns_resources():
    state = make_base_state(
        plan=[{"title": "概念", "desc": "学习概念"}],
        current_step=0,
    )
    result = resource_node(state)
    assert len(result["resources"]) > 0
    assert result["resources"][0]["type"] in ("video", "article")


def test_practice_returns_questions():
    result = practice_node(make_base_state())
    assert len(result["questions"]) > 0
    assert result["waiting_for_answer"] is True


def test_check_answer_correct():
    q: Question = {"id": "q1", "content": "", "options": [], "answer": "B", "kp": ""}
    assert check_answer(q, "B") is True


def test_check_answer_wrong():
    q: Question = {"id": "q1", "content": "", "options": [], "answer": "B", "kp": ""}
    assert check_answer(q, "A") is False


def test_analytics_computes_accuracy():
    state = make_base_state(
        answers=[
            {"question_id": "q1", "student_answer": "A", "is_correct": True, "correct_answer": "A"},
            {"question_id": "q2", "student_answer": "B", "is_correct": False, "correct_answer": "A"},
        ],
    )
    result = analytics_node(state)
    assert result["analytics"]["total_questions"] == 2
    assert result["analytics"]["correct_count"] == 1
    assert result["analytics"]["accuracy"] == 0.5


def test_feedback_repeat_on_low_accuracy():
    """accuracy=0 → repeat_step, current_step 保持不变"""
    state = make_base_state(
        current_step=0,
        analytics={"total_questions": 2, "correct_count": 0, "accuracy": 0.0, "weak_points": []},
    )
    result = feedback_node(state)
    assert result["next_action"] == "repeat_step"
    assert "current_step" not in result  # 不修改


def test_feedback_next_on_high_accuracy():
    """accuracy=1 → next_step, current_step 递增"""
    state = make_base_state(
        current_step=0,
        analytics={"total_questions": 2, "correct_count": 2, "accuracy": 1.0, "weak_points": []},
    )
    result = feedback_node(state)
    assert result["next_action"] == "next_step"
    assert result["current_step"] == 1  # 0 → 1


def test_feedback_repeat_on_mid_accuracy():
    """accuracy=0.5 → repeat_step"""
    state = make_base_state(
        current_step=0,
        analytics={"total_questions": 2, "correct_count": 1, "accuracy": 0.5, "weak_points": []},
    )
    result = feedback_node(state)
    assert result["next_action"] == "repeat_step"
    assert "current_step" not in result


# ---- 图结构测试 ----

def test_graph_has_all_nodes():
    graph = build_graph()
    nodes = list(graph.get_graph().nodes.keys())
    for name in ("planner", "resource", "practice", "analyze", "report"):
        assert name in nodes


def test_graph_edge_chain():
    graph = build_graph()
    edges = list(graph.get_graph().edges)
    # 线性链路存在
    assert ("planner", "resource") in edges or any(
        src == "planner" and dst == "resource" for src, dst, *_ in edges
    )
    assert ("resource", "practice") in edges or any(
        src == "resource" and dst == "practice" for src, dst, *_ in edges
    )


def test_graph_interrupts_before_practice():
    graph = build_graph()
    assert "practice" in (graph.interrupt_after_nodes or [])
