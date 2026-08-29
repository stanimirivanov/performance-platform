"""Unit tests for run routes using a fake service."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_fake_service():
    from perfeng.api.dependencies import get_run_service

    from perfeng.api.app import create_app
    from perfeng.storage.services.run_service import RunService

    app = create_app()

    fake_service = AsyncMock(spec=RunService)
    fake_service.create_run.return_value = {"run_id": "123e4567-e89b-12d3-a456-426614174000"}
    fake_service.get_run.return_value = None
    fake_service.list_runs.return_value = []

    async def override_get_run_service():
        return fake_service

    app.dependency_overrides[get_run_service] = override_get_run_service

    with TestClient(app) as client:
        yield client, fake_service


def test_create_run_with_fake_service(client_with_fake_service):
    client, fake_service = client_with_fake_service
    response = client.post("/api/v1/runs/", json={"test_name": "fake"})
    assert response.status_code == 201
    fake_service.create_run.assert_awaited_once()
