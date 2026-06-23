"""Resource Agent — 调用 LLM 为当前学习步骤推荐学习资料。"""

from orchestrator.state import AgentState
from orchestrator.llm import llm_invoke_json
from orchestrator.prompt import render_prompt


def resource_node(state: AgentState) -> dict:
    """调用 LLM 为当前步骤推荐学习资料。"""
    step = state["plan"][state["current_step"]]
    prompt = render_prompt(
        "resource",
        task_goal=state["task_goal"],
        step_title=step["title"],
        step_desc=step["desc"],
    )
    result = llm_invoke_json(prompt)
    # LLM 输出: {"resources": [{"type": "video"|"article", "title": "...", "url": "..."}, ...]}
    return {"resources": result["resources"]}
