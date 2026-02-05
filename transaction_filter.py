"""Transaction filtering based on ignore patterns."""

import logging
from typing import List
from .models import Transaction

logger = logging.getLogger(__name__)


class TransactionFilter:
    """Filters transactions based on ignore patterns."""

    def __init__(self, ignore_patterns: List[str]):
        """
        Initialize transaction filter.

        Args:
            ignore_patterns: List of patterns to match for ignoring transactions
        """
        self.ignore_patterns = [p.lower() for p in ignore_patterns]
        logger.info(f"Transaction filter initialized with {len(self.ignore_patterns)} ignore patterns")
        logger.debug(f"Ignore patterns: {self.ignore_patterns}")

    def should_ignore(self, description: str) -> bool:
        """
        Check if a transaction description should be ignored.

        Args:
            description: Transaction description to check

        Returns:
            True if transaction should be ignored, False otherwise
        """
        desc_lower = description.lower()

        for pattern in self.ignore_patterns:
            if pattern in desc_lower:
                logger.debug(f"Transaction matches ignore pattern '{pattern}': {description}")
                return True

        return False

    def filter_transactions(self, transactions: List[Transaction]) -> List[Transaction]:
        """
        Filter out transactions matching ignore patterns.

        Args:
            transactions: List of transactions to filter

        Returns:
            List of transactions that don't match ignore patterns
        """
        original_count = len(transactions)
        filtered = [t for t in transactions if not self.should_ignore(t.description)]
        ignored_count = original_count - len(filtered)

        if ignored_count > 0:
            logger.info(f"Filtered out {ignored_count} transactions ({ignored_count/original_count*100:.1f}%)")
        else:
            logger.info("No transactions matched ignore patterns")

        return filtered
