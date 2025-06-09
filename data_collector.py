import requests
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

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
    # for the last 90 days in USD from CoinGecko API.
    # The 'id' for Bitcoin is 'bitcoin'.
    # 'vs_currency' is 'usd'.
    # 'days' is '90'.
    # CoinGecko's market_chart endpoint already includes prices, market_caps, and total_volumes.
    api_endpoint = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=90"

    print(f"Fetching data from: {api_endpoint}")
    btc_data = fetch_data(api_endpoint)

    if btc_data and 'prices' in btc_data and 'total_volumes' in btc_data: # Ensure 'total_volumes' is also present
        print("\nData fetched successfully!")
        
        # 1. Create Pandas DataFrames from 'prices' and 'total_volumes' data.
        # Each list contains sub-lists: [timestamp_ms, value].
        df_prices = pd.DataFrame(btc_data['prices'], columns=['timestamp_ms', 'price'])
        df_volumes = pd.DataFrame(btc_data['total_volumes'], columns=['timestamp_ms', 'volume']) # Create DataFrame for volumes
        
        # 2. Convert milliseconds timestamp to datetime objects for both.
        df_prices['datetime'] = pd.to_datetime(df_prices['timestamp_ms'], unit='ms')
        df_volumes['datetime'] = pd.to_datetime(df_volumes['timestamp_ms'], unit='ms')
        
        # 3. Set 'datetime' as the DataFrame index for time-series analysis for both.
        df_prices.set_index('datetime', inplace=True)
        df_volumes.set_index('datetime', inplace=True)
        
        # 4. Drop the original 'timestamp_ms' column as it's no longer needed for both.
        df_prices.drop('timestamp_ms', axis=1, inplace=True)
        df_volumes.drop('timestamp_ms', axis=1, inplace=True)

        # 5. Merge prices and volumes into a single DataFrame based on their shared datetime index
        # This will be our main DataFrame for analysis.
        df_data = pd.merge(df_prices, df_volumes, left_index=True, right_index=True, how='inner')
        
        # --- Displaying the last 5 rows of the processed DataFrame ---
        print("\nLast 5 rows of the processed DataFrame (with price and volume):")
        print(df_data.tail()) # Using .tail() to show the last 5 entries
        
        print(f"\nDataFrame Information:")
        print(df_data.info())

        # --- Start of Basic Statistical Analysis Section ---
        print("\n--- Basic Statistical Analysis ---")

        # 1. Calculate and display Descriptive Statistics for Price
        print("\nDescriptive Statistics for Bitcoin Price:")
        print(df_data['price'].describe())

        # 2. Calculate and display Descriptive Statistics for Volume
        print("\nDescriptive Statistics for Bitcoin Volume:")
        print(df_data['volume'].describe())

        # 3. Calculate Hourly Returns
        df_data['hourly_return'] = df_data['price'].pct_change() * 100 # Changed to hourly_return
        
        print("\nFirst 5 rows of DataFrame with Hourly Returns:")
        print(df_data.head())

        print("\nLast 5 rows of DataFrame with Hourly Returns:")
        print(df_data.tail())

        # 4. Plotting a Histogram of Hourly Returns
        print("\nPlotting Histogram of Hourly Returns...")
        plt.figure(figsize=(10, 6))
        plt.hist(df_data['hourly_return'].dropna(), bins=50, edgecolor='black', alpha=0.7)
        plt.title('Distribution of Bitcoin Hourly Returns (%)', fontsize=16) 
        plt.xlabel('Hourly Return (%)', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.tight_layout()
        plt.savefig('bitcoin_hourly_returns_histogram.png') 
        print("Bitcoin hourly returns histogram saved as 'bitcoin_hourly_returns_histogram.png'")
        plt.show()
        # --- End of Basic Statistical Analysis Section ---
        
        # --- Start of Risk Analysis (Volatility) Section ---
        print("\n--- Risk Analysis (Volatility) ---")
        daily_return_std = df_data['hourly_return'].dropna().std() # Using hourly_return
        print(f"\nStandard Deviation of Hourly Returns: {daily_return_std:.2f}%")
        print("Note: This is the standard deviation of hourly return percentage.")
        print("A higher Standard Deviation indicates greater volatility and risk.")
        # --- End of Risk Analysis (Volatility) Section ---

        # --- Start of Correlation Analysis Section ---
        print("\n--- Correlation Analysis (Autocorrelation) ---")
        autocorrelation_1h = df_data['hourly_return'].corr(df_data['hourly_return'].shift(1)) # Using hourly_return
        print(f"Autocorrelation of Hourly Returns (lag 1 hour): {autocorrelation_1h:.4f}")
        print("Note: In efficient markets, autocorrelation of returns is often close to zero.")
        print("A positive autocorrelation suggests momentum (trend continuation).")
        print("A negative autocorrelation suggests mean reversion (price bouncing back).")
        # --- End of Correlation Analysis Section ---

        # --- Start of Moving Averages Calculation ---
        print("\n--- Calculating Moving Averages ---")
        df_data['SMA_10'] = df_data['price'].rolling(window=10).mean()
        df_data['SMA_30'] = df_data['price'].rolling(window=30).mean()
        print("Moving Averages (SMA_10 and SMA_30) calculated successfully.")
        print("First few rows with SMAs:")
        print(df_data[['price', 'SMA_10', 'SMA_30']].head(35))
        # --- End of Moving Averages Calculation ---

        # --- Start of Automated Analysis Commentary ---
        print("\n--- Automated Market Analysis ---")

        # 1. Volatility Analysis Commentary
        print("\n**Volatility Analysis:**")
        if daily_return_std > 0.5:
            print(f"  > Bitcoin has shown HIGH volatility in hourly returns ({daily_return_std:.2f}%). This indicates significant price swings and higher risk/reward opportunities.")
        elif daily_return_std > 0.2:
            print(f"  > Bitcoin has shown MODERATE volatility in hourly returns ({daily_return_std:.2f}%). This suggests notable price movements.")
        else:
            print(f"  > Bitcoin has shown LOW volatility in hourly returns ({daily_return_std:.2f}%). Price movements have been relatively stable.")

        # 2. Trend Analysis Commentary (ensuring SMAs are calculated)
        print("\n**Trend Analysis (based on Moving Averages):**")
        # Check for NaN values before accessing iloc[-1] in case DataFrame is too short for SMAs
        if not df_data['SMA_10'].isnull().all() and not df_data['SMA_30'].isnull().all():
            if df_data['SMA_10'].iloc[-1] > df_data['SMA_30'].iloc[-1]:
                if df_data['price'].iloc[-1] > df_data['SMA_10'].iloc[-1]:
                    print("  > Bitcoin appears to be in an UPTREND. The short-term Moving Average (SMA 10h) is above the long-term Moving Average (SMA 30h), and the price is currently above both MAs, suggesting bullish momentum.")
                else:
                    print("  > Bitcoin is in a POTENTIAL UPTREND. While the short-term Moving Average (SMA 10h) is above the long-term (SMA 30h), the price is currently below the short-term MA, which might indicate a temporary pullback or consolidation within the uptrend.")
            elif df_data['SMA_10'].iloc[-1] < df_data['SMA_30'].iloc[-1]:
                if df_data['price'].iloc[-1] < df_data['SMA_10'].iloc[-1]:
                    print("  > Bitcoin appears to be in a DOWNTREND. The short-term Moving Average (SMA 10h) is below the long-term Moving Average (SMA 30h), and the price is currently below both MAs, suggesting bearish momentum.")
                else:
                    print("  > Bitcoin is in a POTENTIAL DOWNTREND. While the short-term Moving Average (SMA 10h) is below the long-term (SMA 30h), the price is currently above the short-term MA, which might indicate a temporary rebound or consolidation within the downtrend.")
            else:
                print("  > Bitcoin is currently in a SIDEWAYS or CONSOLIDATION phase. Moving Averages are intertwined, suggesting a lack of clear trend.")
        else:
            print("  > Not enough data to calculate Moving Averages and determine a clear trend.")


        # 3. Volume Analysis Commentary
        print("\n**Volume Analysis:**")
        avg_volume = df_data['volume'].mean()
        last_volume = df_data['volume'].iloc[-1]
        if last_volume > avg_volume * 1.5: 
            print(f"  > Current trading volume ({last_volume:.2e}) is significantly HIGHER than the average volume ({avg_volume:.2e}). This often accompanies strong price movements, confirming the current trend or indicating high market interest.")
        elif last_volume < avg_volume * 0.5: 
            print(f"  > Current trading volume ({last_volume:.2e}) is significantly LOWER than the average volume ({avg_volume:.2e}). This may indicate a lack of strong conviction behind recent price movements or a quiet period.")
        else:
            print(f"  > Current trading volume ({last_volume:.2e}) is in line with the average volume ({avg_volume:.2e}).")

        # 4. Autocorrelation Commentary
        print("\n**Autocorrelation Analysis:**")
        if abs(autocorrelation_1h) < 0.05: 
            print(f"  > The hourly returns show VERY LOW autocorrelation ({autocorrelation_1h:.4f}). This suggests that past hourly price movements are not a strong predictor of future hourly movements, which aligns with the weak form of the Efficient Market Hypothesis.")
        elif autocorrelation_1h > 0.05:
            print(f"  > The hourly returns show a POSITIVE autocorrelation ({autocorrelation_1h:.4f}). This could indicate some momentum or trend continuation in the short-term.")
        elif autocorrelation_1h < -0.05:
            print(f"  > The hourly returns show a NEGATIVE autocorrelation ({autocorrelation_1h:.4f}). This could indicate some mean reversion in the short-term (prices tending to bounce back).")
        # --- End of Automated Analysis Commentary ---


        # --- Start of Visualization Section (Updated for Volume and Moving Averages) ---
        print("\nPlotting Bitcoin Price, Volume and Moving Averages Chart...")

        # Create a figure with two subplots: one for price/MAs, one for volume
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        
        # Plot the 'price' on the first subplot
        ax1.plot(df_data['price'], color='blue', linewidth=1.5, label='Bitcoin Price')
        
        # Plot the Moving Averages on the first subplot (on top of price)
        ax1.plot(df_data['SMA_10'], color='orange', linewidth=1, label='SMA 10h')
        ax1.plot(df_data['SMA_30'], color='red', linewidth=1, label='SMA 30h')
        
        ax1.set_title('Bitcoin Price, Moving Averages & Volume over 90 Days (USD)', fontsize=16)
        ax1.set_ylabel('Price (USD)', fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.legend() # Add legend to show what each line represents

        # Plot the 'volume' on the second subplot
        ax2.bar(df_data.index, df_data['volume'], color='grey', alpha=0.7)
        ax2.set_title('Bitcoin Trading Volume over 90 Days', fontsize=16)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Volume (USD)', fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.ticklabel_format(style='plain', axis='y') # Prevent scientific notation for volume if numbers are large

        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('bitcoin_price_volume_and_MAS_chart.png') 
        print("Bitcoin price, volume and Moving Averages chart saved as 'bitcoin_price_volume_and_MAS_chart.png'")
        plt.show()
        # --- End of Visualization Section ---

        # --- Start of Data Saving Section ---
        csv_file_path = 'btc_historical_data.csv' 

        # Save the DataFrame (now df_data) to a CSV file
        df_data.to_csv(csv_file_path, index=True)
        print(f"\nDataFrame successfully saved to {csv_file_path}")

        # --- Optional: Verify by loading the data back ---
        try:
            print("\nVerifying CSV by loading it back...")
            df_loaded = pd.read_csv(csv_file_path, parse_dates=True, index_col=0)
            print("First 5 rows of the loaded DataFrame:")
            print(df_loaded.head())
            print(f"Loaded DataFrame Info:")
            df_loaded.info()
        except Exception as e:
            print(f"Error loading CSV for verification: {e}")
        # --- End of Data Saving Section ---

    else:
        print("Failed to fetch data or required keys ('prices', 'total_volumes') not found in the response.")