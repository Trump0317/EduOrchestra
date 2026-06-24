"""记忆系统 — JSON 文件存储 + LangChain Tool。

存储结构:
  data/profile.json   — 长期画像（任务完成后自动提炼）
  data/memories.json  — 键值记忆（Assistant 通过 tool 写入）
  data/tasks/{id}.json — 已完成任务快照
"""

import json
from pathlib import Path
from datetime import datetime
from langchain_core.tools import tool

DATA_DIR = Path("data")
TASKS_DIR = DATA_DIR / "tasks"
PROFILE_PATH = DATA_DIR / "profile.json"
MEMORIES_PATH = DATA_DIR / "memories.json"


def _ensure_dirs():
    TASKS_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default=None):
    if default is None:
        default = {}
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── LangChain Tools ──

@tool
def save_memory(key: str, value: str) -> str:
    """写入一条长期记忆。用于记录学生持续性的学习特征。

    Args:
        key: 记忆键，建议格式 'weakness:<知识点>' 或 'strength:<知识点>' 或 'note:<描述>'
        value: 记忆内容，描述具体观察
    """
    _ensure_dirs()
    memories = _read_json(MEMORIES_PATH)
    memories[key] = value
    _write_json(MEMORIES_PATH, memories)
    return f"记忆已保存: {key}"


@tool
def read_memory(prefix: str = "") -> str:
    """读取长期记忆。用于决策前了解学生过去表现。

    Args:
        prefix: 前缀过滤，如 'weakness:' 只返回薄弱点。空字符串返回全部。
    """
    memories = _read_json(MEMORIES_PATH)
    if prefix:
        memories = {k: v for k, v in memories.items() if k.startswith(prefix)}
    if not memories:
        return "暂无相关记忆。"
    return "\n".join(f"- {k}: {v}" for k, v in memories.items())


# Assistant 绑定的工具列表
MEMORY_TOOLS = [save_memory, read_memory]


# ── 画像管理（任务完成后自动调用，非 Tool）──

def get_profile() -> dict:
    return _read_json(
        PROFILE_PATH, {"topics": {}, "skill_tags": {}, "stats": {}}
    )


def archive_task(task_id: str, state: dict):
    _ensure_dirs()
    _write_json(TASKS_DIR / f"{task_id}.json", state)


def distill_from_task(task_id: str, state: dict):
    """任务完成后提炼长期画像。

    1. 归档任务快照
    2. 更新 topics 知识图谱
    3. 从 feedback 提取 skill_tags
    4. 更新统计
    """
    archive_task(task_id, state)

    task_goal = state.get("task_goal", "")
    topic = task_goal.replace("掌握", "").replace("学会", "").strip()[:20]
    step_history = state.get("step_history", [])
    best = max((h["best_accuracy"] for h in step_history), default=0.0)

    profile = get_profile()
    prev = profile["topics"].get(topic, {})
    profile["topics"][topic] = {
        "best_accuracy": max(best, prev.get("best_accuracy", 0)),
        "sessions": prev.get("sessions", 0) + 1,
        "last_at": datetime.now().isoformat(),
    }

    feedback = state.get("feedback", {})
    tags = profile.get("skill_tags", {})
    strengths = feedback.get("strengths", [])
    weaknesses = feedback.get("weaknesses", [])
    if strengths:
        tags["strengths"] = list(
            set(tags.get("strengths", []) + strengths)
        )[:10]
    if weaknesses:
        tags["weaknesses"] = list(
            set(tags.get("weaknesses", []) + weaknesses)
        )[:10]
    profile["skill_tags"] = tags

    stats = profile.get("stats", {})
    stats["total_tasks"] = stats.get("total_tasks", 0) + 1
    stats["completed_tasks"] = stats.get("completed_tasks", 0) + 1
    stats["total_sessions"] = stats.get("total_sessions", 0) + 1
    profile["stats"] = stats

    _write_json(PROFILE_PATH, profile)
