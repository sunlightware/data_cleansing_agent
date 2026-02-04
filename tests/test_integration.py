"""Integration tests for complete transaction categorization pipeline."""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_cleansing_agent.csv_loader import CSVLoader
from data_cleansing_agent.category_loader import CategoryLoader
from data_cleansing_agent.database import Database
from data_cleansing_agent.categorizer import TransactionCategorizer
from data_cleansing_agent.analytics import Analytics
from data_cleansing_agent.config import Config


class TestIntegration:
    """Integration tests for complete pipeline."""

    def test_end_to_end_pipeline(self):
        """Test complete pipeline from CSV to dashboard."""
        # Setup paths
        fixtures_dir = Path(__file__).parent / "fixtures"
        transactions_csv = fixtures_dir / "sample_transactions.csv"
        categories_csv = fixtures_dir / "category_list.csv"

        # Create config
        config = Config()

        # Step 1: Load transactions
        csv_loader = CSVLoader(config.transaction_columns)
        df = csv_loader.load_file(str(transactions_csv))
        assert len(df) == 20, "Should load 20 transactions"

        csv_loader.validate_data(df)
        transactions = csv_loader.to_transactions(df)
        assert len(transactions) == 20

        # Step 2: Load categories
        category_loader = CategoryLoader(str(categories_csv))
        categories = category_loader.load_categories()
        assert len(categories) == 8, "Should load 8 categories"

        # Verify category names
        category_names = [c.name for c in categories]
        assert "Groceries" in category_names
        assert "Restaurants" in category_names
        assert "Gas" in category_names

        # Step 3: Categorize transactions
        categorizer = TransactionCategorizer(categories, "Uncategorized")
        categorized_transactions = categorizer.categorize_batch(transactions)

        # Verify categorization
        categorized = [t for t in categorized_transactions if t.category != "Uncategorized"]
        assert len(categorized) > 0, "Some transactions should be categorized"

        # Check specific categorizations
        harris_teeter = [t for t in categorized_transactions if "HARRIS TEETER" in t.description][0]
        assert harris_teeter.category == "Groceries"

        starbucks = [t for t in categorized_transactions if "STARBUCKS" in t.description][0]
        assert starbucks.category == "Restaurants"

        shell = [t for t in categorized_transactions if "SHELL" in t.description][0]
        assert shell.category == "Gas"

        # Step 4: Store in database
        db = Database(":memory:")
        count = db.insert_transactions(categorized_transactions)
        assert count == 20

        # Step 5: Analytics
        analytics = Analytics(db)
        summaries = analytics.group_by_category()

        assert len(summaries) > 0, "Should have category summaries"

        # Verify totals
        stats = analytics.get_total_stats()
        assert stats['total_count'] == 20
        assert stats['total_amount'] > 0

        # Verify we have categorized and uncategorized
        categories_found = [s.category for s in summaries]
        assert any(cat != "Uncategorized" for cat in categories_found)

        # Cleanup
        db.close()

    def test_partial_matching(self):
        """Test that partial matching works correctly."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        categories_csv = fixtures_dir / "category_list.csv"

        # Load categories
        category_loader = CategoryLoader(str(categories_csv))
        categories = category_loader.load_categories()

        # Create categorizer
        categorizer = TransactionCategorizer(categories)

        # Test partial matching (description contains merchant pattern)
        assert categorizer.categorize_transaction("HARRIS TEETER #1234 CHARLOTTE") == "Groceries"
        assert categorizer.categorize_transaction("Purchase at STARBUCKS COFFEE SHOP") == "Restaurants"
        assert categorizer.categorize_transaction("SHELL GAS STATION #5678") == "Gas"

        # Test case-insensitive matching
        assert categorizer.categorize_transaction("harris teeter store") == "Groceries"
        assert categorizer.categorize_transaction("COSTCO wholesale") == "Groceries"

        # Test uncategorized
        assert categorizer.categorize_transaction("UNKNOWN MERCHANT 123") == "Uncategorized"

    def test_empty_data(self):
        """Test handling of empty datasets."""
        db = Database(":memory:")
        analytics = Analytics(db)

        summaries = analytics.group_by_category()
        assert summaries == []

        stats = analytics.get_total_stats()
        assert stats['total_count'] == 0
        assert stats['total_amount'] == 0.0

        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
