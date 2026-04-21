from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import JobListResponse, JobResponse
from app.services.jobs_service import list_jobs, read_job

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