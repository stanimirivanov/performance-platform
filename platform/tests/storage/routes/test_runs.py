"""Integration tests for run routes."""

from fastapi.testclient import TestClient


def test_create_run(client: TestClient):
    response = client.post(
        "/api/v1/runs/",
        json={"test_name": "route-test", "status": "pending"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "run_id" in data


def test_get_run_not_found(client: TestClient):
    random_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/runs/{random_id}")
    assert response.status_code == 404


def test_list_runs(client: TestClient):
    # Create two runs first
    for i in range(2):
        client.post("/api/v1/runs/", json={"test_name": f"list-{i}", "status": "completed"})

    response = client.get("/api/v1/runs/?status=completed&limit=10&offset=0")
    assert response.status_code == 200
    runs = response.json()
    assert len(runs) >= 2
