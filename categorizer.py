"""Transaction categorization based on merchant matching."""

import logging
from typing import List
from .models import Transaction, Category

logger = logging.getLogger(__name__)


class TransactionCategorizer:
    """Categorizes transactions based on merchant name matching."""

    def __init__(self, categories: List[Category], default_category: str = "Uncategorized"):
        """
        Initialize categorizer with category definitions.

        Args:
            categories: List of Category objects with merchant patterns
            default_category: Category to assign if no match found
        """
        self.categories = categories
        self.default_category = default_category
        logger.info(f"Categorizer initialized with {len(categories)} categories")

    def categorize_transaction(self, description: str) -> str:
        """
        Categorize a single transaction description.

        Uses partial, case-insensitive matching. Returns the first matching category.

        Args:
            description: Transaction description to categorize

        Returns:
            Category name or default category if no match
        """
        if not description:
            return self.default_category

        desc_lower = description.lower()

        # Check each category for a match
        for category in self.categories:
            for merchant in category.merchants:
                if merchant.lower() in desc_lower:
                    logger.debug(
                        f"Matched '{description}' to category '{category.name}' "
                        f"via merchant '{merchant}'"
                    )
                    return category.name

        logger.debug(f"No match found for '{description}', assigning '{self.default_category}'")
        return self.default_category

    def categorize_batch(self, transactions: List[Transaction]) -> List[Transaction]:
        """
        Categorize multiple transactions efficiently.

        Args:
            transactions: List of transactions to categorize

        Returns:
            Same transactions with category field updated
        """
        if not transactions:
            logger.warning("No transactions to categorize")
            return transactions

        logger.info(f"Categorizing {len(transactions)} transactions")

        categorized_count = 0
        category_distribution = {}

        for transaction in transactions:
            category = self.categorize_transaction(transaction.description)
            transaction.category = category

            # Track distribution
            category_distribution[category] = category_distribution.get(category, 0) + 1

            if category != self.default_category:
                categorized_count += 1

        # Log summary
        categorized_pct = (categorized_count / len(transactions) * 100) if transactions else 0
        logger.info(
            f"Categorized: {categorized_count}/{len(transactions)} "
            f"({categorized_pct:.1f}%)"
        )

        # Log category distribution
        logger.debug("Category distribution:")
        for cat, count in sorted(category_distribution.items(), key=lambda x: x[1], reverse=True):
            logger.debug(f"  {cat}: {count}")

        return transactions

    def get_matching_category(self, description: str) -> tuple:
        """
        Get matching category and the specific merchant that matched.

        Args:
            description: Transaction description

        Returns:
            Tuple of (category_name, matched_merchant) or (default_category, None)
        """
        if not description:
            return (self.default_category, None)

        desc_lower = description.lower()

        for category in self.categories:
            for merchant in category.merchants:
                if merchant.lower() in desc_lower:
                    return (category.name, merchant)

        return (self.default_category, None)
