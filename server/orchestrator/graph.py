"""LangGraph 状态图编排。

v0.7: 五节点架构
  planner → assistant → resource → practice → feedback → assistant
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from orchestrator.state import AgentState
from orchestrator.agents.planner import planner_node
from orchestrator.agents.assistant import assistant_node
from orchestrator.agents.resource import resource_node
from orchestrator.agents.practice import practice_node
from orchestrator.agents.feedback import feedback_node as diagnose_node


def decide_route(state: AgentState) -> str:
    """根据 Assistant 的 next_action 路由。

    - "next" / "repeat" → resource（新一轮学习）
    - "replan" → planner（调整计划）
    - "done" → END
    """
    action = state.get("next_action", "")
    if action == "done":
        return END
    if action == "replan":
        return "planner"
    return "resource"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("assistant", assistant_node)
    graph.add_node("resource", resource_node)
    graph.add_node("practice", practice_node)
    graph.add_node("diagnose", diagnose_node)

    graph.set_entry_point("planner")

    # planner → assistant（首次路由决策）
    graph.add_edge("planner", "assistant")

    # assistant → resource 或 END
    graph.add_conditional_edges("assistant", decide_route)

    # resource → practice
    graph.add_edge("resource", "practice")

    # practice → feedback（答题后诊断）
    graph.add_edge("practice", "diagnose")

    # diagnose → assistant（智能路由）
    graph.add_edge("diagnose", "assistant")

    return graph.compile(
        checkpointer=MemorySaver(),
        interrupt_after=["practice"],
    )
