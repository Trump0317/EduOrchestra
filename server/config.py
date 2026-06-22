import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "deepseek")
        self.LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")

    def validate(self) -> list[str]:
        """校验必要配置，返回缺失项列表"""
        missing = []
        if not self.LLM_API_KEY:
            missing.append("LLM_API_KEY")
        return missing

    def dict(self) -> dict:
        return {
            "provider": self.LLM_PROVIDER,
            "model": self.LLM_MODEL,
            "has_api_key": bool(self.LLM_API_KEY),
        }


config = Config()
