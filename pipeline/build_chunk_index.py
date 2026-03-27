import json
from datetime import datetime
from pathlib import Path

from app.db import SessionLocal
from app.models import Job
from pipeline.run_tracker import finish_run, start_run
from rag.chunking import chunk_text
from rag.embeddings import embed_texts
from rag.vector_store import build_faiss_index, save_faiss_index

CHUNK_RECORDS_PATH = Path("data/processed/job_chunks.json")
CHUNK_INDEX_META_PATH = Path("data/processed/chunk_index_meta.json")


def collect_chunk_records(jobs):
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

    return chunk_records, chunk_texts


def build_chunk_index(full_rebuild: bool = False):
    db = SessionLocal()
    run = start_run(db, pipeline_name="build_chunk_index")

    try:
        CHUNK_RECORDS_PATH.parent.mkdir(parents=True, exist_ok=True)

        jobs = db.query(Job).all()
        chunk_records, chunk_texts = collect_chunk_records(jobs)

        if not chunk_records:
            finish_run(
                db,
                run,
                status="success",
                output_rows=0,
                metrics={
                    "chunk_count": 0,
                    "full_rebuild": full_rebuild,
                    "skipped_rebuild": True,
                    "reason": "no_chunkable_jobs",
                },
            )
            print("Skipped chunk index rebuild: no chunkable jobs.")
            return

        vectors = embed_texts(chunk_texts)
        index = build_faiss_index(vectors)
        save_faiss_index(index)

        with CHUNK_RECORDS_PATH.open("w", encoding="utf-8") as f:
            json.dump(chunk_records, f, ensure_ascii=False, indent=2)

        avg_chunk_length = round(
            sum(item["chunk_length"] for item in chunk_records) / len(chunk_records), 2
        )

        meta = {
            "generated_at": datetime.utcnow().isoformat(),
            "pipeline_run_id": run.id,
            "chunk_count": len(chunk_records),
            "artifact": "job_chunks_index",
            "avg_chunk_length": avg_chunk_length,
            "full_rebuild": full_rebuild,
        }

        with CHUNK_INDEX_META_PATH.open("w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        finish_run(
            db,
            run,
            status="success",
            output_rows=len(chunk_records),
            metrics={
                "chunk_count": len(chunk_records),
                "avg_chunk_length": avg_chunk_length,
                "full_rebuild": full_rebuild,
                "skipped_rebuild": False,
            },
        )
        print(f"Saved {len(chunk_records)} chunks.")

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
    build_chunk_index()