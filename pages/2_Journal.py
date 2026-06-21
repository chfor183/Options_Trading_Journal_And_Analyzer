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
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    filter_ticker = filter_col1.text_input("Filter by Ticker")
    filter_date = filter_col2.date_input("Filter by Date Opened", value=None)
    status_options = ["All"] + list(set([t.status for t in trades]))
    filter_status = filter_col3.selectbox("Filter by Status", status_options)
    strategy_options = ["All"] + list(set([t.strategy_type for t in trades]))
    filter_strategy = filter_col4.selectbox("Filter by Strategy", strategy_options)

    # Apply filters
    filtered_trades = trades
    if filter_ticker:
        filtered_trades = [t for t in filtered_trades if filter_ticker.upper() in t.ticker.upper()]
    if filter_date:
        filtered_trades = [t for t in filtered_trades if t.date_opened.date() == filter_date]
    if filter_status != "All":
        filtered_trades = [t for t in filtered_trades if t.status == filter_status]
    if filter_strategy != "All":
        filtered_trades = [t for t in filtered_trades if t.strategy_type == filter_strategy]
        
    # Sort
    filtered_trades.sort(key=lambda x: x.date_opened, reverse=True)
    
    # Select All / Deselect All / Bulk Delete
    sel_col1, sel_col2, sel_col3, _ = st.columns([1.5, 1, 1.5, 6])
    if sel_col1.button("Select All Filtered"):
        for t in filtered_trades:
            st.session_state.selected_trades[t.id] = True
            st.session_state[f"select_{t.id}"] = True
        st.rerun()
    if sel_col2.button("Deselect All"):
        for t in trades:
            st.session_state.selected_trades[t.id] = False
            st.session_state[f"select_{t.id}"] = False
        st.rerun()
        
    selected_ids = [k for k, v in st.session_state.selected_trades.items() if v]
    if selected_ids:
        if sel_col3.button("Delete all selected", type="primary"):
            trades_to_delete = db.query(Trade).filter(Trade.id.in_(selected_ids)).all()
            for td in trades_to_delete:
                db.delete(td)
            db.commit()
            st.session_state.selected_trades = {}
            st.success(f"Deleted {len(selected_ids)} trades!")
            st.rerun()
            
    st.write("") # small spacing
    
    # Header row
    col_widths = [0.4, 0.7, 1.2, 1.0, 1.2, 1.0, 1.0, 1.2, 0.8, 0.8, 0.8, 0.7, 0.7, 0.7]
    cols = st.columns(col_widths)
    headers = ["Select", "Ticker", "Name", "Date Opened", "Strategy", "Exp. Move", "Current Price", "Break-Even", "Cost", "PnL", "Status", "Details", "Edit", "Close"]
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
        
        def handle_checkbox_change(trade_id):
            # The session state key matches the widget key "select_{trade_id}"
            st.session_state.selected_trades[trade_id] = st.session_state[f"select_{trade_id}"]

        if f"select_{t.id}" not in st.session_state:
            st.session_state[f"select_{t.id}"] = st.session_state.selected_trades.get(t.id, False)
            
        cols[0].checkbox(
            f"Select {t.id}", 
            key=f"select_{t.id}", 
            on_change=handle_checkbox_change,
            args=(t.id,),
            label_visibility="collapsed"
        )
        
        cols[1].markdown(f"<div style='text-align: left;'>{t.ticker}</div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div style='text-align: left;'>{t.underlying_name}</div>", unsafe_allow_html=True)
        cols[3].markdown(f"<div style='text-align: left;'>{t.date_opened.strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)
        cols[4].markdown(f"<div style='text-align: left;'>{t.strategy_type}</div>", unsafe_allow_html=True)
        cols[5].markdown(f"<div style='text-align: left;'>{t.expected_move}</div>", unsafe_allow_html=True)
        
        # Try to get Current Price and Breakevens
        current_price = "N/A"
        breakevens = "N/A"
        metrics = {}
        
        try:
            from src.options_math import calculate_metrics
            from src.market_data import get_live_option_leg_data
            info = get_ticker_info(t.ticker)
            if info and info.get('current_price'):
                cp = float(info['current_price'])
                current_price = f"${cp:.2f}"
                
                # Format legs for options_math
                legs_for_math = []
                # Total trade open cost:
                open_tx = next((tx for tx in t.transactions if tx.action == "Open"), None)
                # Since we don't have individual leg prices stored, we divide the total cost by the number of legs as a rough approximation,
                # or just assign the entire cost to one leg and 0 to others so the total sums correctly.
                # Here we assign cost/num_legs to each leg to preserve the correct total net cost.
                cost_per_leg = open_tx.price / len(t.legs) if open_tx and t.legs else 0.0
                
                for leg in t.legs:
                    price = cost_per_leg
                    iv = 0.0
                    expiry_str = pd.to_datetime(leg.expiry).strftime('%Y-%m-%d')
                    leg_data = get_live_option_leg_data(t.ticker, expiry_str, leg.strike, leg.option_type)
                    if leg_data:
                        bid = leg_data.get('bid', 0.0)
                        ask = leg_data.get('ask', 0.0)
                        
                        if leg.position == "Sell" and bid > 0:
                            price = bid
                        elif leg.position == "Buy" and ask > 0:
                            price = ask
                        else:
                            price = leg_data.get('lastPrice', price)
                            
                        iv = leg_data.get('impliedVolatility', 0.0) * 100

                    legs_for_math.append({
                        "action": leg.position,
                        "qty": 1, # approx
                        "type": leg.option_type,
                        "strike": leg.strike,
                        "price": price,
                        "expiry": pd.to_datetime(leg.expiry),
                        "iv": iv
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
        
        # Initialize details visibility state
        details_key = f"show_details_{t.id}"
        if details_key not in st.session_state:
            st.session_state[details_key] = False
            
        if cols[11].button("Details", key=f"details_btn_{t.id}"):
            st.session_state[details_key] = not st.session_state[details_key]
        
        if cols[12].button("Edit", key=f"edit_{t.id}"):
            st.session_state.edit_trade_id = t.id
            st.switch_page("pages/1_Trade.py")
            
        if cols[13].button("Close", key=f"close_{t.id}"):
            st.session_state.close_trade_id = t.id
            st.switch_page("pages/4_Close Trade.py")
            
        if st.session_state[details_key]:
            st.write("**Legs**")
            legs_df = []
            for leg in t.legs:
                legs_df.append({
                    "Action": leg.position,
                    "Quantity": 1,
                    "Type": leg.option_type,
                    "Strike": f"${leg.strike:.2f}",
                    "Expiry": leg.expiry,
                })
            st.table(pd.DataFrame(legs_df))
            
            st.write("**Metrics Comparison (Current vs. Opening)**")
            comp_cols = st.columns(4)
            
            # Opening stats
            open_up = f"${t.underlying_price_at_open:.2f}" if t.underlying_price_at_open else "N/A"
            open_pop = f"{t.probability_of_profit*100:.1f}%" if t.probability_of_profit is not None else "N/A"
            open_pmp = f"{t.probability_max_profit*100:.1f}%" if t.probability_max_profit is not None else "N/A"
            open_pml = f"{t.probability_max_loss*100:.1f}%" if t.probability_max_loss is not None else "N/A"
            
            # Current stats from metrics dictionary calculated earlier
            curr_up = current_price
            
            if metrics:
                curr_pop = f"{metrics.get('pop', 0)*100:.1f}%"
                curr_pmp = f"{metrics.get('pop_max_profit', 0)*100:.1f}%"
                curr_pml = f"{metrics.get('pop_max_loss', 0)*100:.1f}%"
            else:
                curr_pop = "N/A"
                curr_pmp = "N/A"
                curr_pml = "N/A"
            
            def safe_delta(curr, open_val, is_currency=False):
                if curr != "N/A" and open_val != "N/A":
                    try:
                        c_val = float(curr.replace('$', '').replace('%', ''))
                        o_val = float(open_val.replace('$', '').replace('%', ''))
                        diff = c_val - o_val
                        return f"{diff:.2f}" if is_currency else f"{diff:.1f}%"
                    except:
                        return None
                return None
                
            comp_cols[0].metric("Underlying Price", curr_up, delta=safe_delta(curr_up, open_up, True))
            comp_cols[1].metric("Probability of Profit", curr_pop, delta=safe_delta(curr_pop, open_pop))
            comp_cols[2].metric("Prob. of Max Profit", curr_pmp, delta=safe_delta(curr_pmp, open_pmp))
            comp_cols[3].metric("Prob. of Max Loss", curr_pml, delta=safe_delta(curr_pml, open_pml), delta_color="inverse")
            
            st.write(f"*Opening values:* Price: {open_up} | POP: {open_pop} | Prob Max Profit: {open_pmp} | Prob Max Loss: {open_pml}")
            
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
        
else:
    st.info("No trades found in the journal.")

db.close()
