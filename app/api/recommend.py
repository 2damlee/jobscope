from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import RecommendedJobResponse
from app.services.recommend_service import list_recommendations

router = APIRouter(prefix="/recommend", tags=["recommend"])


# Legacy route — kept for backwards compatibility.
# Prefer: GET /jobs/{job_id}/recommendations
@router.get("/{job_id}", response_model=list[RecommendedJobResponse])
async def read_recommendations(
    request: Request,
    job_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    same_category_only: bool = Query(default=False),
    min_shared_skills: int = Query(default=0, ge=0, le=10),
    min_embedding_score: float | None = Query(default=None, ge=-1.0, le=1.0),
    db: AsyncSession = Depends(get_db),
):
    return await list_recommendations(
        db=db,
        request=request,
        job_id=job_id,
        limit=limit,
        same_category_only=same_category_only,
        min_shared_skills=min_shared_skills,
        min_embedding_score=min_embedding_score,
    )