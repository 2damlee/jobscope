from datetime import datetime

import pandas as pd

from app.config import CSV_PATH
from app.db import SessionLocal
from app.models import Job
from pipeline.run_tracker import finish_run, start_run
from pipeline.state_utils import build_source_hash, has_source_changed

CSV_PATH = "data/raw/jobs.csv"
MIN_DESCRIPTION_LENGTH = 30


def load_csv(path: str | None = None) -> pd.DataFrame:
    csv_path = path or str(CSV_PATH)
    return pd.read_csv(csv_path)


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


def reset_downstream_state(job: Job):
    job.processing_status = "pending"
    job.cleaned_description = None
    job.detected_skills = None
    job.last_processed_at = None
    job.skills_extracted_at = None
    job.embedded_at = None
    job.chunked_at = None

def mark_all_jobs_pending(db):
    db.query(Job).update(
        {
            "processing_status": "pending",
            "cleaned_description": None,
            "detected_skills": None,
            "last_processed_at": None,
            "skills_extracted_at": None,
            "embedded_at": None,
            "chunked_at": None,
        },
        synchronize_session=False,
    )


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


def ingest_jobs(full_rebuild: bool = False):
    df = load_csv()
    db = SessionLocal()

    inserted = 0
    updated = 0
    skipped = 0
    changed = 0
    unchanged = 0

    skip_reasons = {
        "missing_url": 0,
        "missing_title": 0,
        "short_description": 0,
    }

    run = start_run(
        db,
        pipeline_name="ingest_jobs",
        source_name=str(CSV_PATH),
        input_rows=len(df),
    )

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

            valid, reason = is_valid_row(title, description, url)
            if not valid:
                skipped += 1
                skip_reasons[reason] += 1
                continue

            existing_job = db.query(Job).filter(Job.url == url).first()

            if existing_job:
                source_changed = has_source_changed(existing_job.source_hash, source_hash)

                if not full_rebuild and not source_changed:
                    unchanged += 1
                    continue

                existing_job.title = title
                existing_job.company = company
                existing_job.location = location
                existing_job.category = category
                existing_job.seniority = seniority
                existing_job.description = description
                existing_job.date_posted = date_posted
                existing_job.source_hash = source_hash
                existing_job.ingested_at = datetime.utcnow()
                reset_downstream_state(existing_job)

                updated += 1
                changed += 1
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
                    source_hash=source_hash,
                    processing_status="pending",
                )
                db.add(job)
                inserted += 1
                changed += 1

        db.commit()

        summary = {
            "inserted_rows": inserted,
            "updated_rows": updated,
            "skipped_rows": skipped,
            "changed_rows": changed,
            "unchanged_rows": unchanged,
            "skip_reasons": skip_reasons,
            "full_rebuild": full_rebuild,
        }

        finish_run(
            db,
            run,
            status="success",
            output_rows=inserted + updated,
            inserted_rows=inserted,
            updated_rows=updated,
            skipped_rows=skipped,
            metrics=summary,
        )
        return summary
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
                "full_rebuild": full_rebuild,
            },
            error_message=str(e),
        )
        raise
    finally:
        db.close()
        

if __name__ == "__main__":
    ingest_jobs()