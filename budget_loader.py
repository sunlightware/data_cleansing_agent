"""Budget loading from CSV format."""

import pandas as pd
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class BudgetLoader:
    """Loads budget definitions from CSV file."""

    def __init__(self, filepath: Optional[str] = None):
        """
        Initialize budget loader.

        Args:
            filepath: Path to budget.csv file (optional)
        """
        self.filepath = filepath
        if filepath:
            logger.debug(f"Budget loader initialized with file: {filepath}")
        else:
            logger.debug("Budget loader initialized with no file (budgets disabled)")

    def load_budgets(self) -> Dict[str, float]:
        """
        Load budgets from CSV file.

        Format:
        - Two columns: Category, Budget
        - Each row defines budget for a category

        Returns:
            Dictionary mapping category name to budget amount
        """
        if not self.filepath:
            logger.info("No budget file specified - budgets disabled")
            return {}

        logger.info(f"Loading budgets from: {self.filepath}")

        try:
            df = pd.read_csv(self.filepath)
        except Exception as e:
            logger.error(f"Error reading budget file: {e}")
            raise ValueError(f"Could not read budget file {self.filepath}: {e}")

        # Validate required columns
        required_columns = ['Category', 'Budget']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Budget file missing required columns: {missing_columns}")

        budgets = {}

        for _, row in df.iterrows():
            category = str(row['Category']).strip()

            try:
                budget = float(row['Budget'])
            except (ValueError, TypeError):
                logger.warning(f"Invalid budget value for category '{category}': {row['Budget']}")
                continue

            if category and budget >= 0:
                budgets[category] = budget
                logger.debug(f"Loaded budget for '{category}': ${budget:.2f}")

        logger.info(f"Total budgets loaded: {len(budgets)} categories")
        return budgets

    def get_budget_for_category(self, budgets: Dict[str, float], category: str) -> Optional[float]:
        """
        Get budget amount for a specific category.

        Args:
            budgets: Dictionary of budgets
            category: Category name

        Returns:
            Budget amount or None if not found
        """
        return budgets.get(category)

    def validate_budgets(self, budgets: Dict[str, float]) -> bool:
        """
        Validate budget data.

        Args:
            budgets: Dictionary of budgets to validate

        Returns:
            True if validation passes
        """
        if not budgets:
            logger.warning("No budgets defined")
            return True

        # Check for negative budgets
        negative_budgets = {k: v for k, v in budgets.items() if v < 0}
        if negative_budgets:
            logger.error(f"Found negative budgets: {negative_budgets}")
            return False

        logger.debug(f"Validated {len(budgets)} budgets")
        return True

    def get_total_budget(self, budgets: Dict[str, float]) -> float:
        """
        Calculate total budget across all categories.

        Args:
            budgets: Dictionary of budgets

        Returns:
            Total budget amount
        """
        return sum(budgets.values())
