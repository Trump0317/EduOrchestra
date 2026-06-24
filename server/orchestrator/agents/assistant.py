"""Assistant Agent — LLM 智能路由器。

读取全局状态（plan + feedback + step_history + answers），
由 LLM 做出有教学意义的路由决策。

不再承担计划制定（Planner）和答题诊断（Feedback）职责。
"""

import json

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


def _format_step_history(records: list[dict]) -> str:
    if not records:
        return "首次学习本步骤"
    lines = []
    for r in records:
        lines.append(
            f"  第{r.get('rounds', '?')}轮: "
            f"正确率 {r.get('latest_accuracy', 0):.0%}"
        )
    return "\n".join(lines)


def assistant_node(state: AgentState) -> dict:
    """LLM 分析全局状态，决定下一步：repeat / next / done。

    被调用两次：
    1. Planner 之后 — 此时无 feedback/answers，应决定开始学习
    2. Feedback 之后 — 有完整上下文，做智能路由
    """
    plan = state.get("plan", [])
    step_index = state.get("current_step", 0)
    total_steps = len(plan)
    feedback = state.get("feedback")
    answers = state.get("answers", [])
    history = state.get("step_history", [])

    step = plan[step_index] if step_index < total_steps else None
    step_records = [h for h in history if h.get("step_index") == step_index]

    prompt = render_prompt(
        "assistant",
        task_goal=state["task_goal"],
        total_steps=total_steps,
        current_step=step_index + 1,
        step_title=step["title"] if step else "（尚未开始）",
        step_desc=step.get("desc", "") if step else "",
        plan_summary=json.dumps(
            [f"{i+1}. {s['title']}" for i, s in enumerate(plan)],
            ensure_ascii=False,
        ),
        has_feedback="是" if feedback else "否",
        feedback_text=json.dumps(feedback, ensure_ascii=False)
        if feedback
        else "无（首次启动，请直接决定开始学习）",
        step_history_text=_format_step_history(step_records),
        answers_text=_format_answers(answers),
        current_rounds=len(step_records) + 1 if step else 0,
    )
    result = llm_invoke_json(prompt)
    # LLM 输出: {"action": "next"|"repeat"|"done", "reason": "..."}

    update: dict = {
        "next_action": result["action"],
    }

    # 更新 step_history
    if answers:
        total_q = len(answers)
        correct_q = sum(1 for a in answers if a.get("is_correct"))
        accuracy = correct_q / total_q if total_q > 0 else 0
        prev_best = max(
            [h.get("best_accuracy", 0) for h in step_records], default=0
        )
        new_record = {
            "step_index": step_index,
            "rounds": len(step_records) + 1,
            "best_accuracy": max(accuracy, prev_best),
            "latest_accuracy": accuracy,
        }
        filtered = [h for h in history if h.get("step_index") != step_index]
        update["step_history"] = filtered + [new_record]

    # 步骤推进（仅答题后，首次调用不推进）
    if result["action"] == "next" and answers:
        update["current_step"] = step_index + 1

    return update
