import json

from app.db import SessionLocal
from app.models import Job
from rag.chunking import chunk_text
from rag.embeddings import embed_texts
from rag.vector_store import build_faiss_index, save_faiss_index

CHUNK_META_PATH = "data/processed/job_chunks.json"


def build_chunk_index():
    db = SessionLocal()

    try:
        jobs = db.query(Job).all()

        chunk_records = []
        chunk_texts = []

        for job in jobs:
            text = job.cleaned_description or job.description
            if not text:
                continue

            chunks = chunk_text(text)

            for i, chunk in enumerate(chunks):
                chunk_records.append({
                    "chunk_id": len(chunk_records),
                    "job_id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "category": job.category,
                    "seniority": job.seniority,
                    "chunk_text": chunk,
                    "chunk_order": i,
                })
                chunk_texts.append(chunk)

        vectors = embed_texts(chunk_texts)
        index = build_faiss_index(vectors)
        save_faiss_index(index)

        with open(CHUNK_META_PATH, "w") as f:
            json.dump(chunk_records, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(chunk_records)} chunks.")

    finally:
        db.close()


if __name__ == "__main__":
    build_chunk_index()