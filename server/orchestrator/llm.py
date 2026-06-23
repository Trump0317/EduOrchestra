"""LLM 客户端封装。

提供统一的 ChatOpenAI 调用入口：get_llm()、llm_invoke()、llm_invoke_json()。
"""

import json
import re

from langchain_openai import ChatOpenAI

from config import config


def get_llm() -> ChatOpenAI:
    """创建 LLM 客户端实例。

    根据 config 中的 LLM_PROVIDER、LLM_API_KEY、LLM_MODEL 创建 ChatOpenAI。
    缺 API Key 时抛出 ValueError。
    """
    missing = config.validate()
    if missing:
        raise ValueError(
            f"缺少必要配置: {', '.join(missing)}。请检查 .env 文件。"
        )
    kwargs: dict = dict(
        model=config.LLM_MODEL,
        api_key=config.LLM_API_KEY,
    )
    base_url = config.LLM_BASE_URL
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)


def llm_invoke(prompt: str) -> str:
    """调用 LLM，返回纯文本响应。"""
    llm = get_llm()
    resp = llm.invoke(prompt)
    return resp.content


def llm_invoke_json(prompt: str) -> dict:
    """调用 LLM 并解析 JSON 输出。

    自动提取 ```json 代码块或直接的 JSON 对象。
    解析失败时抛出 ValueError。
    """
    text = llm_invoke(prompt)
    # 尝试匹配 JSON 对象（支持代码块和裸 JSON）
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(
        f"LLM 输出中未找到有效 JSON。输出前 200 字符: {text[:200]}"
    )
