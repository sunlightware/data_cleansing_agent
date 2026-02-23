# Quick Start Guide

Get started with Data Cleansing Agent in 3 simple steps!

## Step 1: Install Dependencies (30 seconds)

```bash
cd data_cleansing_agent
pip install -r requirements.txt
```

## Step 2: Prepare Your Data

The system automatically reads CSV files with headers and extracts only the required columns.

### Directory Structure

```
data_cleansing_agent/
├── inputs/
│   ├── transactions/          # Put your CSV files here
│   │   ├── CreditCard4.csv
│   │   └── sample_transactions.csv
│   ├── category/
│   │   └── category_list.csv  # Category definitions
│   └── budget/
│       └── budget.csv         # Budget limits (optional)
```

### CSV Input Files (with Headers)

The system supports multiple CSV formats:

#### **Format 1: Simple (Date, Amount, Description)**
```csv
Date,Amount,Description
01/15/2026,-65.00,SHELL OIL 57444225100 CHARLOTTE NC
01/14/2026,-89.99,COSTCO WHSE #1234 CHARLOTTE NC
01/12/2026,-45.50,STARBUCKS STORE 12345 CHARLOTTE NC
```

#### **Format 2: Post Date variant**
```csv
Post Date,Amount,Description
2026-01-15,-65.00,SHELL OIL 57444225100 CHARLOTTE NC
2026-01-14,-89.99,COSTCO WHSE #1234 CHARLOTTE NC
```

#### **Format 3: Credit/Debit columns**
```csv
Transaction Date,Credit,Debit,Description
01/15/2026,1200.00,0.00,PAYCHECK DEPOSIT
01/14/2026,0.00,89.99,COSTCO WHSE #1234 CHARLOTTE NC
01/12/2026,0.00,45.50,STARBUCKS STORE 12345 CHARLOTTE NC
```
The system automatically combines Credit (positive) and Debit (negative) into Amount.

#### **Format 4: Extra columns (ignored)**
```csv
Date,Amount,Flag,Extra,Description,Notes
01/15/2026,-65.00,*,,SHELL OIL 57444225100 CHARLOTTE NC,Business
01/14/2026,-89.99,*,,COSTCO WHSE #1234 CHARLOTTE NC,Personal
```
Only Date, Amount, and Description are extracted; other columns are ignored.

### Category List (category_list.csv)

```csv
Groceries,Restaurants,Gas,Shopping,Entertainment,ignore
HARRIS TEETER,STARBUCKS,SHELL,WALMART,NETFLIX,ONLINE PAYMENT
COSTCO,CHICK-FIL-A,EXXON,TARGET,FANDANGO,ONLINE ACH PAYMENT
WHOLE FOODS,PAPA JOHNS,BP,,,
PUBLIX,PANERA,,,,
```

- Each column = one category
- Values = merchant patterns to match (case-insensitive, partial matching)
- **ignore** column = patterns to exclude from all calculations

### Budget File (budget.csv) - Optional

```csv
Category,Budget
Groceries,1000.00
Restaurants,700.00
Gas,200.00
Shopping,50.00
Entertainment,20.00
```

- Category name must match category_list.csv
- Budget is monthly spending limit

## Step 3: Run Categorization

### Basic Usage

```bash
cd /Users/rs/anthropic
python3 -m data_cleansing_agent.cli categorize \
  --input data_cleansing_agent/inputs \
  --categories data_cleansing_agent/inputs/category/category_list.csv
```

## Expected Output

```
================================================================================
                       TRANSACTION CATEGORIZATION REPORT
================================================================================
Transactions: 113  |  Categories: 10  |  Uncategorized: 13 (11.5%)

--------------------------------------------------------------------------------
Category           | Count |       Total | % of Total
--------------------------------------------------------------------------------
Groceries          |    21 |   $2,071.74 |      29.2%
Travel             |     3 |   $1,368.97 |      19.3%
Entertainment      |    10 |     $775.02 |      10.9%
Restaurants        |    18 |     $548.56 |       7.7%
Learning           |     9 |     $513.00 |       7.2%
--------------------------------------------------------------------------------
TOTAL              |   113 |   $7,106.71 |     100.0%
================================================================================
```

## Common Usage Examples

### 1. Categorize with Budget Tracking

```bash
python3 -m data_cleansing_agent.cli categorize \
  --input data_cleansing_agent/inputs \
  --categories data_cleansing_agent/inputs/category/category_list.csv \
  --budget data_cleansing_agent/inputs/budget/budget.csv
```

**Output includes Budget and Deviation columns:**
```
Category           | Count |       Total |      Budget |   Deviation | % of Total
--------------------------------------------------------------------------------
Groceries          |    21 |   $2,071.74 |   $1,000.00 |  $-1,071.74 |      29.2%
Restaurants        |    18 |     $548.56 |     $700.00 |     $151.44 |       7.7%
```
- **Negative deviation** = over budget (red flag)
- **Positive deviation** = under budget (good)

### 2. Drill Down into Specific Category

```bash
python3 -m data_cleansing_agent.cli drilldown \
  --input data_cleansing_agent/inputs \
  --categories data_cleansing_agent/inputs/category/category_list.csv \
  --category Groceries
```

**Output shows all transactions in that category:**
```
================================================================================
                    CATEGORY DRILLDOWN: Groceries
================================================================================
Total Transactions: 21  |  Total Amount: $2,071.74

Date          | Description                              | Amount
------------------------------------------------------------------------
01/02/2026    | HARRIS TEETER #0249 MATTHEWS NC         |   $14.57
01/03/2026    | HARRIS TEETER 800-432-6111 NC           |  $156.59
01/07/2026    | HARRIS TEETER #0249 MATTHEWS NC         |   $30.93
...
```

### 3. Export Results to CSV

```bash
python3 -m data_cleansing_agent.cli categorize \
  --input data_cleansing_agent/inputs \
  --categories data_cleansing_agent/inputs/category/category_list.csv \
  --budget data_cleansing_agent/inputs/budget/budget.csv \
  --export summary_report.csv
```

Creates `summary_report.csv` file with all category summaries.

### 4. Debug Mode (Verbose Logging)

```bash
python3 -m data_cleansing_agent.cli --log-level DEBUG categorize \
  --input data_cleansing_agent/inputs \
  --categories data_cleansing_agent/inputs/category/category_list.csv
```

Shows detailed logs:
- CSV columns detected
- Column mapping (date→'Date', amount→'Amount', etc.)
- Each transaction being categorized
- Database operations

## Monthly Review Workflow

```bash
# 1. Categorize with budget
python3 -m data_cleansing_agent.cli categorize \
  --input data_cleansing_agent/inputs \
  --categories data_cleansing_agent/inputs/category/category_list.csv \
  --budget data_cleansing_agent/inputs/budget/budget.csv

# 2. Look at report, identify categories with negative deviation (overspent)

# 3. Drill down into overspent category
python3 -m data_cleansing_agent.cli drilldown \
  --input data_cleansing_agent/inputs \
  --categories data_cleansing_agent/inputs/category/category_list.csv \
  --category Groceries

# 4. Export for spreadsheet analysis
python3 -m data_cleansing_agent.cli categorize \
  --input data_cleansing_agent/inputs \
  --categories data_cleansing_agent/inputs/category/category_list.csv \
  --budget data_cleansing_agent/inputs/budget/budget.csv \
  --export monthly_summary.csv
```

## Key Features

✅ **Flexible CSV Format**: Handles headers with varying column names and counts
✅ **Multiple Date Formats**: 'Date', 'Post Date', 'Transaction Date'
✅ **Credit/Debit Support**: Automatically combines into Amount
✅ **Partial Matching**: "STARBUCKS STORE 12345" matches "STARBUCKS"
✅ **Case Insensitive**: "harris teeter" matches "HARRIS TEETER"
✅ **Ignore Patterns**: Exclude transfers, payments from calculations
✅ **Budget Tracking**: Compare actual vs budget with deviation
✅ **Drill Down**: View all transactions within a category
✅ **Export**: Save results to CSV for spreadsheet analysis

## Run Tests

```bash
cd data_cleansing_agent
python3 -m pytest tests/test_integration.py -v
```

**Expected output:**
```
============================== 12 passed in 0.17s ==============================
```

## Supported Column Names

The system automatically detects these column patterns:

| Required Field | Supported Column Names |
|---------------|------------------------|
| **Date** | 'Date', 'Post Date', 'Transaction Date', or any column containing 'date' |
| **Amount** | 'Amount', OR combined from 'Credit' and 'Debit' columns |
| **Description** | 'Description', 'Desc' |

All other columns are ignored.

## Need Help??

- Read the full [README.md](README.md)
- Check sample data in `inputs/`
- Review the integration test: `tests/test_integration.py`
- Run with `--log-level DEBUG` for detailed logging
