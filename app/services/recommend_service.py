import json

import numpy as np
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.candidates import CandidateIndex
from app.config import EMBEDDING_PATH, JOB_IDS_PATH, RECOMMEND_CANDIDATE_POOL
from app.models import Job
from app.recommendation import compute_hybrid_score, parse_skills


def load_embeddings_from_disk():
    if not EMBEDDING_PATH.exists() or not JOB_IDS_PATH.exists():
        raise FileNotFoundError(
            f"Embedding files not found: {EMBEDDING_PATH} and {JOB_IDS_PATH}"
        )

    embeddings = np.load(EMBEDDING_PATH)
    with JOB_IDS_PATH.open("r", encoding="utf-8") as f:
        job_ids = json.load(f)

    if len(embeddings) == 0 or len(job_ids) == 0:
        raise ValueError("Embedding data is empty.")

    if len(embeddings) != len(job_ids):
        raise ValueError("Embedding data is inconsistent.")

    return embeddings, job_ids


def load_embeddings():
    try:
        return load_embeddings_from_disk()
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Embedding files not found. "
                f"expected={EMBEDDING_PATH} and {JOB_IDS_PATH}. "
                "Run build_embeddings first."
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


def get_cached_embeddings(request: Request):
    embeddings = getattr(request.app.state, "embeddings", None)
    job_ids = getattr(request.app.state, "job_ids", None)

    if embeddings is None or job_ids is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Recommendation artifacts are not loaded. "
                "Run build_embeddings and restart the app."
            ),
        )

    return embeddings, job_ids


def get_candidate_index(request: Request) -> CandidateIndex:
    """Return the app-wide CandidateIndex, building it lazily if needed.

    The index is cached on app.state and keyed to the identity of the
    embeddings array: if the embeddings are ever swapped (e.g. artifact
    reload), the index is rebuilt automatically on the next request.
    """
    embeddings, job_ids = get_cached_embeddings(request)

    state = request.app.state
    cached = getattr(state, "candidate_index", None)
    source = getattr(state, "candidate_index_source", None)
    if cached is not None and source is embeddings:
        return cached

    index = CandidateIndex(embeddings, job_ids)
    state.candidate_index = index
    state.candidate_index_source = embeddings
    return index


def _build_ranked_recommendations(
    db: Session,
    *,
    job_id: int,
    candidate_index: CandidateIndex,
    limit: int = 5,
    same_category_only: bool = False,
    min_shared_skills: int = 0,
    min_embedding_score: float | None = None,
    candidate_pool: int = RECOMMEND_CANDIDATE_POOL,
):
    target_job = db.query(Job).filter(Job.id == job_id).first()
    if not target_job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_id not in candidate_index:
        raise HTTPException(status_code=404, detail="Embedding not found for this job")

    target_skills = parse_skills(target_job.detected_skills)

    # Stage 1: exact top-K candidate generation (FAISS), instead of scoring
    # and loading every job in the corpus on each request.
    candidates = candidate_index.top_k(job_id, candidate_pool)
    candidate_ids = [candidate_id for candidate_id, _ in candidates]
    score_by_id = {candidate_id: score for candidate_id, score in candidates}

    # Stage 2: load only the candidate rows and apply hybrid re-scoring.
    candidate_jobs = db.query(Job).filter(Job.id.in_(candidate_ids)).all()
    candidate_jobs_by_id = {job.id: job for job in candidate_jobs}

    ranked = []

    for candidate_id in candidate_ids:
        embedding_score = score_by_id[candidate_id]

        candidate_job = candidate_jobs_by_id.get(candidate_id)
        if not candidate_job or not candidate_job.title:
            continue

        same_category = bool((target_job.category or "") == (candidate_job.category or ""))
        same_seniority = bool(
            (target_job.seniority or "") == (candidate_job.seniority or "")
        )

        if same_category_only and not same_category:
            continue

        candidate_skills = parse_skills(candidate_job.detected_skills)
        shared_skills = sorted(list(target_skills & candidate_skills))

        if len(shared_skills) < min_shared_skills:
            continue

        if min_embedding_score is not None and float(embedding_score) < min_embedding_score:
            continue

        score_parts = compute_hybrid_score(
            embedding_score=float(embedding_score),
            target_skills=target_skills,
            candidate_skills=candidate_skills,
            same_category=same_category,
            same_seniority=same_seniority,
        )

        score = float(score_parts["final_score"])
        embedding_score_value = float(score_parts["embedding_score"])
        skill_overlap_score = float(score_parts["skill_overlap_score"])

        if (
            np.isnan(score)
            or np.isnan(embedding_score_value)
            or np.isnan(skill_overlap_score)
        ):
            continue

        ranked.append(
            {
                "job_id": int(candidate_job.id),
                "title": str(candidate_job.title),
                "company": candidate_job.company,
                "location": candidate_job.location,
                "category": candidate_job.category,
                "seniority": candidate_job.seniority,
                "url": candidate_job.url,
                "score": score,
                "embedding_score": embedding_score_value,
                "skill_overlap_score": skill_overlap_score,
                "shared_skills": shared_skills,
                "same_category": same_category,
                "same_seniority": same_seniority,
            }
        )

    ranked.sort(
        key=lambda x: (
            x["score"],
            x["embedding_score"],
            len(x["shared_skills"]),
            x["same_category"],
            x["same_seniority"],
        ),
        reverse=True,
    )

    return ranked[:limit]


def list_recommendations(
    db: Session,
    request: Request,
    job_id: int,
    limit: int = 5,
    same_category_only: bool = False,
    min_shared_skills: int = 0,
    min_embedding_score: float | None = None,
):
    candidate_index = get_candidate_index(request)
    return _build_ranked_recommendations(
        db=db,
        job_id=job_id,
        candidate_index=candidate_index,
        limit=limit,
        same_category_only=same_category_only,
        min_shared_skills=min_shared_skills,
        min_embedding_score=min_embedding_score,
    )


def list_recommendations_for_offline_eval(
    db: Session,
    job_id: int,
    limit: int = 5,
    same_category_only: bool = False,
    min_shared_skills: int = 0,
    min_embedding_score: float | None = None,
    candidate_index: CandidateIndex | None = None,
):
    if candidate_index is None:
        embeddings, job_ids = load_embeddings()
        candidate_index = CandidateIndex(embeddings, job_ids)

    return _build_ranked_recommendations(
        db=db,
        job_id=job_id,
        candidate_index=candidate_index,
        limit=limit,
        same_category_only=same_category_only,
        min_shared_skills=min_shared_skills,
        min_embedding_score=min_embedding_score,
    )