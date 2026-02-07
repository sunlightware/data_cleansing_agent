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
        Load a single CSV file with headers and extract required columns.

        Args:
            filepath: Path to CSV file with headers

        Returns:
            DataFrame with date, amount, and description columns
        """
        logger.info(f"Loading CSV file: {filepath}")

        try:
            # Read CSV with headers
            df = pd.read_csv(filepath)
            logger.debug(f"CSV columns found: {list(df.columns)}")

            # Find required columns (case-insensitive)
            column_mapping = {}
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if 'date' in col_lower:
                    column_mapping['date'] = col
                elif 'amount' in col_lower:
                    column_mapping['amount'] = col
                elif 'description' in col_lower or 'desc' in col_lower:
                    column_mapping['description'] = col

            # Verify required columns exist
            required = ['date', 'amount', 'description']
            missing = [col for col in required if col not in column_mapping]
            if missing:
                raise ValueError(f"Missing required columns in {filepath}: {missing}. Found columns: {list(df.columns)}")

            # Extract and rename required columns
            df_extracted = pd.DataFrame()
            df_extracted['date'] = df[column_mapping['date']]
            df_extracted['amount'] = df[column_mapping['amount']]
            df_extracted['description'] = df[column_mapping['description']]

            logger.info(f"Loaded {len(df_extracted)} transactions from {filepath}")
            logger.debug(f"Extracted columns: date='{column_mapping['date']}', amount='{column_mapping['amount']}', description='{column_mapping['description']}'")
            return df_extracted
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            raise

    def load_directory(self, directory: str, pattern: str = "*.csv") -> pd.DataFrame:
        """
        Load all CSV files from the transactions subdirectory.

        Args:
            directory: Path to base input directory (will look in transactions/ subfolder)
            pattern: File pattern to match (default: *.csv)

        Returns:
            Combined DataFrame from all CSV files in transactions folder
        """
        base_path = Path(directory)

        if not base_path.exists():
            raise ValueError(f"Directory not found: {directory}")

        if not base_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        # Look specifically in the transactions subdirectory
        transactions_path = base_path / "transactions"

        if not transactions_path.exists():
            # Fallback: if no transactions folder, use the directory as-is
            logger.warning(f"No 'transactions' subfolder found in {directory}, using directory directly")
            transactions_path = base_path

        csv_files = list(transactions_path.glob(pattern))

        # Exclude category and budget files from transaction files
        csv_files = [f for f in csv_files if 'category' not in f.name.lower() and 'budget' not in f.name.lower()]

        if not csv_files:
            raise ValueError(f"No CSV files found in {transactions_path}")

        logger.info(f"Found {len(csv_files)} CSV files in {transactions_path}")

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

        # Validate amount is numeric (keep original signs)
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
                description=str(row['description']) if pd.notna(row['description']) else ''
            )
            transactions.append(t)

        logger.debug(f"Converted {len(transactions)} rows to Transaction objects")
        return transactions
