from typing import List, Optional, Dict, Any
import httpx
import re
from xml.etree import ElementTree as ET
from html import unescape

from scrapers.base import BaseScraper, JobSchema
from scrapers.level import detect_level, is_junior
from core.config import get_settings


class DOUScraper(BaseScraper):
    """Парсер для DOU.ua через RSS-фід (JS-незалежний)"""

    def __init__(self):
        super().__init__("dou")
        self.base_url = "https://jobs.dou.ua"
        # exp=0-1: без досвіду + junior; exp=1-3: strong junior (middle може потрапити — фільтруємо по title)
        self.feed_urls = [
            f"{self.base_url}/vacancies/feeds/?category=Python&exp=0-1",
            f"{self.base_url}/vacancies/feeds/?category=Python&exp=1-3",
        ]
        self.settings = get_settings()

    def get_source_url(self) -> str:
        return self.base_url

    async def scrape(self) -> List[JobSchema]:
        jobs: List[JobSchema] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(follow_redirects=True) as client:
            for feed_url in self.feed_urls:
                try:
                    self.logger.info(f"Fetching {feed_url}")
                    response = await client.get(
                        feed_url,
                        headers={"User-Agent": self.settings.user_agent},
                        timeout=self.settings.request_timeout_seconds,
                    )
                    response.raise_for_status()

                    root = ET.fromstring(response.content)
                    channel = root.find("channel")
                    items = channel.findall("item") if channel is not None else []
                    self.logger.info(f"Found {len(items)} listings in {feed_url}")

                    for idx, item in enumerate(items, 1):
                        try:
                            job_data = self._extract_job_data(item)
                            if not job_data:
                                continue
                            url = job_data["url"]
                            if url in seen_urls:
                                continue
                            if not is_junior(job_data["title"]):
                                self.logger.debug(f"[{idx}] Skipped (not junior): {job_data['title']}")
                                continue
                            seen_urls.add(url)
                            validated = self.validate_job(job_data)
                            if validated:
                                jobs.append(validated)
                                self.logger.debug(f"[{idx}] Parsed: {job_data['title']}")
                        except Exception as e:
                            self.logger.debug(f"[{idx}] Error: {e}")

                except httpx.HTTPError as e:
                    self.logger.error(f"HTTP error fetching {feed_url}: {e}")
                except Exception as e:
                    self.logger.error(f"Error fetching {feed_url}: {e}", exc_info=True)

        self.logger.info(f"Successfully parsed {len(jobs)} valid jobs from DOU")
        return jobs

    def _extract_job_data(self, item: ET.Element) -> Optional[Dict[str, Any]]:
        try:
            raw_title = (item.findtext("title") or "").strip()
            if not raw_title:
                return None

            title = raw_title
            company = "Unknown"
            if " в " in raw_title:
                parts = raw_title.split(" в ", 1)
                title = parts[0].strip()
                company = parts[1].split(",")[0].strip()

            title = self.cleanup_text(title, max_length=255)
            company = self.cleanup_text(company, max_length=255) or "Unknown"

            job_url = (item.findtext("link") or "").strip()
            if not job_url or not job_url.startswith("http"):
                return None

            raw_desc = item.findtext("description") or ""
            description = self.cleanup_text(
                re.sub(r"<[^>]+>", " ", unescape(raw_desc))
            )
            if not description:
                description = title

            return {
                "title": title,
                "description": description,
                "company": company,
                "url": job_url,
                "source": "dou",
                "source_id": self._extract_job_id(job_url),
                "level": detect_level(title, description),
                "tags": None,
            }

        except Exception as e:
            self.logger.debug(f"Error extracting job data: {e}")
            return None

    def _extract_job_id(self, url: str) -> Optional[str]:
        match = re.search(r"/vacancies/(\d+)/", url)
        return match.group(1) if match else None
