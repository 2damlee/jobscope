from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.models import Job


def get_jobs(
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
    query = db.query(Job)

    if keyword:
        query = query.filter(Job.title.ilike(f"%{keyword}%"))

    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    if category:
        query = query.filter(Job.category.ilike(f"%{category}%"))

    if seniority:
        query = query.filter(Job.seniority.ilike(f"%{seniority}%"))

    allowed_sort_fields = {
        "date_posted": Job.date_posted,
        "title": Job.title,
        "company": Job.company,
        "location": Job.location,
        "category": Job.category,
        "seniority": Job.seniority,
    }

    sort_column = allowed_sort_fields.get(sort_by, Job.date_posted)
    order_fn = desc if sort_order.lower() == "desc" else asc

    total = query.count()

    items = (
        query.order_by(order_fn(sort_column))
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
    }