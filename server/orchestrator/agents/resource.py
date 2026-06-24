"""Resource Agent — 搜索 + LLM 富化推荐学习资料。

v0.6: 改为 DuckDuckGo 搜索 → LLM 过滤富化两步流程。
"""

from orchestrator.state import AgentState
from orchestrator.llm import llm_invoke_json
from orchestrator.prompt import render_prompt
from orchestrator.tools import search_resources, build_search_query


def _format_search_results(results: list[dict]) -> str:
    """将搜索结果格式化为 LLM 可读文本。

    Args:
        results: search_resources 的返回值，每条含 title/url/snippet

    Returns:
        带编号的搜索结果文本，供 LLM prompt 使用
    """
    if not results:
        return "（无搜索结果，请根据步骤信息自行推荐 2-3 条学习资料）"
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   URL: {r['url']}")
        lines.append(f"   摘要: {r['snippet'][:100]}")
    return "\n".join(lines)


def resource_node(state: AgentState) -> dict:
    """搜索并推荐学习资料。

    流程:
    1. 根据步骤信息构建搜索词 → DuckDuckGo 搜索
    2. 将搜索结果交给 LLM 过滤、富化、结构化
    返回含真实 URL + description + knowledge_points 的资源列表。

    降级策略: 搜索失败时 Prompt 中告知 LLM 自行推荐。
    """
    step = state["plan"][state["current_step"]]

    # Step 1: 搜索
    query = build_search_query(step["title"], step["desc"])
    search_results = search_resources(query, max_results=10)

    # Step 2: LLM 过滤富化
    prompt = render_prompt(
        "resource",
        task_goal=state["task_goal"],
        step_title=step["title"],
        step_desc=step["desc"],
        search_results_text=_format_search_results(search_results),
    )
    result = llm_invoke_json(prompt)
    return {"resources": result["resources"]}
