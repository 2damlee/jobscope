import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal
from app.models import Job
from pipeline.clean_jobs import clean_description
from pipeline.extract_skills import extract_skills
from pipeline.run_tracker import finish_run, start_run


def process_jobs():
    db = SessionLocal()
    run = start_run(db, pipeline_name="process_jobs")

    processed = 0

    try:
        jobs = db.query(Job).filter(Job.processing_status == "pending").all()

        for job in jobs:
            cleaned = clean_description(job.description)
            skills = extract_skills(cleaned)

            job.cleaned_description = cleaned
            job.detected_skills = ",".join(skills)
            job.processing_status = "processed"
            job.last_processed_at = datetime.utcnow()

            processed += 1

        db.commit()

        finish_run(
            db,
            run,
            status="success",
            output_rows=processed,
            metrics={"processed_jobs": processed},
        )

        print(f"Processed {processed} jobs.")

    except Exception as e:
        db.rollback()
        finish_run(
            db,
            run,
            status="failed",
            output_rows=processed,
            metrics={"processed_jobs": processed},
            error_message=str(e),
        )
        print("Processing failed:", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    process_jobs()