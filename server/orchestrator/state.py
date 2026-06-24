"""LangGraph 共享状态定义。

Planner 作为全局主管，消费和更新 step_history。
next_action 由 Planner 写入，decide_route 读取做路由。
"""

from typing import TypedDict, Optional


class PlanStep(TypedDict):
    title: str
    desc: str


class ResourceEntry(TypedDict):
    type: str        # "video" | "article"
    title: str
    url: str


class Question(TypedDict):
    id: str
    content: str
    options: list[str]
    answer: str
    kp: str


class Answer(TypedDict):
    question_id: str
    student_answer: str
    is_correct: bool
    correct_answer: str


class StepRecord(TypedDict):
    """每个步骤的学习记录，Planner 用于判断进度。"""
    step_index: int
    rounds: int              # 本步做了几轮
    best_accuracy: float     # 本步最佳正确率
    latest_accuracy: float   # 本步最新正确率


class AgentState(TypedDict):
    task_id: str
    task_goal: str
    plan: list[PlanStep]
    current_step: int

    # 每个步骤的学习记录
    step_history: list[StepRecord]

    # 执行层产出
    resources: list[ResourceEntry]
    questions: list[Question]

    # 答题交互
    waiting_for_answer: bool
    answers: list[Answer]

    # Planner 主管层产出
    feedback: Optional[dict]   # {summary, suggestion}
    next_action: str            # "repeat" | "next" | "done"
