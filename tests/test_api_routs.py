import os

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
    assert "/health/pipeline" in paths
    assert "/health/db" in paths

    rag_enabled = os.getenv("ENABLE_RAG", "false").lower() == "true"
    if rag_enabled:
        assert "/rag/ask" in paths