import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def load_and_clean_data():
    """Load EXPORT.csv from DATA folder"""
    # Setup path to EXPORT.csv
    data_file = Path('DATA/EXPORT.csv')
    
    if not data_file.exists():
        raise FileNotFoundError("EXPORT.csv not found in DATA folder. Please run compiler.py first.")
    
    # Read the CSV file
    df = pd.read_csv(data_file)
    
    # Convert date columns to datetime
    df['date'] = pd.to_datetime(df[['year', 'month', 'date']].astype(str).agg('-'.join, axis=1))
    
    # Sort by date
    df = df.sort_values('date')
    
    # Fill NaN values with 0 for withdrawal and deposit columns
    df['withdrawal'] = df['withdrawal'].fillna(0)
    df['deposit'] = df['deposit'].fillna(0)
    
    return df

def create_graphs(df):
    """Create various graphs from the data"""
    # Set the style
    plt.style.use('fivethirtyeight')
    
    # Create a figure with multiple subplots
    fig = plt.figure(figsize=(15, 20))
    
    # 1. Balance over time
    plt.subplot(4, 1, 1)
    plt.plot(df['date'], df['balance'], label='Balance', color='blue')
    plt.title('Account Balance Over Time')
    plt.xlabel('Date')
    plt.ylabel('Balance ($)')
    plt.grid(True)
    
    # 2. Deposits and Withdrawals
    plt.subplot(4, 1, 2)
    plt.plot(df['date'], df['deposit'], label='Deposits', color='green')
    plt.plot(df['date'], df['withdrawal'], label='Withdrawals', color='red')
    plt.title('Deposits and Withdrawals Over Time')
    plt.xlabel('Date')
    plt.ylabel('Amount ($)')
    plt.legend()
    plt.grid(True)
    
    # 3. Monthly Net Cash Flow
    monthly_net = df.groupby(df['date'].dt.to_period('M')).agg({
        'deposit': 'sum',
        'withdrawal': 'sum'
    })
    monthly_net['net'] = monthly_net['deposit'] - monthly_net['withdrawal']
    
    plt.subplot(4, 1, 3)
    monthly_net['net'].plot(kind='bar')
    plt.title('Monthly Net Cash Flow')
    plt.xlabel('Month')
    plt.ylabel('Net Amount ($)')
    plt.xticks(rotation=45)
    plt.grid(True)
    
    # 4. Top 5 Expenses Table
    plt.subplot(4, 1, 4)
    
    # Get top expenses from entire dataset
    all_expenses = df[df['withdrawal'] > 0]
    top_expenses = all_expenses.nlargest(5, 'withdrawal')[['date', 'description', 'withdrawal']]
    
    # Create table data
    table_data = []
    for _, row in top_expenses.iterrows():
        table_data.append([
            row['date'].strftime('%B %d, %Y'),  # Added year to date
            row['description'],  # Remove truncation
            f"${row['withdrawal']:,.2f}"
        ])
    
    # Create table with adjusted column widths
    plt.table(
        cellText=table_data,
        colLabels=['Date', 'Description', 'Amount'],
        cellLoc='center',
        loc='center',
        colWidths=[0.2, 1.0, 0.2],  # Made description column wider
        bbox=[0, 0, 1.4, 0.8]  # Increased overall width
    )
    
    plt.title('Top 5 Highest Expenses - All Time')
    plt.axis('off')
    
    # Adjust layout and display
    plt.tight_layout()
    
    # Save the figure to DATA folder
    output_file = Path('DATA/financial_analysis.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nGraphs have been saved as '{output_file}'")

def main():
    try:
        # Load and clean data
        print("Loading and cleaning data from EXPORT.csv...")
        df = load_and_clean_data()
        
        # Create graphs
        print("Creating graphs...")
        create_graphs(df)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 