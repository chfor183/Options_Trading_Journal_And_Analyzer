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

import requests
import urllib.parse

@st.cache_data(ttl=300)
def get_barchart_option_chain(ticker_symbol: str, expiry_date: str):
    try:
        s = requests.Session()
        s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        
        # First, visit the options page to get the XSRF token
        s.get(f'https://www.barchart.com/stocks/quotes/{ticker_symbol}/options')
        
        token = s.cookies.get('XSRF-TOKEN')
        if token:
            token = urllib.parse.unquote(token)
            
        headers = {'X-XSRF-TOKEN': token} if token else {}
        params = {
            'symbol': ticker_symbol,
            'fields': 'strikePrice,lastPrice,bidPrice,askPrice,volatility,optionType',
            'expirationDate': expiry_date
        }
        
        api_r = s.get('https://www.barchart.com/proxies/core-api/v1/options/get', headers=headers, params=params)
        
        if api_r.status_code == 200:
            return api_r.json().get('data', [])
        return []
    except Exception as e:
        print(f"Barchart error: {e}")
        return []

def get_barchart_live_option_leg_data(ticker_symbol: str, expiry_date: str, strike: float, option_type: str):
    chain_data = get_barchart_option_chain(ticker_symbol, expiry_date)
    
    for row in chain_data:
        try:
            row_strike = float(str(row.get('strikePrice', '0')).replace(',', ''))
            row_type = str(row.get('optionType', '')).lower()
            
            if abs(row_strike - strike) < 0.01 and row_type == option_type.lower():
                def parse_float(val):
                    if not val: return 0.0
                    if isinstance(val, str):
                        val = val.replace(',', '').replace('%', '')
                        if val == 'NA' or val == '' or val.lower() == 's': return 0.0
                    return float(val)

                vol = parse_float(row.get('volatility', 0.0))
                
                return {
                    "lastPrice": parse_float(row.get('lastPrice')),
                    "bid": parse_float(row.get('bidPrice')),
                    "ask": parse_float(row.get('askPrice')),
                    "impliedVolatility": vol / 100.0
                }
        except Exception as e:
            continue
            
    return None
