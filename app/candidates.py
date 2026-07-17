"""FAISS-backed candidate generation for the recommendation service.

Stage 1 of the two-stage recommendation flow:

    CandidateIndex.top_k()  ->  small candidate set (K jobs)
    hybrid re-scoring        ->  final ranking (Day 4, recommend_service)

Design notes
------------
- ``IndexFlatIP`` performs *exact* inner-product search. Embeddings are
  L2-normalized at build time (pipeline/build_embeddings.py), so inner
  product equals cosine similarity and results are identical to the
  previous full matrix multiplication — only cheaper to post-process,
  because downstream DB loading and re-scoring shrink from N rows to K.
- The index is constructed in-memory when artifacts are loaded. For a
  flat index, "building" is just copying vectors (milliseconds at ~19k
  vectors), so persisting it as a pipeline artifact would only create a
  consistency problem between the index and ``job_embeddings.npy``.
- If the corpus grows to a scale where exact search becomes the
  bottleneck (millions of vectors), swap the index type here (e.g.
  ``IndexIVFFlat``/HNSW) without touching the service layer.
"""

from __future__ import annotations

import faiss
import numpy as np


class UnknownJobError(KeyError):
    """Raised when a job_id has no embedding in the index."""


class CandidateIndex:
    """Exact top-K similarity search over job embeddings."""

    def __init__(self, embeddings: np.ndarray, job_ids: list[int]):
        if len(embeddings) != len(job_ids):
            raise ValueError(
                "embeddings and job_ids length mismatch: "
                f"{len(embeddings)} != {len(job_ids)}"
            )
        if len(embeddings) == 0:
            raise ValueError("Cannot build CandidateIndex from empty embeddings.")

        matrix = np.ascontiguousarray(embeddings, dtype=np.float32)
        if matrix.ndim != 2:
            raise ValueError(f"Expected 2D embeddings, got shape {matrix.shape}")

        self._job_ids = list(job_ids)
        self._id_to_idx = {job_id: idx for idx, job_id in enumerate(self._job_ids)}
        self._index = faiss.IndexFlatIP(matrix.shape[1])
        self._index.add(matrix)
        self._matrix = matrix

    def __len__(self) -> int:
        return len(self._job_ids)

    def __contains__(self, job_id: int) -> bool:
        return job_id in self._id_to_idx

    def vector_for(self, job_id: int) -> np.ndarray:
        idx = self._id_to_idx.get(job_id)
        if idx is None:
            raise UnknownJobError(job_id)
        return self._matrix[idx]

    def top_k(self, job_id: int, k: int) -> list[tuple[int, float]]:
        """Return up to ``k`` most similar jobs as (job_id, score) pairs.

        The target job itself is excluded. ``k`` is capped at corpus
        size; requesting more than available simply returns fewer pairs.
        """
        if k <= 0:
            return []

        target_idx = self._id_to_idx.get(job_id)
        if target_idx is None:
            raise UnknownJobError(job_id)

        # +1 because the target job is its own nearest neighbor and gets
        # filtered out below.
        search_k = min(k + 1, len(self._job_ids))
        query = self._matrix[target_idx : target_idx + 1]
        scores, indices = self._index.search(query, search_k)

        results: list[tuple[int, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx == target_idx:
                continue
            results.append((self._job_ids[idx], float(score)))
            if len(results) == k:
                break
        return results