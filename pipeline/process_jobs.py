from app.db import SessionLocal
from app.models import Job
from app.time_utils import utcnow_naive
from pipeline.clean_jobs import clean_description
from pipeline.extract_skills import extract_skills
from pipeline.run_tracker import finish_run, start_run


def select_pending_jobs(db):
    return db.query(Job).filter(Job.processing_status == "pending").all()


def process_single_job(job: Job) -> dict:
    cleaned = clean_description(job.description)
    skills = extract_skills(cleaned)
    now = utcnow_naive()

    job.cleaned_description = cleaned
    job.detected_skills = ",".join(skills)
    job.processing_status = "processed"
    job.last_processed_at = now
    job.skills_extracted_at = now

    return {
        "job_id": job.id,
        "skills_count": len(skills),
        "cleaned_empty": not bool(cleaned),
    }


def summarize_results(results: list[dict]) -> dict:
    processed_jobs = len(results)
    jobs_without_skills = sum(1 for r in results if r["skills_count"] == 0)
    empty_cleaned_description = sum(1 for r in results if r["cleaned_empty"])
    avg_skills_per_job = (
        round(sum(r["skills_count"] for r in results) / processed_jobs, 3)
        if processed_jobs
        else 0.0
    )

    return {
        "processed_jobs": processed_jobs,
        "jobs_without_skills": jobs_without_skills,
        "empty_cleaned_description": empty_cleaned_description,
        "avg_skills_per_job": avg_skills_per_job,
    }


def process_jobs():
    db = SessionLocal()
    jobs = []
    run = start_run(db, pipeline_name="process_jobs")

    try:
        jobs = select_pending_jobs(db)
        results = [process_single_job(job) for job in jobs]
        db.commit()

        summary = summarize_results(results)

        finish_run(
            db,
            run,
            status="success",
            output_rows=summary["processed_jobs"],
            updated_rows=summary["processed_jobs"],
            metrics=summary,
        )
        return summary
    except Exception as e:
        db.rollback()
        finish_run(
            db,
            run,
            status="failed",
            output_rows=0,
            error_message=str(e),
        )
        raise
    finally:
        db.close()


if __name__ == "__main__":
    result = process_jobs()
    print(result)