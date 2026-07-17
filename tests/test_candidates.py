"""Unit tests for the FAISS-backed candidate generation stage."""

import numpy as np
import pytest

from app.candidates import CandidateIndex, UnknownJobError


def _normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return (matrix / norms).astype(np.float32)


@pytest.fixture
def small_index() -> CandidateIndex:
    # Four 3-dim vectors with a known similarity structure relative to job 1:
    #   job 2 is nearly identical, job 3 is orthogonal-ish, job 4 is opposite.
    embeddings = _normalize(
        np.array(
            [
                [1.0, 0.0, 0.0],   # job 1
                [0.9, 0.1, 0.0],   # job 2 — most similar to job 1
                [0.0, 1.0, 0.0],   # job 3
                [-1.0, 0.0, 0.0],  # job 4 — least similar to job 1
            ]
        )
    )
    return CandidateIndex(embeddings, job_ids=[1, 2, 3, 4])


def test_top_k_orders_by_similarity_and_excludes_self(small_index):
    results = small_index.top_k(job_id=1, k=3)
    result_ids = [job_id for job_id, _ in results]

    assert 1 not in result_ids, "target job must be excluded"
    assert result_ids == [2, 3, 4], "candidates must be ordered by similarity"

    scores = [score for _, score in results]
    assert scores == sorted(scores, reverse=True)


def test_top_k_matches_exact_full_scan(small_index):
    """IndexFlatIP is exact: results must equal a brute-force numpy ranking."""
    embeddings = small_index._matrix
    target = small_index.vector_for(1)
    full_scores = embeddings @ target

    brute_force = sorted(
        (
            (job_id, float(score))
            for job_id, score in zip([1, 2, 3, 4], full_scores)
            if job_id != 1
        ),
        key=lambda pair: pair[1],
        reverse=True,
    )

    assert small_index.top_k(job_id=1, k=3) == pytest.approx(brute_force)


def test_top_k_caps_at_corpus_size(small_index):
    results = small_index.top_k(job_id=1, k=100)
    assert len(results) == 3  # corpus of 4 minus the target itself


def test_top_k_zero_or_negative_k(small_index):
    assert small_index.top_k(job_id=1, k=0) == []
    assert small_index.top_k(job_id=1, k=-5) == []


def test_unknown_job_raises(small_index):
    with pytest.raises(UnknownJobError):
        small_index.top_k(job_id=999, k=3)
    with pytest.raises(UnknownJobError):
        small_index.vector_for(999)


def test_contains_and_len(small_index):
    assert len(small_index) == 4
    assert 3 in small_index
    assert 999 not in small_index


def test_mismatched_lengths_rejected():
    embeddings = _normalize(np.ones((3, 4)))
    with pytest.raises(ValueError):
        CandidateIndex(embeddings, job_ids=[1, 2])


def test_empty_embeddings_rejected():
    with pytest.raises(ValueError):
        CandidateIndex(np.empty((0, 3), dtype=np.float32), job_ids=[])