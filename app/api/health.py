import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import CHUNK_INDEX_META_PATH, EMBEDDING_META_PATH
from app.db import SessionLocal, engine
from app.models import PipelineRun

router = APIRouter(prefix="/health", tags=["health"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def read_json_if_exists(path):
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def compute_staleness(meta: dict | None):
    if not meta or "generated_at" not in meta:
        return {"available": False, "stale": None, "age_hours": None}

    try:
        generated_at = datetime.fromisoformat(meta["generated_at"])
        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age_hours = round((now - generated_at).total_seconds() / 3600, 2)

        return {
            "available": True,
            "stale": age_hours > 24,
            "age_hours": age_hours,
        }
    except Exception:
        return {"available": True, "stale": None, "age_hours": None}


@router.get("/ready")
def health_ready():
    from app.main import artifact_status
    artifacts = artifact_status()

    db_ok = True
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    ready = db_ok and artifacts["ready"]

    payload = {
        "status": "ready" if ready else "degraded",
        "database": "reachable" if db_ok else "unreachable",
        "artifacts": artifacts,
    }

    if ready:
        return payload

    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)


@router.get("/indexes")
def health_indexes():
    embedding_meta = read_json_if_exists(EMBEDDING_META_PATH)
    chunk_meta = read_json_if_exists(CHUNK_INDEX_META_PATH)

    return {
        "embedding_index": {
            "meta": embedding_meta,
            "status": compute_staleness(embedding_meta),
        },
        "chunk_index": {
            "meta": chunk_meta,
            "status": compute_staleness(chunk_meta),
        },
    }


@router.get("/pipeline")
def health_pipeline(db: Session = Depends(get_db)):
    runs = (
        db.query(PipelineRun)
        .order_by(PipelineRun.started_at.desc())
        .limit(10)
        .all()
    )

    return {
        "runs": [
            {
                "id": run.id,
                "pipeline_name": run.pipeline_name,
                "status": run.status,
                "source_name": run.source_name,
                "input_rows": run.input_rows,
                "output_rows": run.output_rows,
                "inserted_rows": run.inserted_rows,
                "updated_rows": run.updated_rows,
                "skipped_rows": run.skipped_rows,
                "metrics": run.metrics,
                "error_message": run.error_message,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            }
            for run in runs
        ]
    }


@router.get("/db")
def health_db():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {"status": "ok", "database": "reachable"}
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "database": "unreachable",
            },
        )