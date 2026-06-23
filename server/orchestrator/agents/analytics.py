from orchestrator.state import AgentState


def analytics_node(state: AgentState) -> dict:
    """空实现：统计答题正确率"""
    answers = state["answers"]
    total = len(answers)
    correct = sum(1 for a in answers if a["is_correct"])
    return {
        "analytics": {
            "total_questions": total,
            "correct_count": correct,
            "accuracy": correct / total if total > 0 else 0,
            "weak_points": ["二次函数顶点"] if correct < total else [],
        }
    }
