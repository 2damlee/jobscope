import json

from app.config import CHUNK_INDEX_META_PATH, CHUNK_INDEX_PATH, CHUNK_META_PATH, ensure_data_dirs
from app.db import SessionLocal
from app.models import Job
from app.time_utils import utcnow_naive
from pipeline.rebuild_utils import should_rebuild_from_dirty_count
from pipeline.run_tracker import finish_run, start_run
from rag.chunking import chunk_text
from rag.embeddings import embed_texts
from rag.vector_store import build_faiss_index, save_faiss_index


def should_rebuild_chunk_index(db) -> tuple[bool, int]:
    dirty_count = db.query(Job).filter(Job.chunked_at.is_(None)).count()
    should_rebuild = should_rebuild_from_dirty_count(
        dirty_count=dirty_count,
        artifact_paths=[
            str(CHUNK_INDEX_PATH),
            str(CHUNK_META_PATH),
            str(CHUNK_INDEX_META_PATH),
        ],
    )
    return should_rebuild, dirty_count


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


def build_chunk_index():
    db = SessionLocal()
    run = start_run(db, pipeline_name="build_chunk_index")

    try:
        should_rebuild, dirty_count = should_rebuild_chunk_index(db)

        if not should_rebuild:
            summary = {
                "skipped_rebuild": True,
                "reason": "no_dirty_jobs",
                "dirty_jobs": dirty_count,
                "artifact_paths": [
                    str(CHUNK_INDEX_PATH),
                    str(CHUNK_META_PATH),
                    str(CHUNK_INDEX_META_PATH),
                ],
            }
            finish_run(db, run, status="success", output_rows=0, metrics=summary)
            return summary

        ensure_data_dirs()

        jobs = db.query(Job).all()
        chunk_records, chunk_texts = collect_chunk_records(jobs)

        embeddings = embed_texts(chunk_texts)
        index = build_faiss_index(embeddings)
        save_faiss_index(index, str(CHUNK_INDEX_PATH))

        with CHUNK_META_PATH.open("w", encoding="utf-8") as f:
            json.dump(chunk_records, f, ensure_ascii=False, indent=2)

        with CHUNK_INDEX_META_PATH.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "generated_at": utcnow_naive().isoformat(),
                    "chunk_count": len(chunk_records),
                    "job_count": len({r["job_id"] for r in chunk_records}),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        now = utcnow_naive()
        touched_job_ids = sorted({r["job_id"] for r in chunk_records})

        if touched_job_ids:
            db.query(Job).filter(Job.id.in_(touched_job_ids)).update(
                {"chunked_at": now},
                synchronize_session=False,
            )
            db.commit()

        summary = {
            "skipped_rebuild": False,
            "dirty_jobs": dirty_count,
            "chunk_count": len(chunk_records),
            "job_count": len(touched_job_ids),
            "artifact_paths": [
                str(CHUNK_INDEX_PATH),
                str(CHUNK_META_PATH),
                str(CHUNK_INDEX_META_PATH),
            ],
        }

        finish_run(
            db,
            run,
            status="success",
            output_rows=len(chunk_records),
            updated_rows=len(touched_job_ids),
            metrics=summary,
        )
        return summary

    except Exception as e:
        db.rollback()
        finish_run(db, run, status="failed", output_rows=0, error_message=str(e))
        raise
    finally:
        db.close()