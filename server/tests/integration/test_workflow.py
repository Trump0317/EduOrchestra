# server/tests/integration/test_workflow.py
# 测试行为：
# - test_workflow_runs_to_practice: invoke → waiting=True, plan/resources/questions 非空
# - test_workflow_resume_after_answer: update_state 注入答案后 invoke(None) → feedback 非空
# - test_workflow_repeat_on_all_wrong: 全答错 → next_action="repeat"
# - test_workflow_completes_on_all_correct: 全答对 → next_action="next"

from orchestrator.graph import build_graph
from orchestrator.agents.practice import check_answer


INIT = {
    "task_id": "",
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


def test_workflow_runs_to_practice():
    """invoke 后停在 practice，plan/resources/questions 均生成"""
    graph = build_graph()
    config = {"configurable": {"thread_id": "flow-1"}}

    state = graph.invoke(dict(INIT, task_id="test-1"), config)

    assert state["waiting_for_answer"] is True
    assert len(state["questions"]) > 0
    assert len(state["plan"]) >= 2
    assert len(state["resources"]) > 0


def test_workflow_resume_after_answer():
    """注入答案后 invoke(None) → feedback 非空"""
    graph = build_graph()
    config = {"configurable": {"thread_id": "flow-2"}}

    state = graph.invoke(dict(INIT, task_id="test-2"), config)

    answers = []
    for q in state["questions"]:
        is_correct = len(answers) == 0
        student = q["answer"] if is_correct else ("A" if q["answer"] != "A" else "B")
        answers.append({
            "question_id": q["id"],
            "student_answer": student,
            "is_correct": check_answer(q, student),
            "correct_answer": q["answer"],
        })

    graph.update_state(config, {"answers": answers, "waiting_for_answer": False})
    state = graph.invoke(None, config)

    assert state["feedback"] is not None
    assert state["feedback"].get("summary") is not None
    assert state["next_action"] in ("repeat", "next")


def test_workflow_repeat_on_all_wrong():
    """全答错 → 图正常流转，有 feedback"""
    graph = build_graph()
    config = {"configurable": {"thread_id": "flow-3"}}

    state = graph.invoke(dict(INIT, task_id="test-3"), config)

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
    # v0.7: Assistant LLM 智能决策，不硬断言 action
    assert state["feedback"] is not None
    assert state["next_action"] in ("repeat", "next")


def test_workflow_completes_on_all_correct():
    """全答对 → 图正常流转"""
    graph = build_graph()
    config = {"configurable": {"thread_id": "flow-4"}}

    state = graph.invoke(dict(INIT, task_id="test-4"), config)

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
    # v0.7: LLM 智能决策
    assert state["feedback"] is not None
    assert state["next_action"] in ("next", "repeat")
