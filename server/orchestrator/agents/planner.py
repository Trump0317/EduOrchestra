from orchestrator.state import AgentState, PlanStep


FIXED_PLAN: list[PlanStep] = [
    {"title": "理解基本概念", "desc": "学习二次函数的基本定义和标准形式"},
    {"title": "掌握图像性质", "desc": "学习二次函数的图像、顶点和对称轴"},
]


def planner_node(state: AgentState) -> dict:
    """空实现：返回固定两步计划，不修改 current_step"""
    return {"plan": FIXED_PLAN}
