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
    normalized_keyword = keyword.strip() if keyword else None
    if normalized_keyword and len(normalized_keyword) < 2:
        normalized_keyword = None

    normalized_location = location.strip() if location else None
    normalized_category = category.strip().lower() if category else None
    normalized_seniority = seniority.strip().lower() if seniority else None

    return get_jobs(
        db=db,
        keyword=normalized_keyword,
        location=normalized_location,
        category=normalized_category,
        seniority=normalized_seniority,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order,
    )