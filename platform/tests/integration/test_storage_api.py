"""Integration tests for storage API."""

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
async def test_create_run(async_client):
    payload = {
        "test_name": "test-suite",
        "test_script": "test-scenario",
        "test_profile": "regression",
        "status": "pending",
        "trigger_type": "manual",
        "environment": {
            "cluster_name": "test-cluster",
            "kubernetes_version": "v1.28.0",
            "fingerprint_hash": "a" * 64,
        },
        "tags": ["integration"],
        "parameters": {
            "tool": "k6",
            "toolVersion": "0.48.0",
            "scenario": "test-scenario",
        },
    }

    resp = await async_client.post("/api/v1/runs/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "run_id" in data
