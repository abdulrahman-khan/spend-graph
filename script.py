import pdfplumber
import pandas as pd
import re
from pathlib import Path

def process_all_files():
    """Main function to process files in two steps"""
    statements_dir = Path('e-statements')
    raw_dir = Path('raw-statement')
    cleaned_dir = Path('cleaned-raw-statement')
    output_dir = Path('csv-statements')

    # Create necessary directories
    statements_dir.mkdir(exist_ok=True)
    raw_dir.mkdir(exist_ok=True)
    cleaned_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Step 1: Process PDFs to raw text files
    for pdf_file in statements_dir.glob('*.pdf'):
        raw_text_path = raw_dir / f"{pdf_file.stem}.txt"
        print(f"\nExtracting text from: {pdf_file.name}")
        pdf_to_raw_text(pdf_file, raw_text_path)
    
    # Step 2: Clean raw text files
    for text_file in raw_dir.glob('*.txt'):
        cleaned_text_path = cleaned_dir / text_file.name
        print(f"\nCleaning text file: {text_file.name}")
        clean_raw_text(text_file, cleaned_text_path)
    
    # Step 3: Process cleaned text files to CSVs  
    for text_file in cleaned_dir.glob('*.txt'):
        csv_file = output_dir / f"{text_file.stem}.csv"
        print(f"\nProcessing text to CSV: {text_file.name}")
        raw_text_to_csv(text_file, csv_file)

def pdf_to_raw_text(pdf_path, output_text):
    """Extract raw text from PDF without any filtering"""
    raw_content = []
    
    with pdfplumber.open(pdf_path) as pdf:
        # Extract raw text from each page
        for page in pdf.pages:
            text = page.extract_text()
            raw_content.append(text)
            
            # Add page break marker between pages
            raw_content.append('=== PAGE BREAK ===')

        # Remove the last page break marker
        raw_content.pop()

        # Save raw content to text file
        with open(output_text, 'w', encoding='utf-8') as f:
            f.write('\n'.join(raw_content))
            print(f"Saved raw text to: {output_text}")

def clean_raw_text(input_path, output_path):
    """Clean raw text file by removing header and footer information"""
    # Read the file content
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the start marker of transaction data
    start_marker = "Here's what happened in your account this statement period"
    
    # Patterns to identify footer/irrelevant information
    footer_patterns = [
        r'Page\s*\d+\s*of\s*\d+',      # Page numbers
        r'VASBS\d*',                    # VASBS markers
        r'[-_]{3,}',                    # Separator lines (3 or more - or _)
        r'\d{6,}',                      # Long number sequences (account numbers, etc)
        r'^\s*\d+\s*$',                 # Lines with just numbers
        r'^\s*$',                       # Empty lines
        r'.*Closing\s*Balance.*'        # Closing balance line
    ]
    
    if start_marker in content:
        # Split content at the start marker and keep everything after it
        _, transaction_content = content.split(start_marker, 1)
        
        # Split lines to process footer
        lines = transaction_content.strip().split('\n')
        cleaned_lines = []
        skip_until_date = False
        
        # Keep only relevant transaction lines
        for line in lines:
            line = line.strip()
            
            # If we hit a page break or continued marker, start skipping until next date
            if '=== PAGE BREAK ===' in line or "Here's what happened in your account (continued)" in line:
                skip_until_date = True
                continue
            
            # Check if line starts with a date pattern (e.g., "Jan9")
            date_pattern = r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{1,2}'
            if re.match(date_pattern, line.replace(' ', '')):
                skip_until_date = False
            
            # Only add line if we're not skipping and it doesn't match footer patterns
            if not skip_until_date and not any(re.search(pattern, line, re.IGNORECASE) for pattern in footer_patterns):
                cleaned_lines.append(line)
        
        # Join cleaned lines back together
        cleaned_content = '\n'.join(cleaned_lines).strip()
        
        # Write to new file in cleaned directory
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
            print(f"Saved cleaned text to: {output_path}")
    else:
        print(f"Warning: Could not find start marker in {input_path}")

def raw_text_to_csv(text_path, output_csv):
    """Process raw text file to create organized CSV using balance changes"""
    transactions = []
    current_transaction = None
    opening_balance = None
    previous_balance = None
    statement_year = None
    
    with open(text_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Find opening balance
        if 'OpeningBalance' in line.replace(' ', ''):
            # Extract amount and balance from line
            parts = line.split()
            opening_balance = float(parts[-1].replace(',', ''))
            previous_balance = opening_balance
            continue
            
        # Check if line starts with a date (e.g., "Jan9")
        date_pattern = r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{1,2}'
        if re.match(date_pattern, line.replace(' ', '')):
            # If we have a previous transaction, save it
            if current_transaction:
                transactions.append(current_transaction)
            
            # Split line into components
            parts = line.split()
            date_str = parts[0]  # e.g., "Jan9"
            balance = float(parts[-1].replace(',', ''))  # Last number is balance
            amount = float(parts[-2].replace(',', ''))   # Second to last is amount
            description = ' '.join(parts[1:-2])          # Everything in between
            
            # Determine if deposit or withdrawal by comparing balances
            if balance > previous_balance:
                deposit = amount
                withdrawal = None
            else:
                deposit = None
                withdrawal = amount
                
            # Create new transaction
            current_transaction = {
                'month': date_str[:3],
                'date': int(date_str[3:]),
                'description': description,
                'withdrawal': withdrawal,
                'deposit': deposit,
                'balance': balance
            }
            
            previous_balance = balance
            
        # If next line doesn't start with date, it's additional description
        elif current_transaction:
            current_transaction['description'] += ' ' + line
    
    # Add final transaction
    if current_transaction:
        transactions.append(current_transaction)
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(transactions)
    
    if not df.empty:
        # Add year column (from existing extract_statement_date function)
        df['year'] = statement_year
        
        # Reorder columns
        columns = ['date', 'month', 'year', 'description', 'withdrawal', 'deposit', 'balance']
        df = df[columns]
        
        # Save to CSV
        df.to_csv(output_csv, index=False)
        print(f"Successfully created CSV file: {output_csv}")
        print(f"Total transactions processed: {len(df)}")
    else:
        print(f"No transactions found in: {text_path}")

def extract_statement_date(text):
    """Extract month and year from statement text"""
    # Patterns to match different date formats in statement
    date_patterns = [
        # Pattern for "March 18 to April 16, 2022" format
        r'(?P<start_month>January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s+to\s+(?P<end_month>January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+(?P<year>\d{4})',
        
        # Pattern for just end date "April 16, 2022"
        r'(?P<end_month>January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+(?P<year>\d{4})',
        
        # Fallback pattern for just year
        r'(?P<year>\d{4})'
    ]
    
    month_to_number = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }

    # Try each pattern
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            data = match.groupdict()
            year = data.get('year')
            
            # Try to get end_month first, then start_month if end_month doesn't exist
            month_name = data.get('end_month') or data.get('start_month')
            
            if month_name:
                month = month_to_number.get(month_name)
                return month, int(year)
            elif year:
                return None, int(year)
    
    print("No date information found in text")
    return None, None

def should_skip_line(line):
    """Check if line should be skipped"""
    skip_patterns = [
        r'continued\s*on\s*next\s*page',
        r'what happened in your account',
        r'StudentBankingAdvantagePlan',
        r'\d{6,}',  # Long number sequences
        r'VASBS',   # Account markers,
        r"YourBasicPlusBankaccount",
    ]
    
    line_lower = line.lower()
    return any(re.search(pattern, line_lower) for pattern in skip_patterns)

def clean_transaction_line(line):
    """Clean and parse a transaction line into structured data"""
    if should_skip_line(line):
        return None
        
    # Remove extra spaces and combine with next line if it's part of description
    line = ' '.join(line.split())
    
    # Pattern to match transaction lines - now includes GST and other deposit types
    pattern = r"(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?P<day>\d+)\s+(?P<type>Pointofsalepurchase|GST|Payrolldep|Opening\s*Balance)\s+(?P<amount>\d+\.\d{2})\s+(?P<total>\d{1,3}(?:,\d{3})*\.\d{2})"

    match = re.match(pattern, line)
    if match:
        month, date, transaction_type, amount1, balance = match.groups()
        
        # Initialize withdrawal and deposit
        withdrawal = None
        deposit = None
        
        # Convert amount to float
        amount = float(amount1.replace(',', ''))
        
        # Determine if amount is withdrawal or deposit based on transaction type
        if transaction_type in ['GST', 'Payrolldep', 'Opening Balance']:
            deposit = amount
        else:
            withdrawal = amount
            
        return {
            'month': month,
            'date': int(date),  # Convert to integer
            'description': transaction_type,
            'withdrawal': withdrawal,
            'deposit': deposit,
            'balance': float(balance.replace(',', ''))
        }
    return None

if __name__ == "__main__":
    process_all_files()