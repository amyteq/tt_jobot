from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import VECTOR
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(BigInteger, primary_key=True, index=True)
    site = Column(String, nullable=False)
    site_job_id = Column(String)
    title = Column(String)
    company = Column(String)
    location = Column(String)
    url = Column(String)
    posted_at = Column(DateTime(timezone=True))
    jd_text = Column(Text)
    jd_embedding = Column(VECTOR(settings.providers["embeddings"].dim)) # Assuming pgvector is enabled
    meta = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=func.now())

    applications = relationship("Application", back_populates="job")

# Other models (Resume, ResumeVersion, Application, ApplicationEvent, Credential) would follow a similar structure