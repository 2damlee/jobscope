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
    return recommend_jobs_for_job(
        db,
        job_id,
        limit=limit,
        same_category_only=same_category_only,
    )