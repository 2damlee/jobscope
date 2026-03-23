from sqlalchemy.orm import Session
from app.models import Job


def get_jobs(
    db: Session,
    keyword: str | None = None,
    location: str | None = None,
    category: str | None = None,
    limit: int = 20,
):
    query = db.query(Job)

    if keyword:
        query = query.filter(Job.title.ilike(f"%{keyword}%") | Job.description.ilike(f"%{keyword}%"))

    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    if category:
        query = query.filter(Job.category.ilike(f"%{category}%"))

    return query.limit(limit).all()