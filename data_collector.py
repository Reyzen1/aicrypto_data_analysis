import requests
import pandas as pd

def fetch_data(api_url):
    """
    Fetches data from a given API URL.

    Args:
        api_url (str): The URL of the API endpoint.

    Returns:
        dict: The JSON response data if successful, None otherwise.
    """
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

if __name__ == "__main__":
    # URL for fetching historical BTC data (prices, market_caps, total_volumes)
    # for the last 90 days in USDT from CoinGecko API.
    # The 'id' for Bitcoin is 'bitcoin'.
    # 'vs_currency' is 'usdt'. (CHANGED FROM USD TO USDT)
    # 'days' is '90'.
    api_endpoint = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=90"

    print(f"Fetching data from: {api_endpoint}")
    btc_data = fetch_data(api_endpoint)

    if btc_data and 'prices' in btc_data:
        print("\nData fetched successfully!")
        
        # 1. Create a Pandas DataFrame from the 'prices' data.
        # The 'prices' list contains sub-lists, each with [timestamp_ms, price].
        df_prices = pd.DataFrame(btc_data['prices'], columns=['timestamp_ms', 'price'])
        
        # 2. Convert milliseconds timestamp to datetime objects.
        # We divide by 1000 to convert from milliseconds to seconds, then use pd.to_datetime.
        df_prices['datetime'] = pd.to_datetime(df_prices['timestamp_ms'], unit='ms')
        
        # 3. Set 'datetime' as the DataFrame index for time-series analysis.
        # 'inplace=True' modifies the DataFrame directly without returning a new one.
        df_prices.set_index('datetime', inplace=True)
        
        # 4. Drop the original 'timestamp_ms' column as it's no longer needed.
        # 'axis=1' indicates that we are dropping a column.
        df_prices.drop('timestamp_ms', axis=1, inplace=True)
        
        # --- Displaying the last 5 rows of the processed DataFrame (CHANGED FROM HEAD TO TAIL) ---
        print("\nLast 5 rows of the processed DataFrame:")
        print(df_prices.tail()) # Using .tail() to show the last 5 entries
        
        print(f"\nDataFrame Information:")
        # df.info() provides a concise summary of the DataFrame, including data types and non-null values.
        print(df_prices.info())

        # You can extend this to process 'market_caps' and 'total_volumes' similarly if needed.
        # For example:
        # df_market_caps = pd.DataFrame(btc_data['market_caps'], columns=['timestamp_ms', 'market_cap'])
        # df_market_caps['datetime'] = pd.to_datetime(df_market_caps['timestamp_ms'], unit='ms')
        # df_market_caps.set_index('datetime', inplace=True)
        # df_market_caps.drop('timestamp_ms', axis=1, inplace=True)
        # print("\nFirst 5 rows of Market Caps DataFrame:")
        # print(df_market_caps.head())

        # --- Start of Visualization Section ---
        import matplotlib.pyplot as plt # Import Matplotlib

        print("\nPlotting Bitcoin Price Chart...")

        # Create a figure and a set of subplots
        plt.figure(figsize=(12, 6)) # Set the figure size (width, height) for better readability

        # Plot the 'price' column from df_prices
        # The index (datetime) will automatically be used for the x-axis
        plt.plot(df_prices['price'], color='blue', linewidth=1.5)

        # Add titles and labels for clarity
        plt.title('Bitcoin Price over the Last 90 Days (USD)', fontsize=16)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Price (USD)', fontsize=12)

        # Add grid for easier reading of values
        plt.grid(True, linestyle='--', alpha=0.7)

        # Customize x-axis ticks to show dates clearly
        plt.xticks(rotation=45) # Rotate date labels for better readability
        plt.tight_layout() # Adjust layout to prevent labels from overlapping

        # Save the plot to a file (optional, but good practice)
        plt.savefig('bitcoin_price_chart.png')
        print("Bitcoin price chart saved as 'bitcoin_price_chart.png'")

        # Display the plot
        plt.show()
        # --- End of Visualization Section ---

        # --- Start of Data Saving Section ---
        # Define the file path for saving the CSV
        csv_file_path = 'btc_historical_prices.csv'

        # Save the DataFrame to a CSV file
        # index=True means the datetime index will be saved as a column in the CSV.
        # This is usually desired for time-series data.
        df_prices.to_csv(csv_file_path, index=True)

        print(f"\nDataFrame successfully saved to {csv_file_path}")

        # --- Optional: Verify by loading the data back ---
        try:
            print("\nVerifying CSV by loading it back...")
            # Load the CSV back into a new DataFrame
            # parse_dates=True converts the index column (which was datetime) back to datetime objects.
            # index_col=0 specifies that the first column (our datetime index) should be used as the index.
            df_loaded = pd.read_csv(csv_file_path, parse_dates=True, index_col=0)
            print("First 5 rows of the loaded DataFrame:")
            print(df_loaded.head())
            print(f"Loaded DataFrame Info:")
            df_loaded.info()
        except Exception as e:
            print(f"Error loading CSV for verification: {e}")
        # --- End of Data Saving Section ---

        # --- Start of Basic Statistical Analysis Section ---
        print("\n--- Basic Statistical Analysis ---")

        # 1. Calculate and display Descriptive Statistics
        # .describe() provides a summary of the central tendency, dispersion, and shape of a dataset's distribution.
        # It includes count, mean, std, min, 25%, 50%, 75%, max.
        print("\nDescriptive Statistics for Bitcoin Price:")
        print(df_prices['price'].describe())

        # 2. Calculate Daily Returns
        # .pct_change() calculates the percentage change between the current and a prior element.
        # This is useful for financial data to see daily gains or losses.
        # We fill NaN (Not a Number) created by the first row (no prior element) with 0.
        df_prices['daily_return'] = df_prices['price'].pct_change() * 100 # Multiply by 100 for percentage
        
        print("\nFirst 5 rows of DataFrame with Daily Returns:")
        print(df_prices.head()) # Show head to see the NaN in the first row

        print("\nLast 5 rows of DataFrame with Daily Returns:")
        print(df_prices.tail()) # Show tail to see actual daily returns

        # 3. Plotting a Histogram of Daily Returns
        print("\nPlotting Histogram of Daily Returns...")
        plt.figure(figsize=(10, 6)) # New figure for the histogram

        # .hist() creates a histogram.
        # bins: number of bins for the histogram. More bins give more detail.
        # edgecolor: color of the edges of the bars.
        # alpha: transparency of the bars.
        plt.hist(df_prices['daily_return'].dropna(), bins=50, edgecolor='black', alpha=0.7) # .dropna() removes NaN for plotting

        plt.title('Distribution of Bitcoin Daily Returns (%)', fontsize=16)
        plt.xlabel('Daily Return (%)', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.tight_layout()

        # Save the histogram plot
        plt.savefig('bitcoin_daily_returns_histogram.png')
        print("Bitcoin daily returns histogram saved as 'bitcoin_daily_returns_histogram.png'")

        # Display the histogram
        plt.show()
        # --- End of Basic Statistical Analysis Section ---

    else:
        print("Failed to fetch data or 'prices' key not found in the response.")