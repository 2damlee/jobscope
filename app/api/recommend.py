from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import RecommendedJobResponse
from app.services.recommend_service import list_recommendations

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.get("/{job_id}", response_model=list[RecommendedJobResponse])
def read_recommendations(
    job_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    same_category_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    return list_recommendations(
        db=db,
        job_id=job_id,
        limit=limit,
        same_category_only=same_category_only,
    )