from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_route_exists():
    response = client.get("/")
    assert response.status_code == 200


def test_registered_paths():
    paths = {route.path for route in app.routes}

    assert "/" in paths
    assert "/jobs" in paths
    assert "/analytics/skills" in paths
    assert "/recommend/{job_id}" in paths
    assert "/rag/ask" in paths
    assert "/health/indexes" in paths
    assert "/health/pipeline" in paths
    assert "/health/db" in paths

def test_list_jobs_supports_pagination():
    response = client.get("/jobs?page=1&size=5")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "size" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["size"] == 5


def test_list_jobs_supports_seniority_filter():
    response = client.get("/jobs?seniority=Senior")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data


def test_list_jobs_supports_sorting():
    response = client.get("/jobs?sort_by=title&sort_order=asc")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data