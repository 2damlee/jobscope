import json
from datetime import datetime

import numpy as np
from sentence_transformers import SentenceTransformer

from app.db import SessionLocal
from app.models import Job
from pipeline.run_tracker import finish_run, start_run

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_PATH = "data/processed/job_embeddings.npy"
JOB_IDS_PATH = "data/processed/job_ids.json"
EMBEDDING_META_PATH = "data/processed/embedding_meta.json"


def build_embeddings():
    db = SessionLocal()
    model = SentenceTransformer(MODEL_NAME)
    run = start_run(db, pipeline_name="build_embeddings")

    try:
        jobs = db.query(Job).all()

        texts = []
        job_ids = []

        for job in jobs:
            text = job.cleaned_description or job.description
            if not text:
                continue
            texts.append(text)
            job_ids.append(job.id)

        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

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

        finish_run(
            db,
            run,
            status="success",
            output_rows=len(job_ids),
            metrics={"job_count": len(job_ids), "model_name": MODEL_NAME},
        )

        print(f"Saved {len(job_ids)} embeddings.")

    except Exception as e:
        finish_run(
            db,
            run,
            status="failed",
            error_message=str(e),
        )
        raise
    finally:
        db.close()


if __name__ == "__main__":
    build_embeddings()