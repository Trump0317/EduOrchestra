"""Prompt 模板引擎。

加载 data/prompts/ 下的模板文件并渲染变量。
"""

from pathlib import Path

# 项目根目录下的 data/prompts/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPT_DIR = _PROJECT_ROOT / "data" / "prompts"


def load_prompt(name: str) -> str:
    """加载 prompt 模板文件。

    Args:
        name: 模板名称，不含扩展名，如 "planner"

    Returns:
        模板文件内容

    Raises:
        FileNotFoundError: 模板文件不存在
    """
    path = PROMPT_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt 模板不存在: {path}")
    return path.read_text(encoding="utf-8")


def render_prompt(name: str, **kwargs) -> str:
    """加载并渲染 prompt 模板。

    Args:
        name: 模板名称
        **kwargs: 模板变量键值对

    Returns:
        渲染后的 prompt 字符串

    Raises:
        FileNotFoundError: 模板文件不存在
        KeyError: 模板中有未传入的变量
    """
    template = load_prompt(name)
    return template.format(**kwargs)
