from sqlalchemy import Column, Integer, String, Text, Date
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