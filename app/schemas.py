from datetime import date
from pydantic import BaseModel


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