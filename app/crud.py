from sqlalchemy import asc, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, PipelineRun


async def get_job_by_id(db: AsyncSession, job_id: int) -> Job | None:
    result = await db.execute(select(Job).where(Job.id == job_id))
    return result.scalar_one_or_none()


async def get_jobs(
    db: AsyncSession,
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
    stmt = select(Job)

    if keyword:
        term = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                Job.title.ilike(term),
                Job.description.ilike(term),
                Job.cleaned_description.ilike(term),
            )
        )

    if location:
        stmt = stmt.where(Job.location.ilike(f"%{location.strip()}%"))

    if category:
        stmt = stmt.where(Job.category.ilike(f"%{category.strip()}%"))

    if seniority:
        stmt = stmt.where(Job.seniority.ilike(f"%{seniority.strip()}%"))

    if skills:
        for skill in [s.strip() for s in skills.split(",") if s.strip()]:
            stmt = stmt.where(Job.detected_skills.ilike(f"%{skill}%"))

    allowed_sort_fields = {
        "date_posted": Job.date_posted,
        "title": Job.title,
        "company": Job.company,
        "location": Job.location,
        "category": Job.category,
        "seniority": Job.seniority,
    }
    sort_col = allowed_sort_fields.get(sort_by, Job.date_posted)
    stmt = stmt.order_by(desc(sort_col) if sort_order.lower() == "desc" else asc(sort_col))

    # COUNT via subquery — works for both SQLite and PostgreSQL
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    paginated = stmt.offset((page - 1) * size).limit(size)
    items = (await db.execute(paginated)).scalars().all()

    return {"items": items, "page": page, "size": size, "total": total}


async def get_top_skills(
    db: AsyncSession,
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

    # PostgreSQL-specific: unnest + string_to_array for skill aggregation.
    # This endpoint is intentionally PostgreSQL-only; SQLite does not support unnest.
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

    rows = (await db.execute(query, params)).fetchall()
    return [{"skill": row.skill, "count": row.count} for row in rows]


async def get_pipeline_runs(db: AsyncSession, limit: int = 10) -> list[PipelineRun]:
    result = await db.execute(
        select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(limit)
    )
    return result.scalars().all()