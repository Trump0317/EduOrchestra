"""Analytics Agent — 统计答题数据 + LLM 分析薄弱知识点。"""

import json

from orchestrator.state import AgentState
from orchestrator.llm import llm_invoke_json
from orchestrator.prompt import render_prompt


def analytics_node(state: AgentState) -> dict:
    """统计分析答题结果，调用 LLM 诊断薄弱点。

    统计部分（不调 LLM）：
    - total_questions / correct_count / accuracy
    LLM 部分（仅当有答错时调用）：
    - weak_points / summary
    """
    answers = state["answers"]
    total = len(answers)
    correct = sum(1 for a in answers if a["is_correct"])
    accuracy = correct / total if total > 0 else 0

    # 统计层面
    stats = {
        "total_questions": total,
        "correct_count": correct,
        "accuracy": accuracy,
    }

    # LLM 分析薄弱点
    if correct < total:
        wrong_details = [
            {
                "question_id": a["question_id"],
                "student_answer": a["student_answer"],
                "correct_answer": a["correct_answer"],
            }
            for a in answers if not a["is_correct"]
        ]
        prompt = render_prompt(
            "analytics",
            task_goal=state["task_goal"],
            wrong_details=json.dumps(wrong_details, ensure_ascii=False),
        )
        llm_result = llm_invoke_json(prompt)
        stats["weak_points"] = llm_result.get("weak_points", [])
        stats["summary"] = llm_result.get("summary", "")
    else:
        stats["weak_points"] = []
        stats["summary"] = "全部正确，掌握良好，可以进入下一步学习。"

    return {"analytics": stats}
