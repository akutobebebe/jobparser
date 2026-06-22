import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Основні настройки проекту"""
    
    # Database
    database_url: str = "sqlite:///./jobs.db"
    
    # Scraping
    scrape_interval_hours: int = 6
    headless_browser: bool = True
    request_timeout_seconds: int = 30
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Logging
    log_level: str = "INFO"
    logs_dir: Path = Path("logs")
    
    # Features
    enable_djinni: bool = True
    enable_dou: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def get_database_url() -> str:
    """Get database URL from settings"""
    settings = get_settings()
    return settings.database_url


def ensure_logs_dir() -> Path:
    """Ensure logs directory exists"""
    settings = get_settings()
    settings.logs_dir.mkdir(exist_ok=True)
    return settings.logs_dir
