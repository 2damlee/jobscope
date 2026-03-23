from fastapi import FastAPI
from app.api.jobs import router as jobs_router
from app.api.analytics import router as analytics_router
from app.api.recommend import router as recommend_router

app = FastAPI(title="JobScope API", version="0.1.0")


@app.get("/")
def read_root():
    return {"message": "JobScope API is running", "status": "ok"}


app.include_router(jobs_router)
app.include_router(analytics_router)
app.include_router(recommend_router)