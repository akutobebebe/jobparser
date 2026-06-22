import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from core.config import get_settings, ensure_logs_dir


def setup_logger(name: str) -> logging.Logger:
    """
    Configure logger with both console and file handlers
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    settings = get_settings()
    logger = logging.getLogger(name)
    
    # Set level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Format
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    
    # File handler
    logs_dir = ensure_logs_dir()
    log_file = logs_dir / f"{name.replace('.', '_')}.log"
    
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)
    
    return logger
