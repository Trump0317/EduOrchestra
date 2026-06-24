"""Feedback Agent — 分析答题表现，生成诊断报告。"""

from orchestrator.state import AgentState
from orchestrator.llm import llm_invoke_json
from orchestrator.prompt import render_prompt


def _format_answers(answers: list[dict]) -> str:
    if not answers:
        return "无答题记录"
    lines = []
    for i, a in enumerate(answers):
        status = "✅" if a.get("is_correct") else "❌"
        lines.append(
            f"  {status} 题{i + 1}: 学生选 {a.get('student_answer', '?')}"
            f"（正确: {a.get('correct_answer', '?')}）"
        )
    return "\n".join(lines)


def _format_history(records: list[dict]) -> str:
    if not records:
        return "无历史记录"
    lines = []
    for r in records:
        lines.append(
            f"  第{r.get('rounds', '?')}轮: "
            f"正确率 {r.get('latest_accuracy', 0):.0%}"
        )
    return "\n".join(lines)


def feedback_node(state: AgentState) -> dict:
    """分析学生本轮答题表现，生成诊断反馈。

    只输出诊断内容，不做路由决策（交给 Assistant）。
    """
    step = state["plan"][state["current_step"]]
    answers = state.get("answers", [])
    history = state.get("step_history", [])

    # 本轮统计
    total_q = len(answers)
    correct_q = sum(1 for a in answers if a.get("is_correct"))
    accuracy = correct_q / total_q if total_q > 0 else 0

    # 本步历史
    step_records = [
        h for h in history
        if h.get("step_index") == state["current_step"]
    ]
    current_rounds = len(step_records) + 1
    prev_best = max(
        [h.get("best_accuracy", 0) for h in step_records], default=0
    )

    prompt = render_prompt(
        "feedback",
        task_goal=state["task_goal"],
        step_title=step["title"],
        step_desc=step["desc"],
        total_questions=total_q,
        correct_count=correct_q,
        accuracy=f"{accuracy:.0%}",
        current_rounds=current_rounds,
        prev_best=f"{prev_best:.0%}",
        answers_detail=_format_answers(answers),
        history_text=_format_history(step_records),
    )
    result = llm_invoke_json(prompt)
    return {"feedback": result["feedback"]}
