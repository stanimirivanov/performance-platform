"""Integration tests for run routes."""

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport

from perfeng.api.app import create_app
from perfeng.storage.database import get_session


@pytest_asyncio.fixture
async def async_client(db_session):
    """Create an async HTTP client for testing the ASGI app."""
    app = create_app()

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_run(async_client):
    response = await async_client.post(
        "/api/v1/runs/",
        json={"test_name": "route-test", "status": "pending"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "run_id" in data


@pytest.mark.asyncio
async def test_get_run_not_found(async_client):
    random_id = "00000000-0000-0000-0000-000000000000"
    response = await async_client.get(f"/api/v1/runs/{random_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_runs(async_client):
    # Create two runs first
    for i in range(2):
        await async_client.post(
            "/api/v1/runs/",
            json={"test_name": f"list-{i}", "status": "completed"},
        )

    response = await async_client.get(
        "/api/v1/runs/",
        params={"status": "completed", "limit": 10, "offset": 0},
    )
    assert response.status_code == 200
    runs = response.json()
    assert len(runs) >= 2
