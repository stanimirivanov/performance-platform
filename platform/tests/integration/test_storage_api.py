"""
Integration tests for the storage service API.
"""

import pytest
from fastapi.testclient import TestClient

from perfeng.api.app import create_app


@pytest.fixture
def client():
    app = create_app(dsn="postgresql://test_user:test_password@localhost:5432/test_metadata")
    with TestClient(app) as client:
        yield client


def test_create_run(client):
    # Minimal payload
    payload = {
        "run_metadata": {
            "run": {
                "id": "perf-20260101-000000-12345678",
                "suite": "test-suite",
                "profile": "regression",
                "timestamp": "2026-01-01T00:00:00Z",
                "trigger": "manual",
                "status": "CREATED",
            },
            "test": {
                "type": "api",
                "tool": "k6",
                "toolVersion": "0.48.0",
                "scenario": "test-scenario",
            },
            "candidate": {"gitSha": "0" * 40},
            "environment": {"cluster": "test-cluster", "kubernetesVersion": "v1.28.0"},
        }
    }
    response = client.post("/api/v1/runs", json=payload)
    assert response.status_code == 201
    assert "run_id" in response.json()
