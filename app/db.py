from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import (
    DATABASE_URL,
    DB_POOL_PRE_PING,
    DB_POOL_RECYCLE_SECONDS,
)


def _make_async_url(url: str) -> str:
    """Convert a sync DB URL to its async driver equivalent."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return url


ASYNC_DATABASE_URL = _make_async_url(DATABASE_URL)

# asyncpg does not accept command_timeout via connect_args.
# Use execution_options per-query if statement-level timeout is needed.
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=DB_POOL_PRE_PING,
    pool_recycle=DB_POOL_RECYCLE_SECONDS,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session