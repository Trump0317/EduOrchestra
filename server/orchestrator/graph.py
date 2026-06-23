from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from orchestrator.state import AgentState
from orchestrator.agents.planner import planner_node
from orchestrator.agents.resource import resource_node
from orchestrator.agents.practice import practice_node
from orchestrator.agents.analytics import analytics_node
from orchestrator.agents.feedback import feedback_node


def decide_next(state: AgentState) -> str:
    """条件路由：根据 next_action 决定跳转"""
    action = state.get("next_action", "")
    if action == "repeat_step":
        return "planner"
    if action == "next_step":
        if state["current_step"] < len(state["plan"]):
            return "resource"
        return END
    return END


def build_graph() -> StateGraph:
    """构建 LangGraph 状态图，在 practice 前中断"""
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("resource", resource_node)
    graph.add_node("practice", practice_node)
    graph.add_node("analyze", analytics_node)
    graph.add_node("report", feedback_node)

    graph.add_edge("planner", "resource")
    graph.add_edge("resource", "practice")
    graph.add_edge("practice", "analyze")
    graph.add_edge("analyze", "report")
    graph.add_conditional_edges("report", decide_next)

    graph.set_entry_point("planner")

    return graph.compile(checkpointer=MemorySaver(), interrupt_after=["practice"])
