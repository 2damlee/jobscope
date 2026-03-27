import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal
from app.models import Job
from pipeline.clean_jobs import clean_description
from pipeline.extract_skills import extract_skills
from pipeline.run_tracker import finish_run, start_run


def select_pending_jobs(db):
    return db.query(Job).filter(Job.processing_status == "pending").all()


def process_single_job(job: Job) -> dict:
    cleaned = clean_description(job.description)
    skills = extract_skills(cleaned)
    now = datetime.utcnow()

    job.cleaned_description = cleaned
    job.detected_skills = ",".join(skills)
    job.processing_status = "processed"
    job.last_processed_at = now
    job.skills_extracted_at = now

    return {
        "job_id": job.id,
        "cleaned_description_empty": not bool(cleaned),
        "skills_count": len(skills),
    }


def summarize_job_results(results: list[dict]) -> dict:
    processed_jobs = len(results)
    jobs_without_skills = sum(1 for result in results if result["skills_count"] == 0)
    empty_cleaned_description = sum(
        1 for result in results if result["cleaned_description_empty"]
    )

    return {
        "processed_jobs": processed_jobs,
        "jobs_without_skills": jobs_without_skills,
        "empty_cleaned_description": empty_cleaned_description,
    }


def process_jobs():
    db = SessionLocal()
    jobs = []
    run = start_run(db, pipeline_name="process_jobs")

    try:
        jobs = select_pending_jobs(db)
        results = [process_single_job(job) for job in jobs]

        db.commit()

        summary = summarize_job_results(results)
        summary["input_jobs"] = len(jobs)

        finish_run(
            db,
            run,
            status="success",
            output_rows=summary["processed_jobs"],
            metrics=summary,
        )
        print(f"Processed {summary['processed_jobs']} jobs.")

    except Exception as e:
        db.rollback()
        finish_run(
            db,
            run,
            status="failed",
            output_rows=0,
            metrics={"input_jobs": len(jobs)},
            error_message=str(e),
        )
        raise
    finally:
        db.close()


if __name__ == "__main__":
    process_jobs()