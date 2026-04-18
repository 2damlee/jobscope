from datetime import date

from pydantic import BaseModel, ConfigDict, Field


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

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    items: list[JobResponse]
    page: int
    size: int
    total: int


class SkillCountResponse(BaseModel):
    skill: str
    count: int


class RecommendedJobResponse(BaseModel):
    job_id: int
    title: str
    score: float
    embedding_score: float
    skill_overlap_score: float
    shared_skills: list[str]
    same_category: bool
    same_seniority: bool


class RagAskRequest(BaseModel):
    question: str = Field(
        ...,
        json_schema_extra={
            "example": "Which backend jobs require FastAPI and PostgreSQL?"
        },
    )
    category: str | None = Field(
        default=None,
        json_schema_extra={"example": "Backend"},
    )
    location: str | None = Field(
        default=None,
        json_schema_extra={"example": "Berlin"},
    )
    seniority: str | None = Field(
        default=None,
        json_schema_extra={"example": "Junior"},
    )
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
    generation_mode: str
    sources: list[RagSource]
    matched_chunks: list[str]