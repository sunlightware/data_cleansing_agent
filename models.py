"""Data models and database schema for transaction categorizer."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Transaction:
    """Represents a single transaction."""

    date: str
    amount: float
    description: str
    category: str = "Uncategorized"
    id: Optional[int] = None

    def to_dict(self) -> dict:
        """
        Convert transaction to dictionary for database insertion.

        Returns:
            Dictionary with transaction data
        """
        return {
            'date': self.date,
            'amount': self.amount,
            'description': self.description,
            'category': self.category
        }


@dataclass
class Category:
    """Represents a category with associated merchants."""

    name: str
    merchants: list

    def matches(self, description: str) -> bool:
        """
        Check if description matches any merchant using partial matching.

        Uses case-insensitive substring matching.

        Args:
            description: Transaction description to check

        Returns:
            True if any merchant pattern matches the description
        """
        desc_lower = description.lower()
        return any(merchant.lower() in desc_lower for merchant in self.merchants)


# Database schema definition
SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Uncategorized'
);

CREATE INDEX IF NOT EXISTS idx_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_description ON transactions(description);
"""
