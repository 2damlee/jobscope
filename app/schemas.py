from pydantic import BaseModel


class JobResponse(BaseModel):
    id: int
    title: str
    company: str | None = None
    location: str | None = None
    category: str | None = None
    seniority: str | None = None
    description: str | None = None
    date_posted: str | None = None
    url: str | None = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    items: list[JobResponse]
    page: int
    size: int
    total: int