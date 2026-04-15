import os
from pathlib import Path

from fastapi import FastAPI

from app.api.analytics import router as analytics_router
from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.recommend import router as recommend_router
from app.config import ARTIFACT_PATHS
from app.logging import setup_logger
from app.middleware import RequestLoggingMiddleware

logger = setup_logger()

app = FastAPI(title="JobScope API", version="0.1.0")
app.add_middleware(RequestLoggingMiddleware)


def artifact_status() -> dict:
    items = []
    missing = []

    for path in ARTIFACT_PATHS:
        path_obj = Path(path)
        exists = path_obj.exists()

        items.append(
            {
                "name": path_obj.name,
                "path": str(path_obj),
                "exists": exists,
            }
        )

        if not exists:
            missing.append(str(path_obj))

    return {
        "ready": len(missing) == 0,
        "missing_count": len(missing),
        "missing": missing,
        "artifacts": items,
    }


@app.on_event("startup")
def validate_artifacts():
    status = artifact_status()

    for item in status["artifacts"]:
        if item["exists"]:
            logger.info(f"artifact found: {item['path']}")
        else:
            logger.warning(f"artifact missing: {item['path']}")

    if status["ready"]:
        logger.info("artifact readiness: ready")
    else:
        logger.warning(
            f"artifact readiness: degraded ({status['missing_count']} missing)"
        )


@app.get("/")
def read_root():
    status = artifact_status()
    return {
        "message": "JobScope API is running",
        "status": "ok",
        "artifact_ready": status["ready"],
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