import yfinance as yf
import pandas as pd

def get_ticker_info(ticker_symbol: str) -> dict:
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        return {
            "name": info.get("shortName", ""),
            "category": info.get("quoteType", ""),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice")
        }
    except Exception as e:
        return {"name": "", "category": "", "current_price": 0.0}

def get_options_chains(ticker_symbol: str):
    try:
        ticker = yf.Ticker(ticker_symbol)
        return ticker.options
    except Exception as e:
        return []

import streamlit as st

@st.cache_data(ttl=300)
def get_option_chain_for_date(ticker_symbol: str, date: str):
    try:
        ticker = yf.Ticker(ticker_symbol)
        chain = ticker.option_chain(date)
        return {
            "calls": chain.calls,
            "puts": chain.puts
        }
    except Exception as e:
        return {"calls": pd.DataFrame(), "puts": pd.DataFrame()}

def get_live_option_leg_data(ticker_symbol: str, expiry_date: str, strike: float, option_type: str):
    """
    Fetches the live price, IV, and required data for an option leg.
    expiry_date should be in 'YYYY-MM-DD' format.
    option_type is 'call' or 'put'.
    """
    try:
        chain = get_option_chain_for_date(ticker_symbol, expiry_date)
        df = chain['calls'] if option_type.lower() == 'call' else chain['puts']
        
        if df.empty:
            return None
            
        # find the strike
        match = df[df['strike'] == strike]
        if not match.empty:
            row = match.iloc[0]
            return {
                "lastPrice": row.get("lastPrice", 0.0),
                "bid": row.get("bid", 0.0),
                "ask": row.get("ask", 0.0),
                "impliedVolatility": row.get("impliedVolatility", 0.0),
            }
        return None
    except Exception as e:
        return None

def get_cad_usd_exchange_rate():
    try:
        ticker = yf.Ticker("CAD=X")
        return ticker.info.get("regularMarketPrice", 1.35)
    except:
        return 1.35
