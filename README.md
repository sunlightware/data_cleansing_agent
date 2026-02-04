# Data Cleansing Agent

A Python program that automatically categorizes CSV transactions using merchant pattern matching and displays results in a terminal dashboard.

## Features

- **Headerless CSV Loading**: Automatically adds column headers to CSV files
- **Flexible Categorization**: Column-based category definitions with merchant patterns
- **Partial Matching**: Case-insensitive substring matching for merchant names
- **In-Memory Database**: Fast SQLite storage for batch processing
- **Analytics Dashboard**: Terminal-based display with category summaries
- **Export Support**: Optional CSV export of categorized results

## Installation

```bash
# Clone or navigate to the project
cd data_cleansing_agent

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Prepare Your Data

**Transaction CSV (without headers):**
```
2024-01-01,45.50,001,ABC,HARRIS TEETER #1234
2024-01-02,120.00,002,DEF,COSTCO WHOLESALE
2024-01-03,25.75,003,GHI,STARBUCKS COFFEE
```

**Category List CSV (`category_list.csv`):**
```
Groceries,Restaurants,Gas,Shopping
HARRIS TEETER,STARBUCKS,SHELL,AMAZON
COSTCO,CHICK-FIL-A,EXXON,TARGET
WHOLE FOODS,DUNKIN,BP,WALMART
```

Each column represents a category, with merchant patterns listed below.

### 2. Run Categorization

```bash
python -m data_cleansing_agent.cli categorize \
  --input ./input \
  --categories ./input/category_list.csv
```

### 3. View Dashboard

```
================================================================================
                    TRANSACTION CATEGORIZATION REPORT
================================================================================
Transactions: 150  |  Categories: 8  |  Uncategorized: 12 (8.0%)

--------------------------------------------------------------------------------
Category              | Count | Total       | Average    | % of Total
--------------------------------------------------------------------------------
Groceries             |    45 |  $1,234.56  |    $27.43  |     25.3%
Restaurants           |    32 |    $876.54  |    $27.39  |     18.0%
Gas                   |    18 |    $654.32  |    $36.35  |     13.4%
Shopping              |    15 |    $432.10  |    $28.81  |      8.9%
Uncategorized         |    12 |    $456.78  |    $38.07  |      9.4%
--------------------------------------------------------------------------------
TOTAL                 |   150 |  $4,876.61  |    $32.51  |    100.0%
================================================================================
```

## Usage

### Basic Command

```bash
python -m data_cleansing_agent.cli categorize \
  --input <directory_with_csv_files> \
  --categories <path_to_category_list.csv>
```

### With Export

```bash
python -m data_cleansing_agent.cli categorize \
  --input ./input \
  --categories ./input/category_list.csv \
  --export ./summary.csv
```

### With Debug Logging

```bash
python -m data_cleansing_agent.cli --log-level DEBUG categorize \
  --input ./input \
  --categories ./input/category_list.csv
```

## CSV Format

### Transaction CSV

Transactions CSV files should **NOT** have headers. The system automatically adds these column names:

1. `date` - Transaction date
2. `amount` - Transaction amount (numeric)
3. `nr_1` - First reference number
4. `nr_2` - Second reference number
5. `description` - Merchant/transaction description

### Category List CSV

Format: Column-based, where each column is a category

- **Column header** = Category name
- **Rows below** = Merchant patterns to match
- **Empty cells** = End of merchant list for that category

Example:
```csv
Groceries,Restaurants,Gas
HARRIS TEETER,STARBUCKS,SHELL
COSTCO,DUNKIN,EXXON
WHOLE FOODS,CHIPOTLE,BP
,PANERA,
```

## How Categorization Works

1. **Partial Matching**: If the transaction description contains a merchant pattern, it's matched
   - Example: "HARRIS TEETER #1234" matches pattern "HARRIS TEETER"

2. **Case-Insensitive**: Matching ignores case
   - "harris teeter" matches "HARRIS TEETER"

3. **First-Match-Wins**: If multiple categories match, the first one found is used

4. **Uncategorized**: Transactions without matches are assigned "Uncategorized"

## Project Structure

```
data_cleansing_agent/
├── __init__.py
├── config.py              # Configuration & constants
├── models.py              # Data models (Transaction, Category)
├── csv_loader.py          # CSV loading with header addition
├── category_loader.py     # Parse category definitions
├── database.py            # SQLite operations
├── categorizer.py         # Merchant matching logic
├── analytics.py           # Grouping & aggregation
├── dashboard.py           # Terminal display
├── cli.py                 # Command-line interface
├── main.py                # Entry point
├── requirements.txt       # Dependencies
└── tests/
    ├── fixtures/          # Test data
    └── test_integration.py # Integration tests
```

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=data_cleansing_agent tests/
```

### Run Integration Test

```bash
python -m pytest tests/test_integration.py -v
```

## Configuration

Default configuration in `config.py`:

- **Database**: In-memory SQLite (`:memory:`)
- **Columns**: `['date', 'amount', 'nr_1', 'nr_2', 'description']`
- **Default Category**: `"Uncategorized"`
- **Log Level**: `INFO`

## Examples

### Example 1: Basic Usage with Sample Data

```bash
# Use provided test fixtures
python -m data_cleansing_agent.cli categorize \
  --input ./tests/fixtures \
  --categories ./tests/fixtures/category_list.csv
```

### Example 2: Multiple CSV Files

Place multiple transaction CSV files in the input directory:

```
input/
├── transactions_jan.csv
├── transactions_feb.csv
├── transactions_mar.csv
└── category_list.csv
```

```bash
python -m data_cleansing_agent.cli categorize \
  --input ./input \
  --categories ./input/category_list.csv
```

### Example 3: Export Results

```bash
python -m data_cleansing_agent.cli categorize \
  --input ./input \
  --categories ./input/category_list.csv \
  --export ./reports/summary_2024.csv
```

## Troubleshooting

### "No CSV files found"
- Ensure your input directory contains `.csv` files
- Category list file is automatically excluded

### "Missing required columns"
- Transaction CSV must have 5 columns (date, amount, nr_1, nr_2, description)
- Verify CSV format matches expected structure

### "No categories found"
- Check that category_list.csv has column headers
- Ensure merchant names are listed below headers
- Verify CSV is properly formatted

### High "Uncategorized" Rate
- Review merchant patterns in category_list.csv
- Add more specific or generic patterns
- Check for typos in merchant names

## Dependencies

- **pandas** (>=2.0.0): CSV handling and data aggregation
- **pytest** (>=7.0.0): Testing framework
- **sqlite3**: Built-in Python module (no installation needed)

## Design Decisions

1. **In-Memory Database**: Fast performance for batch processing, no persistence needed
2. **Partial Matching**: Flexible pattern matching handles merchant name variations
3. **Column-Based Categories**: Easy to maintain in spreadsheet applications
4. **Modular Architecture**: Each module has a single responsibility
5. **Pandas for Aggregation**: Leverages powerful groupby functionality

## License

This project is provided as-is for educational and commercial use.

## Contributing

Contributions welcome! Please submit issues or pull requests.

## Future Enhancements

- [ ] Support for fuzzy matching algorithms
- [ ] Machine learning-based categorization
- [ ] Web-based dashboard (Flask/Streamlit)
- [ ] Database persistence options
- [ ] Multi-currency support
- [ ] Date range filtering
- [ ] Custom rule definitions

## Author

Built following software engineering best practices with modular design, comprehensive testing, and clear documentation.
