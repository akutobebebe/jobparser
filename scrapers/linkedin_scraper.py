import re
from typing import List, Optional, Dict, Any

from playwright.async_api import async_playwright

from scrapers.base import BaseScraper, JobSchema
from scrapers.level import detect_level, is_junior
from core.config import get_settings


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn public job search (no login required)."""

    def __init__(self):
        super().__init__("linkedin")
        self.base_url = "https://www.linkedin.com"
        self.search_url = (
            "https://www.linkedin.com/jobs/search/"
            "?keywords=Python&f_E=1%2C2&location=Ukraine&sortBy=DD"
        )
        self.settings = get_settings()

    def get_source_url(self) -> str:
        return self.base_url

    async def scrape(self) -> List[JobSchema]:
        jobs: List[JobSchema] = []
        try:
            async with async_playwright() as p:
                # Chromium crashes on some macOS builds (SEGV_ACCERR in GPU pipeline).
                # WebKit is native on macOS and works reliably.
                browser = await p.webkit.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.settings.user_agent,
                    locale="en-US",
                    ignore_https_errors=True,
                )
                page = await context.new_page()

                self.logger.info(f"Fetching {self.search_url}")
                await page.goto(
                    self.search_url,
                    wait_until="domcontentloaded",
                    timeout=self.settings.request_timeout_seconds * 1000,
                )

                try:
                    await page.wait_for_selector(
                        "ul.jobs-search__results-list li", timeout=10_000
                    )
                except Exception:
                    self.logger.warning(
                        "Job list selector not found — LinkedIn may be rate-limiting or layout changed"
                    )
                    await browser.close()
                    return jobs

                cards = await page.query_selector_all(
                    "ul.jobs-search__results-list li"
                )
                self.logger.info(f"Found {len(cards)} listings on LinkedIn")

                for idx, card in enumerate(cards, 1):
                    try:
                        job_data = await self._extract_job_data(card)
                        if not job_data:
                            continue
                        if not is_junior(job_data["title"]):
                            self.logger.debug(f"[{idx}] Skipped (not junior): {job_data['title']}")
                            continue
                        validated = self.validate_job(job_data)
                        if validated:
                            jobs.append(validated)
                            self.logger.debug(f"[{idx}] Parsed: {job_data['title']}")
                    except Exception as e:
                        self.logger.debug(f"[{idx}] Error: {e}")

                self.logger.info(f"Successfully parsed {len(jobs)} valid jobs from LinkedIn")
                await browser.close()

        except Exception as e:
            self.logger.warning(f"LinkedIn unavailable: {e}")

        return jobs

    async def _extract_job_data(self, card) -> Optional[Dict[str, Any]]:
        try:
            title_el = await card.query_selector("h3.base-search-card__title")
            if not title_el:
                return None
            title = self.cleanup_text(await title_el.inner_text(), max_length=255)
            if not title:
                return None

            company_el = await card.query_selector("h4.base-search-card__subtitle")
            company = "Unknown"
            if company_el:
                company = self.cleanup_text(await company_el.inner_text(), max_length=255) or "Unknown"

            link_el = await card.query_selector("a.base-card__full-link")
            if not link_el:
                return None
            url = await link_el.get_attribute("href") or ""
            if not url.startswith("http"):
                return None
            url = url.split("?")[0].rstrip("/")

            return {
                "title": title,
                "description": title,
                "company": company,
                "url": url,
                "source": "linkedin",
                "source_id": self._extract_job_id(url),
                "level": detect_level(title, ""),
                "tags": None,
            }
        except Exception as e:
            self.logger.debug(f"Error extracting LinkedIn card: {e}")
            return None

    def _extract_job_id(self, url: str) -> Optional[str]:
        match = re.search(r"(\d{10,})", url)
        return match.group(1) if match else None
