import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import SkillCountResponse
from app.services.analytics_service import list_top_skills

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/skills", response_model=list[SkillCountResponse])
def read_top_skills(
    category: str | None = Query(default=None),
    seniority: str | None = Query(default=None),
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db),
):
    return list_top_skills(
        db=db,
        category=category,
        seniority=seniority,
        limit=limit,
    )