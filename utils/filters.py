"""
Filtering and analysis utilities for job listings
"""

from typing import List, Optional, Callable
import json
import re

from database.models import Job


class JobFilter:
    """Advanced filtering for job listings"""
    
    @staticmethod
    def filter_by_level(jobs: List[Job], level: Optional[str]) -> List[Job]:
        """Filter jobs by experience level"""
        if not level:
            return jobs
        
        return [job for job in jobs if job.level and job.level.lower() == level.lower()]
    
    @staticmethod
    def filter_by_source(jobs: List[Job], source: Optional[str]) -> List[Job]:
        """Filter jobs by source"""
        if not source:
            return jobs
        
        return [job for job in jobs if job.source.lower() == source.lower()]
    
    @staticmethod
    def filter_by_salary_range(
        jobs: List[Job],
        min_salary: Optional[float] = None,
        max_salary: Optional[float] = None
    ) -> List[Job]:
        """Filter jobs by salary range"""
        if min_salary is None and max_salary is None:
            return jobs
        
        filtered = []
        for job in jobs:
            if job.salary_min is None and job.salary_max is None:
                filtered.append(job)  # Include jobs without salary info
                continue
            
            job_max = job.salary_max or job.salary_min or 0
            job_min = job.salary_min or 0
            
            if min_salary and job_max < min_salary:
                continue
            if max_salary and job_min > max_salary:
                continue
            
            filtered.append(job)
        
        return filtered
    
    @staticmethod
    def filter_by_keyword(
        jobs: List[Job],
        keywords: List[str],
        fields: List[str] = None
    ) -> List[Job]:
        """Filter jobs by keywords in specified fields"""
        if not keywords:
            return jobs
        
        if fields is None:
            fields = ['title', 'description', 'company']
        
        filtered = []
        keywords_lower = [k.lower() for k in keywords]
        
        for job in jobs:
            for field in fields:
                if hasattr(job, field):
                    value = getattr(job, field, "")
                    if value and any(kw in str(value).lower() for kw in keywords_lower):
                        filtered.append(job)
                        break
        
        return filtered
    
    @staticmethod
    def filter_active(jobs: List[Job], active_only: bool = True) -> List[Job]:
        """Filter active/inactive jobs"""
        if active_only:
            return [job for job in jobs if job.is_active]
        return jobs


class LevelDetector:
    """Detect job level from title and description"""
    
    SENIOR_KEYWORDS = [
        'senior', 'lead', 'principal', 'architect', 'head of',
        'director', 'manager', 'expert', 'master'
    ]
    
    MIDDLE_KEYWORDS = [
        'middle', 'mid-level', 'intermediate', 'specialist',
        'developer ii', 'engineer ii'
    ]
    
    JUNIOR_KEYWORDS = [
        'junior', 'graduate', 'entry', 'trainee', 'intern',
        'associate', 'developer i', 'engineer i'
    ]
    
    @classmethod
    def detect(cls, title: str, description: str = "") -> Optional[str]:
        """Detect experience level from text"""
        combined = (title + " " + description).lower()
        
        # Count keyword matches
        senior_count = sum(1 for kw in cls.SENIOR_KEYWORDS if kw in combined)
        middle_count = sum(1 for kw in cls.MIDDLE_KEYWORDS if kw in combined)
        junior_count = sum(1 for kw in cls.JUNIOR_KEYWORDS if kw in combined)
        
        # Determine level by highest count
        if senior_count > 0 and senior_count >= middle_count and senior_count >= junior_count:
            return 'senior'
        elif middle_count > 0 and middle_count >= junior_count:
            return 'middle'
        elif junior_count > 0:
            return 'junior'
        
        return None


class SkillExtractor:
    """Extract and parse skills from job descriptions"""
    
    COMMON_PYTHON_SKILLS = {
        'FastAPI', 'Django', 'Flask', 'aiohttp',
        'SQLAlchemy', 'Pydantic', 'Celery',
        'NumPy', 'Pandas', 'Scikit-learn',
        'PostgreSQL', 'MongoDB', 'Redis',
        'Docker', 'Kubernetes', 'pytest',
        'asyncio', 'typing', 'logging',
    }
    
    @classmethod
    def extract_from_description(cls, description: str) -> List[str]:
        """Extract common Python skills from description"""
        found_skills = []
        
        for skill in cls.COMMON_PYTHON_SKILLS:
            if skill.lower() in description.lower():
                found_skills.append(skill)
        
        return sorted(found_skills)
    
    @classmethod
    def parse_tags(cls, tags_json: Optional[str]) -> List[str]:
        """Parse JSON tags string to list"""
        if not tags_json:
            return []
        
        try:
            if isinstance(tags_json, str):
                return json.loads(tags_json)
            return tags_json
        except (json.JSONDecodeError, TypeError):
            return []
