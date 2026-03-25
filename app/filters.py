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

def apply_result_filters(
    results: list[dict],
    category: str | None = None,
    location: str | None = None,
    seniority: str | None = None,
) -> list[dict]:
    filtered = []

    for r in results:
        if category and (r.get("category") or "").lower() != category.lower():
            continue
        if location and (r.get("location") or "").lower() != location.lower():
            continue
        if seniority and (r.get("seniority") or "").lower() != seniority.lower():
            continue
        filtered.append(r)

    return filtered