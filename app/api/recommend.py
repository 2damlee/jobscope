import json
import os
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Job
from app.schemas import RecommendedJobResponse

EMBEDDING_PATH = "data/processed/job_embeddings.npy"
JOB_IDS_PATH = "data/processed/job_ids.json"

router = APIRouter(prefix="/recommend", tags=["recommend"])


def load_embeddings():
    if not os.path.exists(EMBEDDING_PATH) or not os.path.exists(JOB_IDS_PATH):
        raise HTTPException(status_code=500, detail="Embedding files not found. Run build_embeddings first.")

    embeddings = np.load(EMBEDDING_PATH)

    with open(JOB_IDS_PATH, "r") as f:
        job_ids = json.load(f)

    if len(job_ids) == 0 or len(embeddings) == 0:
        raise HTTPException(status_code=500, detail="Embedding data is empty.")

    return embeddings, job_ids


@router.get("/{job_id}", response_model=list[RecommendedJobResponse])
def recommend_jobs(
    job_id: int,
    limit: int = Query(default=5, le=20),
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

    scores = embeddings @ target_vec

    ranked = []
    for idx, score in enumerate(scores):
        candidate_id = job_ids[idx]
        if candidate_id == job_id:
            continue
        ranked.append((candidate_id, float(score)))

    ranked.sort(key=lambda x: x[1], reverse=True)
    top_k = ranked[:limit]

    results = []
    for candidate_id, score in top_k:
        job = db.query(Job).filter(Job.id == candidate_id).first()
        if job:
            results.append({
                "job_id": job.id,
                "title": job.title,
                "score": round(score, 4),
            })

    return results