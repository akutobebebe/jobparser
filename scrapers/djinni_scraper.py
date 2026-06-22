from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
import re
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, JobSchema
from core.config import get_settings


class DjinniScraper(BaseScraper):
    """Парсер для Djinni.ua (без браузера)"""
    
    def __init__(self):
        super().__init__("djinni")
        self.base_url = "https://djinni.co"
        self.jobs_url = f"{self.base_url}/jobs?title=Python"
        self.settings = get_settings()
        self.client = None
    
    def get_source_url(self) -> str:
        return self.base_url
    
    async def scrape(self) -> List[JobSchema]:
        """Scrape jobs from Djinni using httpx + BeautifulSoup"""
        jobs = []
        
        try:
            async with httpx.AsyncClient() as client:
                self.client = client
                
                self.logger.info(f"Fetching {self.jobs_url}")
                response = await client.get(
                    self.jobs_url,
                    headers={"User-Agent": self.settings.user_agent},
                    timeout=self.settings.request_timeout_seconds,
                    follow_redirects=True
                )
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, "html.parser")
                
                # Find job links: /jobs/<id>-<title>
                job_links = soup.find_all("a", href=lambda x: x and re.match(r'^/jobs/\d+', x))
                self.logger.info(f"Found {len(job_links)} job listings on page")
                
                for idx, link in enumerate(job_links, 1):
                    try:
                        job_data = self._extract_job_data(link)
                        if job_data:
                            validated_job = self.validate_job(job_data)
                            if validated_job:
                                jobs.append(validated_job)
                                self.logger.debug(f"[{idx}] Parsed: {job_data.get('title')}")
                            else:
                                self.logger.debug(f"[{idx}] Validation failed for job")
                    except Exception as e:
                        self.logger.debug(f"[{idx}] Error extracting job: {e}")
                
                self.logger.info(f"Successfully parsed {len(jobs)} valid jobs from Djinni")
        
        except Exception as e:
            self.logger.error(f"Error during Djinni scraping: {e}", exc_info=True)
        finally:
            await self.close()
        
        return jobs
    
    def _extract_job_data(self, link) -> Optional[Dict[str, Any]]:
        """Extract job data from job link element"""
        try:
            # Get title (link text, cleaned)
            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                return None
            
            title = self.cleanup_text(title, max_length=255)
            
            # Get URL
            job_url = link.get("href")
            if not job_url:
                return None
            
            if not job_url.startswith("http"):
                job_url = self.base_url + job_url
            
            # Find parent container
            container = link.find_parent("div", class_=lambda x: x and "d-flex" in str(x))
            
            if not container:
                return None
            
            # Extract company - look for company info in the same container
            company = "Unknown"
            company_text = container.find("div", class_=lambda x: x and "company" in str(x).lower() if x else False)
            if company_text:
                company = company_text.get_text(strip=True)
            else:
                # Try to find any text after title
                texts = [t.strip() for t in container.stripped_strings]
                if len(texts) > 1:
                    company = texts[1]
            
            company = self.cleanup_text(company, max_length=255)
            
            # Description is the title (or a combination of texts)
            description = self.cleanup_text(f"Python Developer position: {title}")
            
            # Extract level from title/company
            level = self._extract_level(title, company)
            
            # Build job data
            job_data = {
                "title": title,
                "description": description,
                "company": company,
                "url": job_url,
                "source": "djinni",
                "source_id": self._extract_job_id_from_url(job_url),
                "level": level,
                "tags": None,
            }
            
            return job_data
        
        except Exception as e:
            self.logger.debug(f"Error extracting job data: {e}")
            return None
    
    def _extract_job_id_from_url(self, url: str) -> Optional[str]:
        """Extract job ID from Djinni URL"""
        # URLs like: https://djinni.co/jobs/123456-title
        match = re.search(r'/jobs/(\d+)', url)
        return match.group(1) if match else None
    
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
    
    async def close(self):
        """Close client"""
        if self.client:
            await self.client.aclose()
