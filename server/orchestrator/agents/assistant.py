"""Assistant Agent — LLM 智能路由器（Tool Calling 模式）。

v0.9: 使用 bind_tools + 工具调用循环，支持 save_memory / read_memory。
"""

import json

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from orchestrator.state import AgentState
from orchestrator.llm import get_llm
from orchestrator.prompt import render_prompt
from orchestrator.tools import ASSISTANT_TOOLS, search_web, fetch_page, save_memory, read_memory

_TOOL_MAP = {
    "save_memory": save_memory,
    "read_memory": read_memory,
    "search_web": search_web,
    "fetch_page": fetch_page,
}
_MAX_TOOL_ITERATIONS = 3


def _build_context_json(state: AgentState) -> str:
    """构建 HumanMessage 中的上下文 JSON。"""
    plan = state.get("plan", [])
    step_index = state.get("current_step", 0)
    step = plan[step_index] if step_index < len(plan) else None
    feedback = state.get("feedback")
    answers = state.get("answers", [])
    history = state.get("step_history", [])
    step_records = [h for h in history if h.get("step_index") == step_index]

    # 答题统计
    total_q = len(answers)
    correct_q = sum(1 for a in answers if a.get("is_correct"))
    accuracy = f"{correct_q / total_q:.0%}" if total_q > 0 else "无"

    context = {
        "task_goal": state["task_goal"],
        "total_steps": len(plan),
        "current_step": step_index + 1,
        "step_title": step["title"] if step else "（尚未开始）",
        "step_desc": step.get("desc", "") if step else "",
        "plan_summary": [f"{i+1}. {s['title']}" for i, s in enumerate(plan)],
        "has_feedback": feedback is not None,
        "feedback": feedback,
        "current_rounds": len(step_records) + 1 if step else 0,
        "accuracy": accuracy,
        "answers": [
            {
                "q": a.get("question_id", ""),
                "student": a.get("student_answer", ""),
                "correct": a.get("is_correct", False),
                "answer": a.get("correct_answer", ""),
            }
            for a in answers
        ],
        "step_history_summary": [
            {
                "step": h["step_index"],
                "rounds": h["rounds"],
                "accuracy": f"{h['latest_accuracy']:.0%}",
            }
            for h in step_records
        ],
    }
    return json.dumps(context, ensure_ascii=False, indent=2)


def _parse_decision(content: str) -> dict:
    """从 LLM 最终回答中解析路由决策。"""
    content = content.strip()
    # 去掉 markdown 代码块
    if "```" in content:
        lines = content.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        content = "\n".join(lines).strip()
    # 提取 JSON 对象
    import re
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        content = match.group()
    return json.loads(content)


def _build_update(state: AgentState, decision: dict) -> dict:
    """根据 LLM 决策构建状态更新。"""
    step_index = state.get("current_step", 0)
    answers = state.get("answers", [])
    history = state.get("step_history", [])
    step_records = [h for h in history if h.get("step_index") == step_index]

    update: dict = {"next_action": decision.get("action", "next")}

    # 更新 step_history
    if answers:
        total_q = len(answers)
        correct_q = sum(1 for a in answers if a.get("is_correct"))
        accuracy = correct_q / total_q if total_q > 0 else 0
        prev_best = max(
            [h.get("best_accuracy", 0) for h in step_records], default=0
        )
        new_record = {
            "step_index": step_index,
            "rounds": len(step_records) + 1,
            "best_accuracy": max(accuracy, prev_best),
            "latest_accuracy": accuracy,
        }
        filtered = [h for h in history if h.get("step_index") != step_index]
        update["step_history"] = filtered + [new_record]

    # 步骤推进（仅答题后）
    if decision["action"] == "next" and answers:
        update["current_step"] = step_index + 1

    return update


def assistant_node(state: AgentState) -> dict:
    """LLM 分析全局状态，可调用工具，最终做出路由决策。

    流程:
    1. 构建 SystemMessage + HumanMessage（含上下文 + 已有记忆）
    2. LLM 思考 → 可能 tool_call → 执行工具 → 循环
    3. 最终回答 → 解析 JSON → 路由决策
    """
    llm = get_llm().bind_tools(ASSISTANT_TOOLS)

    system = SystemMessage(content=render_prompt("assistant"))
    context = HumanMessage(content=_build_context_json(state))

    # 注入已有记忆
    memory_text = read_memory.invoke({"prefix": ""})
    memory_hint = HumanMessage(
        content=f"## 已有的长期记忆（来自之前的学习）\n{memory_text}"
    )

    messages = [system, memory_hint, context]

    for _ in range(_MAX_TOOL_ITERATIONS):
        response = llm.invoke(messages)
        messages.append(response)

        if response.tool_calls:
            for tc in response.tool_calls:
                tool_func = _TOOL_MAP[tc["name"]]
                result = tool_func.invoke(tc["args"])
                messages.append(
                    ToolMessage(content=str(result), tool_call_id=tc["id"])
                )
            continue
        else:
            try:
                decision = _parse_decision(response.content)
            except (json.JSONDecodeError, ValueError) as e:
                # 兜底：解析失败时默认 next
                print(f"[Assistant] JSON 解析失败: {e}")
                print(f"[Assistant] 原始输出: {response.content[:200]}")
                decision = {"action": "next", "reason": "解析失败"}
            return _build_update(state, decision)

    # 兜底：超过最大迭代次数
    return {"next_action": "next"}
