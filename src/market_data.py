import streamlit as st
import yfinance as yf
import pandas as pd

@st.cache_data(ttl=900)
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

@st.cache_data(ttl=900)
def get_options_chains(ticker_symbol: str):
    try:
        ticker = yf.Ticker(ticker_symbol)
        return ticker.options
    except Exception as e:
        return []

@st.cache_data(ttl=900)
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

@st.cache_data(ttl=900)
def get_cad_usd_exchange_rate():
    try:
        ticker = yf.Ticker("CAD=X")
        return ticker.info.get("regularMarketPrice", 1.35)
    except:
        return 1.35

import requests
import urllib.parse

@st.cache_data(ttl=900)
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

@st.cache_data(ttl=300)
def get_dcf_financial_data(ticker_symbol: str) -> dict:
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        name = info.get("longName") or info.get("shortName") or ticker_symbol
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
        
        shares = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
        cash = info.get("totalCash")
        debt = info.get("totalDebt")
        beta = info.get("beta") or 1.0
        
        bs = ticker.balance_sheet
        if bs is not None and not bs.empty:
            if not shares:
                if "Ordinary Shares Number" in bs.index:
                    shares = bs.loc["Ordinary Shares Number"].iloc[0]
                elif "Share Issued" in bs.index:
                    shares = bs.loc["Share Issued"].iloc[0]
            if not cash:
                if "Cash Cash Equivalents And Short Term Investments" in bs.index:
                    cash = bs.loc["Cash Cash Equivalents And Short Term Investments"].iloc[0]
                elif "Cash And Cash Equivalents" in bs.index:
                    cash = bs.loc["Cash And Cash Equivalents"].iloc[0]
            if not debt:
                if "Total Debt" in bs.index:
                    debt = bs.loc["Total Debt"].iloc[0]
                elif "Net Debt" in bs.index:
                    net_debt = bs.loc["Net Debt"].iloc[0]
                    if cash:
                        debt = net_debt + cash
                    else:
                        debt = net_debt
                        
        shares = float(shares) if shares else 1.0
        cash = float(cash) if cash else 0.0
        debt = float(debt) if debt else 0.0
        beta = float(beta) if beta else 1.0
        
        cf = ticker.cashflow
        fcf_history = {}
        if cf is not None and not cf.empty:
            fcf_series = None
            if "Free Cash Flow" in cf.index:
                fcf_series = cf.loc["Free Cash Flow"]
            elif "Operating Cash Flow" in cf.index:
                ocf = cf.loc["Operating Cash Flow"]
                capex = cf.loc["Capital Expenditure"] if "Capital Expenditure" in cf.index else 0.0
                fcf_series = ocf + capex
                
            if fcf_series is not None:
                if isinstance(fcf_series, pd.DataFrame):
                    fcf_series = fcf_series.iloc[0]
                for idx, val in fcf_series.items():
                    if pd.notna(val) and pd.notna(idx):
                        date_str = str(idx.date()) if hasattr(idx, "date") else str(idx)
                        fcf_history[date_str] = float(val)
                        
        sorted_fcf = dict(sorted(fcf_history.items()))
        
        target_high = info.get("targetHighPrice")
        target_mean = info.get("targetMeanPrice")
        target_low = info.get("targetLowPrice")
        analyst_count = info.get("numberOfAnalystOpinions")
        recommendation = info.get("recommendationKey") or "hold"
        
        # Determine logical forward growth rate consensus from yfinance estimates
        forward_growth = None
        try:
            # Try EPS estimate +1y growth rate first (standard analyst projection)
            ee = ticker.earnings_estimate
            if ee is not None and "+1y" in ee.index:
                g = ee.loc["+1y", "growth"]
                if g is not None and -0.50 < g < 0.95: # Skip negative anomalies and NVDA-like 100%+ triple-digit spikes
                    forward_growth = float(g)
            
            # Try Revenue estimate +1y growth if EPS growth is missing or anomalous
            if forward_growth is None:
                re = ticker.revenue_estimate
                if re is not None and "+1y" in re.index:
                    g = re.loc["+1y", "growth"]
                    if g is not None and -0.50 < g < 0.95:
                        forward_growth = float(g)
        except:
            pass
            
        # Fallbacks to historical values if forward consensus is not available or over-inflated
        rev_growth = info.get("revenueGrowth")
        earn_growth = info.get("earningsGrowth")
        
        if forward_growth is None:
            # Safe fallbacks (caps at 25% max growth rate to prevent hyper-inflation)
            g_cand = earn_growth or rev_growth or 0.10
            forward_growth = min(0.25, max(-0.25, float(g_cand)))
            
        return {
            "symbol": ticker_symbol,
            "name": name,
            "current_price": float(current_price) if current_price else 0.0,
            "shares_outstanding": shares,
            "total_cash": cash,
            "total_debt": debt,
            "beta": beta,
            "fcf_history": sorted_fcf,
            "target_high": float(target_high) if target_high else None,
            "target_mean": float(target_mean) if target_mean else None,
            "target_low": float(target_low) if target_low else None,
            "analyst_count": int(analyst_count) if analyst_count else None,
            "recommendation": str(recommendation).capitalize(),
            "revenue_growth": float(rev_growth) if rev_growth else None,
            "earnings_growth": float(forward_growth), # Use filtered consensus
        }
    except Exception as e:
        print(f"Error fetching DCF data for {ticker_symbol}: {e}")
        return {
            "symbol": ticker_symbol,
            "name": ticker_symbol,
            "current_price": 0.0,
            "shares_outstanding": 1.0,
            "total_cash": 0.0,
            "total_debt": 0.0,
            "beta": 1.0,
            "fcf_history": {},
            "target_high": None,
            "target_mean": None,
            "target_low": None,
            "analyst_count": None,
            "recommendation": "N/A",
            "revenue_growth": None,
            "earnings_growth": None,
        }

