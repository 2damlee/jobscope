from sqlalchemy.orm import Session

from app.crud import get_top_skills


def list_top_skills(
    db: Session,
    category: str | None = None,
    seniority: str | None = None,
    limit: int = 10,
):
    normalized_category = category.strip().lower() if category else None
    normalized_seniority = seniority.strip().lower() if seniority else None
    normalized_limit = min(max(limit, 1), 50)

    return get_top_skills(
        db=db,
        category=normalized_category,
        seniority=normalized_seniority,
        limit=normalized_limit,
    )