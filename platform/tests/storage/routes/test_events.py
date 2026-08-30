"""Integration tests for event routes."""

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
async def test_create_event(async_client):
    run_resp = await async_client.post(
        "/api/v1/runs/",
        json={"test_name": "event-route", "status": "running"},
    )
    run_id = run_resp.json()["run_id"]

    resp = await async_client.post(
        f"/api/v1/runs/{run_id}/events/",
        json={"event_type": "phase_start", "phase_name": "warmup"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "event_id" in data


@pytest.mark.asyncio
async def test_list_events(async_client):
    run_resp = await async_client.post(
        "/api/v1/runs/",
        json={"test_name": "list-event-route", "status": "completed"},
    )
    run_id = run_resp.json()["run_id"]
    await async_client.post(
        f"/api/v1/runs/{run_id}/events/",
        json={"event_type": "start", "phase_name": "setup"},
    )

    resp = await async_client.get(
        f"/api/v1/runs/{run_id}/events/",
        params={"event_type": "start"},
    )
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 1
    assert events[0]["event_type"] == "start"
