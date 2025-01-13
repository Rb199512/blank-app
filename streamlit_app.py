pip freeze > requirements.txt
import pandas as pd
import numpy as np
import requests
from scipy.stats import norm
import datetime
from io import StringIO
import streamlit as st

# Function to fetch historical data from EOD Historical Data API
def fetch_data_from_eod(symbol, start_date, end_date, api_key):
    url = f"https://eodhistoricaldata.com/api/eod/{symbol}?api_token={api_key}&from={start_date}&to={end_date}&period=d"
    
    response = requests.get(url)
    
    # Check for successful status code
    if response.status_code == 200:
        try:
            # Parse CSV data
            csv_data = response.text
            df = pd.read_csv(StringIO(csv_data))
            
            # Ensure the 'Date' column is in datetime format
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            df.dropna(subset=['Close'], inplace=True)
            
            return df
        except Exception as e:
            st.error(f"Error while decoding CSV: {e}")
            return None
    else:
        st.error(f"Failed to fetch data. Status code: {response.status_code}")
        return None

# Function to calculate Parametric VaR
def calculate_parametric_var(data, confidence_level=0.95):
    returns = data.pct_change().dropna()  # Daily returns
    mean_return = returns.mean()
    std_deviation = returns.std()
    z_score = norm.ppf(confidence_level)
    var = mean_return + (z_score * std_deviation)
    return var

# Function to calculate total risk based on account size and VaR
def calculate_total_risk(account_size, var_percent):
    total_risk = account_size * var_percent  # Multiply account size by VaR (as percentage)
    return total_risk

# Function to calculate pip value for JPY pairs
def calculate_pip_value(pair, lot_size=100000):
    # For JPY pairs, the pip value is approximately 0.01 for 1 lot (100,000 units)
    if pair.endswith('JPY'):
        pip_value = 0.01 * lot_size
    else:
        # For non-JPY pairs, pip value would depend on the exchange rate
        pip_value = 0.0001 * lot_size  # Basic assumption for non-JPY pairs
    return pip_value

# Function to calculate trade risk based on stop loss and pip value
def calculate_trade_risk(stop_loss_pips, pip_value):
    return stop_loss_pips * pip_value

# Function to calculate optimal position size based on risk
def calculate_position_size(account_risk, trade_risk):
    return account_risk / trade_risk

# Streamlit App
def main():
    st.title("VaR and Position Sizing Calculator")

    # User inputs
    symbol = st.text_input("Enter the asset symbol (e.g., GBPJPY.FOREX):", "GBPJPY.FOREX")
    start_date = st.date_input("Enter the start date:", datetime.date(2024, 1, 1))
    end_date = st.date_input("Enter the end date:", datetime.date.today())
    api_key = st.text_input("Enter API Key", "")  # Enter your EOD API key
    
    account_size = st.number_input("Enter your account size (e.g., 5000):", min_value=1, value=5000)
    leverage = st.number_input("Enter your leverage (e.g., 100 for 100:1):", min_value=1, value=100)
    stop_loss_pips = st.number_input("Enter the stop loss in pips (e.g., 50):", min_value=1, value=50)

    # Fetch the data
    df = fetch_data_from_eod(symbol, start_date, end_date, api_key)
    
    if df is not None:
        close_prices = df['Close']
        
        # Calculate Parametric VaR
        var = calculate_parametric_var(close_prices, confidence_level=0.95)
        st.write(f"Parametric VaR at 95% confidence: {var * 100:.2f}%")
        
        # Calculate total risk in monetary terms
        total_risk = calculate_total_risk(account_size, var)
        st.write(f"Total Risk (in USD): {total_risk:.2f} USD")
        
        # Calculate pip value for the selected symbol (asset)
        pip_value = calculate_pip_value(symbol)

	# Calculate the trade risk (stop loss * pip value)
        trade_risk = calculate_trade_risk(stop_loss_pips, pip_value)
        
        # Calculate the ideal position size based on the account risk and trade risk
        position_size = calculate_position_size(total_risk, trade_risk)
        st.write(f"Optimal Position Size: {position_size:.2f} units of {symbol}")
        
    else:
        st.write("No data returned.")

if __name__ == "__main__":
    main()
