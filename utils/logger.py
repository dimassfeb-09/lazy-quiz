# utils/logger.py
"""
Centralized logging configuration for Lazy Quiz.
Provides consistent logging across all modules.
"""

import logging
import sys


def setup_logger(name: str = "lazy-quiz", level: int = logging.INFO) -> logging.Logger:
    """
    Set up and return a configured logger instance.

    Args:
        name: Logger name (default: "lazy-quiz")
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Console handler with color-coded formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Format: [TIME] LEVEL - Message
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


# Create default logger instance
logger = setup_logger()
