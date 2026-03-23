import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal
from app.models import Job
from pipeline.clean_jobs import clean_description
from pipeline.extract_skills import extract_skills


def process_jobs():
    db = SessionLocal()

    try:
        jobs = db.query(Job).all()

        for job in jobs:
            cleaned = clean_description(job.description)
            skills = extract_skills(cleaned)

            job.cleaned_description = cleaned
            job.detected_skills = ",".join(skills)

        db.commit()
        print(f"Processed {len(jobs)} jobs.")

    except Exception as e:
        db.rollback()
        print("Processing failed:", e)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    process_jobs()