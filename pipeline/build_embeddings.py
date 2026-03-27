import json
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer

from app.db import SessionLocal
from app.models import Job
from pipeline.rebuild_utils import should_rebuild_from_dirty_count
from pipeline.run_tracker import finish_run, start_run

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_PATH = "data/processed/job_embeddings.npy"
JOB_IDS_PATH = "data/processed/job_ids.json"
EMBEDDING_META_PATH = "data/processed/embedding_meta.json"


def should_rebuild_embeddings(db) -> bool:
    dirty_count = db.query(Job).filter(Job.embedded_at.is_(None)).count()
    return should_rebuild_from_dirty_count(
        dirty_count=dirty_count,
        artifact_paths=[EMBEDDING_PATH, JOB_IDS_PATH, EMBEDDING_META_PATH],
    )


def build_embeddings():
    db = SessionLocal()
    run = start_run(db, pipeline_name="build_embeddings")

    try:
        if not should_rebuild_embeddings(db):
            finish_run(
                db,
                run,
                status="success",
                output_rows=0,
                metrics={"skipped_rebuild": True, "reason": "no_dirty_jobs"},
            )
            print("Skipped embedding rebuild: no dirty jobs.")
            return

        model = SentenceTransformer(MODEL_NAME)

        jobs = db.query(Job).all()
        texts = []
        job_ids = []

        for job in jobs:
            text = job.cleaned_description or job.description
            if not text:
                continue
            texts.append(text)
            job_ids.append(job.id)

        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        np.save(EMBEDDING_PATH, embeddings)

        with open(JOB_IDS_PATH, "w") as f:
            json.dump(job_ids, f)

        meta = {
            "generated_at": datetime.utcnow().isoformat(),
            "pipeline_run_id": run.id,
            "job_count": len(job_ids),
            "model_name": MODEL_NAME,
            "artifact": "job_embeddings",
        }
        with open(EMBEDDING_META_PATH, "w") as f:
            json.dump(meta, f, indent=2)

        now = datetime.utcnow()
        db.query(Job).filter(Job.cleaned_description.isnot(None)).update(
            {"embedded_at": now},
            synchronize_session=False,
        )
        db.commit()

        finish_run(
            db,
            run,
            status="success",
            output_rows=len(job_ids),
            metrics={"job_count": len(job_ids), "model_name": MODEL_NAME},
        )
        print(f"Saved {len(job_ids)} embeddings.")

    except Exception as e:
        db.rollback()
        finish_run(db, run, status="failed", error_message=str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    build_embeddings()