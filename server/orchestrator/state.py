"""LangGraph 共享状态定义。

核心约束：只有 feedback 节点能修改 current_step，其余节点只读。
"""

from typing import TypedDict, Optional


class PlanStep(TypedDict):
    """计划中的一个学习步骤"""
    title: str
    desc: str


class ResourceEntry(TypedDict):
    """一条学习资料"""
    type: str        # "video" | "article"
    title: str
    url: str


class Question(TypedDict):
    """一道练习题"""
    id: str
    content: str
    options: list[str]
    answer: str
    kp: str


class Answer(TypedDict):
    """学生提交的一道答案"""
    question_id: str
    student_answer: str
    is_correct: bool
    correct_answer: str


class AgentState(TypedDict):
    """LangGraph 共享状态。

    只有 feedback 节点能修改 current_step，其余节点只读。
    next_action 由 feedback 写入，decide_next 读取做路由。
    """
    task_id: str
    task_goal: str
    plan: list[PlanStep]
    current_step: int
    resources: list[ResourceEntry]
    questions: list[Question]
    waiting_for_answer: bool
    answers: list[Answer]
    analytics: Optional[dict]
    feedback: Optional[dict]
    next_action: str
