from orchestrator.state import AgentState


def resource_node(state: AgentState) -> dict:
    """空实现：读取当前步骤，返回固定资料"""
    step = state["plan"][state["current_step"]]
    return {
        "resources": [
            {"type": "video", "title": f"教学视频：{step['title']}", "url": "https://example.com/video"},
            {"type": "article", "title": f"学习文章：{step['title']}", "url": "https://example.com/article"},
        ]
    }
