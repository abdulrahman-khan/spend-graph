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
    pattern = r"(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?P<day>\d+)\s+(?P<type>Pointofsalepurchase)\s+(?P<amount>\d+\.\d{2})\s+(?P<total>\d{1,3}(?:,\d{3})*\.\d{2})"

    match = re.match(pattern, line)
    if match:
        month, date, description, amount1, balance = match.groups()
        
        # Initialize withdrawal and deposit
        withdrawal = None
        deposit = None
        amount2 = None
        
        
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
            'month': month,
            'date': date,  # Convert to integer
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
    statement_month = None
    statement_year = None
    
    with pdfplumber.open(pdf_path) as pdf:

        # Extract month and year from first page
        first_page = pdf.pages[1].extract_text()
        statement_year = extract_statement_date(first_page)[1]

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
        # Add month and year columns
        # df['month'] = statement_month
        df['year'] = statement_year
        
        # Reorder columns
        columns = ['date', 'month', 'year', 'description', 'withdrawal', 'deposit', 'balance']
        df = df[columns]
        
        # Save to CSV
        df.to_csv(output_csv, index=False)
        print(f"Successfully created CSV file: {output_csv}")
        print(f"Total transactions processed: {len(df)}")
        print(f"Statement period: {statement_month} {statement_year}")
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