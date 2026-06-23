# server/tests/integration/test_workflow.py
# 测试行为：
# - test_workflow_runs_to_practice: invoke → waiting=True, plan/resources/questions 非空
# - test_workflow_resume_after_answer: update_state 注入答案后 invoke(None) → analytics/feedback 非空
# - test_workflow_repeat_on_all_wrong: 全答错 → next_action="repeat_step"
# - test_workflow_completes_on_all_correct: 全答对 → next_action="next_step"

from orchestrator.graph import build_graph
from orchestrator.agents.practice import check_answer


def test_workflow_runs_to_practice():
    """invoke 后停在 practice，plan/resources/questions 均生成"""
    graph = build_graph()
    config = {"configurable": {"thread_id": "flow-1"}}

    state = graph.invoke(
        {
            "task_id": "test-1",
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
        },
        config,
    )

    assert state["waiting_for_answer"] is True
    assert len(state["questions"]) > 0
    assert len(state["plan"]) >= 2
    assert len(state["resources"]) > 0
    assert state.get("analytics") is None  # 还未执行


def test_workflow_resume_after_answer():
    """注入答案后 invoke(None) → analytics/feedback 非空"""
    graph = build_graph()
    config = {"configurable": {"thread_id": "flow-2"}}

    # 第一段
    state = graph.invoke(
        {
            "task_id": "test-2",
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
        },
        config,
    )

    # 构造答案（第一题对，第二题错）
    answers = []
    for q in state["questions"]:
        is_correct = True if len(answers) == 0 else False
        student_answer = q["answer"] if is_correct else ("A" if q["answer"] != "A" else "B")
        answers.append({
            "question_id": q["id"],
            "student_answer": student_answer,
            "is_correct": check_answer(q, student_answer),
            "correct_answer": q["answer"],
        })

    graph.update_state(config, {"answers": answers, "waiting_for_answer": False})

    state = graph.invoke(None, config)

    assert state["analytics"] is not None
    assert state["analytics"]["total_questions"] == len(answers)
    assert state["feedback"] is not None
    assert state["next_action"] in ("repeat_step", "next_step")


def test_workflow_repeat_on_all_wrong():
    """全答错 → next_action = repeat_step"""
    graph = build_graph()
    config = {"configurable": {"thread_id": "flow-3"}}

    state = graph.invoke(
        {
            "task_id": "test-3",
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
        },
        config,
    )

    wrong_answers = []
    for q in state["questions"]:
        wrong = "A" if q["answer"] != "A" else "B"
        wrong_answers.append({
            "question_id": q["id"],
            "student_answer": wrong,
            "is_correct": False,
            "correct_answer": q["answer"],
        })

    graph.update_state(config, {"answers": wrong_answers, "waiting_for_answer": False})

    state = graph.invoke(None, config)
    assert state["next_action"] == "repeat_step"


def test_workflow_completes_on_all_correct():
    """全答对 → next_action = next_step"""
    graph = build_graph()
    config = {"configurable": {"thread_id": "flow-4"}}

    state = graph.invoke(
        {
            "task_id": "test-4",
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
        },
        config,
    )

    correct_answers = []
    for q in state["questions"]:
        correct_answers.append({
            "question_id": q["id"],
            "student_answer": q["answer"],
            "is_correct": True,
            "correct_answer": q["answer"],
        })

    graph.update_state(config, {"answers": correct_answers, "waiting_for_answer": False})

    state = graph.invoke(None, config)
    assert state["next_action"] == "next_step"
