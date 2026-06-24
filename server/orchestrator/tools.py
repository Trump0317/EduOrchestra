"""外部工具 — DuckDuckGo 搜索。

为 Resource Agent 提供真实网络搜索能力。
"""

from duckduckgo_search import DDGS


def search_resources(query: str, max_results: int = 10) -> list[dict]:
    """搜索中文学习资源。

    Args:
        query: 搜索关键词
        max_results: 最大结果数

    Returns:
        [{"title": "...", "url": "...", "snippet": "..."}, ...]
        搜索失败时返回空列表（不抛异常，上游降级处理）
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                query,
                region="cn-zh",
                max_results=max_results,
            ))
        return [
            {"title": r["title"], "url": r["href"], "snippet": r["body"]}
            for r in results
        ]
    except Exception:
        # DuckDuckGo 偶发限流或网络异常，返回空列表让上游降级
        return []


def build_search_query(step_title: str, step_desc: str) -> str:
    """根据步骤信息构建中文搜索查询词。

    拼接为 "{step_title} {step_desc} 高一数学"，
    限制总长 80 字符以内。
    """
    base = f"{step_title} {step_desc} 高一数学"
    if len(base) > 80:
        base = base[:77] + "..."
    return base
