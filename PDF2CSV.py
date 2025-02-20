import pdfplumber
import pandas as pd
import re
from pathlib import Path

class StatementProcessor:
    def __init__(self):
        # Define directory paths
        self.statements_dir = Path('e-statements')
        self.raw_dir = Path('raw-statement')
        self.cleaned_dir = Path('cleaned-raw-statement')
        self.output_dir = Path('csv-statements')
        
        # Create all necessary directories
        self._create_directories()
    
    def _create_directories(self):
        """Create all required directories if they don't exist"""
        directories = [
            self.statements_dir,
            self.raw_dir,
            self.cleaned_dir,
            self.output_dir
        ]
        for directory in directories:
            directory.mkdir(exist_ok=True)
    
    def process_all_files(self):
        """Process all PDF files through the pipeline"""
        self._process_pdfs_to_text()
        self._clean_text_files()
        self._convert_to_csv()
    
    def _process_pdfs_to_text(self):
        """Step 1: Convert PDFs to raw text files"""
        for pdf_file in self.statements_dir.rglob('*.pdf'):
            # Maintain folder structure
            relative_path = pdf_file.relative_to(self.statements_dir)
            raw_text_path = self.raw_dir / relative_path.with_suffix('.txt')
            raw_text_path.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"\nExtracting text from: {pdf_file}")
            self._pdf_to_raw_text(pdf_file, raw_text_path)
    
    def _clean_text_files(self):
        """Step 2: Clean raw text files"""
        for text_file in self.raw_dir.rglob('*.txt'):
            # Maintain folder structure
            relative_path = text_file.relative_to(self.raw_dir)
            cleaned_text_path = self.cleaned_dir / relative_path
            cleaned_text_path.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"\nCleaning text file: {text_file}")
            self._clean_raw_text(text_file, cleaned_text_path)
    
    def _convert_to_csv(self):
        """Step 3: Convert cleaned text to CSV files"""
        for text_file in self.cleaned_dir.rglob('*.txt'):
            # Maintain folder structure
            relative_path = text_file.relative_to(self.cleaned_dir)
            csv_file = self.output_dir / relative_path.with_suffix('.csv')
            csv_file.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"\nProcessing text to CSV: {text_file}")
            self._text_to_csv(text_file, csv_file)
    
    def _pdf_to_raw_text(self, pdf_path, output_path):
        """Extract raw text from PDF"""
        raw_content = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                raw_content.append(text)
                raw_content.append('=== PAGE BREAK ===')
            
            # Remove final page break
            raw_content.pop()
            
            # Save content
            output_path.write_text('\n'.join(raw_content), encoding='utf-8')
            print(f"Saved raw text to: {output_path}")
    
    def _clean_raw_text(self, input_path, output_path):
        """Clean raw text and extract transaction data"""
        content = input_path.read_text(encoding='utf-8')
        
        # Find start of transaction data
        start_marker = "Here's what happened in your account this statement period"
        if start_marker not in content:
            print(f"Warning: Could not find transaction section in {input_path}")
            return
        
        # Process content
        _, transaction_content = content.split(start_marker, 1)
        cleaned_lines = self._process_transaction_content(transaction_content)
        
        # Save cleaned content
        output_path.write_text('\n'.join(cleaned_lines), encoding='utf-8')
        print(f"Saved cleaned text to: {output_path}")
    
    def _process_transaction_content(self, content):
        """Process and clean transaction content"""
        lines = content.strip().split('\n')
        cleaned_lines = []
        skip_until_date = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Handle page breaks and section markers
            if self._is_section_break(line):
                skip_until_date = True
                continue
            
            # Check for new transaction
            if self._is_transaction_start(line):
                skip_until_date = False
            
            # Add valid lines
            if not skip_until_date and not self._is_footer_line(line):
                cleaned_lines.append(line)
        
        return cleaned_lines
    
    @staticmethod
    def _is_section_break(line):
        """Check if line is a section break"""
        return any(marker in line for marker in [
            '=== PAGE BREAK ===',
            "Here's what happened in your account (continued)"
        ])
    
    @staticmethod
    def _is_transaction_start(line):
        """Check if line starts a new transaction"""
        date_pattern = r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{1,2}'
        return bool(re.match(date_pattern, line.replace(' ', '')))
    
    @staticmethod
    def _is_footer_line(line):
        """Check if line is footer information"""
        patterns = [
            r'Page\s*\d+\s*of\s*\d+',
            r'VASBS\d*',
            r'[-_]{3,}',
            r'^\d{6,}$',
            r'.*Closing\s*Balance.*'
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns)

def main():
    processor = StatementProcessor()
    processor.process_all_files()

if __name__ == "__main__":
    main()