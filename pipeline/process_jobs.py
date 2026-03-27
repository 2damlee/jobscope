import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal
from app.models import Job
from pipeline.clean_jobs import clean_description
from pipeline.extract_skills import extract_skills
from pipeline.run_tracker import finish_run, start_run


def select_jobs_for_processing(db):
    return db.query(Job).filter(Job.processing_status == "pending").all()


def run_cleaning(job: Job) -> str:
    return clean_description(job.description)


def run_skill_extraction(cleaned_text: str) -> list[str]:
    return extract_skills(cleaned_text)


def process_jobs():
    db = SessionLocal()
    jobs = []
    run = start_run(db, pipeline_name="process_jobs")

    processed = 0
    jobs_without_skills = 0
    empty_cleaned_description = 0

    try:
        jobs = select_jobs_for_processing(db)

        for job in jobs:
            cleaned = run_cleaning(job)
            skills = run_skill_extraction(cleaned)

            if not cleaned:
                empty_cleaned_description += 1
            if not skills:
                jobs_without_skills += 1

            now = datetime.utcnow()
            job.cleaned_description = cleaned
            job.detected_skills = ",".join(skills)
            job.processing_status = "processed"
            job.last_processed_at = now
            job.skills_extracted_at = now

            processed += 1

        db.commit()

        finish_run(
            db,
            run,
            status="success",
            output_rows=processed,
            metrics={
                "input_jobs": len(jobs),
                "processed_jobs": processed,
                "jobs_without_skills": jobs_without_skills,
                "empty_cleaned_description": empty_cleaned_description,
            },
        )
        print(f"Processed {processed} jobs.")

    except Exception as e:
        db.rollback()
        finish_run(
            db,
            run,
            status="failed",
            output_rows=processed,
            metrics={
                "input_jobs": len(jobs),
                "processed_jobs": processed,
            },
            error_message=str(e),
        )
        raise
    finally:
        db.close()


if __name__ == "__main__":
    process_jobs()