"""Planner Agent — 全局学习主管。

职责：
- 首次调用：拆解目标为步骤序列
- 答题后调用：分析表现 → 生成反馈 → 决定路由 (repeat/next/done)
- 维护 step_history：记录每个步骤的学习轮次和正确率
"""

import json

from orchestrator.state import AgentState
from orchestrator.llm import llm_invoke_json
from orchestrator.prompt import render_prompt


def _format_history(records: list[dict]) -> str:
    """格式化 step_history 为可读文本"""
    if not records:
        return "无历史记录"
    lines = []
    for r in records:
        lines.append(
            f"  第{r.get('rounds', '?')}轮: "
            f"正确率 {r.get('latest_accuracy', 0):.0%}"
        )
    return "\n".join(lines)


def _format_answers(answers: list[dict]) -> str:
    """格式化答题记录"""
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


def planner_node(state: AgentState) -> dict:
    """全局主管节点。"""
    plan = state.get("plan", [])
    answers = state.get("answers", [])
    history = state.get("step_history", [])
    step_index = state.get("current_step", 0)

    total_steps = len(plan)

    # 如果已完成全部步骤，直接结束
    if total_steps > 0 and step_index >= total_steps:
        return {
            "next_action": "done",
            "feedback": {
                "summary": f"🎉 恭喜完成全部 {total_steps} 个步骤！",
                "suggestion": "可以设定新的学习目标继续前进",
            },
        }

    # 当前步骤信息
    step = plan[step_index] if step_index < total_steps else None

    # 本步历史记录
    step_records = [h for h in history if h.get("step_index") == step_index]
    prev_best = max(
        [h.get("best_accuracy", 0) for h in step_records], default=None
    )
    current_rounds = len(step_records) + 1

    # 本轮正确率
    total_q = len(answers)
    correct_q = sum(1 for a in answers if a.get("is_correct"))
    accuracy = correct_q / total_q if total_q > 0 else None

    # 渲染 Prompt
    prompt = render_prompt(
        "planner",
        task_goal=state["task_goal"],
        step_index=step_index + 1,
        total_steps=total_steps if total_steps > 0 else "（尚未制定）",
        step_title=step["title"] if step else "（首次规划）",
        step_desc=step.get("desc", "") if step else "",
        plan_summary=json.dumps(
            [s["title"] for s in plan], ensure_ascii=False
        ),
        step_history_text=_format_history(step_records),
        answers_text=_format_answers(answers),
        round_accuracy=f"{accuracy:.0%}" if accuracy is not None else "无（首次调用）",
    )

    result = llm_invoke_json(prompt)

    # 构建更新
    update: dict = {}

    # 首次调用：使用 LLM 输出的 plan
    if not plan and result.get("plan"):
        update["plan"] = result["plan"]

    # 反馈和路由
    update["feedback"] = result.get("feedback") or {}
    update["next_action"] = result.get("action", "next")

    # 更新 step_history
    if accuracy is not None and step is not None:
        new_record = {
            "step_index": step_index,
            "rounds": current_rounds,
            "best_accuracy": (
                max(accuracy, prev_best)
                if prev_best is not None
                else accuracy
            ),
            "latest_accuracy": accuracy,
        }
        filtered = [h for h in history if h.get("step_index") != step_index]
        update["step_history"] = filtered + [new_record]

    # 路由决策 → 步骤推进
    action = update["next_action"]
    if action == "next":
        if answers:
            # 有答题记录 → 前进到下一步
            update["current_step"] = step_index + 1
        # 无答题记录（首次）→ 保持 step_index 不变，从第 0 步开始
    elif action == "repeat":
        pass  # current_step 不变
    # "done" → 不修改

    return update
