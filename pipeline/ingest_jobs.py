import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
from app.db import SessionLocal
from app.models import Job


CSV_PATH = "data/raw/jobs.csv"
MIN_DESCRIPTION_LENGTH = 20


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def clean_text(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text if text else None


def normalize_location(value):
    text = clean_text(value)
    if not text:
        return None

    mapping = {
        "berlin, germany": "Berlin",
        "munich, germany": "Munich",
        "frankfurt, germany": "Frankfurt",
        "hamburg, germany": "Hamburg",
    }

    return mapping.get(text.lower(), text)


def normalize_category(value):
    text = clean_text(value)
    if not text:
        return None
    return text.title()


def normalize_seniority(value):
    text = clean_text(value)
    if not text:
        return None

    mapping = {
        "junior": "Junior",
        "mid": "Mid",
        "senior": "Senior",
    }
    return mapping.get(text.lower(), text)


def parse_date(value):
    if pd.isna(value):
        return None
    dt = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(dt) else dt.date()


def is_valid_row(title, description, url):
    if not url:
        return False, "missing_url"
    if not title:
        return False, "missing_title"
    if not description or len(description) < MIN_DESCRIPTION_LENGTH:
        return False, "short_description"
    return True, None


def ingest_jobs():
    df = load_csv(CSV_PATH)
    db = SessionLocal()

    inserted = 0
    updated = 0
    skipped = 0
    skip_reasons = {
        "missing_url": 0,
        "missing_title": 0,
        "short_description": 0,
    }

    try:
        for _, row in df.iterrows():
            title = clean_text(row.get("title"))
            company = clean_text(row.get("company"))
            location = normalize_location(row.get("location"))
            category = normalize_category(row.get("category"))
            seniority = normalize_seniority(row.get("seniority"))
            description = clean_text(row.get("description"))
            date_posted = parse_date(row.get("date_posted"))
            url = clean_text(row.get("url"))

            valid, reason = is_valid_row(title, description, url)
            if not valid:
                skipped += 1
                skip_reasons[reason] += 1
                continue

            existing_job = db.query(Job).filter(Job.url == url).first()

            if existing_job:
                existing_job.title = title
                existing_job.company = company
                existing_job.location = location
                existing_job.category = category
                existing_job.seniority = seniority
                existing_job.description = description
                existing_job.date_posted = date_posted
                updated += 1
            else:
                job = Job(
                    title=title,
                    company=company,
                    location=location,
                    category=category,
                    seniority=seniority,
                    description=description,
                    cleaned_description=None,
                    detected_skills=None,
                    date_posted=date_posted,
                    url=url,
                )
                db.add(job)
                inserted += 1

        db.commit()

        print(f"Inserted: {inserted}")
        print(f"Updated: {updated}")
        print(f"Skipped: {skipped}")
        print(f"Skip reasons: {skip_reasons}")

    except Exception as e:
        db.rollback()
        print("Ingest failed:", e)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    ingest_jobs()