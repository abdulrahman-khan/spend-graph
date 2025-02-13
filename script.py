import pdfplumber
import pandas as pd
import re
from pathlib import Path

def should_skip_line(line):
    """Check if line should be skipped"""
    skip_patterns = [
        r'page\s*\d+\s*of\s*\d+',
        r'continued\s*on\s*next\s*page',
        r'what happened in your account',
        r'StudentBankingAdvantagePlan',
        r'\d{6,}',  # Long number sequences
        r'----',    # Separator lines
        r'VASBS'   # Account markers
    ]
    
    line_lower = line.lower()
    return any(re.search(pattern, line_lower) for pattern in skip_patterns)

def clean_transaction_line(line):
    """Clean and parse a transaction line into structured data"""
    # Skip informational lines
    if should_skip_line(line):
        return None
        
    # Remove extra spaces and combine with next line if it's part of description
    line = ' '.join(line.split())
    
    # Remove closing balance text and amount if present
    closing_balance_pattern = r'(.*?)\s+(?:May|Apr|Mar|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Jan|Feb)\d{1,2}\s+Closing\s*Balance\s+\$[\d,]+\.\d{2}\s*-?'
    closing_match = re.match(closing_balance_pattern, line, re.IGNORECASE)
    if closing_match:
        line = closing_match.group(1)
    
    # Pattern to match transaction lines
    pattern = r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{1,2})\s+(.*?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})?\s*(\d{1,3}(?:,\d{3})*\.\d{2})?\s+(\d{1,3}(?:,\d{3})*\.\d{2})$"
    
    match = re.match(pattern, line)
    if match:
        date, description, amount1, amount2, balance = match.groups()
        
        # Initialize withdrawal and deposit
        withdrawal = None
        deposit = None
        
        # Determine if amount is withdrawal or deposit based on description
        description = description.strip()
        if amount1:
            amount = float(amount1.replace(',', ''))
            if ('Payrolldep' in description or 
                'GST' in description or 
                'Opening Balance' in description):
                deposit = amount
            else:
                withdrawal = amount
        if amount2:
            amount = float(amount2.replace(',', ''))
            deposit = amount
            
        return {
            'date': date,
            'description': description,
            'withdrawal': withdrawal,
            'deposit': deposit,
            'balance': float(balance.replace(',', ''))
        }
    return None

def process_pdf_to_csv(pdf_path, output_csv):
    """Process PDF file and create organized CSV"""
    transactions = []
    current_transaction = None
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Skip header, empty lines, or informational text
                if not line or 'Date Transactions' in line or should_skip_line(line):
                    continue
                
                # Try to parse as transaction
                transaction = clean_transaction_line(line)
                if transaction:
                    if current_transaction:
                        transactions.append(current_transaction)
                    current_transaction = transaction
                elif current_transaction and not should_skip_line(line):
                    # If line doesn't match transaction pattern and isn't junk text,
                    # it might be additional description
                    current_transaction['description'] += ' ' + line
    
        # Add last transaction
        if current_transaction:
            transactions.append(current_transaction)
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(transactions)
    
    if not df.empty:
        # Reorder columns
        columns = ['date', 'description', 'withdrawal', 'deposit', 'balance']
        df = df[columns]
        
        # Save to CSV
        df.to_csv(output_csv, index=False)
        print(f"Successfully created CSV file: {output_csv}")
        print(f"Total transactions processed: {len(df)}")
    else:
        print(f"No transactions found in: {pdf_path}")

def process_all_statements():
    """Process all PDF files in the e-statements folder"""
    # Create paths
    statements_dir = Path('e-statements')
    output_dir = Path('csv-statements')
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Process each PDF file
    for pdf_file in statements_dir.glob('*.pdf'):
        # Create output CSV path with same name as PDF
        csv_file = output_dir / f"{pdf_file.stem}.csv"
        
        print(f"\nProcessing: {pdf_file.name}")
        process_pdf_to_csv(pdf_file, csv_file)

if __name__ == "__main__":
    process_all_statements()