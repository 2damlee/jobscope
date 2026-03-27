import sys
from pathlib import Path

import pandas as pd
import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal
from app.models import Job
from pipeline.run_tracker import finish_run, start_run
from pipeline.state_utils import build_source_hash, has_source_changed, reset_downstream_state

CSV_PATH = "data/raw/jobs.csv"
MIN_DESCRIPTION_LENGTH = 30


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def clean_text(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


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


def mark_all_jobs_pending(db):
    db.query(Job).update(
        {
            "processing_status": "pending",
            "cleaned_description": None,
            "detected_skills": None,
        },
        synchronize_session=False,
    )


def ingest_jobs(full_rebuild: bool = False):
    df = load_csv(CSV_PATH)
    db = SessionLocal()

    inserted = 0
    updated = 0
    unchanged = 0
    changed = 0

    prepared_rows, skipped, skip_reasons, duplicate_urls_in_file = dedupe_rows_by_url(df)

    run = start_run(
        db,
        pipeline_name="ingest_jobs",
        source_name=CSV_PATH,
        input_rows=len(df),
    )

    try:
        for row in prepared_rows:
            existing_job = db.query(Job).filter(Job.url == row["url"]).first()

            if existing_job:
                if not has_source_changed(existing_job.source_hash, row["source_hash"]):
                    unchanged += 1
                    continue

                existing_job.title = row["title"]
                existing_job.company = row["company"]
                existing_job.location = row["location"]
                existing_job.category = row["category"]
                existing_job.seniority = row["seniority"]
                existing_job.description = row["description"]
                existing_job.date_posted = row["date_posted"]
                existing_job.source_hash = row["source_hash"]
                existing_job.ingested_at = datetime.utcnow()
                reset_downstream_state(existing_job)

                updated += 1
                changed += 1

            else:
                job = Job(
                    title=row["title"],
                    company=row["company"],
                    location=row["location"],
                    category=row["category"],
                    seniority=row["seniority"],
                    description=row["description"],
                    cleaned_description=None,
                    detected_skills=None,
                    date_posted=row["date_posted"],
                    url=row["url"],
                    source_hash=row["source_hash"],
                    processing_status="pending",
                )
                db.add(job)
                inserted += 1
                changed += 1

        db.commit()

        finish_run(
            db,
            run,
            status="success",
            output_rows=inserted + updated,
            inserted_rows=inserted,
            updated_rows=updated,
            skipped_rows=skipped,
            metrics={
                "skip_reasons": skip_reasons,
                "changed_rows": changed,
                "unchanged_rows": unchanged,
                "duplicate_urls_in_file": duplicate_urls_in_file,
                "deduped_input_rows": len(prepared_rows),
            },
        )

        print(f"Inserted: {inserted}")
        print(f"Updated: {updated}")
        print(f"Unchanged: {unchanged}")
        print(f"Changed: {changed}")
        print(f"Skipped: {skipped}")
        print(f"Duplicate URLs in file: {duplicate_urls_in_file}")
        print(f"Skip reasons: {skip_reasons}")

    except Exception as e:
        db.rollback()
        finish_run(
            db,
            run,
            status="failed",
            skipped_rows=skipped,
            metrics={
                "skip_reasons": skip_reasons,
                "changed_rows": changed,
                "unchanged_rows": unchanged,
                "duplicate_urls_in_file": duplicate_urls_in_file,
                "deduped_input_rows": len(prepared_rows),
            },
            error_message=str(e),
        )
        print("Ingest failed:", e)
        raise
    finally:
        db.close()

def normalize_row(row):
    title = clean_text(row.get("title"))
    company = clean_text(row.get("company"))
    location = normalize_location(row.get("location"))
    category = normalize_category(row.get("category"))
    seniority = normalize_seniority(row.get("seniority"))
    description = clean_text(row.get("description"))
    date_posted = parse_date(row.get("date_posted"))
    url = clean_text(row.get("url"))

    source_hash = build_source_hash(
        title=title,
        company=company,
        location=location,
        category=category,
        seniority=seniority,
        description=description,
        date_posted=date_posted,
        url=url,
    )

    return {
        "title": title,
        "company": company,
        "location": location,
        "category": category,
        "seniority": seniority,
        "description": description,
        "date_posted": date_posted,
        "url": url,
        "source_hash": source_hash,
    }


def dedupe_rows_by_url(df):
    deduped_rows = {}
    duplicate_urls_in_file = 0
    skipped = 0
    skip_reasons = {
        "missing_url": 0,
        "missing_title": 0,
        "short_description": 0,
    }

    for _, row in df.iterrows():
        normalized = normalize_row(row)

        valid, reason = is_valid_row(
            normalized["title"],
            normalized["description"],
            normalized["url"],
        )
        if not valid:
            skipped += 1
            skip_reasons[reason] += 1
            continue

        if normalized["url"] in deduped_rows:
            duplicate_urls_in_file += 1

        deduped_rows[normalized["url"]] = normalized

    return list(deduped_rows.values()), skipped, skip_reasons, duplicate_urls_in_file

if __name__ == "__main__":
    ingest_jobs()