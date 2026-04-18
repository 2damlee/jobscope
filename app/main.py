import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.analytics import router as analytics_router
from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.recommend import router as recommend_router
from app.artifacts import artifact_status
from app.logging import setup_logger
from app.middleware import RequestLoggingMiddleware
from app.services.recommend_service import load_embeddings_from_disk

logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    status = artifact_status()

    for item in status["artifacts"]:
        if item["exists"]:
            logger.info(f"artifact found: {item['path']}")
        else:
            logger.warning(f"artifact missing: {item['path']}")

    app.state.embeddings = None
    app.state.job_ids = None

    try:
        embeddings, job_ids = load_embeddings_from_disk()
        app.state.embeddings = embeddings
        app.state.job_ids = job_ids
        logger.info(f"recommendation cache loaded: {len(job_ids)} jobs")
    except Exception as exc:
        logger.warning(f"recommendation cache unavailable at startup: {exc}")

    if status["ready"]:
        logger.info("artifact readiness: ready")
    else:
        logger.warning(
            f"artifact readiness: degraded ({status['missing_count']} missing)"
        )

    yield


app = FastAPI(title="JobScope API", version="0.1.0", lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)


@app.get("/")
def read_root():
    status = artifact_status()
    cache_loaded = (
        getattr(app.state, "embeddings", None) is not None
        and getattr(app.state, "job_ids", None) is not None
    )

    return {
        "message": "JobScope API is running",
        "status": "ok",
        "artifact_ready": status["ready"],
        "recommendation_cache_loaded": cache_loaded,
    }


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