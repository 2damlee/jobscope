import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import get_db
from app.main import app
from app.models import Base, Job, PipelineRun


@pytest.fixture
def integration_env(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path}"

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    import app.api.health as health_module
    import app.main as main_module
    import app.services.recommend_service as recommend_service

    embedding_path = tmp_path / "job_embeddings.npy"
    job_ids_path = tmp_path / "job_ids.json"
    chunk_index_path = tmp_path / "job_chunks.faiss"
    chunk_meta_path = tmp_path / "job_chunks.json"
    embedding_meta_path = tmp_path / "job_embeddings_meta.json"
    chunk_index_meta_path = tmp_path / "job_chunks_index_meta.json"

    monkeypatch.setattr(health_module, "engine", engine)
    monkeypatch.setattr(health_module, "SessionLocal", TestingSessionLocal)

    monkeypatch.setattr(recommend_service, "EMBEDDING_PATH", embedding_path)
    monkeypatch.setattr(recommend_service, "JOB_IDS_PATH", job_ids_path)

    if hasattr(main_module, "ARTIFACT_PATHS"):
        monkeypatch.setattr(
            main_module,
            "ARTIFACT_PATHS",
            [
                embedding_path,
                job_ids_path,
                chunk_index_path,
                chunk_meta_path,
            ],
            raising=False,
        )

    if hasattr(health_module, "EMBEDDING_META_PATH"):
        monkeypatch.setattr(
            health_module,
            "EMBEDDING_META_PATH",
            embedding_meta_path,
            raising=False,
        )

    if hasattr(health_module, "CHUNK_INDEX_META_PATH"):
        monkeypatch.setattr(
            health_module,
            "CHUNK_INDEX_META_PATH",
            chunk_index_meta_path,
            raising=False,
        )

    # 중요: 각 테스트 시작 시 추천 캐시 비우기
    app.state.embeddings = None
    app.state.job_ids = None

    client = TestClient(app)

    yield {
        "client": client,
        "session_factory": TestingSessionLocal,
        "paths": {
            "embedding_path": embedding_path,
            "job_ids_path": job_ids_path,
            "chunk_index_path": chunk_index_path,
            "chunk_meta_path": chunk_meta_path,
            "embedding_meta_path": embedding_meta_path,
            "chunk_index_meta_path": chunk_index_meta_path,
        },
    }

    app.state.embeddings = None
    app.state.job_ids = None
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def seed_jobs(session_factory):
    db = session_factory()

    try:
        job1 = Job(
            id=1,
            title="Backend Engineer",
            company="Alpha",
            location="Berlin",
            category="backend",
            seniority="mid",
            description="Python FastAPI backend role",
            cleaned_description="python fastapi backend api",
            detected_skills='["python", "fastapi", "sql"]',
            url="https://example.com/jobs/1",
            processing_status="done",
        )
        job2 = Job(
            id=2,
            title="Platform Engineer",
            company="Beta",
            location="Berlin",
            category="backend",
            seniority="mid",
            description="Platform and API engineering",
            cleaned_description="python api platform sql",
            detected_skills='["python", "sql", "docker"]',
            url="https://example.com/jobs/2",
            processing_status="done",
        )
        job3 = Job(
            id=3,
            title="Data Engineer",
            company="Gamma",
            location="Munich",
            category="data",
            seniority="senior",
            description="Data pipelines and ETL",
            cleaned_description="spark airflow etl pipeline",
            detected_skills='["spark", "airflow", "etl"]',
            url="https://example.com/jobs/3",
            processing_status="done",
        )

        run = PipelineRun(
            pipeline_name="ingest_jobs",
            status="success",
            source_name="test.csv",
            input_rows=3,
            output_rows=3,
            inserted_rows=3,
            updated_rows=0,
            skipped_rows=0,
            metrics={"changed_rows": 3, "unchanged_rows": 0},
        )

        db.add_all([job1, job2, job3, run])
        db.commit()
    finally:
        db.close()


def load_recommendation_cache_into_app(paths: dict):
    embeddings = np.load(paths["embedding_path"])

    with paths["job_ids_path"].open("r", encoding="utf-8") as f:
        job_ids = json.load(f)

    app.state.embeddings = embeddings
    app.state.job_ids = job_ids


def write_embedding_artifacts(paths: dict, job_ids=None):
    if job_ids is None:
        job_ids = [1, 2, 3]

    embeddings = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [0.0, 1.0, 0.0],
        ],
        dtype=np.float32,
    )

    np.save(paths["embedding_path"], embeddings)

    with paths["job_ids_path"].open("w", encoding="utf-8") as f:
        json.dump(job_ids, f)

    paths["chunk_index_path"].write_bytes(b"dummy-index")

    with paths["chunk_meta_path"].open("w", encoding="utf-8") as f:
        json.dump([], f)

    with paths["embedding_meta_path"].open("w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": "2026-04-15T10:00:00",
                "job_count": len(job_ids),
                "model_name": "test-model",
            },
            f,
        )

    with paths["chunk_index_meta_path"].open("w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": "2026-04-15T10:00:00",
                "chunk_count": 0,
            },
            f,
        )