"""
Job Aggregator - Main entry point for CLI operations
"""

import asyncio
import sys
from datetime import datetime

from database.connection import init_db, create_session
from database.crud import create_job, update_source, get_job_by_url, get_sources
from scrapers.djinni_scraper import DjinniScraper
from scrapers.dou_scraper import DOUScraper
from core.logger import setup_logger
from core.config import get_settings

logger = setup_logger(__name__)


async def run_scraper(scraper_class, source_name: str, db) -> int:
    """
    Run a single scraper and save results to database
    
    Returns:
        Number of new jobs added
    """
    try:
        logger.info(f"Starting scraper: {source_name}")
        scraper = scraper_class()
        
        jobs = await scraper.scrape()
        logger.info(f"Scraper returned {len(jobs)} jobs")
        
        new_jobs = 0
        for job in jobs:
            existing = get_job_by_url(db, job.url)
            if not existing:
                create_job(db, job.dict())
                new_jobs += 1
        
        # Update source stats
        update_source(db, source_name, {
            'last_scraped': datetime.utcnow(),
            'total_jobs_parsed': db.query(type([])).count()  # Placeholder
        })
        
        logger.info(f"Scraper {source_name} completed: {new_jobs} new jobs added")
        return new_jobs
    
    except Exception as e:
        logger.error(f"Error in scraper {source_name}: {e}", exc_info=True)
        return 0


async def main():
    """Main entry point"""
    logger.info("Starting Job Aggregator")
    
    # Initialize database
    try:
        init_db()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return 1
    
    db = create_session()
    
    try:
        settings = get_settings()
        total_new_jobs = 0
        
        # Get enabled sources
        sources = get_sources(db, enabled_only=True)
        source_names = {s.name for s in sources}
        
        # Run scrapers
        if 'djinni' in source_names and settings.enable_djinni:
            new = await run_scraper(DjinniScraper, 'djinni', db)
            total_new_jobs += new
        
        if 'dou' in source_names and settings.enable_dou:
            new = await run_scraper(DOUScraper, 'dou', db)
            total_new_jobs += new
        
        logger.info(f"Job aggregation completed. Total new jobs: {total_new_jobs}")
        print(f"✅ Scraping completed! Added {total_new_jobs} new jobs.")
        
        return 0
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    
    finally:
        db.close()


if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
