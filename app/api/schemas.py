from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class JobCreate(BaseModel):
    site: str
    site_job_id: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    posted_at: Optional[datetime] = None
    jd_text: Optional[str] = None
    meta: Optional[dict] = None

class JobRead(JobCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True # Allow mapping from SQLAlchemy models