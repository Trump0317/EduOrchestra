"""
EduOrchestra 演示脚本 — 调真实 LLM，跑通全链路 + repeat 循环。

用法：
    cd server && python demo.py

流程：
    1. 输入学习目标 → Planner 拆解步骤
    2. Resource 推荐资料
    ┌─ 循环直到全部步骤完成 ──────────────────────┐
    │  3. Practice 出题 → 等待你作答               │
    │  4. Analytics 分析薄弱点                     │
    │  5. Feedback 决定下一步                      │
    │     • repeat_step → 回到第 3 步（重学当前步）│
    │     • next_step   → 进入下一步（回到第 2 步）│
    └─────────────────────────────────────────────┘
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
    """显示学习计划"""
    print_sep("🧠 Planner — 学习计划")
    for i, step in enumerate(state["plan"]):
        print(f"  Step {i+1}: {step['title']}")
        print(f"           {step['desc']}")


def show_resources(state: dict):
    """显示当前步骤的学习资料"""
    title = state["plan"][state["current_step"]]["title"]
    print_sep(f"📚 Resource — 步骤「{title}」的资料")
    for r in state.get("resources", []):
        print(f"  [{r['type']}] {r['title']}")
        print(f"          {r['url']}")


def show_questions(state: dict) -> list[dict]:
    """展示题目，收集学生答案，返回答案列表"""
    print_sep("✏️  Practice — 做题（输入选项字母）")
    questions = state.get("questions", [])
    answers = []
    for q in questions:
        print(f"\n  Q: {q['content']}")
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


def show_analytics(state: dict):
    """显示学情分析"""
    stats = state.get("analytics", {})
    print_sep("📊 Analytics — 学情分析")
    print(f"  答题: {stats.get('correct_count', 0)}/{stats.get('total_questions', 0)} 正确")
    print(f"  正确率: {stats.get('accuracy', 0):.0%}")
    if stats.get("weak_points"):
        print(f"  薄弱点: {', '.join(stats['weak_points'])}")
    if stats.get("summary"):
        print(f"  分析: {stats['summary']}")


def show_feedback(state: dict):
    """显示反馈并返回 next_action"""
    fb = state.get("feedback", {})
    action = state.get("next_action", "")
    print_sep("💡 Feedback — 反馈与建议")
    if fb:
        print(f"  总结: {fb.get('summary', '')}")
        print(f"  建议: {fb.get('suggestion', '')}")
    if action == "repeat_step":
        print("  ➡️  决定: 重新学习当前步骤 🔄")
    elif action == "next_step":
        step_idx = state.get("current_step", 0)
        plan = state.get("plan", [])
        if step_idx < len(plan):
            print(f"  ➡️  决定: 进入下一步「{plan[step_idx]['title']}」✅")
        else:
            print("  ➡️  决定: 全部完成 🎉")
    return action


def demo():
    print("=" * 60)
    print("  EduOrchestra — 多智能体数学学习助手")
    print("=" * 60)

    from config import config
    missing = config.validate()
    if missing:
        print(f"\n⚠️  缺少配置: {', '.join(missing)}")
        print("   请先编辑 .env 文件填入 LLM_API_KEY")
        return

    print(f"  模型: {config.LLM_PROVIDER} / {config.LLM_MODEL}")
    print(f"  API Key: {'✅ 已配置' if config.LLM_API_KEY else '❌ 缺失'}")

    goal = input("\n📝 输入学习目标（如「掌握二次函数」）: ").strip()
    if not goal:
        goal = "掌握二次函数"
        print(f"  使用默认目标: {goal}")

    thread_id = f"demo-{uuid.uuid4().hex[:8]}"
    graph = build_graph()
    cfg = {"configurable": {"thread_id": thread_id}}

    # ── 首次调用：planner → resource → practice（中断）──
    print("\n  ⏳ 正在生成学习计划...")
    state = graph.invoke(
        {
            "task_id": f"task-{thread_id}",
            "task_goal": goal,
            "plan": [],
            "current_step": 0,
            "resources": [],
            "questions": [],
            "waiting_for_answer": False,
            "answers": [],
            "analytics": None,
            "feedback": None,
            "next_action": "",
        },
        cfg,
    )

    show_plan(state)
    show_resources(state)

    # ── 答题循环：直到图结束 ──
    round_num = 1
    while state.get("waiting_for_answer"):
        print(f"\n{'─' * 60}")
        print(f"  第 {round_num} 轮答题")

        # 答题
        answers = show_questions(state)

        # 注入答案，恢复执行
        graph.update_state(cfg, {"answers": answers, "waiting_for_answer": False})

        print("\n  ⏳ 正在分析...")
        state = graph.invoke(None, cfg)

        show_analytics(state)
        action = show_feedback(state)

        round_num += 1

        # 如果图已经结束，退出循环
        if not state.get("waiting_for_answer"):
            break

    # ── 完成 ──
    print()
    print("=" * 60)
    plan = state.get("plan", [])
    current = state.get("current_step", len(plan))
    print(f"  完成进度: {current}/{len(plan)} 个步骤")
    print("  Demo 完成！🎉")
    print("=" * 60)


if __name__ == "__main__":
    demo()
