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
    plt.style.use('fivethirtyeight')  # Using a built-in matplotlib style
    
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
    
    # 4. Transaction Types Distribution
    plt.subplot(4, 1, 4)
    transaction_types = df['description'].str.extract(r'(Payrolldep|Pointofsalepurchase|GST|Opening Balance)')[0]
    transaction_counts = transaction_types.value_counts()
    plt.pie(transaction_counts, labels=transaction_counts.index, autopct='%1.1f%%')
    plt.title('Transaction Type Distribution')
    
    # Adjust layout and display
    plt.tight_layout()
    
    # Save the figure
    plt.savefig('financial_analysis.png')
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