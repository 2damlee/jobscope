import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
from app.db import SessionLocal
from app.models import Job


CSV_PATH = "../data/raw/jobs.csv"


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def parse_date(value):
    if pd.isna(value):
        return None
    dt = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(dt) else dt.date()


def clean_text(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text if text else None


def ingest_jobs():
    df = load_csv(CSV_PATH)
    db = SessionLocal()

    try:
        for _, row in df.iterrows():
            job = Job(
                title=clean_text(row["title"]),
                company=clean_text(row["company"]),
                location=clean_text(row["location"]),
                category=clean_text(row["category"]),
                seniority=clean_text(row["seniority"]),
                description=clean_text(row["description"]),
                cleaned_description=None,
                detected_skills=None,
                date_posted=parse_date(row["date_posted"]),
                url=clean_text(row["url"]),
            )
            db.add(job)

        db.commit()
        print(f"Inserted {len(df)} jobs.")

    except Exception as e:
        db.rollback()
        print("Ingest failed:", e)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    ingest_jobs()