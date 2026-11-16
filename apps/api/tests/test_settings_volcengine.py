"""设置：火山配置读写（无真实外网）。"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.bootstrap.seed import seed_demo_data
from app.core.db import SessionLocal, init_db
from app.main import app


@pytest.fixture
async def client():
    await init_db()
    async with SessionLocal() as session:
        await seed_demo_data(session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _login(client: AsyncClient) -> str:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "linqing@prism.demo", "password": "prism123"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_get_and_put_volcengine(client: AsyncClient) -> None:
    token = await _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    got = await client.get("/api/v1/settings/providers/volcengine", headers=headers)
    assert got.status_code == 200, got.text
    body = got.json()
    assert body["provider"] == "volcengine_ark"
    assert body["enabled"] is False

    put = await client.put(
        "/api/v1/settings/providers/volcengine",
        headers=headers,
        json={
            "enabled": False,
            "chatModel": "doubao-seed-test",
            "imageModel": "seedream-test",
            "videoModel": "seedance-test",
            "embeddingModel": "embed-test",
            "note": "unit-test",
        },
    )
    assert put.status_code == 200, put.text
    saved = put.json()
    assert saved["chatModel"] == "doubao-seed-test"
    assert saved["note"] == "unit-test"
    assert saved["hasApiKey"] is False
