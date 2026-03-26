from sqlalchemy.orm import Session

from app.models import Job


def get_job_by_id(db: Session, job_id: int) -> Job | None:
    return db.query(Job).filter(Job.id == job_id).first()


def get_jobs_by_ids(db: Session, job_ids: list[int]) -> list[Job]:
    if not job_ids:
        return []

    return db.query(Job).filter(Job.id.in_(job_ids)).all()