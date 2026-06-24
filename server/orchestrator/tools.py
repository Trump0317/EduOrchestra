"""外部工具 — DuckDuckGo 搜索 + LangChain Tools。

搜索函数供 Resource Agent 使用，
@tool 装饰的函数供 Assistant Tool Calling 使用。
"""

import re
import httpx
from duckduckgo_search import DDGS
from langchain_core.tools import tool


# ── 底层搜索（Resource Agent 使用）──

def search_resources(query: str, max_results: int = 10) -> list[dict]:
    """搜索中文学习资源。"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                query, region="cn-zh", max_results=max_results,
            ))
        return [
            {"title": r["title"], "url": r["href"], "snippet": r["body"]}
            for r in results
        ]
    except Exception:
        return []


def build_search_query(step_title: str, step_desc: str) -> str:
    """根据步骤信息构建中文搜索查询词。"""
    base = f"{step_title} {step_desc} 高一数学"
    if len(base) > 80:
        base = base[:77] + "..."
    return base


# ── LangChain Tools（Assistant Tool Calling 使用）──

@tool
def search_web(query: str) -> str:
    """搜索网络获取教育相关资料。用于了解知识点难度、查找教学资源。

    Args:
        query: 中文搜索关键词，如 '二次函数顶点坐标 高一数学'
    """
    results = search_resources(query, max_results=5)
    if not results:
        return "未找到相关结果。"
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   {r['url']}")
        lines.append(f"   {r['snippet'][:120]}")
    return "\n".join(lines)


@tool
def fetch_page(url: str) -> str:
    """获取网页文本内容。用于查看资料详情、分析难度。

    Args:
        url: 网页 URL
    """
    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True)
        resp.raise_for_status()
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:2000]
    except Exception as e:
        return f"获取页面失败: {e}"


@tool
def save_memory(key: str, value: str) -> str:
    """写入一条长期记忆。用于记录学生持续性的学习特征。

    Args:
        key: 记忆键，建议格式 'weakness:<知识点>' 或 'strength:<知识点>'
        value: 记忆内容，描述具体观察
    """
    from memory import raw_save_memory
    return raw_save_memory(key, value)


@tool
def read_memory(prefix: str = "") -> str:
    """读取长期记忆。用于决策前了解学生过去表现。

    Args:
        prefix: 前缀过滤，如 'weakness:' 只返回薄弱点。空字符串返回全部。
    """
    from memory import raw_read_memory
    return raw_read_memory(prefix)


# Assistant 绑定的工具列表
ASSISTANT_TOOLS = [search_web, fetch_page, save_memory, read_memory]
