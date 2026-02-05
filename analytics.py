"""Analytics and aggregation for transaction data."""

import pandas as pd
import logging
from dataclasses import dataclass
from typing import List
from .database import Database
from .models import Transaction

logger = logging.getLogger(__name__)


@dataclass
class CategorySummary:
    """Summary statistics for a category."""

    category: str
    count: int
    total: float
    average: float
    percentage: float

    def __repr__(self):
        return (
            f"CategorySummary(category='{self.category}', count={self.count}, "
            f"total=${self.total:.2f}, avg=${self.average:.2f}, pct={self.percentage:.1f}%)"
        )


@dataclass
class TransactionDetail:
    """Detailed transaction information for drill-down reports."""

    date: str
    description: str
    amount: float
    nr_1: str
    nr_2: str

    def __repr__(self):
        return f"TransactionDetail(date='{self.date}', desc='{self.description}', amount=${self.amount:.2f})"


class Analytics:
    """Analyzes transaction data and generates summaries."""

    def __init__(self, database: Database):
        """
        Initialize analytics with database.

        Args:
            database: Database instance containing transactions
        """
        self.db = database
        logger.debug("Analytics initialized")

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

        # Calculate percentages
        grand_total = grouped['total'].sum()
        if grand_total != 0:
            grouped['percentage'] = (grouped['total'] / grand_total * 100)
        else:
            grouped['percentage'] = 0

        # Sort by total descending
        grouped = grouped.sort_values('total', ascending=False)

        # Convert to CategorySummary objects
        summaries = []
        for _, row in grouped.iterrows():
            summary = CategorySummary(
                category=str(row['category']),
                count=int(row['count']),
                total=float(row['total']),
                average=float(row['average']),
                percentage=float(row['percentage'])
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
                amount=t.amount,
                nr_1=t.nr_1,
                nr_2=t.nr_2
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
