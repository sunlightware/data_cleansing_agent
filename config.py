"""Configuration module for transaction categorizer."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Configuration for transaction categorizer."""

    # Directories
    input_dir: str = "./input"
    category_file: str = "./input/category_list.csv"

    # Database
    db_uri: str = ":memory:"  # In-memory SQLite

    # Logging
    log_level: str = "INFO"

    # Column definitions for transactions
    transaction_columns: list = field(default_factory=lambda: [
        "date", "amount", "nr_1", "nr_2", "description"
    ])

    # Default category for unmatched transactions
    default_category: str = "Uncategorized"


def load_config() -> Config:
    """
    Load configuration from environment or use defaults.

    Returns:
        Config object with application settings
    """
    return Config()


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
