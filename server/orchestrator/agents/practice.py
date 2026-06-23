from orchestrator.state import AgentState, Question


QUESTION_BANK: list[Question] = [
    {"id": "q1", "content": "二次函数 y=x² 的对称轴是？", "options": ["A. x=0", "B. x=1", "C. y=0", "D. y=1"], "answer": "A", "kp": "二次函数"},
    {"id": "q2", "content": "二次函数 y=(x-1)²+2 的顶点坐标是？", "options": ["A. (1,2)", "B. (-1,2)", "C. (1,-2)", "D. (-1,-2)"], "answer": "A", "kp": "二次函数"},
    {"id": "q3", "content": "二次函数 y=x²-2x+1 的判别式 Δ 的值是？", "options": ["A. 0", "B. 1", "C. 2", "D. 4"], "answer": "A", "kp": "二次函数"},
]


def practice_node(state: AgentState) -> dict:
    """空实现：返回固定题目，设置 waiting 标记"""
    return {
        "questions": QUESTION_BANK[:2],
        "waiting_for_answer": True,
    }


def check_answer(question: Question, student_answer: str) -> bool:
    """判题：比对答案字符串"""
    return student_answer == question["answer"]
