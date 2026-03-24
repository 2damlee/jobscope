import json
import os
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


def read_json_if_exists(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


@router.get("/indexes")
def health_indexes():
    embedding_meta = read_json_if_exists("data/processed/embedding_meta.json")
    chunk_meta = read_json_if_exists("data/processed/chunk_index_meta.json")

    return {
        "embedding_index": embedding_meta,
        "chunk_index": chunk_meta,
    }