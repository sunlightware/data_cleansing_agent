"""Command-line interface for data cleansing agent."""

import argparse
import logging
import sys
from pathlib import Path

from .config import load_config, setup_logging
from .csv_loader import CSVLoader
from .category_loader import CategoryLoader
from .database import Database
from .categorizer import TransactionCategorizer
from .analytics import Analytics
from .dashboard import Dashboard
from .transaction_filter import TransactionFilter
from .budget_loader import BudgetLoader

logger = logging.getLogger(__name__)


def cmd_drilldown(args: argparse.Namespace) -> int:
    """
    Display detailed transactions for a specific category.

    Pipeline:
    1. Initialize database
    2. Load CSV transactions
    3. Load categories
    4. Categorize transactions
    5. Insert into database
    6. Display drill-down report for specified category

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    config = load_config()
    setup_logging(args.log_level or config.log_level)

    logger.info(f"Starting category drill-down for: {args.category}")

    try:
        # Initialize database
        logger.info("Initializing database...")
        db = Database(config.db_uri)

        # Load CSV transactions
        logger.info(f"Loading transactions from: {args.input}")
        csv_loader = CSVLoader(config.transaction_columns)
        df = csv_loader.load_directory(args.input)
        csv_loader.validate_data(df)
        transactions = csv_loader.to_transactions(df)
        logger.info(f"Loaded {len(transactions)} transactions")

        # Load categories
        logger.info(f"Loading categories from: {args.categories}")
        category_loader = CategoryLoader(args.categories)
        categories = category_loader.load_categories()
        category_loader.validate_categories(categories)

        # Load ignore patterns and filter transactions
        ignore_patterns = category_loader.load_ignore_patterns()
        if ignore_patterns:
            logger.info(f"Filtering transactions using {len(ignore_patterns)} ignore patterns...")
            transaction_filter = TransactionFilter(ignore_patterns)
            transactions = transaction_filter.filter_transactions(transactions)
            logger.info(f"Remaining transactions after filtering: {len(transactions)}")

        # Categorize transactions
        logger.info("Categorizing transactions...")
        categorizer = TransactionCategorizer(categories, config.default_category)
        categorized_transactions = categorizer.categorize_batch(transactions)

        # Insert into database
        logger.info("Storing transactions in database...")
        db.insert_transactions(categorized_transactions)

        # Load budgets if provided
        budgets = {}
        if hasattr(args, 'budget') and args.budget:
            logger.info(f"Loading budgets from: {args.budget}")
            budget_loader = BudgetLoader(args.budget)
            budgets = budget_loader.load_budgets()
            budget_loader.validate_budgets(budgets)

        # Display drill-down report
        logger.info(f"Generating drill-down report for category: {args.category}")
        analytics = Analytics(db, budgets)
        dashboard = Dashboard(analytics)
        print()  # Blank line before dashboard
        dashboard.display_category_drilldown(args.category)

        db.close()
        logger.info("Drill-down complete")
        return 0

    except Exception as e:
        logger.error(f"Error during drill-down: {e}", exc_info=True)
        print(f"\nError: {e}", file=sys.stderr)
        return 1


def cmd_categorize(args: argparse.Namespace) -> int:
    """
    Main categorization command.

    Pipeline:
    1. Initialize database
    2. Load CSV transactions
    3. Load categories
    4. Categorize transactions
    5. Insert into database
    6. Display dashboard

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    config = load_config()
    setup_logging(args.log_level or config.log_level)

    logger.info("Starting transaction categorization")

    try:
        # Initialize database
        logger.info("Initializing database...")
        db = Database(config.db_uri)

        # Load CSV transactions
        logger.info(f"Loading transactions from: {args.input}")
        csv_loader = CSVLoader(config.transaction_columns)
        df = csv_loader.load_directory(args.input)
        csv_loader.validate_data(df)
        transactions = csv_loader.to_transactions(df)
        logger.info(f"Loaded {len(transactions)} transactions")

        # Load categories
        logger.info(f"Loading categories from: {args.categories}")
        category_loader = CategoryLoader(args.categories)
        categories = category_loader.load_categories()
        category_loader.validate_categories(categories)

        # Load ignore patterns and filter transactions
        ignore_patterns = category_loader.load_ignore_patterns()
        if ignore_patterns:
            logger.info(f"Filtering transactions using {len(ignore_patterns)} ignore patterns...")
            transaction_filter = TransactionFilter(ignore_patterns)
            transactions = transaction_filter.filter_transactions(transactions)
            logger.info(f"Remaining transactions after filtering: {len(transactions)}")

        # Categorize transactions
        logger.info("Categorizing transactions...")
        categorizer = TransactionCategorizer(categories, config.default_category)
        categorized_transactions = categorizer.categorize_batch(transactions)

        # Insert into database
        logger.info("Storing transactions in database...")
        db.insert_transactions(categorized_transactions)

        # Load budgets if provided
        budgets = {}
        if hasattr(args, 'budget') and args.budget:
            logger.info(f"Loading budgets from: {args.budget}")
            budget_loader = BudgetLoader(args.budget)
            budgets = budget_loader.load_budgets()
            budget_loader.validate_budgets(budgets)

        # Display dashboard
        logger.info("Generating dashboard...")
        analytics = Analytics(db, budgets)
        dashboard = Dashboard(analytics)
        print()  # Blank line before dashboard
        dashboard.display()

        # Optional: Export to CSV
        if args.export:
            logger.info(f"Exporting summary to: {args.export}")
            summary_df = analytics.get_summary_dataframe()
            summary_df.to_csv(args.export, index=False)
            print(f"\nExported summary to: {args.export}")

        db.close()
        logger.info("Categorization complete")
        return 0

    except Exception as e:
        logger.error(f"Error during categorization: {e}", exc_info=True)
        print(f"\nError: {e}", file=sys.stderr)
        return 1


def main(argv: list = None) -> int:
    """
    Main entry point for CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        prog="data_cleansing_agent",
        description="Categorize CSV transactions using merchant matching",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python -m data_cleansing_agent.cli categorize --input ./input --categories ./input/category_list.csv

  # With budget tracking
  python -m data_cleansing_agent.cli categorize --input ./input --categories ./input/category_list.csv --budget ./input/budget.csv

  # With export
  python -m data_cleansing_agent.cli categorize --input ./input --categories ./input/category_list.csv --export summary.csv

  # Drill down into a specific category
  python -m data_cleansing_agent.cli drilldown --input ./input --categories ./input/category_list.csv --category Groceries

  # With debug logging
  python -m data_cleansing_agent.cli --log-level DEBUG categorize --input ./input --categories ./input/category_list.csv
        """
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Categorize command
    categorize_parser = subparsers.add_parser(
        "categorize",
        help="Categorize transactions from CSV files"
    )
    categorize_parser.add_argument(
        "--input", "-i",
        required=True,
        help="Directory containing CSV files (without headers)"
    )
    categorize_parser.add_argument(
        "--categories", "-c",
        required=True,
        help="Path to category_list.csv file"
    )
    categorize_parser.add_argument(
        "--export", "-e",
        help="Export summary to CSV file (optional)"
    )
    categorize_parser.add_argument(
        "--budget", "-b",
        help="Path to budget.csv file (optional)"
    )
    categorize_parser.set_defaults(func=cmd_categorize)

    # Drilldown command
    drilldown_parser = subparsers.add_parser(
        "drilldown",
        help="Display detailed transactions for a specific category"
    )
    drilldown_parser.add_argument(
        "--input", "-i",
        required=True,
        help="Directory containing CSV files (without headers)"
    )
    drilldown_parser.add_argument(
        "--categories", "-c",
        required=True,
        help="Path to category_list.csv file"
    )
    drilldown_parser.add_argument(
        "--category",
        required=True,
        help="Category name to drill down into (e.g., 'Groceries', 'Gas')"
    )
    drilldown_parser.add_argument(
        "--budget", "-b",
        help="Path to budget.csv file (optional)"
    )
    drilldown_parser.set_defaults(func=cmd_drilldown)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
