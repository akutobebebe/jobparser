"""
Background scheduler for periodic job scraping using APScheduler
"""

import asyncio
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from database.connection import create_session
from database.crud import create_job, update_source, get_job_by_url, get_sources
from scrapers.djinni_scraper import DjinniScraper
from scrapers.dou_scraper import DOUScraper
from core.logger import setup_logger
from core.config import get_settings

logger = setup_logger(__name__)


class JobScraperScheduler:
    """Manage scheduled scraping tasks"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self.settings = get_settings()
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting job scraper scheduler")
        
        # Schedule scrapers based on interval
        interval_hours = self.settings.scrape_interval_hours
        
        if self.settings.enable_djinni:
            self.scheduler.add_job(
                self._run_djinni_scraper,
                trigger=IntervalTrigger(hours=interval_hours),
                id='djinni_scraper',
                name='Djinni Job Scraper',
                replace_existing=True,
            )
            logger.info(f"Scheduled Djinni scraper every {interval_hours} hours")
        
        if self.settings.enable_dou:
            self.scheduler.add_job(
                self._run_dou_scraper,
                trigger=IntervalTrigger(hours=interval_hours),
                id='dou_scraper',
                name='DOU Job Scraper',
                replace_existing=True,
            )
            logger.info(f"Scheduled DOU scraper every {interval_hours} hours")
        
        self.scheduler.start()
        self.is_running = True
        logger.info("Scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        logger.info("Stopping scheduler...")
        self.scheduler.shutdown(wait=True)
        self.is_running = False
        logger.info("Scheduler stopped")
    
    def _run_djinni_scraper(self):
        """Scheduled task for Djinni scraper"""
        logger.info("Running scheduled Djinni scraper")
        
        try:
            asyncio.run(self._scrape_and_save('djinni', DjinniScraper))
        except Exception as e:
            logger.error(f"Error in scheduled Djinni scraper: {e}", exc_info=True)
    
    def _run_dou_scraper(self):
        """Scheduled task for DOU scraper"""
        logger.info("Running scheduled DOU scraper")
        
        try:
            asyncio.run(self._scrape_and_save('dou', DOUScraper))
        except Exception as e:
            logger.error(f"Error in scheduled DOU scraper: {e}", exc_info=True)
    
    async def _scrape_and_save(self, source_name: str, scraper_class):
        """Run scraper and save results to database"""
        db = create_session()
        
        try:
            logger.info(f"Starting {source_name} scraping")
            scraper = scraper_class()
            jobs = await scraper.scrape()
            
            new_jobs = 0
            for job in jobs:
                existing = get_job_by_url(db, job.url)
                if not existing:
                    create_job(db, job.dict())
                    new_jobs += 1
            
            # Update source
            update_source(db, source_name, {
                'last_scraped': datetime.utcnow(),
            })
            
            logger.info(f"Scraper {source_name}: Added {new_jobs} new jobs")
        
        except Exception as e:
            logger.error(f"Error scraping {source_name}: {e}", exc_info=True)
        
        finally:
            db.close()
    
    def get_jobs(self):
        """Get list of scheduled jobs"""
        jobs = self.scheduler.get_jobs()
        return [(job.id, job.name, job.next_run_time) for job in jobs]


# Global scheduler instance
_scheduler: Optional[JobScraperScheduler] = None


def get_scheduler() -> JobScraperScheduler:
    """Get or create global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScraperScheduler()
    return _scheduler


def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler"""
    scheduler = get_scheduler()
    scheduler.stop()
