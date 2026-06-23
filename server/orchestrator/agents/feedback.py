from orchestrator.state import AgentState


def feedback_node(state: AgentState) -> dict:
    """空实现：根据正确率决定路由和步骤推进。

    <0.6 → repeat_step（current_step 不变）
    ≥0.6 → next_step + current_step += 1
    """
    accuracy = state["analytics"]["accuracy"]
    if accuracy < 0.6:
        return {
            "feedback": {"summary": f"正确率 {accuracy:.0%}", "suggestion": "建议重新学习当前步骤"},
            "next_action": "repeat_step",
        }
    else:
        return {
            "feedback": {"summary": f"正确率 {accuracy:.0%}", "suggestion": "可以进入下一步"},
            "next_action": "next_step",
            "current_step": state["current_step"] + 1,
        }
