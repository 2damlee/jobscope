from sqlalchemy.orm import Session

from app.crud import get_jobs


def list_jobs(
    db: Session,
    keyword: str | None = None,
    location: str | None = None,
    category: str | None = None,
    seniority: str | None = None,
    page: int = 1,
    size: int = 20,
    sort_by: str = "date_posted",
    sort_order: str = "desc",
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