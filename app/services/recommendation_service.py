import json
import os

import numpy as np
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.recommendation import build_recommendation_rows, parse_skills
from app.repositories.job_repository import get_job_by_id, get_jobs_by_ids

EMBEDDING_PATH = "data/processed/job_embeddings.npy"
JOB_IDS_PATH = "data/processed/job_ids.json"


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


def recommend_jobs_for_job(
    db: Session,
    job_id: int,
    *,
    limit: int = 5,
    same_category_only: bool = False,
) -> list[dict]:
    target_job = get_job_by_id(db, job_id)
    if not target_job:
        raise HTTPException(status_code=404, detail="Job not found")

    embeddings, embedding_job_ids = load_embeddings()

    if job_id not in embedding_job_ids:
        raise HTTPException(status_code=404, detail="Embedding not found for this job")

    target_idx = embedding_job_ids.index(job_id)
    target_vec = embeddings[target_idx]
    target_skills = parse_skills(target_job.detected_skills)

    embedding_scores = embeddings @ target_vec

    candidate_ids = [candidate_id for candidate_id in embedding_job_ids if candidate_id != job_id]
    candidate_jobs = get_jobs_by_ids(db, candidate_ids)
    candidate_map = {job.id: job for job in candidate_jobs}

    ranked = build_recommendation_rows(
        target_job=target_job,
        target_skills=target_skills,
        embedding_job_ids=embedding_job_ids,
        embedding_scores=embedding_scores,
        candidate_map=candidate_map,
        limit=limit,
        same_category_only=same_category_only,
    )

    return ranked