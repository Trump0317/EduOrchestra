"""Practice Agent — LLM 出题 + 判题。

v0.10: 从固定题库改为 LLM 根据当前步骤动态出题，repeat 时缓存复用。
"""

from orchestrator.state import AgentState, Question
from orchestrator.llm import llm_invoke_json
from orchestrator.prompt import render_prompt


def practice_node(state: AgentState) -> dict:
    """根据当前学习步骤，调用 LLM 生成 2-3 道选择题。

    如果 state.questions 已有值（repeat 场景），直接复用不重新生成。
    """
    # 缓存：已有题目时复用
    if state.get("questions"):
        return {"waiting_for_answer": True}

    step = state["plan"][state["current_step"]]
    prompt = render_prompt(
        "practice",
        task_goal=state["task_goal"],
        step_title=step["title"],
        step_desc=step["desc"],
    )
    result = llm_invoke_json(prompt)
    return {
        "questions": result["questions"],
        "waiting_for_answer": True,
    }


def check_answer(question: Question, student_answer: str) -> bool:
    """判题：比对答案字符串。"""
    return student_answer == question["answer"]
