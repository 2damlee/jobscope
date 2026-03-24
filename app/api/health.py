import json
import os
from datetime import datetime, timezone
from fastapi import APIRouter
from app.config import EMBEDDING_META_PATH, CHUNK_INDEX_META_PATH

router = APIRouter(prefix="/health", tags=["health"])


def read_json_if_exists(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def compute_staleness(meta: dict | None):
    if not meta or "generated_at" not in meta:
        return {"available": False, "stale": None}

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
        return {"available": True, "stale": None}


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