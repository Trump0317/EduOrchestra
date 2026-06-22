from fastapi import APIRouter
from pydantic import BaseModel
from config import config as app_config

router = APIRouter(prefix="/api/config", tags=["config"])


class ConfigResponse(BaseModel):
    provider: str
    model: str
    has_api_key: bool


class ConfigUpdate(BaseModel):
    provider: str | None = None
    api_key: str | None = None
    model: str | None = None


@router.get("")
def get_config() -> ConfigResponse:
    return ConfigResponse(**app_config.dict())


@router.put("")
def update_config(body: ConfigUpdate):
    """更新运行内存中的配置（不写入 .env 文件）"""
    if body.provider:
        app_config.LLM_PROVIDER = body.provider
    if body.api_key:
        app_config.LLM_API_KEY = body.api_key
    if body.model:
        app_config.LLM_MODEL = body.model
    return ConfigResponse(**app_config.dict())
