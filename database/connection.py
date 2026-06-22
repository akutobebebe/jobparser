from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator

from core.config import get_database_url
from core.logger import setup_logger
from database.models import Base

logger = setup_logger(__name__)


def get_engine():
    """Create database engine"""
    db_url = get_database_url()
    logger.info(f"Connecting to database: {db_url}")
    
    # Use StaticPool для SQLite (за замовчуванням)
    if "sqlite" in db_url:
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(db_url, echo=False)
    
    return engine


def init_db():
    """Initialize database (create all tables)"""
    engine = get_engine()
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    return engine


def create_session() -> Session:
    """Create and return a new database session"""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    db = create_session()
    try:
        yield db
    finally:
        db.close()
