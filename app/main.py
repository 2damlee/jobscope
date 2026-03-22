from fastapi import FastAPI

app = FastAPI(title="JobScope API", version="0.1.0")


@app.get("/")
def read_root():
    return {
        "message": "JobScope API is running",
        "status": "ok"
    }