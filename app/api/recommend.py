import json
import os
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Job
from app.schemas import RecommendedJobResponse
from app.recommendation import parse_skills, compute_hybrid_score

EMBEDDING_PATH = "data/processed/job_embeddings.npy"
JOB_IDS_PATH = "data/processed/job_ids.json"

router = APIRouter(prefix="/recommend", tags=["recommend"])


def load_embeddings():
    if not os.path.exists(EMBEDDING_PATH) or not os.path.exists(JOB_IDS_PATH):
        raise HTTPException(status_code=500, detail="Embedding files not found. Run build_embeddings first.")

    embeddings = np.load(EMBEDDING_PATH)
    with open(JOB_IDS_PATH, "r") as f:
        job_ids = json.load(f)

    if len(embeddings) == 0 or len(job_ids) == 0:
        raise HTTPException(status_code=500, detail="Embedding data is empty.")

    if len(embeddings) != len(job_ids):
        raise HTTPException(status_code=500, detail="Embedding data is inconsistent.")

    return embeddings, job_ids


@router.get("/{job_id}", response_model=list[RecommendedJobResponse])
def recommend_jobs(
    job_id: int,
    limit: int = Query(default=5, le=20),
    same_category_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    target_job = db.query(Job).filter(Job.id == job_id).first()
    if not target_job:
        raise HTTPException(status_code=404, detail="Job not found")

    embeddings, job_ids = load_embeddings()

    if job_id not in job_ids:
        raise HTTPException(status_code=404, detail="Embedding not found for this job")

    target_idx = job_ids.index(job_id)
    target_vec = embeddings[target_idx]
    target_skills = parse_skills(target_job.detected_skills)

    embedding_scores = embeddings @ target_vec
    ranked = []

    for idx, embedding_score in enumerate(embedding_scores):
        candidate_id = job_ids[idx]
        if candidate_id == job_id:
            continue

        candidate_job = db.query(Job).filter(Job.id == candidate_id).first()
        if not candidate_job:
            continue

        if not candidate_job.title:
            continue

        same_category = bool((target_job.category or "") == (candidate_job.category or ""))
        same_seniority = bool((target_job.seniority or "") == (candidate_job.seniority or ""))

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

        if np.isnan(score) or np.isnan(embedding_score_value) or np.isnan(skill_overlap_score):
            continue

        ranked.append({
            "job_id": int(candidate_job.id),
            "title": str(candidate_job.title),
            "score": score,
            "embedding_score": embedding_score_value,
            "skill_overlap_score": skill_overlap_score,
            "shared_skills": shared_skills,
            "same_category": same_category,
            "same_seniority": same_seniority,
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:limit]