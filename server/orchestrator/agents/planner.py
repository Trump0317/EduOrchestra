"""Planner Agent — 将学习目标拆解为步骤序列。"""

from orchestrator.state import AgentState
from orchestrator.llm import llm_invoke_json
from orchestrator.prompt import render_prompt


def planner_node(state: AgentState) -> dict:
    """根据学习目标制定学习计划。

    Args:
        state: 含 task_goal

    Returns:
        {"plan": [{"title": "...", "desc": "..."}, ...]}
    """
    prompt = render_prompt(
        "planner",
        task_goal=state["task_goal"],
    )
    result = llm_invoke_json(prompt)
    return {"plan": result["plan"]}
