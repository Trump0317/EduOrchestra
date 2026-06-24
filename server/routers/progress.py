"""学习进度 API — 查询长期记忆和画像。"""

from fastapi import APIRouter, Query

from memory import get_profile, read_memory

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("")
def get_progress():
    """获取学习画像总览。"""
    return get_profile()


@router.get("/memory")
def get_memories(prefix: str = Query("", description="前缀过滤，如 weakness:")):
    """读取长期记忆。"""
    return {"memories": read_memory.invoke({"prefix": prefix})}
