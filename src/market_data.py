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

def get_cad_usd_exchange_rate():
    try:
        ticker = yf.Ticker("CAD=X")
        return ticker.info.get("regularMarketPrice", 1.35)
    except:
        return 1.35
