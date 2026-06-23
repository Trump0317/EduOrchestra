"""Feedback Agent — 调用 LLM 生成反馈报告并决定下一步路由。"""

import json

from orchestrator.state import AgentState
from orchestrator.llm import llm_invoke_json
from orchestrator.prompt import render_prompt


def feedback_node(state: AgentState) -> dict:
    """调用 LLM 综合学情分析结果，生成反馈报告并决定下一步。

    LLM 输出 action 为 "repeat_step" 或 "next_step"，
    feedback 节点对 next_step 递增 current_step。
    """
    analytics = state["analytics"]

    prompt = render_prompt(
        "feedback",
        task_goal=state["task_goal"],
        accuracy=analytics["accuracy"],
        weak_points=json.dumps(
            analytics.get("weak_points", []), ensure_ascii=False
        ),
        total_questions=analytics["total_questions"],
        correct_count=analytics["correct_count"],
    )
    result = llm_invoke_json(prompt)

    update = {
        "feedback": {
            "summary": result["summary"],
            "suggestion": result["suggestion"],
        },
        "next_action": result["action"],
    }

    # action 为 next_step 时递增 current_step
    if result["action"] == "next_step":
        update["current_step"] = state["current_step"] + 1

    return update
