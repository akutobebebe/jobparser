#!/usr/bin/env python3
"""Debug script to test scrapers directly"""

import asyncio
from scrapers.djinni_scraper import DjinniScraper
from scrapers.dou_scraper import DOUScraper
from core.logger import setup_logger

logger = setup_logger(__name__)


async def test_djinni():
    """Test Djinni scraper"""
    logger.info("=" * 60)
    logger.info("Testing DjinniScraper...")
    logger.info("=" * 60)
    
    try:
        scraper = DjinniScraper()
        logger.info(f"Scraper URL: {scraper.jobs_url}")
        
        jobs = await scraper.scrape()
        logger.info(f"✅ Djinni returned {len(jobs)} jobs")
        
        if jobs:
            for idx, job in enumerate(jobs[:3], 1):
                logger.info(f"\n[Job {idx}]")
                logger.info(f"  Title: {job.title[:50]}...")
                logger.info(f"  Company: {job.company}")
                logger.info(f"  URL: {job.url}")
                logger.info(f"  Level: {job.level}")
        else:
            logger.warning("❌ No jobs returned from Djinni!")
        
        return len(jobs) > 0
    
    except Exception as e:
        logger.error(f"❌ Djinni scraper error: {e}", exc_info=True)
        return False


async def test_dou():
    """Test DOU scraper"""
    logger.info("=" * 60)
    logger.info("Testing DOUScraper...")
    logger.info("=" * 60)
    
    try:
        scraper = DOUScraper()
        logger.info(f"Scraper URL: {scraper.jobs_url}")
        
        jobs = await scraper.scrape()
        logger.info(f"✅ DOU returned {len(jobs)} jobs")
        
        if jobs:
            for idx, job in enumerate(jobs[:3], 1):
                logger.info(f"\n[Job {idx}]")
                logger.info(f"  Title: {job.title[:50]}...")
                logger.info(f"  Company: {job.company}")
                logger.info(f"  URL: {job.url}")
                logger.info(f"  Level: {job.level}")
        else:
            logger.warning("❌ No jobs returned from DOU!")
        
        return len(jobs) > 0
    
    except Exception as e:
        logger.error(f"❌ DOU scraper error: {e}", exc_info=True)
        return False


async def main():
    """Run all scraper tests"""
    logger.info("\n" * 2)
    logger.info("🔍 SCRAPER DIAGNOSTIC TEST")
    logger.info("=" * 60)
    
    djinni_ok = await test_djinni()
    logger.info("\n")
    dou_ok = await test_dou()
    
    logger.info("\n" + "=" * 60)
    logger.info("RESULTS:")
    logger.info(f"  Djinni: {'✅ OK' if djinni_ok else '❌ FAILED'}")
    logger.info(f"  DOU: {'✅ OK' if dou_ok else '❌ FAILED'}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
