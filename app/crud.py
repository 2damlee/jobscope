from collections import Counter

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
        keyword_term = f"%{keyword.strip()}%"
        query = query.filter(Job.title.ilike(keyword_term))

    if location:
        location_term = f"%{location.strip()}%"
        query = query.filter(Job.location.ilike(location_term))

    if category:
        category_term = f"%{category.strip()}%"
        query = query.filter(Job.category.ilike(category_term))

    if seniority:
        seniority_term = f"%{seniority.strip()}%"
        query = query.filter(Job.seniority.ilike(seniority_term))

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
        category_term = f"%{category.strip()}%"
        query = query.filter(Job.category.ilike(category_term))

    if seniority:
        seniority_term = f"%{seniority.strip()}%"
        query = query.filter(Job.seniority.ilike(seniority_term))

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