import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import glob

def load_and_clean_data():
    """Load all CSV files and combine them into one DataFrame"""
    # Get all CSV files in the directory
    csv_files = glob.glob('csv-statements/*.csv')
    
    # Read and combine all CSV files
    dfs = []
    for file in csv_files:
        df = pd.read_csv(file)
        dfs.append(df)
    
    # Combine all DataFrames
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Convert date columns to datetime
    combined_df['date'] = pd.to_datetime(combined_df[['year', 'month', 'date']].astype(str).agg('-'.join, axis=1))
    
    # Sort by date
    combined_df = combined_df.sort_values('date')
    
    # Fill NaN values with 0 for withdrawal and deposit columns
    combined_df['withdrawal'] = combined_df['withdrawal'].fillna(0)
    combined_df['deposit'] = combined_df['deposit'].fillna(0)
    
    return combined_df

def create_graphs(df):
    """Create various graphs from the data"""
    # Set the style
    plt.style.use('fivethirtyeight')
    
    # Create a figure with multiple subplots
    fig = plt.figure(figsize=(15, 20))  # Adjusted height
    
    # 1. Balance over time
    plt.subplot(4, 1, 1)  # Changed to 4,1 since we removed one plot
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
    current_month = df['date'].max().strftime('%B %Y')
    current_month_data = df[
        (df['date'].dt.month == df['date'].max().month) & 
        (df['date'].dt.year == df['date'].max().year) &
        (df['withdrawal'] > 0)
    ]
    
    top_expenses = current_month_data.nlargest(5, 'withdrawal')[['date', 'description', 'withdrawal']]
    
    # Create table data
    table_data = []
    for _, row in top_expenses.iterrows():
        table_data.append([
            row['date'].strftime('%B %d'),
            row['description'][:30] + '...' if len(row['description']) > 30 else row['description'],
            f"${row['withdrawal']:,.2f}"
        ])
    
    # Create table
    plt.table(
        cellText=table_data,
        colLabels=['Date', 'Description', 'Amount'],
        cellLoc='center',
        loc='center',
        colWidths=[0.2, 0.6, 0.2],
        bbox=[0, 0, 1, 0.8]  # [left, bottom, width, height]
    )
    
    plt.title(f'Top 5 Highest Expenses - {current_month}')
    plt.axis('off')  # Hide axes for table
    
    # Adjust layout and display
    plt.tight_layout()
    
    # Save the figure
    plt.savefig('financial_analysis.png', dpi=300, bbox_inches='tight')
    print("Graphs have been saved as 'financial_analysis.png'")
    
    # Generate summary statistics
    print("\nSummary Statistics:")
    print(f"Total Deposits: ${df['deposit'].sum():,.2f}")
    print(f"Total Withdrawals: ${df['withdrawal'].sum():,.2f}")
    print(f"Net Change: ${(df['deposit'].sum() - df['withdrawal'].sum()):,.2f}")
    print(f"Average Balance: ${df['balance'].mean():,.2f}")
    print(f"Number of Transactions: {len(df)}")

def main():
    try:
        # Load and clean data
        print("Loading and cleaning data...")
        df = load_and_clean_data()
        
        # Create graphs
        print("Creating graphs...")
        create_graphs(df)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 