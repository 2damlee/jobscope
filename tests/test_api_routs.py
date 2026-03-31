from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_route_exists():
    response = client.get("/")
    assert response.status_code == 200


def test_registered_paths():
    paths = {route.path for route in app.routes}
    assert "/analytics/skills" in paths
    assert "/recommend/{job_id}" in paths