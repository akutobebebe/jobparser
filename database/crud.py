from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from core.logger import setup_logger
from database.models import Job, Source

logger = setup_logger(__name__)


# ============= Job CRUD =============

def create_job(db: Session, job_data: dict) -> Job:
    """Create new job in database"""
    job = Job(**job_data)
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.debug(f"Created job: {job.id} - {job.title}")
    return job


def get_job_by_url(db: Session, url: str) -> Optional[Job]:
    """Get job by URL"""
    return db.query(Job).filter(Job.url == url).first()


def get_job(db: Session, job_id: int) -> Optional[Job]:
    """Get job by ID"""
    return db.query(Job).filter(Job.id == job_id).first()


def get_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None,
    level: Optional[str] = None,
    is_active: Optional[bool] = True,
) -> List[Job]:
    """Get jobs with optional filtering"""
    query = db.query(Job)
    
    if source:
        query = query.filter(Job.source == source)
    if level:
        query = query.filter(Job.level == level)
    if is_active is not None:
        query = query.filter(Job.is_active == is_active)
    
    return query.order_by(desc(Job.created_at)).offset(skip).limit(limit).all()


def update_job(db: Session, job_id: int, update_data: dict) -> Optional[Job]:
    """Update job"""
    job = get_job(db, job_id)
    if not job:
        return None
    
    for key, value in update_data.items():
        setattr(job, key, value)
    
    db.commit()
    db.refresh(job)
    logger.debug(f"Updated job: {job_id}")
    return job


def delete_job(db: Session, job_id: int) -> bool:
    """Delete job"""
    job = get_job(db, job_id)
    if not job:
        return False
    
    db.delete(job)
    db.commit()
    logger.debug(f"Deleted job: {job_id}")
    return True


def mark_inactive_jobs(db: Session, source: str, last_seen_before: datetime) -> int:
    """Mark jobs as inactive if not seen for specified time"""
    jobs = db.query(Job).filter(
        and_(
            Job.source == source,
            Job.last_seen < last_seen_before,
            Job.is_active == True
        )
    ).all()
    
    count = len(jobs)
    for job in jobs:
        job.is_active = False
    
    db.commit()
    logger.info(f"Marked {count} jobs as inactive for source {source}")
    return count


def get_job_count(db: Session, source: Optional[str] = None, is_active: bool = True) -> int:
    """Get total job count"""
    query = db.query(Job).filter(Job.is_active == is_active)
    if source:
        query = query.filter(Job.source == source)
    return query.count()


# ============= Source CRUD =============

def create_source(db: Session, name: str, url: str) -> Source:
    """Create new source"""
    source = Source(name=name, url=url)
    db.add(source)
    db.commit()
    db.refresh(source)
    logger.info(f"Created source: {name}")
    return source


def get_source(db: Session, name: str) -> Optional[Source]:
    """Get source by name"""
    return db.query(Source).filter(Source.name == name).first()


def get_sources(db: Session, enabled_only: bool = True) -> List[Source]:
    """Get all sources"""
    query = db.query(Source)
    if enabled_only:
        query = query.filter(Source.enabled == True)
    return query.all()


def update_source(db: Session, name: str, update_data: dict) -> Optional[Source]:
    """Update source"""
    source = get_source(db, name)
    if not source:
        return None
    
    for key, value in update_data.items():
        setattr(source, key, value)
    
    db.commit()
    db.refresh(source)
    logger.debug(f"Updated source: {name}")
    return source
