from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import get_top_skills


async def list_top_skills(
    db: AsyncSession,
    category: str | None = None,
    seniority: str | None = None,
    limit: int = 10,
):
    normalized_category = category.strip().lower() if category else None
    normalized_seniority = seniority.strip().lower() if seniority else None
    normalized_limit = min(max(limit, 1), 50)

    return await get_top_skills(
        db=db,
        category=normalized_category,
        seniority=normalized_seniority,
        limit=normalized_limit,
    )