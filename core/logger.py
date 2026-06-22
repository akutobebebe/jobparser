import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from core.config import get_settings

_LOGS_DIR = Path("logs")


def setup_logger(name: str) -> logging.Logger:
    settings = get_settings()
    logger = logging.getLogger(name)

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    _LOGS_DIR.mkdir(exist_ok=True)
    log_file = _LOGS_DIR / f"{name.replace('.', '_')}.log"
    file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)

    return logger
