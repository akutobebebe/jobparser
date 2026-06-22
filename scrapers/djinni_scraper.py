from typing import List, Optional, Dict, Any
import httpx
import re
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, JobSchema
from scrapers.level import detect_level, is_junior
from core.config import get_settings


class DjinniScraper(BaseScraper):
    """Парсер для Djinni.co (без браузера)"""

    def __init__(self):
        super().__init__("djinni")
        self.base_url = "https://djinni.co"
        # exp_level=no_exp + exp_level=1y → junior / strong junior / без досвіду
        self.jobs_url = (
            f"{self.base_url}/jobs/?primary_keyword=Python"
            "&exp_level=no_exp&exp_level=1y"
        )
        self.settings = get_settings()

    def get_source_url(self) -> str:
        return self.base_url

    async def scrape(self) -> List[JobSchema]:
        jobs = []
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                self.logger.info(f"Fetching {self.jobs_url}")
                response = await client.get(
                    self.jobs_url,
                    headers={"User-Agent": self.settings.user_agent},
                    timeout=self.settings.request_timeout_seconds,
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.content, "html.parser")
                job_links = soup.find_all(
                    "a",
                    href=lambda x: x and re.match(r"^/jobs/\d+", x),
                )
                self.logger.info(f"Found {len(job_links)} job listings on page")

                for idx, link in enumerate(job_links, 1):
                    try:
                        job_data = self._extract_job_data(link)
                        if job_data and is_junior(job_data["title"]):
                            validated = self.validate_job(job_data)
                            if validated:
                                jobs.append(validated)
                                self.logger.debug(f"[{idx}] Parsed: {job_data['title']}")
                    except Exception as e:
                        self.logger.debug(f"[{idx}] Error: {e}")

                self.logger.info(f"Successfully parsed {len(jobs)} valid jobs from Djinni")

        except Exception as e:
            self.logger.error(f"Error during Djinni scraping: {e}", exc_info=True)

        return jobs

    def _extract_job_data(self, link) -> Optional[Dict[str, Any]]:
        try:
            # Title is in <h2 class="job-item__position">
            h2 = link.find("h2", class_="job-item__position")
            if not h2:
                return None
            title = self.cleanup_text(h2.get_text(), max_length=255)
            if not title:
                return None

            # URL
            job_url = link.get("href", "")
            if not job_url.startswith("http"):
                job_url = self.base_url + job_url

            # Company is in <span class="... text-gray-800 ...">
            company_span = link.find(
                "span",
                class_=lambda x: x and "text-gray-800" in x if x else False,
            )
            company = self.cleanup_text(
                company_span.get_text() if company_span else "Unknown",
                max_length=255,
            ) or "Unknown"

            # Details row (location, experience, remote)
            parent = link.find_parent("div", class_=lambda x: x and "job-item" in str(x) if x else False)
            details = ""
            if parent:
                detail_div = parent.find("div", class_=lambda x: x and "fw-medium" in str(x) if x else False)
                if detail_div:
                    details = detail_div.get_text(separator=" ", strip=True)

            description = self.cleanup_text(f"{title}. {details}") if details else self.cleanup_text(title)

            return {
                "title": title,
                "description": description or title,
                "company": company,
                "url": job_url,
                "source": "djinni",
                "source_id": self._extract_job_id(job_url),
                "level": detect_level(title, details),
                "tags": None,
            }

        except Exception as e:
            self.logger.debug(f"Error extracting job data: {e}")
            return None

    def _extract_job_id(self, url: str) -> Optional[str]:
        match = re.search(r"/jobs/(\d+)", url)
        return match.group(1) if match else None

