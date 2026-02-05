"""Category loading from column-based CSV format."""

import pandas as pd
import logging
from typing import List, Dict
from .models import Category

logger = logging.getLogger(__name__)


class CategoryLoader:
    """Loads category definitions from CSV file."""

    def __init__(self, filepath: str):
        """
        Initialize category loader.

        Args:
            filepath: Path to category_list.csv file
        """
        self.filepath = filepath
        logger.debug(f"Category loader initialized with file: {filepath}")

    def load_categories(self) -> List[Category]:
        """
        Load categories from CSV where each column represents a category.

        Format:
        - Column headers are category names
        - Rows below contain merchant names
        - Empty cells indicate end of merchant list for that category
        - 'ignore' column is excluded from categories

        Returns:
            List of Category objects
        """
        logger.info(f"Loading categories from: {self.filepath}")

        try:
            df = pd.read_csv(self.filepath)
        except Exception as e:
            logger.error(f"Error reading category file: {e}")
            raise ValueError(f"Could not read category file {self.filepath}: {e}")

        categories = []

        for column_name in df.columns:
            # Skip the 'ignore' column
            if column_name.lower() == 'ignore':
                logger.debug(f"Skipping 'ignore' column")
                continue

            # Get all non-null values in this column
            merchants = df[column_name].dropna().tolist()

            # Remove empty strings and whitespace
            merchants = [str(m).strip() for m in merchants if str(m).strip() and str(m).strip().lower() != 'nan']

            if merchants:
                category = Category(name=column_name, merchants=merchants)
                categories.append(category)
                logger.info(f"Loaded category '{column_name}' with {len(merchants)} merchants")
                logger.debug(f"  Merchants: {merchants}")

        if not categories:
            raise ValueError("No categories found in file")

        logger.info(f"Total categories loaded: {len(categories)}")
        return categories

    def load_ignore_patterns(self) -> List[str]:
        """
        Load ignore patterns from the 'ignore' column in category CSV.

        Transactions matching any ignore pattern will be excluded from processing.

        Returns:
            List of ignore patterns (strings to match in transaction descriptions)
        """
        logger.info(f"Loading ignore patterns from: {self.filepath}")

        try:
            df = pd.read_csv(self.filepath)
        except Exception as e:
            logger.error(f"Error reading category file: {e}")
            raise ValueError(f"Could not read category file {self.filepath}: {e}")

        ignore_patterns = []

        # Check if 'ignore' column exists
        ignore_col = None
        for col in df.columns:
            if col.lower() == 'ignore':
                ignore_col = col
                break

        if ignore_col:
            # Get all non-null values from ignore column
            patterns = df[ignore_col].dropna().tolist()

            # Remove empty strings and whitespace
            ignore_patterns = [str(p).strip() for p in patterns if str(p).strip() and str(p).strip().lower() != 'nan']

            logger.info(f"Loaded {len(ignore_patterns)} ignore patterns")
            logger.debug(f"  Ignore patterns: {ignore_patterns}")
        else:
            logger.info("No 'ignore' column found - no patterns to ignore")

        return ignore_patterns

    def validate_categories(self, categories: List[Category]) -> bool:
        """
        Validate categories for duplicate merchant names across categories.

        Args:
            categories: List of Category objects to validate

        Returns:
            True if validation passes (logs warnings for duplicates)
        """
        merchant_map = {}

        for category in categories:
            for merchant in category.merchants:
                merchant_lower = merchant.lower()
                if merchant_lower in merchant_map:
                    logger.warning(
                        f"Duplicate merchant '{merchant}' found in categories "
                        f"'{merchant_map[merchant_lower]}' and '{category.name}'"
                    )
                else:
                    merchant_map[merchant_lower] = category.name

        logger.debug(f"Validated {len(merchant_map)} unique merchants across {len(categories)} categories")
        return True

    def get_merchant_to_category_map(self, categories: List[Category]) -> Dict[str, str]:
        """
        Create a mapping of merchant (lowercase) to category name for quick lookup.

        Args:
            categories: List of Category objects

        Returns:
            Dictionary mapping merchant name (lowercase) to category name
        """
        merchant_map = {}

        for category in categories:
            for merchant in category.merchants:
                merchant_map[merchant.lower()] = category.name

        return merchant_map

    def get_category_summary(self, categories: List[Category]) -> str:
        """
        Get a formatted summary of loaded categories.

        Args:
            categories: List of Category objects

        Returns:
            Formatted string with category summary
        """
        lines = ["Category Summary:", "=" * 50]

        for category in categories:
            lines.append(f"{category.name}: {len(category.merchants)} merchants")

        total_merchants = sum(len(cat.merchants) for cat in categories)
        lines.append("=" * 50)
        lines.append(f"Total: {len(categories)} categories, {total_merchants} merchants")

        return "\n".join(lines)
