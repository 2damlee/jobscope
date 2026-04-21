from sqlalchemy import asc, desc, or_, text
from sqlalchemy.orm import Session

from app.models import Job


def get_job_by_id(db: Session, job_id: int) -> Job | None:
    return db.query(Job).filter(Job.id == job_id).first()


def get_jobs(
    db: Session,
    keyword: str | None = None,
    location: str | None = None,
    category: str | None = None,
    seniority: str | None = None,
    skills: str | None = None,
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
                Job.cleaned_description.ilike(keyword_term),
            )
        )

    if location:
        query = query.filter(Job.location.ilike(f"%{location.strip()}%"))

    if category:
        query = query.filter(Job.category.ilike(f"%{category.strip()}%"))

    if seniority:
        query = query.filter(Job.seniority.ilike(f"%{seniority.strip()}%"))

    if skills:
        skill_list = [skill.strip() for skill in skills.split(",") if skill.strip()]
        for skill in skill_list:
            query = query.filter(Job.detected_skills.ilike(f"%{skill}%"))

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
    filters = ["detected_skills IS NOT NULL", "detected_skills != ''"]
    params: dict[str, object] = {"limit": limit}

    if category:
        filters.append("category ILIKE :category")
        params["category"] = f"%{category.strip()}%"

    if seniority:
        filters.append("seniority ILIKE :seniority")
        params["seniority"] = f"%{seniority.strip()}%"

    where_clause = " AND ".join(filters)

    query = text(
        f"""
        SELECT skill, COUNT(*) AS count
        FROM (
            SELECT TRIM(unnest(string_to_array(detected_skills, ','))) AS skill
            FROM jobs
            WHERE {where_clause}
        ) AS expanded
        WHERE skill != ''
        GROUP BY skill
        ORDER BY count DESC, skill ASC
        LIMIT :limit
        """
    )

    rows = db.execute(query, params).fetchall()

    return [{"skill": row.skill, "count": row.count} for row in rows]