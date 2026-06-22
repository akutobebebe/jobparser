from typing import List, Optional, Dict, Any
from datetime import datetime

from playwright.async_api import async_playwright, Page
import re

from scrapers.base import BaseScraper, JobSchema
from core.config import get_settings


class DjinniScraper(BaseScraper):
    """Парсер для Djinni.ua"""
    
    def __init__(self):
        super().__init__("djinni")
        self.base_url = "https://djinni.co"
        self.jobs_url = f"{self.base_url}/jobs?title=Python"
        self.settings = get_settings()
        self.browser = None
        self.page = None
    
    def get_source_url(self) -> str:
        return self.base_url
    
    async def scrape(self) -> List[JobSchema]:
        """Scrape jobs from Djinni"""
        jobs = []
        
        try:
            await self._init_browser()
            
            self.logger.info(f"Navigating to {self.jobs_url}")
            await self.page.goto(self.jobs_url, wait_until="networkidle")
            
            # Wait for jobs to load
            await self.page.wait_for_selector("a.list-item__title", timeout=5000)
            
            job_elements = await self.page.query_selector_all("a.list-item__title")
            self.logger.info(f"Found {len(job_elements)} job listings on page")
            
            for idx, element in enumerate(job_elements, 1):
                try:
                    job_data = await self._extract_job_data(element)
                    if job_data:
                        validated_job = self.validate_job(job_data)
                        if validated_job:
                            jobs.append(validated_job)
                            self.logger.debug(f"[{idx}] Parsed: {job_data.get('title')}")
                        else:
                            self.logger.warning(f"[{idx}] Validation failed for job")
                except Exception as e:
                    self.logger.error(f"[{idx}] Error extracting job: {e}", exc_info=True)
            
            self.logger.info(f"Successfully parsed {len(jobs)} valid jobs from Djinni")
            
        except Exception as e:
            self.logger.error(f"Error during Djinni scraping: {e}", exc_info=True)
        finally:
            await self.close()
        
        return jobs
    
    async def _init_browser(self):
        """Initialize Playwright browser"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=self.settings.headless_browser
            )
            self.page = await self.browser.new_page()
            self.page.set_default_timeout(self.settings.request_timeout_seconds * 1000)
            
            await self.page.set_extra_http_headers({
                'User-Agent': self.settings.user_agent
            })
            
            self.logger.debug("Browser initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing browser: {e}")
            raise
    
    async def _extract_job_data(self, element) -> Optional[Dict[str, Any]]:
        """Extract job data from job element"""
        try:
            # Get title and URL
            title_text = await element.inner_text()
            title = self.cleanup_text(title_text, max_length=255)
            
            job_url = await element.get_attribute("href")
            if not job_url:
                return None
            
            if not job_url.startswith("http"):
                job_url = self.base_url + job_url
            
            # Get parent card to extract more info
            card = await element.evaluate("el => el.closest('.list-item')")
            
            # Try to extract company
            company_elem = await element.evaluate(
                "el => el.closest('.list-item')?.querySelector('.list-item__company')"
            )
            company = "Unknown"
            if company_elem:
                company = await element.evaluate(
                    "el => el.closest('.list-item')?.querySelector('.list-item__company')?.innerText || 'Unknown'"
                )
            
            # Try to extract description (preview)
            description_elem = await element.evaluate(
                "el => el.closest('.list-item')?.querySelector('.list-item__description')"
            )
            description = ""
            if description_elem:
                description = await element.evaluate(
                    "el => el.closest('.list-item')?.querySelector('.list-item__description')?.innerText || ''"
                )
            
            if not description:
                description = f"Position: {title}"
            
            description = self.cleanup_text(description)
            company = self.cleanup_text(company, max_length=255)
            
            # Extract level if present in title or description
            level = self._extract_level(title, description)
            
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
        """Close browser"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            self.logger.debug("Browser closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")
