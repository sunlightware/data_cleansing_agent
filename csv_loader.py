"""CSV file loading with header management."""

import pandas as pd
import logging
from pathlib import Path
from typing import List
from .models import Transaction

logger = logging.getLogger(__name__)


class CSVLoader:
    """Loads CSV transaction files and adds headers."""

    def __init__(self, columns: list):
        """
        Initialize CSV loader with column names.

        Args:
            columns: List of column names to add as headers
        """
        self.columns = columns
        logger.debug(f"CSV loader initialized with columns: {columns}")

    def load_file(self, filepath: str) -> pd.DataFrame:
        """
        Load a single CSV file without headers and add column names.

        Args:
            filepath: Path to CSV file without headers

        Returns:
            DataFrame with added headers
        """
        logger.info(f"Loading CSV file: {filepath}")

        try:
            df = pd.read_csv(filepath, header=None, names=self.columns)
            logger.info(f"Loaded {len(df)} transactions from {filepath}")
            return df
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            raise

    def load_directory(self, directory: str, pattern: str = "*.csv") -> pd.DataFrame:
        """
        Load all CSV files from a directory.

        Args:
            directory: Path to directory containing CSV files
            pattern: File pattern to match (default: *.csv)

        Returns:
            Combined DataFrame from all CSV files
        """
        path = Path(directory)

        if not path.exists():
            raise ValueError(f"Directory not found: {directory}")

        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        csv_files = list(path.glob(pattern))

        # Exclude category_list.csv from transaction files
        csv_files = [f for f in csv_files if 'category' not in f.name.lower()]

        if not csv_files:
            raise ValueError(f"No CSV files found in {directory}")

        logger.info(f"Found {len(csv_files)} CSV files in {directory}")

        dfs = []
        for csv_file in csv_files:
            try:
                df = self.load_file(str(csv_file))
                dfs.append(df)
            except Exception as e:
                logger.warning(f"Skipping {csv_file}: {e}")

        if not dfs:
            raise ValueError("No valid CSV files could be loaded")

        combined = pd.concat(dfs, ignore_index=True)
        logger.info(f"Combined total: {len(combined)} transactions")

        return combined

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate that required columns exist and have valid data.

        Args:
            df: DataFrame to validate

        Returns:
            True if validation passes

        Raises:
            ValueError: If validation fails
        """
        # Check required columns
        required = ['date', 'amount', 'description']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Validate amount is numeric
        try:
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            if df['amount'].isna().any():
                logger.warning("Some amount values could not be converted to numbers")
        except Exception as e:
            raise ValueError(f"Amount column must be numeric: {e}")

        # Check for empty descriptions
        if df['description'].isna().all():
            raise ValueError("Description column cannot be empty")

        logger.debug("Data validation passed")
        return True

    def to_transactions(self, df: pd.DataFrame) -> List[Transaction]:
        """
        Convert DataFrame to list of Transaction objects.

        Args:
            df: DataFrame with transaction data

        Returns:
            List of Transaction objects
        """
        transactions = []

        for _, row in df.iterrows():
            t = Transaction(
                date=str(row['date']) if pd.notna(row['date']) else '',
                amount=float(row['amount']) if pd.notna(row['amount']) else 0.0,
                nr_1=str(row.get('nr_1', '')) if pd.notna(row.get('nr_1')) else '',
                nr_2=str(row.get('nr_2', '')) if pd.notna(row.get('nr_2')) else '',
                description=str(row['description']) if pd.notna(row['description']) else ''
            )
            transactions.append(t)

        logger.debug(f"Converted {len(transactions)} rows to Transaction objects")
        return transactions
