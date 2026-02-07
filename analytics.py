"""Analytics and aggregation for transaction data."""

import pandas as pd
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
from .database import Database
from .models import Transaction

logger = logging.getLogger(__name__)


@dataclass
class CategorySummary:
    """Summary statistics for a category."""

    category: str
    count: int
    total: float  # Absolute value of aggregated amount
    average: float
    percentage: float
    budget: Optional[float] = None
    deviation: Optional[float] = None
    raw_total: Optional[float] = None  # Original aggregated amount (with sign)

    def __repr__(self):
        budget_str = f", budget=${self.budget:.2f}" if self.budget is not None else ""
        deviation_str = f", deviation=${self.deviation:.2f}" if self.deviation is not None else ""
        return (
            f"CategorySummary(category='{self.category}', count={self.count}, "
            f"total=${self.total:.2f}, avg=${self.average:.2f}, pct={self.percentage:.1f}%"
            f"{budget_str}{deviation_str})"
        )


@dataclass
class TransactionDetail:
    """Detailed transaction information for drill-down reports."""

    date: str
    description: str
    amount: float

    def __repr__(self):
        return f"TransactionDetail(date='{self.date}', desc='{self.description}', amount=${self.amount:.2f})"


class Analytics:
    """Analyzes transaction data and generates summaries."""

    def __init__(self, database: Database, budgets: Optional[Dict[str, float]] = None):
        """
        Initialize analytics with database.

        Args:
            database: Database instance containing transactions
            budgets: Optional dictionary mapping category names to budget amounts
        """
        self.db = database
        self.budgets = budgets or {}
        logger.debug(f"Analytics initialized with {len(self.budgets)} budgets")

    def group_by_category(self) -> List[CategorySummary]:
        """
        Group transactions by category and calculate aggregates.

        Calculates:
        - Total amount per category
        - Transaction count per category
        - Average transaction amount
        - Percentage of total spending

        Returns:
            List of CategorySummary objects sorted by total descending
        """
        transactions = self.db.get_all_transactions()

        if not transactions:
            logger.warning("No transactions found for analysis")
            return []

        # Convert to DataFrame for aggregation
        data = [
            {
                'category': t.category,
                'amount': t.amount
            }
            for t in transactions
        ]
        df = pd.DataFrame(data)

        # Calculate aggregates
        grouped = df.groupby('category').agg({
            'amount': ['count', 'sum', 'mean']
        }).reset_index()

        grouped.columns = ['category', 'count', 'total', 'average']

        # Store raw totals and convert to absolute values
        grouped['raw_total'] = grouped['total']
        grouped['total'] = grouped['total'].abs()

        # Calculate percentages based on absolute totals
        grand_total = grouped['total'].sum()

        if grand_total > 0:
            # Each category's percentage = (abs(category_total) / sum(abs(totals))) * 100
            grouped['percentage'] = (grouped['total'] / grand_total * 100)
        else:
            grouped['percentage'] = 0

        # Sort by absolute total descending
        grouped = grouped.sort_values('total', ascending=False)

        # Convert to CategorySummary objects
        summaries = []
        for _, row in grouped.iterrows():
            category_name = str(row['category'])
            total_amount = float(row['total'])  # Absolute value
            raw_total_amount = float(row['raw_total'])  # Original with sign

            # Get budget and calculate deviation if available
            budget = self.budgets.get(category_name)
            deviation = None
            if budget is not None:
                # Deviation = budget - absolute(aggregated amount)
                #   - Positive deviation = under budget (good)
                #   - Negative deviation = over budget (bad)
                deviation = budget - total_amount

            summary = CategorySummary(
                category=category_name,
                count=int(row['count']),
                total=total_amount,  # Absolute value for display
                average=float(row['average']),
                percentage=float(row['percentage']),
                budget=budget,
                deviation=deviation,
                raw_total=raw_total_amount  # Keep original for reference
            )
            summaries.append(summary)

        logger.info(f"Generated summaries for {len(summaries)} categories")
        return summaries

    def get_summary_dataframe(self) -> pd.DataFrame:
        """
        Return pandas DataFrame with category summaries.

        Returns:
            DataFrame with columns: Category, Count, Total, Average, Percentage
        """
        summaries = self.group_by_category()

        if not summaries:
            return pd.DataFrame(columns=['Category', 'Count', 'Total', 'Average', 'Percentage'])

        data = [
            {
                'Category': s.category,
                'Count': s.count,
                'Total': s.total,
                'Average': s.average,
                'Percentage': s.percentage
            }
            for s in summaries
        ]
        return pd.DataFrame(data)

    def get_top_categories(self, n: int = 5) -> List[CategorySummary]:
        """
        Get top N categories by total amount.

        Args:
            n: Number of top categories to return

        Returns:
            List of top N CategorySummary objects
        """
        summaries = self.group_by_category()
        return summaries[:n]

    def get_uncategorized_count(self) -> int:
        """
        Count of transactions that are uncategorized.

        Returns:
            Number of uncategorized transactions
        """
        transactions = self.db.get_by_category("Uncategorized")
        return len(transactions)

    def get_total_stats(self) -> dict:
        """
        Get overall statistics for all transactions.

        Returns:
            Dictionary with total count, total amount, average amount
        """
        transactions = self.db.get_all_transactions()

        if not transactions:
            return {
                'total_count': 0,
                'total_amount': 0.0,
                'average_amount': 0.0
            }

        total_amount = sum(t.amount for t in transactions)
        count = len(transactions)

        return {
            'total_count': count,
            'total_amount': total_amount,
            'average_amount': total_amount / count if count > 0 else 0.0
        }

    def get_category_count(self) -> int:
        """
        Get number of unique categories (excluding Uncategorized).

        Returns:
            Number of categories
        """
        summaries = self.group_by_category()
        return len([s for s in summaries if s.category != "Uncategorized"])

    def get_transactions_by_category(self, category: str) -> List[TransactionDetail]:
        """
        Get detailed transactions for a specific category.

        Args:
            category: Category name to filter by

        Returns:
            List of TransactionDetail objects sorted by date
        """
        logger.info(f"Retrieving transactions for category: {category}")

        transactions = self.db.get_by_category(category)

        if not transactions:
            logger.warning(f"No transactions found for category: {category}")
            return []

        # Convert to TransactionDetail objects
        details = []
        for t in transactions:
            detail = TransactionDetail(
                date=t.date,
                description=t.description,
                amount=t.amount
            )
            details.append(detail)

        # Sort by date
        details.sort(key=lambda x: x.date)

        logger.info(f"Found {len(details)} transactions for category: {category}")
        return details

    def get_all_categories(self) -> List[str]:
        """
        Get list of all unique category names.

        Returns:
            List of category names sorted alphabetically
        """
        summaries = self.group_by_category()
        categories = [s.category for s in summaries]
        return sorted(categories)
