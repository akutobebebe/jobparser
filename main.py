"""
FastAPI application for Job Aggregator (Optional REST API)

Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from database.connection import create_session, init_db
from database.crud import get_jobs, get_job, create_job, get_job_count
from scrapers.base import JobSchema
from core.logger import setup_logger

logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Job Aggregator API",
    description="API for accessing aggregated job listings",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= Startup/Shutdown =============
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")


# ============= Dependency =============
def get_db() -> Session:
    """Get database session"""
    db = create_session()
    try:
        yield db
    finally:
        db.close()


# ============= Routes =============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Job Aggregator API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/jobs/", response_model=List[dict])
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source: Optional[str] = None,
    level: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get list of jobs with optional filtering
    
    Parameters:
    - skip: Number of records to skip
    - limit: Number of records to return
    - source: Filter by source (djinni, dou)
    - level: Filter by level (junior, middle, senior)
    - is_active: Show active jobs only
    """
    try:
        jobs = get_jobs(
            db,
            skip=skip,
            limit=limit,
            source=source,
            level=level,
            is_active=is_active
        )
        
        return [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "url": job.url,
                "source": job.source,
                "level": job.level,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "created_at": job.created_at.isoformat(),
            }
            for job in jobs
        ]
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/jobs/{job_id}", response_model=dict)
async def get_job_detail(job_id: int, db: Session = Depends(get_db)):
    """Get job details by ID"""
    try:
        job = get_job(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "company": job.company,
            "url": job.url,
            "source": job.source,
            "level": job.level,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "tags": job.tags,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/stats/")
async def get_stats(db: Session = Depends(get_db)):
    """Get aggregated statistics"""
    try:
        total_active = get_job_count(db, is_active=True)
        total_inactive = get_job_count(db, is_active=False)
        djinni_count = get_job_count(db, source="djinni", is_active=True)
        dou_count = get_job_count(db, source="dou", is_active=True)
        
        return {
            "total_active": total_active,
            "total_inactive": total_inactive,
            "by_source": {
                "djinni": djinni_count,
                "dou": dou_count,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/jobs/", response_model=dict)
async def create_new_job(job: JobSchema, db: Session = Depends(get_db)):
    """Create new job (admin only in production)"""
    try:
        from database.crud import get_job_by_url
        
        existing = get_job_by_url(db, job.url)
        if existing:
            raise HTTPException(status_code=409, detail="Job with this URL already exists")
        
        new_job = create_job(db, job.dict())
        return {"id": new_job.id, "message": "Job created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
