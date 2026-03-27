import json
from datetime import datetime
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from app.db import SessionLocal
from app.models import Job
from pipeline.run_tracker import finish_run, start_run

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_PATH = Path("data/processed/job_embeddings.npy")
JOB_IDS_PATH = Path("data/processed/job_ids.json")
EMBEDDING_META_PATH = Path("data/processed/embedding_meta.json")


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


def build_embeddings(full_rebuild: bool = False):
    db = SessionLocal()
    run = start_run(db, pipeline_name="build_embeddings")

    try:
        EMBEDDING_PATH.parent.mkdir(parents=True, exist_ok=True)

        model = SentenceTransformer(MODEL_NAME)
        jobs = db.query(Job).all()
        texts, job_ids = collect_embedding_inputs(jobs)

        if not texts:
            finish_run(
                db,
                run,
                status="success",
                output_rows=0,
                metrics={
                    "job_count": 0,
                    "model_name": MODEL_NAME,
                    "full_rebuild": full_rebuild,
                    "skipped_rebuild": True,
                    "reason": "no_jobs_with_text",
                },
            )
            print("Skipped embedding rebuild: no jobs with text.")
            return

        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        np.save(EMBEDDING_PATH, embeddings)

        with JOB_IDS_PATH.open("w", encoding="utf-8") as f:
            json.dump(job_ids, f)

        meta = {
            "generated_at": datetime.utcnow().isoformat(),
            "pipeline_run_id": run.id,
            "job_count": len(job_ids),
            "model_name": MODEL_NAME,
            "artifact": "job_embeddings",
            "full_rebuild": full_rebuild,
        }
        with EMBEDDING_META_PATH.open("w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        finish_run(
            db,
            run,
            status="success",
            output_rows=len(job_ids),
            metrics={
                "job_count": len(job_ids),
                "model_name": MODEL_NAME,
                "full_rebuild": full_rebuild,
                "skipped_rebuild": False,
            },
        )
        print(f"Saved {len(job_ids)} embeddings.")

    except Exception as e:
        finish_run(
            db,
            run,
            status="failed",
            metrics={"full_rebuild": full_rebuild},
            error_message=str(e),
        )
        raise
    finally:
        db.close()


if __name__ == "__main__":
    build_embeddings()