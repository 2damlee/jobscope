from collections import Counter

from sqlalchemy import asc, desc, or_
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
        keyword_term = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(keyword_term),
                Job.description.ilike(keyword_term),
            )
        )

    if location:
        query = query.filter(Job.location.ilike(f"%{location.strip()}%"))

    if category:
        query = query.filter(Job.category.ilike(f"%{category.strip()}%"))

    if seniority:
        query = query.filter(Job.seniority.ilike(f"%{seniority.strip()}%"))

    allowed_sort_fields = {
        "date_posted": Job.date_posted,
        "title": Job.title,
        "company": Job.company,
        "location": Job.location,
        "category": Job.category,
        "seniority": Job.seniority,
    }

    sort_column = allowed_sort_fields.get(sort_by, Job.date_posted)
    sort_fn = desc if sort_order.lower() == "desc" else asc

    total = query.count()

    items = (
        query.order_by(sort_fn(sort_column))
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


def get_top_skills(
    db: Session,
    category: str | None = None,
    seniority: str | None = None,
    limit: int = 10,
):
    query = db.query(Job)

    if category:
        query = query.filter(Job.category.ilike(f"%{category.strip()}%"))

    if seniority:
        query = query.filter(Job.seniority.ilike(f"%{seniority.strip()}%"))

    jobs = query.all()

    counter = Counter()
    for job in jobs:
        if not job.detected_skills:
            continue

        skills = [
            skill.strip()
            for skill in job.detected_skills.split(",")
            if skill.strip()
        ]
        counter.update(skills)

    return [
        {"skill": skill, "count": count}
        for skill, count in counter.most_common(limit)
    ]