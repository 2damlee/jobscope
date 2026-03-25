import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.crud import get_jobs
from app.schemas import JobsListResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobsListResponse)
def read_jobs(
    keyword: str | None = Query(default=None),
    location: str | None = Query(default=None),
    category: str | None = Query(default=None),
    seniority: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    sort_by: str = Query(default="date_posted"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    return get_jobs(
        db=db,
        keyword=keyword,
        location=location,
        category=category,
        seniority=seniority,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order,
    )