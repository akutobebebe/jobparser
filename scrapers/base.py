from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator

from core.logger import setup_logger

logger = setup_logger(__name__)


class JobSchema(BaseModel):
    """Pydantic schema для валідації вакансії"""
    
    title: str
    description: str
    company: Optional[str] = "Unknown"
    url: str
    source: str
    source_id: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = "USD"
    level: Optional[str] = None
    experience_years: Optional[int] = None
    tags: Optional[str] = None  # JSON string
    posted_at: Optional[datetime] = None
    
    @field_validator('title', 'description', 'url')
    @classmethod
    def check_not_empty(cls, v):
        """Ensure required fields are not empty"""
        if not v or not str(v).strip():
            raise ValueError('Field cannot be empty')
        return str(v).strip()
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Basic URL validation"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Invalid URL format')
        return v
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        """Validate source is known"""
        valid_sources = {'djinni', 'dou', 'linkedin'}
        if v.lower() not in valid_sources:
            raise ValueError(f'Source must be one of {valid_sources}')
        return v.lower()
    
    def dict(self, **kwargs):
        """Override dict method to handle company default"""
        d = super().dict(**kwargs)
        if not d.get('company'):
            d['company'] = 'Unknown'
        return d


class BaseScraper(ABC):
    """Абстрактний базовий клас для всіх парсерів"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = setup_logger(f"scrapers.{self.__class__.__name__}")
    
    @abstractmethod
    async def scrape(self) -> List[JobSchema]:
        """
        Main scraping method (must be implemented by subclasses)
        
        Returns:
            List of validated JobSchema objects
        """
        pass
    
    @abstractmethod
    def get_source_url(self) -> str:
        """
        Get main URL of the source
        
        Returns:
            Source URL
        """
        pass
    
    def validate_job(self, job_data: Dict[str, Any]) -> Optional[JobSchema]:
        """
        Validate job data against schema
        
        Args:
            job_data: Raw job data dict
        
        Returns:
            JobSchema if valid, None if invalid
        """
        try:
            job = JobSchema(**job_data)
            return job
        except ValueError as e:
            self.logger.warning(f"Job validation failed: {e}")
            self.logger.debug(f"Invalid job data: {job_data}")
            return None
    
    def cleanup_text(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text
            max_length: Optional max length
        
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        cleaned = " ".join(text.split())
        
        # Limit length
        if max_length and len(cleaned) > max_length:
            cleaned = cleaned[:max_length - 3] + "..."
        
        return cleaned
    
    async def close(self):
        """
        Cleanup resources (for browser, connections, etc.)
        Override if needed
        """
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(source={self.source_name})>"
