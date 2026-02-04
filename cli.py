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

logger = logging.getLogger(__name__)


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

        # Categorize transactions
        logger.info("Categorizing transactions...")
        categorizer = TransactionCategorizer(categories, config.default_category)
        categorized_transactions = categorizer.categorize_batch(transactions)

        # Insert into database
        logger.info("Storing transactions in database...")
        db.insert_transactions(categorized_transactions)

        # Display dashboard
        logger.info("Generating dashboard...")
        analytics = Analytics(db)
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

  # With export
  python -m data_cleansing_agent.cli categorize --input ./input --categories ./input/category_list.csv --export summary.csv

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
    categorize_parser.set_defaults(func=cmd_categorize)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
