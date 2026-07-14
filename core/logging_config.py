"""Application logging configuration."""

import logging
import os
from logging.handlers import RotatingFileHandler


def get_log_dir() -> str:
    """Return the log directory path, honoring ANKA_LOG_DIR if set."""
    return os.getenv(
        "ANKA_LOG_DIR",
        os.path.join(os.path.dirname(__file__), os.pardir, "logs"),
    )


def get_log_file() -> str:
    """Return the log file path."""
    return os.path.join(get_log_dir(), "anka.log")


def configure_logging() -> None:
    """Configure application logging with console and rotating file handlers."""
    log_dir = get_log_dir()
    log_file = get_log_file()
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        handler.close()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
