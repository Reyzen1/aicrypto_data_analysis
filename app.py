import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas_ta as ta
import time

# --- Function to fetch the list of coins ---
@st.cache_data(ttl=86400)  # Cache coin list for 24 hours as it doesn't change often
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

# --- Low-level function to make an API call with rate limiting ---
def _api_call_with_rate_limit(coin_id, vs_currency, days):
    """
    Makes the actual CoinGecko API call, applying the rate limiting delay.
    This function is intended to be called by higher-level caching logic.
    """
    MIN_TIME_BETWEEN_CALLS = 2.5 # Minimum time in seconds between API calls

    current_time = time.time()
    if 'last_api_call_time' not in st.session_state:
        st.session_state.last_api_call_time = 0 

    time_since_last_call = current_time - st.session_state.last_api_call_time

    if time_since_last_call < MIN_TIME_BETWEEN_CALLS:
        sleep_duration = MIN_TIME_BETWEEN_CALLS - time_since_last_call
        st.info(f"⏳ Rate limit: Waiting for **{sleep_duration:.2f} seconds** before making API call for {days} days.")
        time.sleep(sleep_duration)

    api_endpoint = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={vs_currency}&days={days}"
    try:
        response = requests.get(api_endpoint)
        response.raise_for_status()
        data = response.json()
        
        # Update last API call time AFTER a successful request
        st.session_state.last_api_call_time = time.time() 
        
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching data for {coin_id} for {days} days: {e}")
        st.warning("🚨 You might have hit the CoinGecko API rate limit. Please wait a moment before trying again or change the selected days less frequently. Consider a paid CoinGecko API key for higher limits.")
        return None

# --- Main data fetching and caching logic ---
def get_cached_or_fetch_data(coin_id, vs_currency, days_requested):
    """
    Manages caching for 90-day hourly and 365-day daily data.
    Fetches if not cached, then returns the relevant slice.
    """
    MAX_HOURLY_DAYS = 90
    MAX_DAILY_DAYS = 365 # CoinGecko typically provides daily data beyond 90 days

    # Initialize cache if not present
    if 'data_cache' not in st.session_state:
        st.session_state.data_cache = {}

    final_data_to_process = None

    if days_requested <= MAX_HOURLY_DAYS:
        cache_key = f"{coin_id}_{vs_currency}_hourly_{MAX_HOURLY_DAYS}"
        if cache_key not in st.session_state.data_cache:
            st.info(f"📈 Fetching **{MAX_HOURLY_DAYS} days of HOURLY** data for **{coin_id}**...")
            fetched_data = _api_call_with_rate_limit(coin_id, vs_currency, MAX_HOURLY_DAYS)
            if fetched_data:
                st.session_state.data_cache[cache_key] = fetched_data
                st.success(f"Successfully fetched {MAX_HOURLY_DAYS} days of hourly data.")
            else:
                return None # Failed to fetch
        else:
            st.info(f"💾 Using **cached HOURLY data ({MAX_HOURLY_DAYS} days)** for **{coin_id}**.")
        
        # Slice the cached hourly data
        full_data = st.session_state.data_cache.get(cache_key)
        if full_data:
            # CoinGecko returns data from oldest to newest.
            # We want the *last* 'days_requested' entries.
            final_data_to_process = {
                'prices': full_data['prices'][-int(days_requested * 24):], # Approx 24 data points per day
                'total_volumes': full_data['total_volumes'][-int(days_requested * 24):]
            }
            # Handle cases where days_requested is small, might not have enough points.
            # Take minimum of requested points and available points.
            if len(final_data_to_process['prices']) < int(days_requested * 24) and days_requested > 1:
                # If we asked for e.g. 10 days, but only 5 days of hourly data is returned by CoinGecko for some reason.
                # This also accounts for the specific hourly points vs calendar days.
                st.warning(f"Note: Requested {days_requested} days, but cached hourly data has fewer points. Displaying all available hourly data (prices: {len(final_data_to_process['prices'])}).")
        
    else: # days_requested > MAX_HOURLY_DAYS, so we need daily data
        cache_key = f"{coin_id}_{vs_currency}_daily_{MAX_DAILY_DAYS}"
        if cache_key not in st.session_state.data_cache:
            st.info(f"📊 Fetching **{MAX_DAILY_DAYS} days of DAILY** data for **{coin_id}**...")
            fetched_data = _api_call_with_rate_limit(coin_id, vs_currency, MAX_DAILY_DAYS)
            if fetched_data:
                st.session_state.data_cache[cache_key] = fetched_data
                st.success(f"Successfully fetched {MAX_DAILY_DAYS} days of daily data.")
            else:
                return None # Failed to fetch
        else:
            st.info(f"💾 Using **cached DAILY data ({MAX_DAILY_DAYS} days)** for **{coin_id}**.")
        
        # Slice the cached daily data
        full_data = st.session_state.data_cache.get(cache_key)
        if full_data:
            # Slice to 'days_requested' daily points
            final_data_to_process = {
                'prices': full_data['prices'][-days_requested:],
                'total_volumes': full_data['total_volumes'][-days_requested:]
            }
        
    return final_data_to_process

# --- Main Streamlit App Logic ---
def main():
    st.set_page_config(layout="wide")
    st.title('Test2: Cryptocurrency Historical Data Analysis Dashboard 📊')
    st.markdown("---")

    # --- Sidebar for user inputs ---
    st.sidebar.header("Configuration")

    # 1. Select Cryptocurrency
    coins_list = fetch_coin_list()
    coin_names = [coin['name'] for coin in coins_list]

    common_coins = ["Bitcoin", "Ethereum", "Ripple", "Litecoin", "Cardano", "Solana", "Dogecoin", "Tron"]
    preselected_options = [name for name in common_coins if name in coin_names]
    other_options = sorted([name for name in coin_names if name not in preselected_options])
    full_dropdown_options = preselected_options + other_options

    default_coin_index = full_dropdown_options.index("Bitcoin") if "Bitcoin" in full_dropdown_options else 0

    selected_coin_name = st.sidebar.selectbox(
        "Select Cryptocurrency:",
        full_dropdown_options,
        index=default_coin_index,
        key='selected_coin_name_sb'
    )
    selected_coin_id = next((coin['id'] for coin in coins_list if coin['name'] == selected_coin_name), "bitcoin")

    # 2. Select Number of Days
    # Using a key for the slider
    days_input = st.sidebar.slider("Select number of days for data:", min_value=1, max_value=365, value=90, step=1, key='days_slider')

    # 3. Select vs. Currency
    vs_currency = st.sidebar.selectbox("Select vs. Currency:", ["usd", "eur", "jpy", "gbp", "cad"], index=0, key='vs_currency_sb')

    st.sidebar.markdown("---")
    st.sidebar.info("Data fetched from CoinGecko API.")

    # --- Initialize session state variables if not present for initial display ---
    if 'data_fetched_flag' not in st.session_state:
        st.session_state.data_fetched_flag = False
        st.session_state.current_coin_id = selected_coin_id # Initial values
        st.session_state.current_vs_currency = vs_currency
        st.session_state.current_days = days_input
        st.session_state.initial_load_done = False # New flag for initial load

    # --- Implement a "Fetch Data" button ---
    # This is crucial to avoid hitting rate limits on every slider/selectbox change
    fetch_button_clicked = st.sidebar.button("Fetch & Analyze Data")
    
    # Trigger initial fetch if not done yet
    if not st.session_state.initial_load_done:
        fetch_button_clicked = True
        st.session_state.initial_load_done = True # Set flag to true after initial load

    # Check if coin/currency/days combination has changed OR button was clicked
    # This logic determines WHEN to try fetching new core data
    data_params_changed = (selected_coin_id != st.session_state.current_coin_id or
                           vs_currency != st.session_state.current_vs_currency)

    # If parameters defining the *core* dataset (coin/currency) change, or button is clicked
    if data_params_changed or fetch_button_clicked:
        st.session_state.current_coin_id = selected_coin_id
        st.session_state.current_vs_currency = vs_currency
        # The days_input is just the requested slice; the underlying fetch uses MAX_HOURLY/DAILY
        # We don't update current_days here, as the slice is handled by get_cached_or_fetch_data
        
        # This will trigger the actual API call/caching based on the new coin/currency
        btc_data_full_range = get_cached_or_fetch_data(st.session_state.current_coin_id, st.session_state.current_vs_currency, days_input)
        st.session_state.last_full_range_data = btc_data_full_range # Store the full range data
        st.session_state.last_processed_days_input = days_input # Store the days input that resulted in this full data
    else:
        # If parameters haven't changed and button not clicked, use previously fetched full data
        btc_data_full_range = st.session_state.get('last_full_range_data')
        # If days_input has changed, but coin/currency hasn't, we just re-slice from the full data
        if btc_data_full_range and days_input != st.session_state.last_processed_days_input:
            st.info(f"✨ Slicing cached data for new days range: {days_input} days.")
            btc_data_full_range = get_cached_or_fetch_data(st.session_state.current_coin_id, st.session_state.current_vs_currency, days_input)
            st.session_state.last_processed_days_input = days_input # Update the last processed days input

    # --- Actual processing and plotting using the data that was either newly fetched or sliced ---
    if btc_data_full_range and 'prices' in btc_data_full_range and 'total_volumes' in btc_data_full_range:
        st.success(f"Data for {st.session_state.current_coin_id.capitalize()} processed for {days_input} days!")

        selected_coin_name_display = next((coin['name'] for coin in coins_list if coin['id'] == st.session_state.current_coin_id), st.session_state.current_coin_id.capitalize())
        
        # --- Data Processing ---
        df_prices = pd.DataFrame(btc_data_full_range['prices'], columns=['timestamp_ms', 'price'])
        df_volumes = pd.DataFrame(btc_data_full_range['total_volumes'], columns=['timestamp_ms', 'volume'])

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

        # Calculate MACD and RSI (Direct function calls)
        macd_result = ta.macd(df_data['price'], fast=12, slow=26, signal=9)
        df_data = pd.concat([df_data, macd_result], axis=1)

        rsi_result = ta.rsi(df_data['price'], length=14)
        df_data['RSI_14'] = rsi_result

        # Filter df_data based on days_input for actual display, ensuring it's the right length
        # This slicing needs to happen BEFORE statistical analysis if we're only displaying for 'days_input'
        # The 'get_cached_or_fetch_data' already does the slicing, so df_data should already be correct length
        
        st.subheader("Raw Data Preview")
        st.dataframe(df_data.tail())
        st.info(f"DataFrame contains {len(df_data)} entries from {df_data.index.min().strftime('%Y-%m-%d %H:%M')} to {df_data.index.max().strftime('%Y-%m-%d %H:%M')}.")

        # --- Visualization Section ---
        st.subheader(f"{selected_coin_name_display} Price, Moving Averages & Volume Chart")

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})

        ax1.plot(df_data['price'], color='blue', linewidth=1.5, label=f'{selected_coin_name_display} Price')
        ax1.plot(df_data['SMA_10'], color='orange', linewidth=1, label='SMA 10h')
        ax1.plot(df_data['SMA_30'], color='red', linewidth=1, label='SMA 30h')

        ax1.set_title(f'{selected_coin_name_display} Price, Moving Averages & Volume over {days_input} Days ({st.session_state.current_vs_currency.upper()})', fontsize=16)
        ax1.set_ylabel(f'Price ({st.session_state.current_vs_currency.upper()})', fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.legend()

        # --- Volume Chart Enhancement ---
        df_data['price_change'] = df_data['price'].diff()
        volume_bar_colors = ['green' if x > 0 else 'red' for x in df_data['price_change']] # THIS IS THE LINE FOR COLORED VOLUME

        ax2.bar(df_data.index, df_data['volume'], color=volume_bar_colors, alpha=0.7, width=0.8)
        ax2.set_title(f'{selected_coin_name_display} Trading Volume over {days_input} Days', fontsize=16)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel(f'Volume ({st.session_state.current_vs_currency.upper()})', fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.ticklabel_format(style='plain', axis='y')

        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

        # --- Basic Statistical Analysis ---
        st.subheader(f"{selected_coin_name_display} Basic Statistical Analysis")
        col1, col2 = st.columns(2)

        with col1:
            st.write("#### Price Statistics:")
            st.write(df_data['price'].describe())

        with col2:
            st.write("#### Volume Statistics:")
            st.write(df_data['volume'].describe())

        # Plotting a Histogram of Hourly Returns
        st.subheader(f"Distribution of {selected_coin_name_display} Hourly Returns")
        fig_hist, ax_hist = plt.subplots(figsize=(10, 6))
        ax_hist.hist(df_data['hourly_return'].dropna(), bins=50, edgecolor='black', alpha=0.7)
        ax_hist.set_title(f'Distribution of {selected_coin_name_display} Hourly Returns (%)', fontsize=16)
        ax_hist.set_xlabel('Hourly Return (%)', fontsize=12)
        ax_hist.set_ylabel('Frequency', fontsize=12)
        ax_hist.grid(True, linestyle=':', alpha=0.6)
        plt.tight_layout()
        st.pyplot(fig_hist)

        # --- Risk Analysis (Volatility) ---
        st.subheader(f"{selected_coin_name_display} Risk Analysis (Volatility)")
        daily_return_std = df_data['hourly_return'].dropna().std()
        st.info(f"**Standard Deviation of Hourly Returns:** {daily_return_std:.2f}%")
        st.write("A higher Standard Deviation indicates greater volatility and risk.")

        # --- Correlation Analysis ---
        st.subheader(f"{selected_coin_name_display} Correlation Analysis (Autocorrelation)")
        autocorrelation_1h = df_data['hourly_return'].corr(df_data['hourly_return'].shift(1))
        st.info(f"**Autocorrelation of Hourly Returns (lag 1 hour):** {autocorrelation_1h:.4f}")
        st.write("Note: In efficient markets, autocorrelation of returns is often close to zero.")
        st.write("A positive autocorrelation suggests momentum (trend continuation).")
        st.write("A negative autocorrelation suggests mean reversion (price bouncing back).")

        # --- Visualization Section for MACD ---
        st.subheader(f"{selected_coin_name_display} MACD (Moving Average Convergence Divergence)")
        fig_macd, ax_macd = plt.subplots(figsize=(12, 6))

        if 'MACD_12_26_9' in df_data.columns and 'MACDs_12_26_9' in df_data.columns and 'MACDh_12_26_9' in df_data.columns:
            ax_macd.plot(df_data.index, df_data['MACD_12_26_9'], label='MACD Line', color='blue', linewidth=2)
            ax_macd.plot(df_data.index, df_data['MACDs_12_26_9'], label='Signal Line', color='red', linewidth=1.5, linestyle='--')
            bar_colors_macd = ['green' if x >= 0 else 'red' for x in df_data['MACDh_12_26_9']]
            ax_macd.bar(df_data.index, df_data['MACDh_12_26_9'], label='Histogram', color=bar_colors_macd, alpha=0.6, width=0.8)

            ax_macd.axhline(0, color='black', linestyle=':', linewidth=0.8)
            ax_macd.set_title(f'{selected_coin_name_display} MACD over {days_input} Days', fontsize=16)
            ax_macd.set_xlabel('Date', fontsize=12)
            ax_macd.set_ylabel('MACD Value', fontsize=12)
            ax_macd.grid(True, linestyle='--', alpha=0.7)
            ax_macd.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig_macd)
        else:
            st.warning(f"  > Not enough data to calculate MACD for {selected_coin_name_display}.")
            plt.close(fig_macd)

        # --- Visualization Section for RSI ---
        st.subheader(f"{selected_coin_name_display} RSI (Relative Strength Index)")
        fig_rsi, ax_rsi = plt.subplots(figsize=(12, 6))

        if 'RSI_14' in df_data.columns:
            ax_rsi.plot(df_data.index, df_data['RSI_14'], label='RSI (14)', color='green', linewidth=1.5)
            ax_rsi.axhline(70, color='red', linestyle='--', label='Overbought (70)', linewidth=0.8)
            ax_rsi.axhline(30, color='blue', linestyle='--', label='Oversold (30)', linewidth=0.8)
            ax_rsi.set_ylim(0, 100)
            ax_rsi.set_title(f'{selected_coin_name_display} RSI over {days_input} Days', fontsize=16)
            ax_rsi.set_xlabel('Date', fontsize=12)
            ax_rsi.set_ylabel('RSI Value', fontsize=12)
            ax_rsi.grid(True, linestyle='--', alpha=0.7)
            ax_rsi.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig_rsi)
        else:
            st.warning(f"  > Not enough data to calculate RSI for {selected_coin_name_display}.")
            plt.close(fig_rsi)

        # --- Automated Analysis Commentary ---
        st.subheader(f"{selected_coin_name_display} Automated Market Analysis 🤖")
        st.markdown("---")

        st.markdown("##### Volatility Analysis:")
        if daily_return_std > 0.5:
            st.write(f"  **> {selected_coin_name_display} has shown HIGH volatility** in hourly returns ({daily_return_std:.2f}%). This indicates significant price swings and higher risk/reward opportunities.")
        elif daily_return_std > 0.2:
            st.write(f"  **> {selected_coin_name_display} has shown MODERATE volatility** in hourly returns ({daily_return_std:.2f}%). This suggests notable price movements.")
        else:
            st.write(f"  **> {selected_coin_name_display} has shown LOW volatility** in hourly returns ({daily_return_std:.2f}%). Price movements have been relatively stable.")

        st.markdown("##### Trend Analysis (based on Moving Averages):")
        if not df_data['SMA_10'].isnull().all() and not df_data['SMA_30'].isnull().all() and len(df_data) >= 30:
            if df_data['SMA_10'].iloc[-1] > df_data['SMA_30'].iloc[-1]:
                if df_data['price'].iloc[-1] > df_data['SMA_10'].iloc[-1]:
                    st.success(f"  **> {selected_coin_name_display} appears to be in an UPTREND.** The short-term Moving Average (SMA 10h) is above the long-term Moving Average (SMA 30h), and the price is currently above both MAs, suggesting bullish momentum.")
                else:
                    st.info(f"  **> {selected_coin_name_display} is in a POTENTIAL UPTREND.** While the short-term Moving Average (SMA 10h) is above the long-term (SMA 30h), the price is currently below the short-term MA, which might indicate a temporary pullback or consolidation within the uptrend.")
            elif df_data['SMA_10'].iloc[-1] < df_data['SMA_30'].iloc[-1]:
                if df_data['price'].iloc[-1] < df_data['SMA_10'].iloc[-1]:
                    st.error(f"  **> {selected_coin_name_display} appears to be in a DOWNTREND.** The short-term Moving Average (SMA 10h) is below the long-term Moving Average (SMA 30h), and the price is currently below both MAs, suggesting bearish momentum.")
                else:
                    st.warning(f"  **> {selected_coin_name_display} is in a POTENTIAL DOWNTREND.** While the short-term Moving Average (SMA 10h) is below the long-term (SMA 30h), the price is currently above the short-term MA, which might indicate a temporary rebound or consolidation within the downtrend.")
            else:
                st.warning(f"  **> {selected_coin_name_display} is currently in a SIDEWAYS or CONSOLIDATION phase.** Moving Averages are intertwined, suggesting a lack of clear trend.")
        else:
            st.warning(f"  > Not enough data for {selected_coin_name_display} to calculate Moving Averages and determine a clear trend for comment.")

        st.markdown("##### MACD Analysis:")
        if 'MACD_12_26_9' in df_data.columns and 'MACDs_12_26_9' in df_data.columns and len(df_data) >= 26:
            last_macd = df_data['MACD_12_26_9'].iloc[-1]
            last_signal = df_data['MACDs_12_26_9'].iloc[-1]

            if last_macd > last_signal and (df_data['MACD_12_26_9'].iloc[-2] <= df_data['MACDs_12_26_9'].iloc[-2] if len(df_data) >= 2 else True):
                st.success(f"  **> MACD Bullish Crossover:** The MACD line for {selected_coin_name_display} has just crossed ABOVE the signal line, suggesting potential **upward momentum**.")
            elif last_macd < last_signal and (df_data['MACD_12_26_9'].iloc[-2] >= df_data['MACDs_12_26_9'].iloc[-2] if len(df_data) >= 2 else True):
                st.error(f"  **> MACD Bearish Crossover:** The MACD line for {selected_coin_name_display} has just crossed BELOW the signal line, suggesting potential **downward momentum**.")
            elif last_macd > last_signal:
                st.info(f"  **> MACD is bullish:** The MACD line for {selected_coin_name_display} is currently above its signal line, indicating **bullish momentum**.")
            elif last_macd < last_signal:
                st.warning(f"  **> MACD is bearish:** The MACD line for {selected_coin_name_display} is currently below its signal line, indicating **bearish momentum**.")
            else:
                st.info(f"  > MACD for {selected_coin_name_display} is flat or near the signal line, suggesting **neutral momentum**.")

            if last_macd > 0:
                st.info(f"  > MACD is currently above the zero line, reinforcing **bullish momentum**.")
            elif last_macd < 0:
                st.info(f"  > MACD is currently below the zero line, reinforcing **bearish momentum**.")
        else:
            st.warning(f"  > Not enough data to calculate MACD for {selected_coin_name_display}.")

        st.markdown("##### RSI Analysis:")
        if 'RSI_14' in df_data.columns and not df_data['RSI_14'].isnull().all() and len(df_data) >= 14:
            last_rsi = df_data['RSI_14'].iloc[-1]

            if last_rsi >= 70:
                st.warning(f"  **> RSI for {selected_coin_name_display} ({last_rsi:.2f}) is in the OVERBOUGHT zone (>=70).** This may indicate a temporary top and potential for a pullback.")
            elif last_rsi <= 30:
                st.success(f"  **> RSI for {selected_coin_name_display} ({last_rsi:.2f}) is in the OVERSOLD zone (<=30).** This may indicate a temporary bottom and potential for a rebound.")
            else:
                st.info(f"  > RSI for {selected_coin_name_display} ({last_rsi:.2f}) is in the **neutral zone** (between 30 and 70), suggesting no immediate overbought/oversold conditions.")
        else:
            st.warning(f"  > Not enough data to calculate RSI for {selected_coin_name_display}.")

        st.markdown("##### Volume Analysis:")
        avg_volume = df_data['volume'].mean()
        last_volume = df_data['volume'].iloc[-1]
        if last_volume > avg_volume * 1.5:
            st.success(f"  **> Current trading volume for {selected_coin_name_display} ({last_volume:.2e}) is significantly HIGHER** than the average volume ({avg_volume:.2e}). This often accompanies strong price movements, confirming the current trend or indicating high market interest.")
        elif last_volume < avg_volume * 0.5:
            st.warning(f"  **> Current trading volume for {selected_coin_name_display} ({last_volume:.2e}) is significantly LOWER** than the average volume ({avg_volume:.2e}). This may indicate a lack of strong conviction behind recent price movements or a quiet period.")
        else:
            st.info(f"  **> Current trading volume for {selected_coin_name_display} ({last_volume:.2e}) is in line** with the average volume ({avg_volume:.2e}).")

        st.markdown("##### Autocorrelation Analysis:")
        if not df_data['hourly_return'].isnull().all() and len(df_data) >= 2:
            autocorrelation_1h = df_data['hourly_return'].corr(df_data['hourly_return'].shift(1))
            if abs(autocorrelation_1h) < 0.05:
                st.info(f"  **> The hourly returns for {selected_coin_name_display} show VERY LOW autocorrelation** ({autocorrelation_1h:.4f}). This suggests that past hourly price movements are not a strong predictor of future hourly movements, which aligns with the weak form of the Efficient Market Hypothesis.")
            elif autocorrelation_1h > 0.05:
                st.warning(f"  **> The hourly returns for {selected_coin_name_display} show a POSITIVE autocorrelation** ({autocorrelation_1h:.4f}). This could indicate some momentum or trend continuation in the short-term.")
            elif autocorrelation_1h < -0.05:
                st.warning(f"  **> The hourly returns for {selected_coin_name_display} show a NEGATIVE autocorrelation** ({autocorrelation_1h:.4f}). This could indicate some mean reversion in the short-term (prices tending to bounce back).")
        else:
            st.warning(f"  > Not enough data to calculate Autocorrelation for {selected_coin_name_display}.")

    else:
        st.info("📊 Please select your options and click 'Fetch & Analyze Data' to load cryptocurrency data.")
        st.error(f"Failed to retrieve data for {selected_coin_id.capitalize()}. Please check the API status, your internet connection, or try a different coin/timeframe. If you just changed a setting, please click 'Fetch & Analyze Data' in the sidebar.")


# Run the Streamlit app
if __name__ == "__main__":
    # Initialize all necessary session_state variables
    if 'data_cache' not in st.session_state:
        st.session_state.data_cache = {}
    if 'last_api_call_time' not in st.session_state:
        st.session_state.last_api_call_time = 0
    if 'current_coin_id' not in st.session_state:
        st.session_state.current_coin_id = None
    if 'current_vs_currency' not in st.session_state:
        st.session_state.current_vs_currency = None
    if 'current_days' not in st.session_state:
        st.session_state.current_days = None
    if 'last_full_range_data' not in st.session_state: # Stores the full 90-day hourly or 365-day daily data
        st.session_state.last_full_range_data = None
    if 'last_processed_days_input' not in st.session_state: # Stores the days_input that was used for the last display
        st.session_state.last_processed_days_input = None
        
    main()