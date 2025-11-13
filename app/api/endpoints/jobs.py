from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models import Job
from app.api.schemas import JobCreate, JobRead # You'll define these in app/api/schemas.py

router = APIRouter()

@router.post("/", response_model=JobRead)
async def create_job(job: JobCreate, db: AsyncSession = Depends(get_db)):
    db_job = Job(**job.dict())
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    return db_job

@router.get("/{job_id}", response_model=JobRead)
async def read_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job