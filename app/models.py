from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Integer, JSON, String, Text

from app.db import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=True)
    location = Column(String, nullable=True)
    category = Column(String, nullable=True)
    seniority = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    cleaned_description = Column(Text, nullable=True)
    detected_skills = Column(Text, nullable=True)
    date_posted = Column(Date, nullable=True)
    url = Column(String, unique=True, nullable=False)

    processing_status = Column(String, nullable=False, default="pending")
    ingested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_processed_at = Column(DateTime, nullable=True)

    source_hash = Column(String, nullable=True, index=True)
    skills_extracted_at = Column(DateTime, nullable=True)
    embedded_at = Column(DateTime, nullable=True)
    chunked_at = Column(DateTime, nullable=True)
    
class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_name = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    source_name = Column(String, nullable=True)

    input_rows = Column(Integer, nullable=True)
    output_rows = Column(Integer, nullable=True)
    inserted_rows = Column(Integer, nullable=True)
    updated_rows = Column(Integer, nullable=True)
    skipped_rows = Column(Integer, nullable=True)

    metrics = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)