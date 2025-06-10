import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas_ta as ta # Import and alias it for direct function calls

# --- Function to fetch the list of coins ---
@st.cache_data(ttl=86400) # Cache coin list for 24 hours as it doesn't change often
def fetch_coin_list():
    """
    Fetches the list of all supported coins from CoinGecko API.
    Returns:
        list: A list of dictionaries, each representing a coin with 'id', 'symbol', 'name'.
    """
    list_api_url = "https://api.coingecko.com/api/v3/coins/list"
    try:
        response = requests.get(list_api_url)
        response.raise_for_status()
        coins = response.json()
        return coins
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching coin list: {e}")
        return []

# --- Function to fetch historical data for a specific coin ---
@st.cache_data(ttl=3600) # Cache data for 1 hour to avoid refetching on every interaction
def fetch_data(coin_id, vs_currency, days):
    """
    Fetches historical data (prices, total_volumes) for a given coin.
    Args:
        coin_id (str): The ID of the cryptocurrency (e.g., "bitcoin", "ethereum").
        vs_currency (str): The target currency (e.g., "usd", "eur").
        days (int): Number of days of historical data.
    Returns:
        dict: The JSON response data if successful, None otherwise.
    """
    api_endpoint = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={vs_currency}&days={days}"
    try:
        response = requests.get(api_endpoint)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data for {coin_id}: {e}")
        return None

# --- Main Streamlit App Logic ---
def main():
    st.set_page_config(layout="wide") # Use wide layout for better display
    st.title('Cryptocurrency Historical Data Analysis Dashboard 📊')
    st.markdown("---")

    # --- Sidebar for user inputs ---
    st.sidebar.header("Configuration")
    
    # 1. Select Cryptocurrency
    coins_list = fetch_coin_list()
    coin_names = [coin['name'] for coin in coins_list]
    
    # Add some common coins at the top for easier selection
    common_coins = ["Bitcoin", "Ethereum", "Ripple", "Litecoin", "Cardano", "Solana", "Dogecoin", "Tron"]
    preselected_options = [name for name in common_coins if name in coin_names]
    other_options = sorted([name for name in coin_names if name not in preselected_options])
    full_dropdown_options = preselected_options + other_options

    default_coin_index = full_dropdown_options.index("Bitcoin") if "Bitcoin" in full_dropdown_options else 0
    
    selected_coin_name = st.sidebar.selectbox(
        "Select Cryptocurrency:",
        full_dropdown_options,
        index=default_coin_index 
    )
    selected_coin_id = next((coin['id'] for coin in coins_list if coin['name'] == selected_coin_name), "bitcoin")

    # 2. Select Number of Days
    days = st.sidebar.slider("Select number of days for data:", min_value=1, max_value=365, value=90, step=1)
    
    # 3. Select vs. Currency
    vs_currency = st.sidebar.selectbox("Select vs. Currency:", ["usd", "eur", "jpy", "gbp", "cad"], index=0)

    st.sidebar.markdown("---")
    st.sidebar.info("Data fetched from CoinGecko API.")

    st.write(f"Fetching data for **{selected_coin_name}** ({vs_currency.upper()}) for the last {days} days...")
    btc_data = fetch_data(selected_coin_id, vs_currency, days)

    if btc_data and 'prices' in btc_data and 'total_volumes' in btc_data:
        st.success(f"Data for {selected_coin_name} fetched successfully!")
        
        # --- Data Processing ---
        df_prices = pd.DataFrame(btc_data['prices'], columns=['timestamp_ms', 'price'])
        df_volumes = pd.DataFrame(btc_data['total_volumes'], columns=['timestamp_ms', 'volume'])
        
        df_prices['datetime'] = pd.to_datetime(df_prices['timestamp_ms'], unit='ms')
        df_volumes['datetime'] = pd.to_datetime(df_volumes['timestamp_ms'], unit='ms')
        
        df_prices.set_index('datetime', inplace=True)
        df_volumes.set_index('datetime', inplace=True)
        
        df_prices.drop('timestamp_ms', axis=1, inplace=True)
        df_volumes.drop('timestamp_ms', axis=1, inplace=True)

        df_data = pd.merge(df_prices, df_volumes, left_index=True, right_index=True, how='inner')
        
        # Calculate Hourly Returns
        df_data['hourly_return'] = df_data['price'].pct_change() * 100
        
        # Calculate Moving Averages
        df_data['SMA_10'] = df_data['price'].rolling(window=10).mean()
        df_data['SMA_30'] = df_data['price'].rolling(window=30).mean()
        
        # --- New: Calculate MACD and RSI (Direct function calls) ---
        # MACD (Moving Average Convergence Divergence)
        # We will manually concatenate the results to df_data
        macd_result = ta.macd(df_data['price'], fast=12, slow=26, signal=9)
        df_data = pd.concat([df_data, macd_result], axis=1)

        # RSI (Relative Strength Index)
        df_data['RSI_14'] = ta.rsi(df_data['price'], length=14)
        # --- End New: Calculate MACD and RSI ---
        
        # --- Display Data Info ---
        st.subheader("Raw Data Preview")
        st.dataframe(df_data.tail())
        st.info(f"DataFrame contains {len(df_data)} entries from {df_data.index.min().strftime('%Y-%m-%d %H:%M')} to {df_data.index.max().strftime('%Y-%m-%d %H:%M')}.")


        # --- Visualization Section ---
        st.subheader(f"{selected_coin_name} Price, Moving Averages & Volume Chart")
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        
        ax1.plot(df_data['price'], color='blue', linewidth=1.5, label=f'{selected_coin_name} Price')
        ax1.plot(df_data['SMA_10'], color='orange', linewidth=1, label='SMA 10h')
        ax1.plot(df_data['SMA_30'], color='red', linewidth=1, label='SMA 30h')
        
        ax1.set_title(f'{selected_coin_name} Price, Moving Averages & Volume over {days} Days ({vs_currency.upper()})', fontsize=16)
        ax1.set_ylabel(f'Price ({vs_currency.upper()})', fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.legend()

        # --- Volume Chart Enhancement ---
        # Calculate price change for dynamic volume bar coloring
        # We need to shift the price to get the previous day's close for comparison
        df_data['price_change'] = df_data['price'].diff()

        # Define colors for volume bars based on price change
        volume_bar_colors = ['green' if x > 0 else 'red' for x in df_data['price_change']]

        ax2.bar(df_data.index, df_data['volume'], color=volume_bar_colors, alpha=0.7) # Set width for better appearance
        ax2.set_title(f'{selected_coin_name} Trading Volume over {days} Days', fontsize=16)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel(f'Volume ({vs_currency.upper()})', fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.ticklabel_format(style='plain', axis='y') # Ensure plain style for large numbers on y-axis
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

        # --- Basic Statistical Analysis ---
        st.subheader(f"{selected_coin_name} Basic Statistical Analysis")
        col1, col2 = st.columns(2)

        with col1:
            st.write("#### Price Statistics:")
            st.write(df_data['price'].describe())
        
        with col2:
            st.write("#### Volume Statistics:")
            st.write(df_data['volume'].describe())
            
        # Plotting a Histogram of Hourly Returns
        st.subheader(f"Distribution of {selected_coin_name} Hourly Returns")
        fig_hist, ax_hist = plt.subplots(figsize=(10, 6))
        ax_hist.hist(df_data['hourly_return'].dropna(), bins=50, edgecolor='black', alpha=0.7)
        ax_hist.set_title(f'Distribution of {selected_coin_name} Hourly Returns (%)', fontsize=16)
        ax_hist.set_xlabel('Hourly Return (%)', fontsize=12)
        ax_hist.set_ylabel('Frequency', fontsize=12)
        ax_hist.grid(True, linestyle=':', alpha=0.6)
        plt.tight_layout()
        st.pyplot(fig_hist)


        # --- Risk Analysis (Volatility) ---
        st.subheader(f"{selected_coin_name} Risk Analysis (Volatility)")
        daily_return_std = df_data['hourly_return'].dropna().std()
        st.info(f"**Standard Deviation of Hourly Returns:** {daily_return_std:.2f}%")
        st.write("A higher Standard Deviation indicates greater volatility and risk.")

        # --- Correlation Analysis ---
        st.subheader(f"{selected_coin_name} Correlation Analysis (Autocorrelation)")
        autocorrelation_1h = df_data['hourly_return'].corr(df_data['hourly_return'].shift(1))
        st.info(f"**Autocorrelation of Hourly Returns (lag 1 hour):** {autocorrelation_1h:.4f}")
        st.write("Note: In efficient markets, autocorrelation of returns is often close to zero.")
        st.write("A positive autocorrelation suggests momentum (trend continuation).")
        st.write("A negative autocorrelation suggests mean reversion (price bouncing back).")

        # --- New: Visualization Section for MACD ---
        st.subheader(f"{selected_coin_name} MACD (Moving Average Convergence Divergence)")
        fig_macd, ax_macd = plt.subplots(figsize=(12, 6))

        # Check if MACD columns exist before plotting
        if 'MACD_12_26_9' in df_data.columns and 'MACDs_12_26_9' in df_data.columns and 'MACDh_12_26_9' in df_data.columns:
            # Plot MACD Line: Thicker, distinctive color (e.g., blue) for better visibility
            ax_macd.plot(df_data.index, df_data['MACD_12_26_9'], label='MACD Line', color='blue', linewidth=2)
            
            # Plot Signal Line: Slightly thinner, dashed, and a contrasting color (e.g., red)
            ax_macd.plot(df_data.index, df_data['MACDs_12_26_9'], label='Signal Line', color='red', linewidth=1.5, linestyle='--')
            
            # Plot Histogram: Dynamically colored based on positive (green) or negative (red) values
            # Add some transparency (alpha) so lines underneath can be seen
            bar_colors = ['green' if x >= 0 else 'red' for x in df_data['MACDh_12_26_9']]
            ax_macd.bar(df_data.index, df_data['MACDh_12_26_9'], label='Histogram', color=bar_colors, alpha=0.6)

            ax_macd.axhline(0, color='black', linestyle=':', linewidth=0.8) # Zero line for reference
            ax_macd.set_title(f'MACD for {selected_coin_name} over {days} Days', fontsize=16)
            ax_macd.set_xlabel('Date', fontsize=12)
            ax_macd.set_ylabel('MACD Value', fontsize=12)
            ax_macd.grid(True, linestyle='--', alpha=0.7) # Add a grid for better readability
            ax_macd.legend() # Display the legend for all plotted elements
            plt.xticks(rotation=45) # Rotate x-axis labels for readability
            plt.tight_layout() # Adjust plot to ensure everything fits
            st.pyplot(fig_macd) # Display the Matplotlib figure in Streamlit
        else:
            st.warning(f"  > Not enough data to calculate MACD for {selected_coin_name}.")
            plt.close(fig_macd) # Close empty plot to prevent display issues

        # --- New: Visualization Section for RSI ---
        st.subheader(f"{selected_coin_name} RSI (Relative Strength Index)")
        fig_rsi, ax_rsi = plt.subplots(figsize=(12, 6))

        if 'RSI_14' in df_data.columns: # pandas_ta creates RSI_14 by default for length=14
            ax_rsi.plot(df_data.index, df_data['RSI_14'], label='RSI (14)', color='green', linewidth=1.5)
            ax_rsi.axhline(70, color='red', linestyle='--', label='Overbought (70)', linewidth=0.8) # Overbought line
            ax_rsi.axhline(30, color='blue', linestyle='--', label='Oversold (30)', linewidth=0.8) # Oversold line
            ax_rsi.set_ylim(0, 100) # RSI values are always between 0 and 100
            ax_rsi.set_title(f'{selected_coin_name} RSI over {days} Days', fontsize=16)
            ax_rsi.set_xlabel('Date', fontsize=12)
            ax_rsi.set_ylabel('RSI Value', fontsize=12)
            ax_rsi.grid(True, linestyle='--', alpha=0.7)
            ax_rsi.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig_rsi)
        else:
            st.warning(f"  > Not enough data to calculate RSI for {selected_coin_name}.")
            plt.close(fig_rsi) # Close empty plot to prevent display issues


        # --- Automated Analysis Commentary ---
        st.subheader(f"{selected_coin_name} Automated Market Analysis 🤖")
        
        st.markdown("---") 

        st.markdown("##### Volatility Analysis:")
        if daily_return_std > 0.5:
            st.write(f"  **> {selected_coin_name} has shown HIGH volatility** in hourly returns ({daily_return_std:.2f}%). This indicates significant price swings and higher risk/reward opportunities.")
        elif daily_return_std > 0.2:
            st.write(f"  **> {selected_coin_name} has shown MODERATE volatility** in hourly returns ({daily_return_std:.2f}%). This suggests notable price movements.")
        else:
            st.write(f"  **> {selected_coin_name} has shown LOW volatility** in hourly returns ({daily_return_std:.2f}%). Price movements have been relatively stable.")

        st.markdown("##### Trend Analysis (based on Moving Averages):")
        # Check if SMAs have enough data before commenting
        if not df_data['SMA_10'].isnull().all() and not df_data['SMA_30'].isnull().all() and len(df_data) >= 30:
            if df_data['SMA_10'].iloc[-1] > df_data['SMA_30'].iloc[-1]:
                if df_data['price'].iloc[-1] > df_data['SMA_10'].iloc[-1]:
                    st.success(f"  **> {selected_coin_name} appears to be in an UPTREND.** The short-term Moving Average (SMA 10h) is above the long-term Moving Average (SMA 30h), and the price is currently above both MAs, suggesting bullish momentum.")
                else:
                    st.info(f"  **> {selected_coin_name} is in a POTENTIAL UPTREND.** While the short-term Moving Average (SMA 10h) is above the long-term (SMA 30h), the price is currently below the short-term MA, which might indicate a temporary pullback or consolidation within the uptrend.")
            elif df_data['SMA_10'].iloc[-1] < df_data['SMA_30'].iloc[-1]:
                if df_data['price'].iloc[-1] < df_data['SMA_10'].iloc[-1]:
                    st.error(f"  **> {selected_coin_name} appears to be in a DOWNTREND.** The short-term Moving Average (SMA 10h) is below the long-term Moving Average (SMA 30h), and the price is currently below both MAs, suggesting bearish momentum.")
                else:
                    st.warning(f"  **> {selected_coin_name} is in a POTENTIAL DOWNTREND.** While the short-term Moving Average (SMA 10h) is below the long-term (SMA 30h), the price is currently above the short-term MA, which might indicate a temporary rebound or consolidation within the downtrend.")
            else:
                st.warning(f"  **> {selected_coin_name} is currently in a SIDEWAYS or CONSOLIDATION phase.** Moving Averages are intertwined, suggesting a lack of clear trend.")
        else:
            st.warning(f"  > Not enough data for {selected_coin_name} to calculate Moving Averages and determine a clear trend for comment.")


        # --- MACD Analysis Commentary ---
        st.markdown("##### MACD Analysis:")
        # Check if MACD values exist before commenting
        if 'MACD_12_26_9' in df_data.columns and 'MACDs_12_26_9' in df_data.columns and len(df_data) >= 26: # MACD needs 26+ data points
            last_macd = df_data['MACD_12_26_9'].iloc[-1]
            last_signal = df_data['MACDs_12_26_9'].iloc[-1]
            
            # Check for MACD Crossover
            # Check if MACD crossed above Signal (bullish)
            if last_macd > last_signal and (df_data['MACD_12_26_9'].iloc[-2] <= df_data['MACDs_12_26_9'].iloc[-2] if len(df_data) >= 2 else True):
                st.success(f"  **> MACD Bullish Crossover:** The MACD line for {selected_coin_name} has just crossed ABOVE the signal line, suggesting potential **upward momentum**.")
            # Check if MACD crossed below Signal (bearish)
            elif last_macd < last_signal and (df_data['MACD_12_26_9'].iloc[-2] >= df_data['MACDs_12_26_9'].iloc[-2] if len(df_data) >= 2 else True):
                st.error(f"  **> MACD Bearish Crossover:** The MACD line for {selected_coin_name} has just crossed BELOW the signal line, suggesting potential **downward momentum**.")
            elif last_macd > last_signal:
                st.info(f"  **> MACD is bullish:** The MACD line for {selected_coin_name} is currently above its signal line, indicating **bullish momentum**.")
            elif last_macd < last_signal:
                st.warning(f"  **> MACD is bearish:** The MACD line for {selected_coin_name} is currently below its signal line, indicating **bearish momentum**.")
            else:
                st.info(f"  > MACD for {selected_coin_name} is flat or near the signal line, suggesting **neutral momentum**.")
            
            # Check for MACD above/below zero line
            if last_macd > 0:
                st.info(f"  > MACD is currently above the zero line, reinforcing **bullish momentum**.")
            elif last_macd < 0:
                st.info(f"  > MACD is currently below the zero line, reinforcing **bearish momentum**.")
        else:
            st.warning(f"  > Not enough data to calculate MACD for {selected_coin_name}.")

        # --- RSI Analysis Commentary ---
        st.markdown("##### RSI Analysis:")
        if 'RSI_14' in df_data.columns and not df_data['RSI_14'].isnull().all() and len(df_data) >= 14: # RSI needs 14+ data points
            last_rsi = df_data['RSI_14'].iloc[-1]
            
            if last_rsi >= 70:
                st.warning(f"  **> RSI for {selected_coin_name} ({last_rsi:.2f}) is in the OVERBOUGHT zone (>=70).** This may indicate a temporary top and potential for a pullback.")
            elif last_rsi <= 30:
                st.success(f"  **> RSI for {selected_coin_name} ({last_rsi:.2f}) is in the OVERSOLD zone (<=30).** This may indicate a temporary bottom and potential for a rebound.")
            else:
                st.info(f"  > RSI for {selected_coin_name} ({last_rsi:.2f}) is in the **neutral zone** (between 30 and 70), suggesting no immediate overbought/oversold conditions.")
        else:
            st.warning(f"  > Not enough data to calculate RSI for {selected_coin_name}.")


        # --- Volume Analysis Commentary ---
        st.markdown("##### Volume Analysis:")
        avg_volume = df_data['volume'].mean()
        last_volume = df_data['volume'].iloc[-1]
        if last_volume > avg_volume * 1.5: 
            st.success(f"  **> Current trading volume for {selected_coin_name} ({last_volume:.2e}) is significantly HIGHER** than the average volume ({avg_volume:.2e}). This often accompanies strong price movements, confirming the current trend or indicating high market interest.")
        elif last_volume < avg_volume * 0.5: 
            st.warning(f"  **> Current trading volume for {selected_coin_name} ({last_volume:.2e}) is significantly LOWER** than the average volume ({avg_volume:.2e}). This may indicate a lack of strong conviction behind recent price movements or a quiet period.")
        else:
            st.info(f"  **> Current trading volume for {selected_coin_name} ({last_volume:.2e}) is in line** with the average volume ({avg_volume:.2e}).")

        # --- Autocorrelation Analysis Commentary ---
        st.markdown("##### Autocorrelation Analysis:")
        # Ensure enough data for autocorrelation
        if not df_data['hourly_return'].isnull().all() and len(df_data) >= 2:
            autocorrelation_1h = df_data['hourly_return'].corr(df_data['hourly_return'].shift(1))
            if abs(autocorrelation_1h) < 0.05: 
                st.info(f"  **> The hourly returns for {selected_coin_name} show VERY LOW autocorrelation** ({autocorrelation_1h:.4f}). This suggests that past hourly price movements are not a strong predictor of future hourly movements, which aligns with the weak form of the Efficient Market Hypothesis.")
            elif autocorrelation_1h > 0.05:
                st.warning(f"  **> The hourly returns for {selected_coin_name} show a POSITIVE autocorrelation** ({autocorrelation_1h:.4f}). This could indicate some momentum or trend continuation in the short-term.")
            elif autocorrelation_1h < -0.05:
                st.warning(f"  **> The hourly returns for {selected_coin_name} show a NEGATIVE autocorrelation** ({autocorrelation_1h:.4f}). This could indicate some mean reversion in the short-term (prices tending to bounce back).")
        else:
            st.warning(f"  > Not enough data to calculate Autocorrelation for {selected_coin_name}.")
        # --- End of Automated Analysis Commentary ---

    else:
        st.error(f"Failed to retrieve data for {selected_coin_name}. Please check the API status, your internet connection, or try a different coin/timeframe.")

# Run the Streamlit app
if __name__ == "__main__":
    main()