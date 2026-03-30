from sqlalchemy.orm import Session

from app.crud import get_top_skills


def list_top_skills(
    db: Session,
    category: str | None = None,
    seniority: str | None = None,
    limit: int = 10,
):
    return get_top_skills(
        db=db,
        category=category,
        seniority=seniority,
        limit=limit,
    )