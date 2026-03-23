from datetime import date
from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    id: int
    title: str
    company: str | None = None
    location: str | None = None
    category: str | None = None
    seniority: str | None = None
    description: str
    cleaned_description: str | None = None
    detected_skills: str | None = None
    date_posted: date | None = None
    url: str | None = None

    class Config:
        from_attributes = True


class SkillCountResponse(BaseModel):
    skill: str
    count: int


class RecommendedJobResponse(BaseModel):
    job_id: int
    title: str
    score: float


class RagAskRequest(BaseModel):
    question: str = Field(..., example="Which backend jobs require FastAPI and PostgreSQL?")
    category: str | None = Field(default=None, example="Backend")
    location: str | None = Field(default=None, example="Berlin")
    seniority: str | None = Field(default=None, example="Junior")
    top_k: int = Field(default=3, ge=1, le=10)


class RagSource(BaseModel):
    job_id: int
    title: str
    company: str | None = None
    location: str | None = None
    category: str | None = None
    seniority: str | None = None
    chunk_id: int
    score: float


class RagAskResponse(BaseModel):
    answer: str
    sources: list[RagSource]
    matched_chunks: list[str]