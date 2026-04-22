import subprocess
import time

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine


def _table_exists(table_name: str) -> bool:
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def _has_alembic_version_row() -> bool:
    if not _table_exists("alembic_version"):
        return False

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) FROM alembic_version"))
            count = result.scalar() or 0
            return count > 0
    except SQLAlchemyError:
        return False


def _reconcile_legacy_schema() -> int:
    jobs_exists = _table_exists("jobs")
    pipeline_runs_exists = _table_exists("pipeline_runs")
    has_revision = _has_alembic_version_row()

    if (jobs_exists or pipeline_runs_exists) and not has_revision:
        print(
            "Existing tables detected without alembic_version. "
            "Stamping database to head."
        )
        result = subprocess.run(["alembic", "stamp", "head"], check=False)
        if result.returncode != 0:
            print("Failed to stamp existing database to head.")
            return result.returncode

    return 0


def wait_for_db(max_attempts: int = 30, sleep_seconds: int = 2) -> int:
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print(f"Database is ready (attempt {attempt}/{max_attempts}).")
            return _reconcile_legacy_schema()
        except SQLAlchemyError as exc:
            print(
                f"Database not ready yet "
                f"(attempt {attempt}/{max_attempts}): {exc}"
            )
            time.sleep(sleep_seconds)

    print("Database connection failed after maximum retry attempts.")
    return 1


if __name__ == "__main__":
    raise SystemExit(wait_for_db())