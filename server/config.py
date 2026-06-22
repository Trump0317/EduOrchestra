import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "deepseek")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")

    @classmethod
    def validate(cls) -> list[str]:
        """校验必要配置，返回缺失项列表"""
        missing = []
        if not cls.LLM_API_KEY:
            missing.append("LLM_API_KEY")
        return missing

    @classmethod
    def dict(cls) -> dict:
        return {
            "provider": cls.LLM_PROVIDER,
            "model": cls.LLM_MODEL,
            "has_api_key": bool(cls.LLM_API_KEY),
        }


config = Config()
