import json
from datetime import datetime

from app.config import CHUNK_INDEX_META_PATH, CHUNK_META_PATH, ensure_data_dirs
from app.db import SessionLocal
from app.models import Job
from rag.chunking import chunk_text
from rag.embeddings import embed_texts
from rag.vector_store import build_faiss_index, save_faiss_index


def build_chunk_index():
    db = SessionLocal()

    try:
        ensure_data_dirs()

        jobs = db.query(Job).all()
        chunk_records = []
        chunk_texts = []

        for job in jobs:
            text = job.cleaned_description or job.description
            if not text:
                continue

            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                chunk_records.append(
                    {
                        "chunk_id": len(chunk_records),
                        "job_id": job.id,
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "category": job.category,
                        "seniority": job.seniority,
                        "chunk_text": chunk,
                        "chunk_order": i,
                        "chunk_length": len(chunk),
                    }
                )
                chunk_texts.append(chunk)

        vectors = embed_texts(chunk_texts)
        index = build_faiss_index(vectors)
        save_faiss_index(index)

        with CHUNK_META_PATH.open("w", encoding="utf-8") as f:
            json.dump(chunk_records, f, ensure_ascii=False, indent=2)

        meta = {
            "generated_at": datetime.utcnow().isoformat(),
            "chunk_count": len(chunk_records),
            "artifact": "job_chunks_index",
            "avg_chunk_length": round(
                sum(item["chunk_length"] for item in chunk_records) / len(chunk_records), 2
            )
            if chunk_records
            else 0,
        }

        with CHUNK_INDEX_META_PATH.open("w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        return {
            "chunk_count": len(chunk_records),
            "chunk_meta_path": str(CHUNK_META_PATH),
            "meta_path": str(CHUNK_INDEX_META_PATH),
        }
    finally:
        db.close()


if __name__ == "__main__":
    build_chunk_index()