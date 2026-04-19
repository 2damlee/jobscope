import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="Postgres integration test requires a PostgreSQL DATABASE_URL",
)


def test_health_db_and_pipeline_with_postgres(monkeypatch):
    from app.db import SessionLocal
    from app.models import Base, PipelineRun, engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        run = PipelineRun(
            pipeline_name="ingest_jobs",
            status="success",
            source_name="ci.csv",
            input_rows=3,
            output_rows=3,
            inserted_rows=3,
            updated_rows=0,
            skipped_rows=0,
            metrics={"changed_rows": 3, "unchanged_rows": 0},
        )
        db.add(run)
        db.commit()
    finally:
        db.close()

    app.state.embeddings = None
    app.state.job_ids = None

    client = TestClient(app)

    db_response = client.get("/health/db")
    assert db_response.status_code == 200
    assert db_response.json() == {
        "status": "ok",
        "database": "reachable",
    }

    pipeline_response = client.get("/health/pipeline")
    assert pipeline_response.status_code == 200

    data = pipeline_response.json()
    assert "runs" in data
    assert len(data["runs"]) >= 1
    assert data["runs"][0]["pipeline_name"] == "ingest_jobs"

    Base.metadata.drop_all(bind=engine)