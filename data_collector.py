import requests

def fetch_data(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# URL for fetching historical BTC data (prices, market_caps, total_volumes) for the last 90 days in USD
# The 'id' for Bitcoin is 'bitcoin'
# 'vs_currency' is 'usd'
# 'days' is '90'
api_endpoint = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=90"

if __name__ == "__main__":
    print(f"Fetching data from: {api_endpoint}")
    btc_data = fetch_data(api_endpoint)
    if btc_data:
        print("\nData fetched successfully!")
        print("Keys available in the response:", btc_data.keys())

        if 'prices' in btc_data:
            print(f"\nFirst 5 price entries (timestamp, price):")
            for entry in btc_data['prices'][:5]:
                # Prices are usually in milliseconds timestamp, convert to seconds for readability if needed
                # import datetime
                # print(f"  Time: {datetime.datetime.fromtimestamp(entry[0]/1000)} Price: {entry[1]}")
                print(f"  Timestamp (ms): {entry[0]}, Price (USD): {entry[1]:.2f}")
        else:
            print("No 'prices' key found in the response.")
    else:
        print("Failed to fetch data.")