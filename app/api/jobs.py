from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.crud import get_jobs
from app.db import get_db
from app.schemas import JobListResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
def list_jobs(
    keyword: str | None = None,
    location: str | None = None,
    category: str | None = None,
    seniority: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("date_posted"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db),
):
    result = get_jobs(
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

    return result