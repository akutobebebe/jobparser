"""
Validation utilities for job data and URLs
"""

import re
from urllib.parse import urlparse
from typing import Tuple, Optional


class URLValidator:
    """Validate and normalize URLs"""
    
    VALID_SOURCES = {'djinni', 'dou'}
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL (remove fragment, trailing slash, etc.)"""
        try:
            parsed = urlparse(url)
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            return normalized.rstrip('/')
        except Exception:
            return url
    
    @staticmethod
    def is_djinni_url(url: str) -> bool:
        """Check if URL is from Djinni"""
        return 'djinni.co' in url.lower()
    
    @staticmethod
    def is_dou_url(url: str) -> bool:
        """Check if URL is from DOU"""
        return 'dou.ua' in url.lower()
    
    @staticmethod
    def get_source_from_url(url: str) -> Optional[str]:
        """Determine source from URL"""
        if URLValidator.is_djinni_url(url):
            return 'djinni'
        elif URLValidator.is_dou_url(url):
            return 'dou'
        return None


class SalaryValidator:
    """Validate and parse salary information"""
    
    @staticmethod
    def parse_salary_range(text: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Parse salary range from text
        
        Examples:
            "$1000 - $2000" -> (1000, 2000)
            "1000-2000 USD" -> (1000, 2000)
            "$2000" -> (2000, 2000)
        """
        try:
            # Extract all numbers
            numbers = re.findall(r'[\d\s,.]+', text)
            
            if not numbers:
                return None, None
            
            # Clean and convert to floats
            cleaned = []
            for num_str in numbers:
                cleaned_num = re.sub(r'[^\d.]', '', num_str.strip())
                if cleaned_num:
                    try:
                        cleaned.append(float(cleaned_num))
                    except ValueError:
                        pass
            
            if not cleaned:
                return None, None
            
            cleaned.sort()
            
            if len(cleaned) == 1:
                return cleaned[0], cleaned[0]
            else:
                return cleaned[0], cleaned[-1]
        
        except Exception:
            return None, None
    
    @staticmethod
    def is_valid_salary_range(min_sal: Optional[float], max_sal: Optional[float]) -> bool:
        """Check if salary range is valid"""
        if min_sal is None or max_sal is None:
            return True  # Allow if either is missing
        
        return min_sal <= max_sal


class ExperienceValidator:
    """Validate experience requirements"""
    
    @staticmethod
    def parse_experience_years(text: str) -> Optional[int]:
        """
        Parse experience requirement in years
        
        Examples:
            "2+ years" -> 2
            "2-3 years" -> 2
            "3 years experience" -> 3
        """
        try:
            match = re.search(r'(\d+)[+\-]?\s*(?:years?|yrs?|лет)', text.lower())
            if match:
                return int(match.group(1))
            return None
        except Exception:
            return None
    
    @staticmethod
    def get_level_from_experience(years: Optional[int]) -> Optional[str]:
        """Infer level from years of experience"""
        if years is None:
            return None
        
        if years < 2:
            return 'junior'
        elif years < 5:
            return 'middle'
        else:
            return 'senior'


class TextValidator:
    """Validate and clean text fields"""
    
    MIN_TITLE_LENGTH = 3
    MIN_DESC_LENGTH = 10
    MAX_TITLE_LENGTH = 255
    MAX_DESC_LENGTH = 10000
    
    @staticmethod
    def is_valid_title(title: str) -> bool:
        """Check if title is valid"""
        if not title:
            return False
        
        title = title.strip()
        return (
            len(title) >= TextValidator.MIN_TITLE_LENGTH and
            len(title) <= TextValidator.MAX_TITLE_LENGTH and
            title.isascii() or any(ord(c) > 127 for c in title)  # Allow non-ASCII
        )
    
    @staticmethod
    def is_valid_description(description: str) -> bool:
        """Check if description is valid"""
        if not description:
            return False
        
        description = description.strip()
        return (
            len(description) >= TextValidator.MIN_DESC_LENGTH and
            len(description) <= TextValidator.MAX_DESC_LENGTH
        )
    
    @staticmethod
    def clean_text(text: str, max_length: Optional[int] = None) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        cleaned = " ".join(text.split())
        
        # Limit length
        if max_length and len(cleaned) > max_length:
            cleaned = cleaned[:max_length - 3] + "..."
        
        return cleaned
