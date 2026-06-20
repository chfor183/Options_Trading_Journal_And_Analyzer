import streamlit as st
import pandas as pd
import numpy as np
import math
from src.db import SessionLocal
from src.models import Trade, Transaction
from src.market_data import get_ticker_info

st.set_page_config(page_title="Trading Journal", page_icon="📓", layout="wide")
st.title("Trading Journal")

db = SessionLocal()

trades = db.query(Trade).all()

if trades:
    # Initialize session state for checkboxes
    if "selected_trades" not in st.session_state:
        st.session_state.selected_trades = {}
    
    st.write("### All Trades")
    
    # Filtering logic
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    filter_ticker = filter_col1.text_input("Filter by Ticker")
    filter_date = filter_col2.date_input("Filter by Date Opened", value=None)
    status_options = ["All"] + list(set([t.status for t in trades]))
    filter_status = filter_col3.selectbox("Filter by Status", status_options)

    # Apply filters
    filtered_trades = trades
    if filter_ticker:
        filtered_trades = [t for t in filtered_trades if filter_ticker.upper() in t.ticker.upper()]
    if filter_date:
        filtered_trades = [t for t in filtered_trades if t.date_opened.date() == filter_date]
    if filter_status != "All":
        filtered_trades = [t for t in filtered_trades if t.status == filter_status]
        
    # Sort
    filtered_trades.sort(key=lambda x: x.date_opened, reverse=True)
    
    # Header row
    col_widths = [0.4, 0.7, 1.2, 1.0, 1.2, 1.0, 1.0, 1.2, 0.8, 0.8, 0.8, 0.7, 0.7]
    cols = st.columns(col_widths)
    headers = ["Select", "Ticker", "Name", "Date Opened", "Strategy", "Exp. Move", "Current Price", "Break-Even", "Cost", "PnL", "Status", "Edit", "Close"]
    for col, header in zip(cols, headers):
        col.markdown(f"<div style='text-align: left; white-space: nowrap; font-weight: bold;'>{header}</div>", unsafe_allow_html=True)
    
    # Pagination Logic
    ROWS_PER_PAGE = 10
    total_pages = max(1, math.ceil(len(filtered_trades) / ROWS_PER_PAGE))
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1
        
    start_idx = (st.session_state.current_page - 1) * ROWS_PER_PAGE
    end_idx = start_idx + ROWS_PER_PAGE
    paginated_trades = filtered_trades[start_idx:end_idx]

    for t in paginated_trades:
        cols = st.columns(col_widths)
        
        # Calculate Cost and PnL
        open_tx = next((tx for tx in t.transactions if tx.action == "Open"), None)
        raw_cost = open_tx.price if open_tx else 0.0
        display_cost = -raw_cost # Positive for credit received, negative for debit paid
        
        pnl = 0.0
        for tx in t.transactions:
            if tx.action == "Open":
                pnl += -tx.price - tx.commission
            else:
                pnl += tx.price - tx.commission
        
        # Checkbox for selection
        selected = cols[0].checkbox(f"Select {t.id}", key=f"select_{t.id}", value=st.session_state.selected_trades.get(t.id, False), label_visibility="collapsed")
        st.session_state.selected_trades[t.id] = selected
        
        cols[1].markdown(f"<div style='text-align: left;'>{t.ticker}</div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div style='text-align: left;'>{t.underlying_name}</div>", unsafe_allow_html=True)
        cols[3].markdown(f"<div style='text-align: left;'>{t.date_opened.strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)
        cols[4].markdown(f"<div style='text-align: left;'>{t.strategy_type}</div>", unsafe_allow_html=True)
        cols[5].markdown(f"<div style='text-align: left;'>{t.expected_move}</div>", unsafe_allow_html=True)
        
        # Try to get Current Price and Breakevens
        current_price = "N/A"
        breakevens = "N/A"
        
        try:
            from src.options_math import calculate_metrics
            info = get_ticker_info(t.ticker)
            if info and info.get('current_price'):
                cp = float(info['current_price'])
                current_price = f"${cp:.2f}"
                
                # Format legs for options_math
                legs_for_math = []
                for leg in t.legs:
                    open_tx = next((tx for tx in t.transactions if tx.action == "Open"), None)
                    price = open_tx.price if open_tx else 0.0
                    legs_for_math.append({
                        "action": leg.position,
                        "qty": 1, # approx
                        "type": leg.option_type,
                        "strike": leg.strike,
                        "price": price,
                        "expiry": pd.to_datetime(leg.expiry)
                    })
                    
                metrics = calculate_metrics(legs_for_math, cp)
                bes = metrics.get('breakevens', [])
                if bes:
                    breakevens = ", ".join([f"${b:.2f}" for b in bes])
        except Exception as e:
            pass
            
        cols[6].markdown(f"<div style='text-align: left;'>{current_price}</div>", unsafe_allow_html=True)
        cols[7].markdown(f"<div style='text-align: left;'>{breakevens}</div>", unsafe_allow_html=True)
        cols[8].markdown(f"<div style='text-align: left;'>${display_cost:.2f}</div>", unsafe_allow_html=True)
        
        color = "green" if pnl > 0 else "red" if pnl < 0 else "inherit"
        cols[9].markdown(f"<div style='text-align: left; color: {color};'>${pnl:.2f}</div>", unsafe_allow_html=True)
        
        cols[10].markdown(f"<div style='text-align: left;'>{t.status}</div>", unsafe_allow_html=True)
        
        if cols[11].button("Edit", key=f"edit_{t.id}"):
            st.session_state.edit_trade_id = t.id
            st.switch_page("pages/1_Trade.py")
            
        if cols[12].button("Close", key=f"close_{t.id}"):
            st.session_state.close_trade_id = t.id
            st.switch_page("pages/4_Close Trade.py")
            
    st.divider()
    
    # Pagination UI
    page_col1, page_col2, page_col3 = st.columns([1, 2, 1])
    if page_col1.button("Previous Page") and st.session_state.current_page > 1:
        st.session_state.current_page -= 1
        st.rerun()
    page_col2.write(f"Page {st.session_state.current_page} of {total_pages}")
    if page_col3.button("Next Page") and st.session_state.current_page < total_pages:
        st.session_state.current_page += 1
        st.rerun()
        
    st.divider()
    
    # Bulk delete
    selected_ids = [k for k, v in st.session_state.selected_trades.items() if v]
    if selected_ids:
        if st.button("Delete all selected", type="primary"):
            trades_to_delete = db.query(Trade).filter(Trade.id.in_(selected_ids)).all()
            for td in trades_to_delete:
                db.delete(td)
            db.commit()
            st.session_state.selected_trades = {}
            st.success(f"Deleted {len(selected_ids)} trades!")
            st.rerun()
else:
    st.info("No trades found in the journal.")

db.close()
