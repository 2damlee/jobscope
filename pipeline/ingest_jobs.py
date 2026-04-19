import pandas as pd

from app.config import CSV_PATH
from app.db import SessionLocal
from app.models import Job
from app.time_utils import utcnow_naive
from pipeline.run_tracker import finish_run, start_run
from pipeline.state_utils import build_source_hash, has_source_changed

MIN_DESCRIPTION_LENGTH = 30


def clean_text(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text if text else None


def normalize_location(value):
    value = clean_text(value)
    if not value:
        return None
    city = value.split(",")[0].strip()
    return city.title() if city else None


def normalize_category(value):
    value = clean_text(value)
    return value.lower() if value else None


def normalize_seniority(value):
    value = clean_text(value)
    if not value:
        return None

    normalized = value.strip().lower()
    mapping = {
        "junior": "Junior",
        "jr": "Junior",
        "mid": "Mid",
        "middle": "Mid",
        "intermediate": "Mid",
        "senior": "Senior",
        "sr": "Senior",
        "lead": "Lead",
        "staff": "Staff",
        "principal": "Principal",
    }
    return mapping.get(normalized, value.strip().title())


def parse_date(value):
    if pd.isna(value):
        return None
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def is_valid_row(title, description, url):
    if not url:
        return False, "missing_url"
    if not title:
        return False, "missing_title"
    if not description or len(description.strip()) < MIN_DESCRIPTION_LENGTH:
        return False, "short_description"
    return True, None


def load_csv(path: str | None = None) -> pd.DataFrame:
    csv_path = path or str(CSV_PATH)
    return pd.read_csv(csv_path)


def reset_downstream_state(job: Job):
    job.processing_status = "pending"
    job.cleaned_description = None
    job.detected_skills = None
    job.last_processed_at = None
    job.skills_extracted_at = None
    job.embedded_at = None
    job.chunked_at = None


def mark_all_jobs_pending(db):
    jobs = db.query(Job).all()
    for job in jobs:
        reset_downstream_state(job)
    db.flush()
    return len(jobs)


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
        reset_count = 0
        if full_rebuild:
            reset_count = mark_all_jobs_pending(db)

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
                existing_job.ingested_at = utcnow_naive()
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
            "reset_jobs": reset_count,
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
    result = ingest_jobs()
    print(result)