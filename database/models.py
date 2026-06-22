from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Job(Base):
    """Модель вакансії"""
    
    __tablename__ = "jobs"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Основна інформація
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    company = Column(String(255), nullable=False, index=True)
    
    # URL та джерело
    url = Column(String(1024), unique=True, nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)  # "djinni", "dou"
    source_id = Column(String(255), nullable=True)  # ID вакансії на джерелі
    
    # Зарплата
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(10), default="USD", nullable=True)
    
    # Вимоги та фільтри
    level = Column(String(50), nullable=True, index=True)  # "junior", "middle", "senior"
    experience_years = Column(Integer, nullable=True)
    
    # Теги та навички
    tags = Column(Text, nullable=True)  # JSON: ["Python", "FastAPI", "PostgreSQL"]
    
    # Статус
    is_active = Column(Boolean, default=True, index=True)
    
    # Часові мітки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    posted_at = Column(DateTime, nullable=True)  # Коли вакансія була розміщена
    
    # Індекси
    __table_args__ = (
        Index('idx_source_level', 'source', 'level'),
        Index('idx_company_source', 'company', 'source'),
    )
    
    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title={self.title}, company={self.company}, source={self.source})>"


class Source(Base):
    """Модель джерела парсингу"""
    
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # "djinni", "dou"
    url = Column(String(500), nullable=False)
    enabled = Column(Boolean, default=True, index=True)
    
    # Статистика
    last_scraped = Column(DateTime, nullable=True)
    total_jobs_parsed = Column(Integer, default=0)
    
    # Часові мітки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Source(name={self.name}, enabled={self.enabled})>"
