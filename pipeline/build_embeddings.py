import json
from datetime import datetime

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import (
    EMBEDDING_META_PATH,
    EMBEDDING_PATH,
    JOB_IDS_PATH,
    ensure_data_dirs,
)
from app.db import SessionLocal
from app.models import Job

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
    model = SentenceTransformer(MODEL_NAME)

    try:
        ensure_data_dirs()

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

        with JOB_IDS_PATH.open("w", encoding="utf-8") as f:
            json.dump(job_ids, f)

        meta = {
            "generated_at": datetime.utcnow().isoformat(),
            "job_count": len(job_ids),
            "model_name": MODEL_NAME,
            "artifact": "job_embeddings",
        }

        with EMBEDDING_META_PATH.open("w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        return {
            "embedded_jobs": len(job_ids),
            "artifact_path": str(EMBEDDING_PATH),
            "job_ids_path": str(JOB_IDS_PATH),
            "meta_path": str(EMBEDDING_META_PATH),
        }
    finally:
        db.close()

if __name__ == "__main__":
    build_embeddings()