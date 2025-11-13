from fastapi import FastAPI
from app.api.endpoints import jobs, applications # Import your API routes
from app.config import settings

app = FastAPI(
    title="Jobot API",
    version="0.1.0",
    description="Automated Job Application and Tracking System",
)

# Include your API routers
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(applications.router, prefix="/applications", tags=["applications"])

@app.get("/")
async def root():
    return {"message": "Jobot API is running!"}