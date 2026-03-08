# Bank Statement Analyzer

Python scripts to parse through PDF bank statements, created structured data and generating spending visualizations. 

# Process

PDFs go through a multi-stage pipeline:

1. `script.py` — extracts and cleans raw text from PDFs, converts to CSV
2. `compiler.py` — merges individual statement CSVs into one
3. `analyze_statements.py` — generates visualizations and spending breakdowns

## Output

- Balance over time
- Monthly cash flow
- Deposit and withdrawal tracking
- Top 5 expenses

