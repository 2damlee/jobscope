import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine


def wait_for_db(max_attempts: int = 30, sleep_seconds: int = 2) -> int:
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print(f"Database is ready (attempt {attempt}/{max_attempts}).")
            return 0
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