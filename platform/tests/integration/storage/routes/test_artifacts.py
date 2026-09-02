"""Integration tests for artifact routes."""

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
async def test_create_artifact(async_client):
    run_resp = await async_client.post(
        "/api/v1/runs/",
        json={"test_name": "artifact-route", "status": "completed"},
    )
    run_id = run_resp.json()["run_id"]

    resp = await async_client.post(
        f"/api/v1/runs/{run_id}/artifacts/",
        json={
            "artifact_type": "raw_data",
            "data_type": "current",
            "storage_path": "s3://bucket/file.json",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "artifact_id" in data


@pytest.mark.asyncio
async def test_list_artifacts(async_client):
    run_resp = await async_client.post(
        "/api/v1/runs/",
        json={"test_name": "list-artifact-route", "status": "completed"},
    )
    run_id = run_resp.json()["run_id"]
    await async_client.post(
        f"/api/v1/runs/{run_id}/artifacts/",
        json={"artifact_type": "raw", "data_type": "baseline", "storage_path": "b.json"},
    )

    resp = await async_client.get(
        f"/api/v1/runs/{run_id}/artifacts/",
        params={"data_type": "baseline"},
    )
    assert resp.status_code == 200
    artifacts = resp.json()
    assert len(artifacts) == 1
    assert artifacts[0]["data_type"] == "baseline"
