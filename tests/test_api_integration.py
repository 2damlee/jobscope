from tests.conftest import seed_jobs, write_embedding_artifacts


def test_health_ready_returns_503_when_artifacts_are_missing(integration_env):
    client = integration_env["client"]
    session_factory = integration_env["session_factory"]

    seed_jobs(session_factory)

    response = client.get("/health/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] in {"degraded", "error"}
    assert data["database"] == "reachable"


def test_recommend_returns_503_when_embedding_artifacts_are_missing(integration_env):
    client = integration_env["client"]
    session_factory = integration_env["session_factory"]

    seed_jobs(session_factory)

    response = client.get("/recommend/1")

    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert "Embedding" in data["detail"]


def test_recommend_returns_ranked_results_when_artifacts_exist(integration_env):
    client = integration_env["client"]
    session_factory = integration_env["session_factory"]
    paths = integration_env["paths"]

    seed_jobs(session_factory)
    write_embedding_artifacts(paths)

    response = client.get("/recommend/1?limit=2")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    first = data[0]
    assert first["job_id"] != 1
    assert "title" in first
    assert "score" in first
    assert "embedding_score" in first
    assert "skill_overlap_score" in first
    assert "shared_skills" in first


def test_health_pipeline_returns_recent_runs(integration_env):
    client = integration_env["client"]
    session_factory = integration_env["session_factory"]

    seed_jobs(session_factory)

    response = client.get("/health/pipeline")

    assert response.status_code == 200
    data = response.json()

    assert "runs" in data
    assert len(data["runs"]) >= 1
    assert data["runs"][0]["pipeline_name"] == "ingest_jobs"