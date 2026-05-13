from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import JobListResponse, JobResponse, RecommendedJobResponse
from app.services.jobs_service import list_jobs, read_job
from app.services.recommend_service import list_recommendations

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
def read_jobs(
    keyword: str | None = Query(default=None),
    location: str | None = Query(default=None),
    category: str | None = Query(default=None),
    seniority: str | None = Query(default=None),
    skills: str | None = Query(
        default=None,
        description="Comma-separated skills. Example: python,sql,fastapi",
    ),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    sort_by: Literal[
        "date_posted",
        "title",
        "company",
        "location",
        "category",
        "seniority",
    ] = "date_posted",
    sort_order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
):
    return list_jobs(
        db=db,
        keyword=keyword,
        location=location,
        category=category,
        seniority=seniority,
        skills=skills,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/{job_id}", response_model=JobResponse)
def read_job_detail(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = read_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/recommendations", response_model=list[RecommendedJobResponse])
def read_job_recommendations(
    request: Request,
    job_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    same_category_only: bool = Query(default=False),
    min_shared_skills: int = Query(default=0, ge=0, le=10),
    min_embedding_score: float | None = Query(default=None, ge=-1.0, le=1.0),
    db: Session = Depends(get_db),
):
    return list_recommendations(
        db=db,
        request=request,
        job_id=job_id,
        limit=limit,
        same_category_only=same_category_only,
        min_shared_skills=min_shared_skills,
        min_embedding_score=min_embedding_score,
    )