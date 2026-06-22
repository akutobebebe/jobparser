from typing import List, Optional, Dict, Any
from datetime import datetime

from bs4 import BeautifulSoup
import httpx
import re

from scrapers.base import BaseScraper, JobSchema
from core.config import get_settings


class DOUScraper(BaseScraper):
    """Парсер для DOU.ua"""
    
    def __init__(self):
        super().__init__("dou")
        self.base_url = "https://jobs.dou.ua"  # Updated to correct domain
        self.jobs_url = f"{self.base_url}/?category=Python"
        self.settings = get_settings()
    
    def get_source_url(self) -> str:
        return self.base_url
    
    async def scrape(self) -> List[JobSchema]:
        """Scrape jobs from DOU"""
        jobs = []
        
        try:
            self.logger.info(f"Fetching {self.jobs_url}")
            
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                # Set headers to avoid being blocked
                headers = {
                    'User-Agent': self.settings.user_agent,
                    'Accept': 'text/html,application/xhtml+xml',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                
                response = await client.get(self.jobs_url, headers=headers, follow_redirects=True)
                response.raise_for_status()
                
                html_content = response.text
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find job listings - look for different selectors
            job_elements = soup.find_all('div', class_='vacancy')
            
            if not job_elements:
                # Alternative selector
                job_elements = soup.find_all(['div', 'article'], class_=lambda x: x and 'job' in str(x).lower() if x else False)
            
            self.logger.info(f"Found {len(job_elements)} job listings on page")
            
            for idx, element in enumerate(job_elements, 1):
                try:
                    job_data = self._extract_job_data(element)
                    if job_data:
                        validated_job = self.validate_job(job_data)
                        if validated_job:
                            jobs.append(validated_job)
                            self.logger.debug(f"[{idx}] Parsed: {job_data.get('title')}")
                        else:
                            self.logger.debug(f"[{idx}] Validation failed for job")
                except Exception as e:
                    self.logger.debug(f"[{idx}] Error extracting job: {e}")
            
            self.logger.info(f"Successfully parsed {len(jobs)} valid jobs from DOU")
            
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error during DOU scraping: {e}")
        except Exception as e:
            self.logger.error(f"Error during DOU scraping: {e}", exc_info=True)
        
        return jobs
    
    def _extract_job_data(self, element) -> Optional[Dict[str, Any]]:
        """Extract job data from job element"""
        try:
            # Extract title and URL
            title_elem = element.find('a', class_='vacancy__title')
            if not title_elem:
                return None
            
            title = self.cleanup_text(title_elem.get_text(), max_length=255)
            job_url = title_elem.get('href', '')
            
            if not job_url:
                return None
            
            if not job_url.startswith('http'):
                job_url = self.base_url + job_url
            
            # Extract company
            company_elem = element.find('div', class_='vacancy__company')
            company = 'Unknown'
            if company_elem:
                company = self.cleanup_text(company_elem.get_text(), max_length=255)
            
            # Extract description/summary
            description_elem = element.find('div', class_='vacancy__desc')
            description = ''
            if description_elem:
                description = self.cleanup_text(description_elem.get_text())
            
            if not description:
                description = f"Position: {title}"
            
            # Extract salary if available
            salary_min, salary_max = self._extract_salary(element)
            
            # Extract level
            level = self._extract_level(title, description)
            
            # Extract experience
            experience_years = self._extract_experience_years(element)
            
            # Build job data
            job_data = {
                "title": title,
                "description": description,
                "company": company,
                "url": job_url,
                "source": "dou",
                "source_id": self._extract_job_id_from_url(job_url),
                "salary_min": salary_min,
                "salary_max": salary_max,
                "level": level,
                "experience_years": experience_years,
                "tags": None,
            }
            
            return job_data
        
        except Exception as e:
            self.logger.debug(f"Error extracting job data: {e}")
            return None
    
    def _extract_job_id_from_url(self, url: str) -> Optional[str]:
        """Extract job ID from DOU URL"""
        # URLs like: https://dou.ua/companies/job/123456
        match = re.search(r'/job/(\d+)', url)
        return match.group(1) if match else None
    
    def _extract_salary(self, element) -> tuple[Optional[float], Optional[float]]:
        """Extract salary range from element"""
        try:
            salary_elem = element.find('div', class_='vacancy__salary')
            if not salary_elem:
                return None, None
            
            salary_text = salary_elem.get_text().strip()
            
            # Try to parse salary (e.g., "$1000 - $2000" or "1000 - 2000 USD")
            numbers = re.findall(r'[\d\s]+', salary_text)
            
            if len(numbers) >= 2:
                try:
                    salary_min = float(numbers[0].strip())
                    salary_max = float(numbers[1].strip())
                    return salary_min, salary_max
                except ValueError:
                    pass
            
            return None, None
        except Exception as e:
            self.logger.debug(f"Error extracting salary: {e}")
            return None, None
    
    def _extract_level(self, title: str, description: str) -> Optional[str]:
        """Extract level from title/description"""
        combined = (title + " " + description).lower()
        
        if any(word in combined for word in ['senior', 'lead', 'principal']):
            return 'senior'
        elif any(word in combined for word in ['middle', 'mid-level', 'intermediate']):
            return 'middle'
        elif any(word in combined for word in ['junior', 'graduate', 'entry']):
            return 'junior'
        
        return None
    
    def _extract_experience_years(self, element) -> Optional[int]:
        """Extract experience requirement from element"""
        try:
            text = element.get_text().lower()
            
            # Look for patterns like "2+ years", "2-3 years"
            match = re.search(r'(\d+)[+\-]?\s*(?:years?|лет)', text)
            if match:
                return int(match.group(1))
            
            return None
        except Exception:
            return None
