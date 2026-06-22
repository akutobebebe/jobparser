import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import asyncio
from typing import List, Optional

from database.connection import init_db, create_session
from database.crud import (
    get_jobs, 
    get_job_count, 
    get_sources,
    update_source,
)
from scrapers.djinni_scraper import DjinniScraper
from scrapers.dou_scraper import DOUScraper
from core.logger import setup_logger
from core.config import get_settings

logger = setup_logger(__name__)

# ============= Page Config =============
st.set_page_config(
    page_title="Job Aggregator",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("💼 Job Aggregator & Analyzer")
st.markdown("Automated job market analysis for Python developers")

# ============= Initialize Database =============
if 'db_initialized' not in st.session_state:
    try:
        init_db()
        st.session_state.db_initialized = True
        logger.info("Database initialized")
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        logger.error(f"DB init error: {e}", exc_info=True)
        st.stop()


# ============= Sidebar Configuration =============
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Settings
    settings = get_settings()
    
    st.subheader("Scraping Settings")
    col1, col2 = st.columns(2)
    with col1:
        enable_djinni = st.checkbox("Djinni.ua", value=settings.enable_djinni, key="djinni_check")
    with col2:
        enable_dou = st.checkbox("DOU.ua", value=settings.enable_dou, key="dou_check")
    
    scrape_button = st.button("🔄 Run Scraping", use_container_width=True, type="primary")
    
    st.divider()
    st.subheader("Filters")
    
    # Filter options
    selected_sources = []
    if enable_djinni:
        selected_sources.append("djinni")
    if enable_dou:
        selected_sources.append("dou")
    
    selected_level = st.multiselect(
        "Level",
        options=["junior", "middle", "senior"],
        default=[],
        help="Filter by experience level"
    )
    
    show_inactive = st.checkbox("Show inactive jobs", value=False)


# ============= Main Content =============
db = create_session()

try:
    # Tabs
    tab_overview, tab_jobs, tab_sources = st.tabs(["📊 Overview", "📋 Jobs", "🔗 Sources"])
    
    # ============= TAB: Overview =============
    with tab_overview:
        st.header("Market Overview")
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        total_active = get_job_count(db, is_active=True) or 0
        total_inactive = get_job_count(db, is_active=False) or 0
        djinni_count = get_job_count(db, source="djinni", is_active=True) or 0
        dou_count = get_job_count(db, source="dou", is_active=True) or 0
        
        with col1:
            st.metric("Total Active Jobs", total_active, delta=f"Inactive: {total_inactive}")
        with col2:
            st.metric("Djinni.ua", djinni_count, delta="Active")
        with col3:
            st.metric("DOU.ua", dou_count, delta="Active")
        with col4:
            st.metric("Last Updated", datetime.now().strftime("%H:%M:%S"))
        
        st.divider()
        
        # Level distribution
        if total_active > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Distribution by Level")
                levels = ["junior", "middle", "senior"]
                counts = [len(get_jobs(db, level=level, is_active=True, limit=1000)) for level in levels]
                
                fig_data = pd.DataFrame({
                    "Level": [level.title() for level in levels],
                    "Count": counts
                })
                
                st.bar_chart(fig_data.set_index("Level"))
            
            with col2:
                st.subheader("Jobs by Source")
                source_data = pd.DataFrame({
                    "Source": ["Djinni", "DOU"],
                    "Count": [djinni_count, dou_count]
                })
                st.pie_chart(source_data.set_index("Source"))
        else:
            st.info("No jobs parsed yet. Click '🔄 Run Scraping' in the sidebar to start!")
    
    # ============= TAB: Jobs =============
    with tab_jobs:
        st.header("Job Listings")
        
        # Prepare filters
        filters = {
            'is_active': not show_inactive,
        }
        
        if selected_sources:
            # Filter by source if selected
            pass  # TODO: Implement in CRUD
        
        if selected_level:
            # Filter by level if selected
            pass  # TODO: Implement in CRUD
        
        # Get jobs
        jobs = get_jobs(db, skip=0, limit=100, **filters)
        
        if jobs:
            # Convert to DataFrame for display
            jobs_data = []
            for job in jobs:
                jobs_data.append({
                    "Title": job.title,
                    "Company": job.company,
                    "Source": job.source.upper(),
                    "Level": job.level or "N/A",
                    "URL": job.url,
                    "Posted": job.created_at.strftime("%Y-%m-%d %H:%M"),
                })
            
            df = pd.DataFrame(jobs_data)
            
            # Display as table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn(),
                }
            )
            
            st.caption(f"Showing {len(jobs)} jobs")
        else:
            st.info("No jobs found matching the filters.")
    
    # ============= TAB: Sources =============
    with tab_sources:
        st.header("Scraping Sources")
        
        sources = get_sources(db, enabled_only=False)
        
        for source in sources:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.subheader(f"{source.name.upper()}")
                st.caption(source.url)
            
            with col2:
                if st.button(f"Enable" if not source.enabled else "Disable", 
                           key=f"btn_{source.name}"):
                    update_source(db, source.name, {"enabled": not source.enabled})
                    st.rerun()
            
            with col3:
                st.metric("Jobs", source.total_jobs_parsed or 0)
            
            st.divider()


finally:
    db.close()


# ============= Scraping Handler =============
if scrape_button:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    async def run_scrapers():
        scrapers = []
        
        if enable_djinni:
            scrapers.append(("Djinni", DjinniScraper()))
        if enable_dou:
            scrapers.append(("DOU", DOUScraper()))
        
        db = create_session()
        total_jobs = 0
        
        try:
            for idx, (name, scraper) in enumerate(scrapers):
                progress = (idx) / len(scrapers)
                progress_bar.progress(progress)
                status_text.text(f"Scraping {name}...")
                
                try:
                    logger.info(f"Starting scraper: {name}")
                    jobs = await scraper.scrape()
                    
                    # Save jobs to DB
                    from database.crud import create_job, get_job_by_url
                    for job in jobs:
                        existing = get_job_by_url(db, job.url)
                        if not existing:
                            create_job(db, job.dict())
                            total_jobs += 1
                    
                    logger.info(f"Scraper {name} completed: {len(jobs)} jobs")
                
                except Exception as e:
                    logger.error(f"Error scraping {name}: {e}", exc_info=True)
                    status_text.error(f"Error scraping {name}: {e}")
            
            progress_bar.progress(1.0)
            status_text.success(f"✅ Scraping completed! Added {total_jobs} new jobs.")
            st.rerun()
        
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {e}", exc_info=True)
            status_text.error(f"Unexpected error: {e}")
        
        finally:
            db.close()
    
    # Run async scrapers
    try:
        asyncio.run(run_scrapers())
    except Exception as e:
        st.error(f"Scraping failed: {e}")
        logger.error(f"Scraping error: {e}", exc_info=True)
