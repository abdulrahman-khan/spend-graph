import pandas as pd
from pathlib import Path

def compile_csv_files():
    """Combine all CSV files from csv-statements into DATA/EXPORT.csv"""
    # Setup paths
    csv_dir = Path('csv-statements')
    data_dir = Path('DATA')
    data_dir.mkdir(exist_ok=True)  # Create DATA directory if it doesn't exist
    output_file = data_dir / 'EXPORT.csv'
    
    # Get list of all CSV files from csv-statements
    csv_files = [f for f in csv_dir.glob('*.csv')]
    
    if not csv_files:
        print("No CSV files found in csv-statements directory")
        return
        
    print("Found CSV files:")
    for file in csv_files:
        print(f"  - {file.name}")
    
    # Read and combine all CSV files
    dfs = []
    for file in csv_files:
        print(f"\nReading: {file.name}")
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