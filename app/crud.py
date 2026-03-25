from collections import Counter
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Job


ALLOWED_SORT_FIELDS = {
    "date_posted": Job.date_posted,
    "title": Job.title,
    "company": Job.company,
}


def get_jobs(
    db: Session,
    keyword: str | None = None,
    location: str | None = None,
    category: str | None = None,
    seniority: str | None = None,
    page: int = 1,
    size: int = 10,
    sort_by: str = "date_posted",
    sort_order: str = "desc",
):
    query = db.query(Job)

    if keyword:
        query = query.filter(
            or_(
                Job.title.ilike(f"%{keyword}%"),
                Job.description.ilike(f"%{keyword}%"),
            )
        )

    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    if category:
        query = query.filter(Job.category.ilike(f"%{category}%"))

    if seniority:
        query = query.filter(Job.seniority.ilike(f"%{seniority}%"))

    total = query.count()

    sort_column = ALLOWED_SORT_FIELDS.get(sort_by, Job.date_posted)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "has_next": offset + size < total,
    }


def get_top_skills(
    db: Session,
    category: str | None = None,
    seniority: str | None = None,
    limit: int = 10,
):
    query = db.query(Job)

    if category:
        query = query.filter(Job.category.ilike(f"%{category}%"))

    if seniority:
        query = query.filter(Job.seniority.ilike(f"%{seniority}%"))

    jobs = query.all()

    counter = Counter()

    for job in jobs:
        if not job.detected_skills:
            continue

        skills = [s.strip() for s in job.detected_skills.split(",") if s.strip()]
        counter.update(skills)

    return [{"skill": skill, "count": count} for skill, count in counter.most_common(limit)]