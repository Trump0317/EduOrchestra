from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from orchestrator.state import AgentState
from orchestrator.agents.planner import planner_node
from orchestrator.agents.resource import resource_node
from orchestrator.agents.practice import practice_node


def decide_route(state: AgentState) -> str:
    """Planner 输出 next/repeat → resource → practice
       Planner 输出 done → END"""
    action = state.get("next_action", "")
    if action == "done":
        return END
    return "resource"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("resource", resource_node)
    graph.add_node("practice", practice_node)

    graph.set_entry_point("planner")

    # planner → decide → resource or END
    graph.add_conditional_edges("planner", decide_route)

    # resource → practice
    graph.add_edge("resource", "practice")

    # practice → planner（答题完成后回到主管审查）
    graph.add_edge("practice", "planner")

    return graph.compile(
        checkpointer=MemorySaver(),
        interrupt_after=["practice"],
    )
