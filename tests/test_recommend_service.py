import json
from types import SimpleNamespace

import numpy as np
import pytest
from fastapi import HTTPException

from app.services import recommend_service


def test_load_embeddings_reads_from_configured_paths(tmp_path, monkeypatch):
    embedding_path = tmp_path / "job_embeddings.npy"
    job_ids_path = tmp_path / "job_ids.json"

    np.save(embedding_path, np.array([[0.1, 0.2], [0.3, 0.4]]))
    job_ids_path.write_text(json.dumps([101, 102]), encoding="utf-8")

    monkeypatch.setattr(recommend_service, "EMBEDDING_PATH", embedding_path)
    monkeypatch.setattr(recommend_service, "JOB_IDS_PATH", job_ids_path)

    embeddings, job_ids = recommend_service.load_embeddings()

    assert embeddings.shape == (2, 2)
    assert job_ids == [101, 102]


def test_load_embeddings_raises_when_files_are_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(recommend_service, "EMBEDDING_PATH", tmp_path / "missing.npy")
    monkeypatch.setattr(recommend_service, "JOB_IDS_PATH", tmp_path / "missing.json")

    with pytest.raises(HTTPException) as exc:
        recommend_service.load_embeddings()

    assert exc.value.status_code == 503
    assert "Embedding files not found" in exc.value.detail


def test_load_embeddings_from_disk_reads_files(tmp_path, monkeypatch):
    embedding_path = tmp_path / "job_embeddings.npy"
    job_ids_path = tmp_path / "job_ids.json"

    np.save(embedding_path, np.array([[1.0, 0.0], [0.0, 1.0]]))
    job_ids_path.write_text(json.dumps([1, 2]), encoding="utf-8")

    monkeypatch.setattr(recommend_service, "EMBEDDING_PATH", embedding_path)
    monkeypatch.setattr(recommend_service, "JOB_IDS_PATH", job_ids_path)

    embeddings, job_ids = recommend_service.load_embeddings_from_disk()

    assert embeddings.shape == (2, 2)
    assert job_ids == [1, 2]


def test_get_cached_embeddings_returns_app_state():
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                embeddings=np.array([[1.0, 0.0]]),
                job_ids=[123],
            )
        )
    )

    embeddings, job_ids = recommend_service.get_cached_embeddings(request)

    assert embeddings.shape == (1, 2)
    assert job_ids == [123]


def test_get_cached_embeddings_raises_when_cache_missing():
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                embeddings=None,
                job_ids=None,
            )
        )
    )

    with pytest.raises(HTTPException) as exc:
        recommend_service.get_cached_embeddings(request)

    assert exc.value.status_code == 503
    assert "Recommendation artifacts are not loaded" in exc.value.detail