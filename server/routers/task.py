"""学习任务 API — 创建/查询/提交答案。"""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from orchestrator.graph import build_graph
from orchestrator.agents.practice import check_answer

router = APIRouter(prefix="/api/task", tags=["task"])
_graph = build_graph()


# ── Pydantic 模型 ──

class TaskCreate(BaseModel):
    goal: str


class AnswerItem(BaseModel):
    question_id: str
    student_answer: str


class AnswerBody(BaseModel):
    answers: list[AnswerItem]


# ── 内部辅助 ──

def _format_response(task_id: str, state: dict) -> dict:
    """格式化响应，去除 questions 中的 answer 字段。"""
    return {
        "task_id": task_id,
        "task_goal": state.get("task_goal", ""),
        "status": "completed"
        if not state.get("waiting_for_answer")
        else "waiting_for_answer",
        "plan": state.get("plan", []),
        "current_step": state.get("current_step", 0),
        "resources": state.get("resources", []),
        "questions": [
            {
                "id": q["id"],
                "content": q["content"],
                "options": q["options"],
                "kp": q.get("kp", ""),
            }
            for q in state.get("questions", [])
        ],
        "analytics": state.get("analytics"),
        "feedback": state.get("feedback"),
        "next_action": state.get("next_action", ""),
    }


def _get_state_or_404(task_id: str):
    """查状态，不存在时 404。"""
    cfg = {"configurable": {"thread_id": task_id}}
    snapshot = _graph.get_state(cfg)
    if snapshot is None or not snapshot.values:
        raise HTTPException(status_code=404, detail="任务不存在")
    return snapshot


# ── 端点 ──

@router.post("", status_code=201)
def create_task(body: TaskCreate):
    """创建任务，首次 invoke 跑到 practice 中断，返回状态。"""
    task_id = str(uuid.uuid4())
    cfg = {"configurable": {"thread_id": task_id}}
    state = _graph.invoke(
        {
            "task_id": task_id,
            "task_goal": body.goal,
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
    return _format_response(task_id, state)


@router.get("/{task_id}")
def get_task(task_id: str):
    """查询任务当前状态。"""
    snapshot = _get_state_or_404(task_id)
    return _format_response(task_id, snapshot.values)


@router.post("/{task_id}/answer")
def submit_answer(task_id: str, body: AnswerBody):
    """提交答案，恢复图执行，返回新状态。"""
    # 查当前状态，获取 questions（含正确答案）
    snapshot = _get_state_or_404(task_id)
    current_state = snapshot.values
    questions = {q["id"]: q for q in current_state.get("questions", [])}

    # 后端判题
    answers = []
    for a in body.answers:
        q = questions.get(a.question_id)
        if not q:
            raise HTTPException(
                status_code=422,
                detail=f"题目 {a.question_id} 不存在",
            )
        answers.append(
            {
                "question_id": a.question_id,
                "student_answer": a.student_answer,
                "is_correct": check_answer(q, a.student_answer),
                "correct_answer": q["answer"],
            }
        )

    cfg = {"configurable": {"thread_id": task_id}}
    _graph.update_state(cfg, {"answers": answers, "waiting_for_answer": False})
    state = _graph.invoke(None, cfg)
    return _format_response(task_id, state)
