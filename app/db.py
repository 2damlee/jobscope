from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import (
    DATABASE_URL,
    DB_CONNECT_TIMEOUT_SECONDS,
    DB_POOL_PRE_PING,
    DB_POOL_RECYCLE_SECONDS,
)

engine_kwargs = {
    "pool_pre_ping": DB_POOL_PRE_PING,
    "pool_recycle": DB_POOL_RECYCLE_SECONDS,
}

if DATABASE_URL.startswith("postgresql"):
    engine_kwargs["connect_args"] = {
        "connect_timeout": DB_CONNECT_TIMEOUT_SECONDS,
    }

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()