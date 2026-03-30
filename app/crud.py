from collections import Counter

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
        query = query.filter(
            Job.title.ilike(f"%{keyword}%") | Job.description.ilike(f"%{keyword}%")
        )

    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    if category:
        query = query.filter(Job.category.ilike(f"%{category}%"))

    return query.limit(limit).all()


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