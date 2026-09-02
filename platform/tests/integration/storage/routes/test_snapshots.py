"""Integration tests for snapshot routes."""

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport

from perfeng.api.app import create_app
from perfeng.storage.database import get_session


@pytest_asyncio.fixture
async def async_client(db_session):
    app = create_app()

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_snapshot(async_client):
    # First create a run
    run_resp = await async_client.post(
        "/api/v1/runs/",
        json={"test_name": "snap-route", "status": "running"},
    )
    assert run_resp.status_code == 201
    run_id = run_resp.json()["run_id"]

    resp = await async_client.post(
        f"/api/v1/runs/{run_id}/snapshots/",
        json={"resource_type": "cpu", "value_current": 33.3},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "snapshot_id" in data


@pytest.mark.asyncio
async def test_list_snapshots(async_client):
    # Create run and one snapshot
    run_resp = await async_client.post(
        "/api/v1/runs/",
        json={"test_name": "list-snap-route", "status": "completed"},
    )
    run_id = run_resp.json()["run_id"]
    await async_client.post(
        f"/api/v1/runs/{run_id}/snapshots/",
        json={"resource_type": "memory", "value_current": 100},
    )

    resp = await async_client.get(
        f"/api/v1/runs/{run_id}/snapshots/",
        params={"resource_type": "memory"},
    )
    assert resp.status_code == 200
    snaps = resp.json()
    assert len(snaps) == 1
    assert snaps[0]["resource_type"] == "memory"
