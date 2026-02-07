"""SQLite database operations for transactions."""

import sqlite3
import logging
from typing import List, Optional
from .models import Transaction, SCHEMA

logger = logging.getLogger(__name__)


class Database:
    """SQLite database for storing and querying transactions."""

    def __init__(self, uri: str = ":memory:"):
        """
        Initialize database connection.

        Args:
            uri: Database URI (default: in-memory database)
        """
        self.uri = uri
        self.connection = sqlite3.connect(uri)
        self.connection.row_factory = sqlite3.Row
        self._initialize_schema()
        logger.info(f"Database initialized: {uri}")

    def _initialize_schema(self):
        """Create tables and indexes from schema definition."""
        logger.debug("Creating database schema")
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def insert_transactions(self, transactions: List[Transaction]) -> int:
        """
        Bulk insert transactions into database.

        Args:
            transactions: List of Transaction objects to insert

        Returns:
            Number of transactions inserted
        """
        cursor = self.connection.cursor()

        data = [
            (t.date, t.amount, t.description, t.category)
            for t in transactions
        ]

        cursor.executemany(
            "INSERT INTO transactions (date, amount, description, category) "
            "VALUES (?, ?, ?, ?)",
            data
        )

        self.connection.commit()
        count = cursor.rowcount
        logger.info(f"Inserted {count} transactions into database")
        return count

    def update_category(self, transaction_id: int, category: str):
        """
        Update category for a specific transaction.

        Args:
            transaction_id: ID of transaction to update
            category: New category name
        """
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE transactions SET category = ? WHERE id = ?",
            (category, transaction_id)
        )
        self.connection.commit()
        logger.debug(f"Updated transaction {transaction_id} to category '{category}'")

    def get_all_transactions(self) -> List[Transaction]:
        """
        Retrieve all transactions from database.

        Returns:
            List of Transaction objects
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM transactions ORDER BY id")

        transactions = []
        for row in cursor.fetchall():
            t = Transaction(
                id=row['id'],
                date=row['date'],
                amount=row['amount'],
                description=row['description'],
                category=row['category']
            )
            transactions.append(t)

        logger.debug(f"Retrieved {len(transactions)} transactions from database")
        return transactions

    def get_by_category(self, category: str) -> List[Transaction]:
        """
        Get transactions for a specific category.

        Args:
            category: Category name to filter by

        Returns:
            List of transactions in the category
        """
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM transactions WHERE category = ? ORDER BY id",
            (category,)
        )

        transactions = []
        for row in cursor.fetchall():
            t = Transaction(
                id=row['id'],
                date=row['date'],
                amount=row['amount'],
                description=row['description'],
                category=row['category']
            )
            transactions.append(t)

        logger.debug(f"Retrieved {len(transactions)} transactions for category '{category}'")
        return transactions

    def get_transaction_count(self) -> int:
        """
        Get total number of transactions in database.

        Returns:
            Count of transactions
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM transactions")
        result = cursor.fetchone()
        return result['count'] if result else 0

    def close(self):
        """Close database connection."""
        self.connection.close()
        logger.debug("Database connection closed")
