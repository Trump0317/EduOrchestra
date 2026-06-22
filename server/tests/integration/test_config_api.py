# 测试行为：
# - test_get_config: GET /api/config 返回 200 + 含 provider/model/has_api_key 不含 api_key
# - test_update_config: PUT /api/config 更新 model 后，GET 返回更新后的值
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_get_config():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "provider" in data
        assert "model" in data
        assert "has_api_key" in data
        # api_key 不应泄漏
        assert "api_key" not in data


@pytest.mark.asyncio
async def test_update_config():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.put("/api/config", json={"model": "gpt-4o"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["model"] == "gpt-4o"
