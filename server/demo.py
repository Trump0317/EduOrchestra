"""
EduOrchestra 演示脚本 — Planner 全局主管模式。

用法：
    cd server && python demo.py

流程：
    Planner → Resource → Practice(中断)
        ↑                              │
        └──── repeat/next ────────────┘ (Planner 决策)
                                  done → END
"""

import uuid
from orchestrator.graph import build_graph
from orchestrator.agents.practice import check_answer


def print_sep(title: str):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def show_plan(state: dict):
    print_sep("🧠 Planner — 学习计划")
    for i, step in enumerate(state["plan"]):
        print(f"  {i + 1}. {step['title']}")
        print(f"     {step['desc']}")


def show_resources_and_questions(state: dict):
    step = state["plan"][state["current_step"]]
    print_sep(f"📚 第 {state['current_step'] + 1} 步「{step['title']}」")
    print(f"  {step['desc']}")
    print()
    for r in state.get("resources", []):
        print(f"  [{r['type']}] {r['title']}")
        print(f"          {r['url']}")


def collect_answers(state: dict) -> list[dict]:
    print_sep("✏️  练习题")
    questions = state.get("questions", [])
    answers = []
    for q in questions:
        print(f"\n  {q['content']}")
        for opt in q["options"]:
            print(f"     {opt}")
        student = input("  你的答案: ").strip().upper()
        is_correct = check_answer(q, student)
        print(f"  {'✅ 正确' if is_correct else '❌ 错误'}（正确答案: {q['answer']}）")
        answers.append({
            "question_id": q["id"],
            "student_answer": student,
            "is_correct": is_correct,
            "correct_answer": q["answer"],
        })
    return answers


def show_feedback(state: dict):
    fb = state.get("feedback", {})
    print_sep("🧠 Planner 反馈")
    if fb.get("summary"):
        print(f"  {fb['summary']}")
    if fb.get("suggestion"):
        print(f"  💡 {fb['suggestion']}")

    action = state.get("next_action", "")
    plan = state.get("plan", [])
    step = state.get("current_step", 0)
    history = state.get("step_history", [])

    # 显示本轮统计
    if history:
        last = history[-1]
        acc = last.get("latest_accuracy", 0)
        rounds = last.get("rounds", "?")
        print()
        print(f"  正确率: {acc:.0%}  |  本步第 {rounds} 轮")

    if action == "repeat":
        print("  ➡️  决定: 重新学习当前步骤 🔄")
    elif action == "next":
        if step < len(plan):
            next_title = plan[step]["title"] if step < len(plan) else ""
            print(f"  ➡️  决定: 进入下一步「{next_title}」✅")
        else:
            print("  ➡️  决定: 进入下一步 ✅")
    elif action == "done":
        print("  🎉 全部完成！")


def demo():
    print("=" * 60)
    print("  EduOrchestra — Planner 主管模式")
    print("=" * 60)

    from config import config
    missing = config.validate()
    if missing:
        print(f"\n⚠️  缺少配置: {', '.join(missing)}")
        return
    print(f"  模型: {config.LLM_PROVIDER} / {config.LLM_MODEL}")

    goal = input("\n📝 输入学习目标: ").strip()
    if not goal:
        goal = "掌握二次函数"
        print(f"  使用默认目标: {goal}")

    thread_id = f"demo-{uuid.uuid4().hex[:8]}"
    graph = build_graph()
    cfg = {"configurable": {"thread_id": thread_id}}

    # 首次调用
    print("\n  ⏳ Planner 正在制定计划...")
    state = graph.invoke(
        {
            "task_id": f"task-{thread_id}",
            "task_goal": goal,
            "plan": [],
            "current_step": 0,
            "step_history": [],
            "resources": [],
            "questions": [],
            "waiting_for_answer": False,
            "answers": [],
            "feedback": None,
            "next_action": "",
        },
        cfg,
    )

    show_plan(state)

    # 答题循环
    while state.get("waiting_for_answer"):
        show_resources_and_questions(state)
        answers = collect_answers(state)

        graph.update_state(cfg, {"answers": answers, "waiting_for_answer": False})

        print("\n  ⏳ Planner 正在分析...")
        state = graph.invoke(None, cfg)

        show_feedback(state)

    print()
    print("=" * 60)
    print("  Demo 完成！🎉")
    print("=" * 60)


if __name__ == "__main__":
    demo()
