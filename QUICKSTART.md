# Quick Start Guide

Get started with Data Cleansing Agent in 3 simple steps!

## Step 1: Install Dependencies (30 seconds)

```bash
cd data_cleansing_agent
pip install -r requirements.txt
```

## Step 2: Prepare Your Data

### Option A: Use Sample Data (Fastest)

```bash
# Run with included sample data
python3 -m data_cleansing_agent.cli categorize \
  --input tests/fixtures \
  --categories tests/fixtures/category_list.csv
```

### Option B: Use Your Own Data

Create your files:

**1. Transaction CSV (no headers):**
```csv
2024-01-01,45.50,001,ABC,HARRIS TEETER #1234
2024-01-02,120.00,002,DEF,COSTCO WHOLESALE
2024-01-03,25.75,003,GHI,STARBUCKS COFFEE
```

**2. Category List CSV:**
```csv
Groceries,Restaurants,Gas,Shopping
HARRIS TEETER,STARBUCKS,SHELL,AMAZON
COSTCO,CHICK-FIL-A,EXXON,TARGET
WHOLE FOODS,DUNKIN,BP,WALMART
```

## Step 3: Run Categorization

```bash
python3 -m data_cleansing_agent.cli categorize \
  --input ./your_input_folder \
  --categories ./your_input_folder/category_list.csv
```

## Expected Output

```
================================================================================
                    TRANSACTION CATEGORIZATION REPORT
================================================================================
Transactions: 20  |  Categories: 5  |  Uncategorized: 1 (5.0%)

--------------------------------------------------------------------------------
Category             | Count |       Total |    Average | % of Total
--------------------------------------------------------------------------------
Groceries            |     5 |     $533.30 |    $106.66 |      37.1%
Gas                  |     4 |     $380.00 |     $95.00 |      26.4%
Shopping             |     4 |     $320.99 |     $80.25 |      22.3%
Restaurants          |     5 |     $164.45 |     $32.89 |      11.4%
Uncategorized        |     1 |      $22.99 |     $22.99 |       1.6%
--------------------------------------------------------------------------------
TOTAL                |    20 |   $1,437.72 |     $71.89 |     100.0%
================================================================================
```

## That's It!

For more options and advanced usage, see [README.md](README.md)

## Common Commands

```bash
# Export summary to CSV
python3 -m data_cleansing_agent.cli categorize \
  --input ./input \
  --categories ./input/category_list.csv \
  --export ./summary.csv

# Run tests
python3 -m pytest tests/ -v

# Debug mode
python3 -m data_cleansing_agent.cli --log-level DEBUG categorize \
  --input ./input \
  --categories ./input/category_list.csv
```

## Need Help?

- Read the full [README.md](README.md)
- Check test examples in `tests/fixtures/`
- Review the integration test: `tests/test_integration.py`
