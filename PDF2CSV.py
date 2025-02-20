import pdfplumber
import pandas as pd
import re
from pathlib import Path
import shutil

def clean_working_directories():
    """Remove contents of all working directories and EXPORT.csv"""
    # Remove EXPORT.csv if it exists
    export_file = Path('DATA/EXPORT.csv')
    if export_file.exists():
        export_file.unlink()
        print("Removed existing EXPORT.csv")
    
    # Clean directories
    working_dirs = [
        Path('raw-statement'),
        Path('csv-statements'),
        Path('cleaned-raw-statement'),
        Path('DATA')
    ]
    
    for directory in working_dirs:
        if directory.exists():
            shutil.rmtree(directory)
            directory.mkdir()
            print(f"Cleaned {directory} directory")
    
    # Create new empty EXPORT.csv
    export_file.parent.mkdir(exist_ok=True)
    export_file.touch()
    print("Created new EXPORT.csv")

def process_all_files():
    """Main function to process files in two steps"""
    # Clean all working directories first
    clean_working_directories()
    
    statements_dir = Path('e-statements')
    raw_dir = Path('raw-statement')
    cleaned_dir = Path('cleaned-raw-statement')
    output_dir = Path('csv-statements')

    # Create necessary directories
    statements_dir.mkdir(exist_ok=True)
    raw_dir.mkdir(exist_ok=True)
    cleaned_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Step 1: Process PDFs to raw text files - now with recursive search
    for pdf_file in statements_dir.rglob('*.pdf'):
        # Maintain folder structure in raw_dir
        relative_path = pdf_file.relative_to(statements_dir)
        raw_text_path = raw_dir / relative_path.with_suffix('.txt')
        
        # Create parent directories if they don't exist
        raw_text_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\nExtracting text from: {pdf_file}")
        pdf_to_raw_text(pdf_file, raw_text_path)
    
    # Step 2: Clean raw text files - now with recursive search
    for text_file in raw_dir.rglob('*.txt'):
        # Maintain folder structure in cleaned_dir
        relative_path = text_file.relative_to(raw_dir)
        cleaned_text_path = cleaned_dir / relative_path
        
        # Create parent directories if they don't exist
        cleaned_text_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\nCleaning text file: {text_file}")
        clean_raw_text(text_file, cleaned_text_path)
    
    # Step 3: Process cleaned text files to CSVs - now with recursive search
    for text_file in cleaned_dir.rglob('*.txt'):
        # Maintain folder structure in output_dir
        relative_path = text_file.relative_to(cleaned_dir)
        csv_file = output_dir / relative_path.with_suffix('.csv')
        
        # Create parent directories if they don't exist
        csv_file.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\nProcessing text to CSV: {text_file}")
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
    previous_balance = None
    
    # Extract year from filename
    year = int(re.search(r'20\d{2}', text_path.name).group())
    
    with open(text_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Handle opening balance
        if 'OpeningBalance' in line.replace(' ', ''):
            parts = line.split()
            previous_balance = float(parts[-1].replace(',', ''))
            continue
        
        # Check for new transaction (starts with date)
        date_pattern = r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{1,2}'
        if re.match(date_pattern, line.replace(' ', '')):
            try:
                # Save previous transaction if exists
                if current_transaction:
                    transactions.append(current_transaction)
                
                # Parse new transaction
                parts = line.split()
                date_str = parts[0]
                balance = float(parts[-1].replace(',', ''))
                amount = float(parts[-2].replace(',', ''))
                description = ' '.join(parts[1:-2])
                
                # Determine transaction type by balance change
                if balance > previous_balance:
                    deposit, withdrawal = amount, None
                else:
                    deposit, withdrawal = None, amount
                
                # Adjust year for December transactions
                transaction_year = year
                if date_str.startswith('Dec'):
                    transaction_year = year - 1
                
                # Create transaction record
                current_transaction = {
                    'month': date_str[:3],
                    'date': int(date_str[3:]),
                    'description': description,
                    'withdrawal': withdrawal,
                    'deposit': deposit,
                    'balance': balance,
                    'year': transaction_year
                }
                
                previous_balance = balance
            
            except (IndexError, ValueError, AttributeError) as e:
                print(f"Error processing line: {line}")
                print(f"Error details: {str(e)}")
                continue
        
        # Add additional description lines
        elif current_transaction:
            try:
                current_transaction['description'] += ' ' + line
            except Exception as e:
                print(f"Error adding description line: {line}")
                print(f"Error details: {str(e)}")
                continue
    
    # Add final transaction
    if current_transaction:
        transactions.append(current_transaction)
    
    # Create and save DataFrame
    if transactions:
        df = pd.DataFrame(transactions)
        columns = ['date', 'month', 'year', 'description', 'withdrawal', 'deposit', 'balance']
        df = df[columns]
        df.to_csv(output_csv, index=False)
        print(f"Processed {len(df)} transactions")
    else:
        print(f"No transactions found in {text_path}")

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