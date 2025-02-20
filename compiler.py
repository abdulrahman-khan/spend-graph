import pandas as pd
from pathlib import Path
import shutil

def clean_data_directory():
    """Remove and recreate DATA directory"""
    data_dir = Path('DATA')
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir()
    print("Cleaned DATA directory")

def compile_csv_files():
    """Combine all CSV files from csv-statements into DATA/EXPORT.csv"""
    # Clean DATA directory first
    clean_data_directory()
    
    # Setup paths
    csv_dir = Path('csv-statements')
    data_dir = Path('DATA')
    output_file = data_dir / 'EXPORT.csv'
    
    # Get list of all CSV files recursively from csv-statements
    csv_files = list(csv_dir.rglob('*.csv'))
    
    if not csv_files:
        print("No CSV files found in csv-statements directory")
        return
        
    print("Found CSV files:")
    for file in csv_files:
        print(f"  - {file}")
    
    # Read and combine all CSV files
    dfs = []
    for file in csv_files:
        print(f"\nReading: {file}")
        df = pd.read_csv(file)
        dfs.append(df)
    
    # Combine all dataframes
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Sort by date
    combined_df['date_sort'] = pd.to_datetime(
        combined_df['year'].astype(str) + '-' + 
        combined_df['month'] + '-' + 
        combined_df['date'].astype(str)
    )
    combined_df = combined_df.sort_values('date_sort')
    combined_df = combined_df.drop('date_sort', axis=1)
    
    # Save to DATA/EXPORT.csv
    combined_df.to_csv(output_file, index=False)
    print(f"\nCreated: {output_file}")
    print(f"Total transactions: {len(combined_df)}")

if __name__ == "__main__":
    compile_csv_files()