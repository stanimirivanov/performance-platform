"""Tests for the FastAPI application factory."""

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport

from perfeng.api.app import create_app


@pytest_asyncio.fixture
async def app_client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_openapi_schema(app_client):
    response = await app_client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/api/v1/runs/" in schema["paths"]
