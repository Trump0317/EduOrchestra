"""Planner Agent — 调用 LLM 拆解学习目标为步骤序列。"""

from orchestrator.state import AgentState
from orchestrator.llm import llm_invoke_json
from orchestrator.prompt import render_prompt


def planner_node(state: AgentState) -> dict:
    """调用 LLM 将学习目标拆解为步骤序列。不修改 current_step。"""
    goal = state["task_goal"]
    prompt = render_prompt("planner", task_goal=goal)
    result = llm_invoke_json(prompt)
    # LLM 输出: {"steps": [{"title": "...", "desc": "..."}, ...]}
    return {"plan": result["steps"]}
