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
from data_cleansing_agent.analytics import Analytics, TransactionDetail
from data_cleansing_agent.config import Config
from data_cleansing_agent.transaction_filter import TransactionFilter
from data_cleansing_agent.models import Transaction
from data_cleansing_agent.dashboard import Dashboard


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
        assert len(categories) == 10, "Should load 10 categories"

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

    def test_ignore_patterns(self):
        """Test that ignore patterns filter out transactions correctly."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        categories_csv = fixtures_dir / "category_list.csv"

        # Load ignore patterns
        category_loader = CategoryLoader(str(categories_csv))
        ignore_patterns = category_loader.load_ignore_patterns()

        # Should have ignore patterns from the CSV
        assert len(ignore_patterns) > 0, "Should load ignore patterns"
        assert "ONLINE PAYMENT" in ignore_patterns
        assert "ONLINE ACH PAYMENT" in ignore_patterns

        # Create test transactions
        transactions = [
            Transaction("2024-01-01", 100.0, "001", "ABC", "GROCERY STORE", "Uncategorized"),
            Transaction("2024-01-02", 200.0, "002", "DEF", "ONLINE PAYMENT TO BANK", "Uncategorized"),
            Transaction("2024-01-03", 150.0, "003", "GHI", "ONLINE ACH PAYMENT FROM SAVINGS", "Uncategorized"),
            Transaction("2024-01-04", 50.0, "004", "JKL", "COFFEE SHOP", "Uncategorized"),
            Transaction("2024-01-05", 75.0, "005", "MNO", "RETAIL PURCHASE", "Uncategorized"),
        ]

        # Filter transactions
        transaction_filter = TransactionFilter(ignore_patterns)
        filtered = transaction_filter.filter_transactions(transactions)

        # Should filter out transactions with ONLINE PAYMENT and ONLINE ACH PAYMENT
        assert len(filtered) == 3, "Should filter out 2 transactions"

        # Check that only non-ignored transactions remain
        descriptions = [t.description for t in filtered]
        assert "GROCERY STORE" in descriptions
        assert "COFFEE SHOP" in descriptions
        assert "RETAIL PURCHASE" in descriptions
        assert "ONLINE PAYMENT TO BANK" not in descriptions
        assert "ONLINE ACH PAYMENT FROM SAVINGS" not in descriptions

    def test_ignore_patterns_case_insensitive(self):
        """Test that ignore pattern matching is case-insensitive."""
        ignore_patterns = ["PAYMENT", "TRANSFER"]
        transaction_filter = TransactionFilter(ignore_patterns)

        # Test various cases
        assert transaction_filter.should_ignore("payment to bank") == True
        assert transaction_filter.should_ignore("PAYMENT TO BANK") == True
        assert transaction_filter.should_ignore("Payment to Bank") == True
        assert transaction_filter.should_ignore("transfer from savings") == True
        assert transaction_filter.should_ignore("grocery store") == False

    def test_category_drilldown(self):
        """Test getting detailed transactions for a specific category."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        transactions_csv = fixtures_dir / "sample_transactions.csv"
        categories_csv = fixtures_dir / "category_list.csv"

        # Create config
        config = Config()

        # Load and categorize transactions
        csv_loader = CSVLoader(config.transaction_columns)
        df = csv_loader.load_file(str(transactions_csv))
        transactions = csv_loader.to_transactions(df)

        category_loader = CategoryLoader(str(categories_csv))
        categories = category_loader.load_categories()

        categorizer = TransactionCategorizer(categories, "Uncategorized")
        categorized_transactions = categorizer.categorize_batch(transactions)

        # Store in database
        db = Database(":memory:")
        db.insert_transactions(categorized_transactions)

        # Test drill-down for Groceries category
        analytics = Analytics(db)
        groceries_transactions = analytics.get_transactions_by_category("Groceries")

        # Should have grocery transactions
        assert len(groceries_transactions) > 0, "Should have grocery transactions"

        # Check that all are TransactionDetail objects
        for txn in groceries_transactions:
            assert isinstance(txn, TransactionDetail)
            assert hasattr(txn, 'date')
            assert hasattr(txn, 'description')
            assert hasattr(txn, 'amount')

        # Check specific grocery merchants
        descriptions = [t.description for t in groceries_transactions]
        grocery_merchants = ["HARRIS TEETER", "COSTCO", "WHOLE FOODS", "PUBLIX"]
        matched = any(merchant in desc for desc in descriptions for merchant in grocery_merchants)
        assert matched, "Should have transactions from known grocery merchants"

        db.close()

    def test_get_all_categories(self):
        """Test getting list of all categories."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        transactions_csv = fixtures_dir / "sample_transactions.csv"
        categories_csv = fixtures_dir / "category_list.csv"

        config = Config()

        csv_loader = CSVLoader(config.transaction_columns)
        df = csv_loader.load_file(str(transactions_csv))
        transactions = csv_loader.to_transactions(df)

        category_loader = CategoryLoader(str(categories_csv))
        categories = category_loader.load_categories()

        categorizer = TransactionCategorizer(categories, "Uncategorized")
        categorized_transactions = categorizer.categorize_batch(transactions)

        db = Database(":memory:")
        db.insert_transactions(categorized_transactions)

        analytics = Analytics(db)
        all_categories = analytics.get_all_categories()

        # Should have multiple categories
        assert len(all_categories) > 0
        assert isinstance(all_categories, list)

        # Should be sorted
        assert all_categories == sorted(all_categories)

        db.close()

    def test_drilldown_empty_category(self):
        """Test drill-down for a category with no transactions."""
        db = Database(":memory:")
        analytics = Analytics(db)

        # Try to get transactions for non-existent category
        transactions = analytics.get_transactions_by_category("NonExistent")

        assert transactions == [], "Should return empty list for non-existent category"

        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
