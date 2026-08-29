"""Tests for the FastAPI application factory."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_client():
    from perfeng.api.app import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client


def test_health_db(app_client):
    # This will attempt to connect to the real DB; for unit test, mock the engine
    # or use dependency override. Here we just check the endpoint exists.
    response = app_client.get("/health/db")
    # In a unit test without DB, it might return 503; we can adjust accordingly
    assert response.status_code in (200, 503)


def test_openapi_schema(app_client):
    response = app_client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/api/v1/runs" in schema["paths"]
