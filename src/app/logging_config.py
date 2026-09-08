"""Basic console + rotating-file logging setup (design-document Component 8).

Per requirements' "Basic console/file logging for debugging" constraint —
deliberately not a structured-logging/ELK stack.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "locator-lens.log"
LOGGER_NAME = "locator_lens"


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Idempotently configure and return the application logger."""
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger  # already configured (e.g., re-imported in tests)

    logger.setLevel(level)
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        # File logging is best-effort; console logging alone is acceptable
        # if the filesystem is read-only or unavailable (e.g., some CI).
        logger.warning("File logging unavailable; continuing console-only.")

    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)
