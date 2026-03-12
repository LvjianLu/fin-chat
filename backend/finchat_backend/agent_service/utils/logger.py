"""Logging configuration and utilities."""

import logging
import sys
from typing import Optional


def get_logger(
    name: str,
    level: Optional[str] = None,
    log_format: Optional[str] = None,
) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format string

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        if log_format is None:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Set level from parameter, env var, or default
        if level is None:
            level = "INFO"  # Default
        logger.setLevel(getattr(logging, level.upper()))

        # Don't propagate to root logger
        logger.propagate = False

    return logger


def configure_root_logger(level: str = "INFO") -> None:
    """Configure the root logger for the application.

    Args:
        level: Log level for root logger
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
