from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from orchestrator.state import AgentState
from orchestrator.agents.assistant import assistant_node
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

    graph.add_node("assistant", assistant_node)
    graph.add_node("resource", resource_node)
    graph.add_node("practice", practice_node)

    graph.set_entry_point("assistant")

    # planner → decide → resource or END
    graph.add_conditional_edges("assistant", decide_route)

    # resource → practice
    graph.add_edge("resource", "practice")

    # practice → planner（答题完成后回到主管审查）
    graph.add_edge("practice", "assistant")

    return graph.compile(
        checkpointer=MemorySaver(),
        interrupt_after=["practice"],
    )
