from sqlalchemy.orm import Session

from app.crud import get_jobs


def list_jobs(
    db: Session,
    keyword: str | None = None,
    location: str | None = None,
    category: str | None = None,
    limit: int = 20,
):
    return get_jobs(
        db=db,
        keyword=keyword,
        location=location,
        category=category,
        limit=limit,
    )