"""Terminal-based dashboard for displaying transaction summaries."""

import logging
from typing import List
from .analytics import Analytics, CategorySummary, TransactionDetail

logger = logging.getLogger(__name__)


class Dashboard:
    """Terminal-based dashboard for displaying transaction summaries."""

    def __init__(self, analytics: Analytics):
        """
        Initialize dashboard with analytics.

        Args:
            analytics: Analytics instance for data access
        """
        self.analytics = analytics
        self.width = 80
        logger.debug("Dashboard initialized")

    def display(self):
        """Display complete dashboard in terminal."""
        self._display_header()
        summaries = self.analytics.group_by_category()

        if summaries:
            self._display_summary_table(summaries)
            self._display_totals(summaries)
        else:
            print("No transactions to display")

    def _display_header(self):
        """Show dashboard title and metadata."""
        print("=" * self.width)
        print("TRANSACTION CATEGORIZATION REPORT".center(self.width))
        print("=" * self.width)

        # Get statistics
        stats = self.analytics.get_total_stats()
        category_count = self.analytics.get_category_count()
        uncategorized = self.analytics.get_uncategorized_count()

        total_transactions = stats['total_count']
        uncategorized_pct = (uncategorized / total_transactions * 100) if total_transactions > 0 else 0

        print(f"Transactions: {total_transactions}  |  " +
              f"Categories: {category_count}  |  " +
              f"Uncategorized: {uncategorized} ({uncategorized_pct:.1f}%)")
        print()

    def _display_summary_table(self, summaries: List[CategorySummary]):
        """
        Display formatted table with category summaries.

        Args:
            summaries: List of CategorySummary objects
        """
        # Column widths
        cat_width = 20
        count_width = 5
        total_width = 11
        avg_width = 10
        pct_width = 10

        # Header
        print("-" * self.width)
        header = (
            f"{'Category':<{cat_width}} | "
            f"{'Count':>{count_width}} | "
            f"{'Total':>{total_width}} | "
            f"{'Average':>{avg_width}} | "
            f"{'% of Total':>{pct_width}}"
        )
        print(header)
        print("-" * self.width)

        # Data rows
        for summary in summaries:
            row = (
                f"{summary.category:<{cat_width}} | "
                f"{summary.count:>{count_width}} | "
                f"{self._format_currency(summary.total):>{total_width}} | "
                f"{self._format_currency(summary.average):>{avg_width}} | "
                f"{self._format_percentage(summary.percentage):>{pct_width}}"
            )
            print(row)

        print("-" * self.width)

    def _display_totals(self, summaries: List[CategorySummary]):
        """
        Display overall totals and statistics.

        Args:
            summaries: List of CategorySummary objects
        """
        total_count = sum(s.count for s in summaries)
        total_amount = sum(s.total for s in summaries)
        avg_amount = total_amount / total_count if total_count > 0 else 0

        # Column widths
        cat_width = 20
        count_width = 5
        total_width = 11
        avg_width = 10
        pct_width = 10

        row = (
            f"{'TOTAL':<{cat_width}} | "
            f"{total_count:>{count_width}} | "
            f"{self._format_currency(total_amount):>{total_width}} | "
            f"{self._format_currency(avg_amount):>{avg_width}} | "
            f"{'100.0%':>{pct_width}}"
        )
        print(row)
        print("=" * self.width)

    def _format_currency(self, amount: float) -> str:
        """
        Format number as currency string.

        Args:
            amount: Amount to format

        Returns:
            Formatted currency string (e.g., "$1,234.56")
        """
        return f"${amount:,.2f}"

    def _format_percentage(self, value: float) -> str:
        """
        Format decimal as percentage string.

        Args:
            value: Percentage value to format

        Returns:
            Formatted percentage string (e.g., "25.3%")
        """
        return f"{value:.1f}%"

    def display_simple(self):
        """Display simplified summary without table formatting."""
        summaries = self.analytics.group_by_category()

        print("\nCategory Summary:")
        print("-" * 40)

        for summary in summaries:
            print(f"{summary.category}: {summary.count} transactions, "
                  f"Total: {self._format_currency(summary.total)}")

        stats = self.analytics.get_total_stats()
        print("-" * 40)
        print(f"TOTAL: {stats['total_count']} transactions, "
              f"Total: {self._format_currency(stats['total_amount'])}")

    def display_category_drilldown(self, category: str):
        """
        Display detailed transaction list for a specific category.

        Args:
            category: Category name to drill down into
        """
        logger.info(f"Displaying drill-down for category: {category}")

        # Get transactions for this category
        transactions = self.analytics.get_transactions_by_category(category)

        if not transactions:
            print(f"\nNo transactions found for category: {category}")
            return

        # Get category summary
        summaries = self.analytics.group_by_category()
        category_summary = next((s for s in summaries if s.category == category), None)

        # Display header
        print("=" * self.width)
        print(f"CATEGORY DRILL-DOWN: {category}".center(self.width))
        print("=" * self.width)

        if category_summary:
            print(f"Count: {category_summary.count}  |  " +
                  f"Total: {self._format_currency(category_summary.total)}  |  " +
                  f"Average: {self._format_currency(category_summary.average)}")
            print()

        # Display transaction table
        self._display_transaction_table(transactions)

    def _display_transaction_table(self, transactions: List[TransactionDetail]):
        """
        Display formatted table of transaction details.

        Args:
            transactions: List of TransactionDetail objects
        """
        # Column widths
        date_width = 10
        desc_width = 40
        amount_width = 12

        # Header
        print("-" * self.width)
        header = (
            f"{'Date':<{date_width}} | "
            f"{'Description':<{desc_width}} | "
            f"{'Amount':>{amount_width}}"
        )
        print(header)
        print("-" * self.width)

        # Data rows
        total = 0.0
        for txn in transactions:
            # Truncate description if too long
            desc = txn.description
            if len(desc) > desc_width:
                desc = desc[:desc_width-3] + "..."

            row = (
                f"{txn.date:<{date_width}} | "
                f"{desc:<{desc_width}} | "
                f"{self._format_currency(txn.amount):>{amount_width}}"
            )
            print(row)
            total += txn.amount

        # Display total
        print("-" * self.width)
        total_row = (
            f"{'TOTAL':<{date_width}} | "
            f"{'':<{desc_width}} | "
            f"{self._format_currency(total):>{amount_width}}"
        )
        print(total_row)
        print("=" * self.width)
