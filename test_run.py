#!/usr/bin/env python3
"""Test script to verify all components work correctly"""

import asyncio
from database.connection import init_db, create_session
from database.crud import get_job_count
from core.logger import setup_logger

logger = setup_logger(__name__)


def test_database():
    """Test database connection and initialization"""
    logger.info("Testing database...")
    try:
        init_db()
        logger.info("✅ Database initialized")
        
        db = create_session()
        count = get_job_count(db)
        db.close()
        
        logger.info(f"✅ Database connection working. Total jobs: {count or 0}")
        return True
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}", exc_info=True)
        return False


async def test_scrapers():
    """Test scraper initialization"""
    logger.info("Testing scrapers...")
    try:
        from scrapers.djinni_scraper import DjinniScraper
        from scrapers.dou_scraper import DOUScraper
        
        djinni = DjinniScraper()
        dou = DOUScraper()
        
        logger.info(f"✅ DjinniScraper initialized: {djinni}")
        logger.info(f"✅ DOUScraper initialized: {dou}")
        
        # Don't actually scrape, just verify initialization
        return True
    except Exception as e:
        logger.error(f"❌ Scraper test failed: {e}", exc_info=True)
        return False


def main():
    """Run all tests"""
    logger.info("=" * 50)
    logger.info("Running diagnostic tests...")
    logger.info("=" * 50)
    
    db_ok = test_database()
    scraper_ok = asyncio.run(test_scrapers())
    
    logger.info("=" * 50)
    if db_ok and scraper_ok:
        logger.info("✅ All tests passed!")
    else:
        logger.error("❌ Some tests failed")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
