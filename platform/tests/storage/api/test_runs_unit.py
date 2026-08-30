"""Unit tests for run routes using a fake service."""

from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport

from perfeng.api.app import create_app
from perfeng.api.dependencies import get_run_service
from perfeng.storage.services.run_service import RunService


@pytest_asyncio.fixture
async def client_with_fake_service():
    app = create_app()

    fake_service = AsyncMock(spec=RunService)
    fake_service.create_run.return_value = {"run_id": "123e4567-e89b-12d3-a456-426614174000"}
    fake_service.get_run.return_value = None
    fake_service.list_runs.return_value = []

    async def override_get_run_service():
        return fake_service

    app.dependency_overrides[get_run_service] = override_get_run_service

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, fake_service


@pytest.mark.asyncio
async def test_create_run_with_fake_service(client_with_fake_service):
    client, fake_service = client_with_fake_service
    response = await client.post("/api/v1/runs/", json={"test_name": "fake"})
    assert response.status_code == 201
    fake_service.create_run.assert_awaited_once()
