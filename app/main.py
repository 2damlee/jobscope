import os
from fastapi import FastAPI

from app.api.jobs import router as jobs_router
from app.api.analytics import router as analytics_router
from app.api.recommend import router as recommend_router
from app.api.health import router as health_router
from app.config import EMBEDDING_PATH, JOB_IDS_PATH, CHUNK_INDEX_PATH, CHUNK_META_PATH
from app.logging import setup_logger
from app.middleware import RequestLoggingMiddleware

logger = setup_logger()

app = FastAPI(title="JobScope API", version="0.1.0")
app.add_middleware(RequestLoggingMiddleware)


@app.on_event("startup")
def validate_artifacts():
    checks = {
        "embedding_file": EMBEDDING_PATH,
        "job_ids_file": JOB_IDS_PATH,
        "chunk_index_file": CHUNK_INDEX_PATH,
        "chunk_meta_file": CHUNK_META_PATH,
    }

    for name, path in checks.items():
        if os.path.exists(path):
            logger.info(f"{name} found: {path}")
        else:
            logger.warning(f"{name} missing: {path}")


@app.get("/")
def read_root():
    return {"message": "JobScope API is running", "status": "ok"}


app.include_router(jobs_router)
app.include_router(analytics_router)
app.include_router(recommend_router)
app.include_router(health_router)

ENABLE_RAG = os.getenv("ENABLE_RAG", "false").lower() == "true"

if ENABLE_RAG:
    from app.api.rag import router as rag_router
    app.include_router(rag_router)
else:
    logger.info("RAG router disabled in current runtime.")