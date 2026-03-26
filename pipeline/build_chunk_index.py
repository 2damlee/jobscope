import json
import os
from datetime import datetime

from app.db import SessionLocal
from app.models import Job
from pipeline.rebuild_utils import should_rebuild_from_dirty_count
from pipeline.run_tracker import finish_run, start_run
from rag.chunking import chunk_text
from rag.embeddings import embed_texts
from rag.vector_store import build_faiss_index, save_faiss_index

FAISS_PATH = "data/processed/job_chunks.faiss"
CHUNK_RECORDS_PATH = "data/processed/job_chunks.json"
CHUNK_INDEX_META_PATH = "data/processed/chunk_index_meta.json"


def should_rebuild_chunk_index(db) -> bool:
    dirty_count = db.query(Job).filter(Job.chunked_at.is_(None)).count()
    return should_rebuild_from_dirty_count(
        dirty_count=dirty_count,
        artifact_paths=[FAISS_PATH, CHUNK_RECORDS_PATH, CHUNK_INDEX_META_PATH],
    )


def build_chunk_index():
    db = SessionLocal()
    run = start_run(db, pipeline_name="build_chunk_index")

    try:
        if not should_rebuild_chunk_index(db):
            finish_run(
                db,
                run,
                status="success",
                output_rows=0,
                metrics={"skipped_rebuild": True, "reason": "no_dirty_jobs"},
            )
            print("Skipped chunk index rebuild: no dirty jobs.")
            return

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

        with open(CHUNK_RECORDS_PATH, "w") as f:
            json.dump(chunk_records, f, ensure_ascii=False, indent=2)

        avg_chunk_length = (
            round(sum(item["chunk_length"] for item in chunk_records) / len(chunk_records), 2)
            if chunk_records
            else 0
        )

        meta = {
            "generated_at": datetime.utcnow().isoformat(),
            "pipeline_run_id": run.id,
            "chunk_count": len(chunk_records),
            "artifact": "job_chunks_index",
            "avg_chunk_length": avg_chunk_length,
        }

        with open(CHUNK_INDEX_META_PATH, "w") as f:
            json.dump(meta, f, indent=2)

        now = datetime.utcnow()
        db.query(Job).filter(Job.cleaned_description.isnot(None)).update(
            {"chunked_at": now},
            synchronize_session=False,
        )
        db.commit()

        finish_run(
            db,
            run,
            status="success",
            output_rows=len(chunk_records),
            metrics={
                "chunk_count": len(chunk_records),
                "avg_chunk_length": avg_chunk_length,
            },
        )

        print(f"Saved {len(chunk_records)} chunks.")

    except Exception as e:
        db.rollback()
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
    build_chunk_index()