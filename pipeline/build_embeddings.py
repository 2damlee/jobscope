import json
from datetime import datetime

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_META_PATH, EMBEDDING_PATH, JOB_IDS_PATH, ensure_data_dirs
from app.db import SessionLocal
from app.models import Job
from pipeline.rebuild_utils import should_rebuild_from_dirty_count
from pipeline.run_tracker import finish_run, start_run

MODEL_NAME = "all-MiniLM-L6-v2"


def should_rebuild_embeddings(db) -> tuple[bool, int]:
    dirty_count = db.query(Job).filter(Job.embedded_at.is_(None)).count()
    should_rebuild = should_rebuild_from_dirty_count(
        dirty_count=dirty_count,
        artifact_paths=[
            str(EMBEDDING_PATH),
            str(JOB_IDS_PATH),
            str(EMBEDDING_META_PATH),
        ],
    )
    return should_rebuild, dirty_count


def collect_embedding_inputs(jobs):
    texts = []
    job_ids = []

    for job in jobs:
        text = job.cleaned_description or job.description
        if not text:
            continue
        texts.append(text)
        job_ids.append(job.id)

    return texts, job_ids


def build_embeddings():
    db = SessionLocal()
    run = start_run(db, pipeline_name="build_embeddings")

    try:
        should_rebuild, dirty_count = should_rebuild_embeddings(db)

        if not should_rebuild:
            summary = {
                "skipped_rebuild": True,
                "reason": "no_dirty_jobs",
                "dirty_jobs": dirty_count,
                "artifact_paths": [
                    str(EMBEDDING_PATH),
                    str(JOB_IDS_PATH),
                    str(EMBEDDING_META_PATH),
                ],
            }
            finish_run(
                db,
                run,
                status="success",
                output_rows=0,
                metrics=summary,
            )
            return summary

        ensure_data_dirs()

        model = SentenceTransformer(MODEL_NAME)
        jobs = db.query(Job).all()
        texts, job_ids = collect_embedding_inputs(jobs)

        embeddings = model.encode(texts, normalize_embeddings=True)
        np.save(EMBEDDING_PATH, embeddings)

        with JOB_IDS_PATH.open("w", encoding="utf-8") as f:
            json.dump(job_ids, f, ensure_ascii=False)

        with EMBEDDING_META_PATH.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "model_name": MODEL_NAME,
                    "generated_at": datetime.utcnow().isoformat(),
                    "job_count": len(job_ids),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        now = datetime.utcnow()
        db.query(Job).filter(Job.id.in_(job_ids)).update(
            {"embedded_at": now},
            synchronize_session=False,
        )
        db.commit()

        summary = {
            "skipped_rebuild": False,
            "dirty_jobs": dirty_count,
            "embedded_jobs": len(job_ids),
            "artifact_paths": [
                str(EMBEDDING_PATH),
                str(JOB_IDS_PATH),
                str(EMBEDDING_META_PATH),
            ],
        }

        finish_run(
            db,
            run,
            status="success",
            output_rows=len(job_ids),
            updated_rows=len(job_ids),
            metrics=summary,
        )
        return summary

    except Exception as e:
        db.rollback()
        finish_run(db, run, status="failed", output_rows=0, error_message=str(e))
        raise
    finally:
        db.close()