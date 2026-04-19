import json

import numpy as np
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.config import EMBEDDING_PATH, JOB_IDS_PATH
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


def _build_ranked_recommendations(
    db: Session,
    *,
    job_id: int,
    embeddings,
    job_ids,
    limit: int = 5,
    same_category_only: bool = False,
):
    target_job = db.query(Job).filter(Job.id == job_id).first()
    if not target_job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_id not in job_ids:
        raise HTTPException(status_code=404, detail="Embedding not found for this job")

    target_idx = job_ids.index(job_id)
    target_vec = embeddings[target_idx]
    target_skills = parse_skills(target_job.detected_skills)
    embedding_scores = embeddings @ target_vec

    candidate_jobs = db.query(Job).filter(Job.id.in_(job_ids)).all()
    candidate_jobs_by_id = {job.id: job for job in candidate_jobs}

    ranked = []

    for idx, embedding_score in enumerate(embedding_scores):
        candidate_id = job_ids[idx]
        if candidate_id == job_id:
            continue

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
                "score": score,
                "embedding_score": embedding_score_value,
                "skill_overlap_score": skill_overlap_score,
                "shared_skills": shared_skills,
                "same_category": same_category,
                "same_seniority": same_seniority,
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:limit]


def list_recommendations(
    db: Session,
    request: Request,
    job_id: int,
    limit: int = 5,
    same_category_only: bool = False,
):
    embeddings, job_ids = get_cached_embeddings(request)

    return _build_ranked_recommendations(
        db=db,
        job_id=job_id,
        embeddings=embeddings,
        job_ids=job_ids,
        limit=limit,
        same_category_only=same_category_only,
    )


def list_recommendations_for_offline_eval(
    db: Session,
    job_id: int,
    limit: int = 5,
    same_category_only: bool = False,
):
    embeddings, job_ids = load_embeddings()

    return _build_ranked_recommendations(
        db=db,
        job_id=job_id,
        embeddings=embeddings,
        job_ids=job_ids,
        limit=limit,
        same_category_only=same_category_only,
    )