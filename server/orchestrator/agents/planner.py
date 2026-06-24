"""Planner Agent — 双模式学习计划制定。

模式 1 — 初始规划：根据学习目标创建全新计划
模式 2 — 动态重规划：根据学情调整剩余步骤
"""

import json

from orchestrator.state import AgentState
from orchestrator.llm import llm_invoke_json
from orchestrator.prompt import render_prompt


def planner_node(state: AgentState) -> dict:
    """制定或调整学习计划。

    自动判断模式：
    - plan 为空 → 初始规划
    - plan 非空 → 动态重规划
    """
    plan = state.get("plan", [])

    if not plan:
        return _initial_plan(state)
    else:
        return _replan(state)


def _initial_plan(state: AgentState) -> dict:
    """模式 1：根据目标创建新计划。"""
    prompt = render_prompt(
        "planner",
        task_goal=state["task_goal"],
        mode_section="",
    )
    result = llm_invoke_json(prompt)
    return {"plan": result["plan"]}


def _replan(state: AgentState) -> dict:
    """模式 2：根据学情动态调整剩余步骤。

    已完成步骤不变，只调整当前步及之后的步骤。
    """
    step_index = state["current_step"]
    completed = state["plan"][:step_index]
    remaining = state["plan"][step_index:]

    replan_context = f"""
## 重规划模式

学生已完成部分步骤，当前在第 {step_index + 1} / {len(state["plan"])} 步遇到问题。

### 已完成步骤（保持不变）
{json.dumps(completed, ensure_ascii=False)}

### 当前及剩余步骤（需要调整）
{json.dumps(remaining, ensure_ascii=False)}

### 学习历史
{json.dumps(state.get("step_history", []), ensure_ascii=False)}

### 诊断反馈
{json.dumps(state.get("feedback", {}), ensure_ascii=False)}

### 调整策略
1. **步骤卡住**（多轮正确率低）→ 拆分当前步为 2-3 个更细的小步骤
2. **基础薄弱**（feedback.weaknesses 暴露前置知识欠缺）→ 插入前置补救步骤
3. **掌握迅速**（连续多步全对）→ 合并后续相似步骤
4. **正常推进** → 保持剩余步骤不变

### 重要规则
- plan 只包含**当前及剩余步骤**（不含已完成的）
- 当前步骤为 plan[0]
- 如果无需调整，原样返回剩余步骤
"""

    prompt = render_prompt(
        "planner",
        task_goal=state["task_goal"],
        mode_section=replan_context,
    )
    result = llm_invoke_json(prompt)
    # LLM 输出: {"plan": [...]} — 仅当前及剩余步骤
    new_remaining = result["plan"]
    return {
        "plan": completed + new_remaining,
        "current_step": step_index,
    }
