import json
import numpy as np
from sentence_transformers import SentenceTransformer

from app.db import SessionLocal
from app.models import Job


MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_PATH = "data/processed/job_embeddings.npy"
JOB_IDS_PATH = "data/processed/job_ids.json"


def build_embeddings():
    db = SessionLocal()
    model = SentenceTransformer(MODEL_NAME)

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

        print(f"Saved {len(job_ids)} embeddings.")

    finally:
        db.close()


if __name__ == "__main__":
    build_embeddings()