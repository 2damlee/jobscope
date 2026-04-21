import json

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_META_PATH, EMBEDDING_PATH, JOB_IDS_PATH, ensure_data_dirs
from app.db import SessionLocal
from app.models import Job
from app.time_utils import utcnow_naive
from pipeline.run_tracker import finish_run, start_run

MODEL_NAME = "all-MiniLM-L6-v2"


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
        ensure_data_dirs()

        jobs = (
            db.query(Job)
            .filter(Job.processing_status == "processed")
            .order_by(Job.id.asc())
            .all()
        )

        texts, job_ids = collect_embedding_inputs(jobs)

        if not texts:
            meta = {
                "generated_at": utcnow_naive().isoformat(),
                "job_count": 0,
                "model_name": MODEL_NAME,
                "artifact": "job_embeddings",
            }

            np.save(EMBEDDING_PATH, np.empty((0, 0), dtype=np.float32))
            with JOB_IDS_PATH.open("w", encoding="utf-8") as f:
                json.dump([], f)
            with EMBEDDING_META_PATH.open("w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            summary = {
                "embedded_jobs": 0,
                "artifact_path": str(EMBEDDING_PATH),
                "job_ids_path": str(JOB_IDS_PATH),
                "meta_path": str(EMBEDDING_META_PATH),
                "model_name": MODEL_NAME,
            }
            finish_run(db, run, status="success", output_rows=0, metrics=summary)
            return summary

        model = SentenceTransformer(MODEL_NAME)
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        np.save(EMBEDDING_PATH, embeddings)

        with JOB_IDS_PATH.open("w", encoding="utf-8") as f:
            json.dump(job_ids, f)

        now = utcnow_naive()

        db.query(Job).filter(Job.id.in_(job_ids)).update(
            {"embedded_at": now},
            synchronize_session=False,
        )
        db.commit()

        meta = {
            "generated_at": now.isoformat(),
            "job_count": len(job_ids),
            "model_name": MODEL_NAME,
            "artifact": "job_embeddings",
        }

        with EMBEDDING_META_PATH.open("w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        summary = {
            "embedded_jobs": len(job_ids),
            "artifact_path": str(EMBEDDING_PATH),
            "job_ids_path": str(JOB_IDS_PATH),
            "meta_path": str(EMBEDDING_META_PATH),
            "model_name": MODEL_NAME,
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
    result = build_embeddings()
    print(result)