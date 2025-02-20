# 📊 Bank Statement Analyzer

A Python-based tool for analyzing bank statements and generating financial insights. This tool processes PDF bank statements through multiple stages to create detailed financial visualizations.

<div align="center">
  <img src="docs/workflow.png" alt="Processing Workflow" width="800"/>
</div>

## 🌟 Features

- 📄 Converts PDF bank statements to structured data
- 💰 Tracks deposits and withdrawals
- 📈 Generates visual financial analysis
- 📅 Handles multi-month statements
- 🔄 Automatic transaction categorization
- 📊 Multi-stage data processing pipeline
- 🔍 Intelligent transaction detection

## 📊 Sample Output

<div align="center">
  <img src="docs/balance_graph.png" alt="Balance Over Time" width="400"/>
  <img src="docs/cash_flow.png" alt="Monthly Cash Flow" width="400"/>
</div>

## 🏗️ Project Structure

```
bank-statement-analyzer/
├── e-statements/        # PDF bank statements (private)
├── raw-statement/      # Extracted raw text
├── cleaned-raw-statement/  # Cleaned text data
├── csv-statements/     # Individual CSV files
├── DATA/               # Output data and analysis
├── docs/              # Documentation and sample images
├── script.py          # PDF Processing, cleaning, and CSV conversion
├── compiler.py        # CSV compilation script
└── analyze_statements.py   # Analysis and visualization
```

## 🔄 Processing Pipeline

1. **PDF Text Extraction** (`script.py`)
   - Uses pdfplumber for accurate text extraction
   - Maintains page structure with markers
   - Preserves transaction formatting

2. **Text Cleaning** (`script.py`)
   - Removes headers and footers
   - Handles multi-page transactions
   - Intelligent date detection
   - Year adjustment for cross-year statements

3. **CSV Conversion** (`script.py`)
   - Structured data extraction
   - Balance-based transaction type detection
   - Multi-line description handling
   - Date normalization

4. **Data Compilation** (`compiler.py`)
   - Combines individual statement CSVs
   - Chronological sorting
   - Data validation
   - Export to unified format

5. **Analysis & Visualization** (`analyze_statements.py`)
   - Time series analysis
   - Cash flow tracking
   - Expense categorization
   - High-resolution graph generation

## 📊 Data Structure

### CSV Format
```csv
date,month,year,description,withdrawal,deposit,balance
5,Jan,2021,Point of Sale Purchase,50.00,,4114.06
9,Jan,2021,GST Canada,,74.00,4188.06
```

### Transaction Detection
The system uses balance changes to determine transaction types:
```python
if balance > previous_balance:
    transaction_type = "deposit"
else:
    transaction_type = "withdrawal"
```

## 🚀 Getting Started

1. Place your bank statements in the `e-statements` folder
2. Run the processing pipeline:
```bash
python script.py      # Process PDFs to CSVs
python compiler.py    # Compile CSVs to EXPORT.csv
python analyze_statements.py  # Generate analysis
```

## 📊 Analysis Output

The tool generates several visualizations:
- Account balance over time
- Deposits and withdrawals tracking
- Monthly net cash flow analysis
- Top 5 highest expenses

## 🛠️ Requirements

- Python 3.8+
- pdfplumber>=0.7.0
- pandas>=1.3.0
- matplotlib>=3.4.0
- seaborn>=0.11.0

Install dependencies:
```bash
pip install -r requirements.txt
```

## 📁 Directory Setup

The tool will automatically create these directories:
- `e-statements/` - Place your PDF statements here
- `DATA/` - Contains the final EXPORT.csv and analysis
- Other working directories are created as needed

## 🔒 Privacy

- All data stays local on your machine
- Sensitive directories are gitignored
- No data is transmitted or stored online

## 📝 Technical Notes

- Uses regex patterns for robust text parsing
- Implements state machine for transaction detection
- Handles cross-month statement periods
- Automatic year adjustment for December transactions
- Balance-based transaction type verification
- Multi-threaded PDF processing
- Automated directory management
- Error handling and validation

---
Made with 💻 by Abdulrahman Khan