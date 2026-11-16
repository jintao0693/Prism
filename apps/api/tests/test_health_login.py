"""冒烟：健康检查 + 演示账号登录。"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.bootstrap.seed import seed_demo_data
from app.core.db import SessionLocal, init_db
from app.main import app


@pytest.fixture
async def client():
    # 不依赖 ASGI lifespan（部分 httpx 版本无 lifespan 参数）
    await init_db()
    async with SessionLocal() as session:
        await seed_demo_data(session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data.get("db") is True


@pytest.mark.asyncio
async def test_demo_login(client: AsyncClient) -> None:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "linqing@prism.demo", "password": "prism123"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data.get("access_token")
    assert data["user"]["email"] == "linqing@prism.demo"
