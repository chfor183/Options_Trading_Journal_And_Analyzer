import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta
from src.db import SessionLocal
from src.models import Trade, Transaction
from src.market_data import get_ticker_info

st.set_page_config(page_title="Trading Journal", page_icon="📓", layout="wide")
st.title("Trading Journal")

db = SessionLocal()

if "sort_column" not in st.session_state:
    st.session_state.sort_column = "Date Opened"
if "sort_desc" not in st.session_state:
    st.session_state.sort_desc = True

active_portfolio_id = st.session_state.get("active_portfolio_id")

# Reset pagination on portfolio change
if "journal_last_portfolio_id" not in st.session_state:
    st.session_state.journal_last_portfolio_id = active_portfolio_id
elif active_portfolio_id != st.session_state.journal_last_portfolio_id:
    st.session_state.current_page = 1
    st.session_state.journal_last_portfolio_id = active_portfolio_id

if active_portfolio_id:
    trades = db.query(Trade).filter(Trade.portfolio_id == active_portfolio_id).all()
else:
    trades = []
    st.warning("No portfolio selected. Please select one from the sidebar.")

if trades:
    # Initialize session state for checkboxes
    if "selected_trades" not in st.session_state:
        st.session_state.selected_trades = {}
    
    st.write("### All Trades")
    
    # Custom CSS to prevent button text wrapping and force perfect text centering
    st.markdown("""
        <style>
        div.stButton > button {
            white-space: nowrap;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            text-align: center !important;
            padding: 0px 4px !important;
        }
        div.stButton > button * {
            display: inline-flex !important;
            justify-content: center !important;
            align-items: center !important;
            text-align: center !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    components.html("""
    <script>
    const observer = new MutationObserver(() => {
        const parentDoc = window.parent.document;
        const buttons = parentDoc.querySelectorAll('.stButton button');
        const sortableHeaders = ["#", "Ticker", "Name", "Date Opened", "Date Closed", "Strategy", "DTE", "Exp. Move", "Cost", "PnL", "Status"];
        buttons.forEach(b => {
            const text = b.innerText.trim();
            if (sortableHeaders.includes(text)) {
                b.style.backgroundColor = 'transparent';
                b.style.border = 'none';
                b.style.boxShadow = 'none';
                b.style.padding = '0';
                b.style.fontWeight = 'bold';
                b.style.textAlign = 'left';
                b.style.justifyContent = 'flex-start';
                b.style.minHeight = 'unset';
                b.style.height = 'auto';
                b.style.color = 'inherit';
                
                const p = b.querySelector('p');
                if (p) {
                    p.style.fontWeight = 'bold';
                    p.style.color = 'inherit';
                    p.style.margin = '0';
                }
            }
        });
    });
    observer.observe(window.parent.document.body, {childList: true, subtree: true});
    </script>
    """, height=0, width=0)
    
    def reset_page():
        st.session_state.current_page = 1
    
    # Filtering logic
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    filter_ticker = filter_col1.text_input("Filter by Ticker", on_change=reset_page)
    
    date_options = ["Last 7 days", "Last month", "Last 3 Months", "Last Year", "YTD", "All"]
    date_filter = filter_col2.selectbox("Filter by Date", date_options, index=5, on_change=reset_page)
    
    today = datetime.today().date()
    if date_filter == "Last 7 days":
        start_date = today - timedelta(days=7)
    elif date_filter == "Last month":
        start_date = today - timedelta(days=30)
    elif date_filter == "Last 3 Months":
        start_date = today - timedelta(days=90)
    elif date_filter == "Last Year":
        start_date = today - timedelta(days=365)
    elif date_filter == "YTD":
        start_date = datetime(today.year, 1, 1).date()
    else:
        start_date = datetime.min.date()
        
    filter_status = filter_col3.radio("Filter by Status", ["All", "Open Trades", "Closed Trades"], horizontal=True, on_change=reset_page)
    
    strategy_options = ["All"] + list(set([t.strategy_type for t in trades]))
    filter_strategy = filter_col4.selectbox("Filter by Strategy", strategy_options, on_change=reset_page)

    # Apply filters
    filtered_trades = trades
    if filter_ticker:
        filtered_trades = [t for t in filtered_trades if filter_ticker.upper() in t.ticker.upper()]
    if date_filter != "All":
        def get_reference_date(t):
            if t.status == "Open":
                return t.date_opened.date()
            else:
                close_dates = [tx.date for tx in t.transactions if tx.action != "Open"]
                if close_dates:
                    return max(close_dates).date()
                return t.date_opened.date()
                
        filtered_trades = [t for t in filtered_trades if get_reference_date(t) >= start_date]
    if filter_status != "All":
        if filter_status == "Open Trades":
            filtered_trades = [t for t in filtered_trades if t.status == "Open"]
        elif filter_status == "Closed Trades":
            filtered_trades = [t for t in filtered_trades if t.status != "Open"]
            
    if filter_strategy != "All":
        filtered_trades = [t for t in filtered_trades if t.strategy_type == filter_strategy]
        
    def get_sort_value(t, col_name):
        if col_name == "#":
            return t.trade_number or 0
        elif col_name == "Ticker":
            return t.ticker or ""
        elif col_name == "Name":
            return t.underlying_name or ""
        elif col_name == "Date Opened":
            return t.date_opened or datetime.min
        elif col_name == "Date Closed":
            close_dates = [tx.date for tx in t.transactions if tx.action != "Open"]
            return max(close_dates) if close_dates else datetime.min
        elif col_name == "Strategy":
            return t.strategy_type or ""
        elif col_name == "DTE":
            if t.legs:
                first_leg = min(t.legs, key=lambda l: l.expiry)
                return (first_leg.expiry - t.date_opened.date()).days
            return -1
        elif col_name == "Exp. Move":
            return t.expected_move or ""
        elif col_name == "Cost":
            open_tx = next((tx for tx in t.transactions if tx.action == "Open"), None)
            return open_tx.price if open_tx else 0.0
        elif col_name == "PnL":
            val = 0.0
            for tx in t.transactions:
                if tx.action == "Open":
                    val += -tx.price - tx.commission
                else:
                    val += tx.price - tx.commission
            return val
        elif col_name == "Status":
            return t.status or ""
        return 0

    # Sort
    reverse_sort = st.session_state.sort_desc
    sort_col = st.session_state.sort_column

    def sorting_key(trade):
        val = get_sort_value(trade, sort_col)
        if isinstance(val, str):
            return val.lower()
        return val

    filtered_trades.sort(key=sorting_key, reverse=reverse_sort)
    
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
            
    # Header row
    # Adjusting column widths so Details/Edit/Action buttons have a bit more space
    # Ticker was index 2 with width 0.9 -> reduced to 0.6 (reduced by 0.3)
    # Name was index 3 with width 1.3 -> increased to 1.6 (increased by 0.3)
    # Cost was index 11 with width 1.0 -> increased to 1.2 (increased by 0.2)
    # Status changed to 1.7
    # Date Opened and Date Closed increased by 0.1 each (from 1.0 to 1.1)
    col_widths = [0.4, 0.5, 0.6, 1.4, 1.1, 1.1, 1.5, 0.5, 1.0, 1.1, 1.0, 1.2, 1.2, 1.7, 0.8, 0.7, 0.9]
    cols = st.columns(col_widths)
    headers_config = [
        ("", False),
        ("#", True),
        ("Ticker", True),
        ("Name", True),
        ("Date Opened", True),
        ("Date Closed", True),
        ("Strategy", True),
        ("DTE", True),
        ("Exp. Move", True),
        ("Current or Closed Price", False),
        ("Break-Even", False),
        ("Cost", True),
        ("PnL", True),
        ("Status", True),
        ("Details", False),
        ("Edit", False),
        ("Action", False)
    ]
    
    for col, (header, sortable) in zip(cols, headers_config):
        if sortable:
            if col.button(header, key=f"hdr_{header}", use_container_width=True):
                if st.session_state.sort_column == header:
                    st.session_state.sort_desc = not st.session_state.sort_desc
                else:
                    st.session_state.sort_column = header
                    st.session_state.sort_desc = False
                st.rerun()
        else:
            col.markdown(f"<div style='text-align: left; white-space: normal; font-weight: bold; font-size: 13px; line-height: 1.2;'>{header}</div>", unsafe_allow_html=True)
    
    # Pagination Logic
    ROWS_PER_PAGE = 10
    total_pages = max(1, math.ceil(len(filtered_trades) / ROWS_PER_PAGE))
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1
        
    if st.session_state.current_page > total_pages:
        st.session_state.current_page = total_pages
        
    start_idx = (st.session_state.current_page - 1) * ROWS_PER_PAGE
    end_idx = start_idx + ROWS_PER_PAGE
    paginated_trades = filtered_trades[start_idx:end_idx]

    trade_data_list = []
    with st.spinner("Fetching live data for trades..."):
        for t in paginated_trades:
            # Calculate Cost and PnL
            open_tx = next((tx for tx in t.transactions if tx.action == "Open"), None)
            raw_cost = open_tx.price if open_tx else 0.0
            display_cost = -raw_cost # Positive for credit received, negative for debit paid
            
            # Find close date
            close_dates = [tx.date for tx in t.transactions if tx.action != "Open"]
            close_date_str = max(close_dates).strftime('%Y-%m-%d') if close_dates else "-"
            
            # Calculate DTE (Days to Expiry at time of opening)
            if t.legs:
                first_leg = min(t.legs, key=lambda l: l.expiry)
                dte_val = (first_leg.expiry - t.date_opened.date()).days
                if dte_val <= 0:
                    dte_val = 1
                dte_str = str(dte_val)
            else:
                dte_str = "-"
            
            pnl = 0.0
            for tx in t.transactions:
                if tx.action == "Open":
                    pnl += -tx.price - tx.commission
                else:
                    pnl += tx.price - tx.commission

            # Try to get Current Price and Breakevens
            current_price = "N/A"
            breakevens = "N/A"
            metrics = {}
            
            if t.status == "Open":
                try:
                    from src.options_math import calculate_metrics
                    from src.market_data import get_barchart_live_option_leg_data
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
                            price = leg.price
                            iv = leg.iv
                            expiry_str = pd.to_datetime(leg.expiry).strftime('%Y-%m-%d')
                            leg_data = get_barchart_live_option_leg_data(t.ticker, expiry_str, leg.strike, leg.option_type)
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
                                "qty": leg.quantity if leg.quantity else 1,
                                "type": leg.option_type,
                                "strike": leg.strike,
                                "price": price,
                                "expiry": pd.to_datetime(leg.expiry),
                                "iv": iv
                            })
                            
                        metrics = calculate_metrics(legs_for_math, cp)
                        bes = metrics.get('breakevens', [])
                        if bes:
                            breakevens = ", ".join([f"&#36;{b:.2f}" for b in bes])
                except Exception as e:
                    pass
            else:
                close_tx = next((tx for tx in t.transactions if tx.action != "Open"), None)
                if close_tx:
                    if close_tx.price < 0:
                        current_price = f"-${abs(close_tx.price):.2f}"
                    else:
                        current_price = f"${close_tx.price:.2f}"
                else:
                    current_price = "N/A"
                
                try:
                    from src.options_math import calculate_metrics
                    legs_for_math = []
                    for leg in t.legs:
                        legs_for_math.append({
                            "action": leg.position,
                            "qty": leg.quantity if leg.quantity else 1,
                            "type": leg.option_type,
                            "strike": leg.strike,
                            "price": float(leg.price),
                            "expiry": pd.to_datetime(leg.expiry),
                            "iv": float(leg.iv)
                        })
                    cp = t.underlying_price_at_open if t.underlying_price_at_open else (t.legs[0].strike if t.legs else 100.0)
                    metrics = calculate_metrics(legs_for_math, cp)
                    bes = metrics.get('breakevens', [])
                    if bes:
                        breakevens = ", ".join([f"&#36;{b:.2f}" for b in bes])
                except Exception as e:
                    pass
                
            trade_data_list.append({
                "t": t,
                "display_cost": display_cost,
                "pnl": pnl,
                "current_price": current_price,
                "breakevens": breakevens,
                "metrics": metrics,
                "close_date_str": close_date_str,
                "dte_str": dte_str
            })

    for item in trade_data_list:
        t = item["t"]
        display_cost = item["display_cost"]
        pnl = item["pnl"]
        current_price = item["current_price"]
        breakevens = item["breakevens"]
        metrics = item["metrics"]
        close_date_str = item["close_date_str"]
        dte_str = item["dte_str"]
        
        # Calculate Expected Move value numerically for the pinescript
        em_val = 0.0
        try:
            if t.expected_move:
                # Expected move might be e.g. "Bullish ↗" or "Neutral →", let's parse actual expected move width
                # Let's extract numeric expected move from some standard calculation or if average IV is available
                if t.legs:
                    first_leg = min(t.legs, key=lambda l: l.expiry)
                    days_to_expiry = (first_leg.expiry - t.date_opened.date()).days
                    if days_to_expiry <= 0:
                        days_to_expiry = 1
                else:
                    days_to_expiry = 30
                term = days_to_expiry / 365.0
                ivs = [float(leg.iv) for leg in t.legs if leg.iv and float(leg.iv) > 0]
                avg_iv = (sum(ivs) / len(ivs)) / 100.0 if ivs else 0.3
                em_pct = avg_iv * np.sqrt(term)
                underlying_price = t.underlying_price_at_open if t.underlying_price_at_open else 100.0
                em_val = float(underlying_price * em_pct)
        except Exception as e:
            pass

        cols = st.columns(col_widths)
        
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
        
        trade_num = t.trade_number if t.trade_number is not None else ""
        cols[1].markdown(f"<div style='text-align: left;'>{trade_num}</div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div style='text-align: left;'>{t.ticker}</div>", unsafe_allow_html=True)
        cols[3].markdown(f"<div style='text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{t.underlying_name}</div>", unsafe_allow_html=True)
        cols[4].markdown(f"<div style='text-align: left;'>{t.date_opened.strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)
        cols[5].markdown(f"<div style='text-align: left;'>{close_date_str}</div>", unsafe_allow_html=True)
        cols[6].markdown(f"<div style='text-align: left;'>{t.strategy_type}</div>", unsafe_allow_html=True)
        cols[7].markdown(f"<div style='text-align: left;'>{dte_str}</div>", unsafe_allow_html=True)
        cols[8].markdown(f"<div style='text-align: left;'>{t.expected_move}</div>", unsafe_allow_html=True)
        cols[9].markdown(f"<div style='text-align: left;'>{current_price}</div>", unsafe_allow_html=True)
        cols[10].markdown(f"<div style='text-align: left;'>{breakevens}</div>", unsafe_allow_html=True)
        cols[11].markdown(f"<div style='text-align: left;'>${display_cost:.2f}</div>", unsafe_allow_html=True)
        
        color = "green" if pnl > 0 else "red" if pnl < 0 else "inherit"
        cols[12].markdown(f"<div style='text-align: left; color: {color};'>${pnl:.2f}</div>", unsafe_allow_html=True)
        
        cols[13].markdown(f"<div style='text-align: left;'>{t.status}</div>", unsafe_allow_html=True)
        
        # Initialize details visibility state
        if "expanded_trade_id" not in st.session_state:
            st.session_state.expanded_trade_id = None
            
        if cols[14].button("Details", key=f"details_btn_{t.id}", use_container_width=True):
            if st.session_state.expanded_trade_id == t.id:
                st.session_state.expanded_trade_id = None
            else:
                st.session_state.expanded_trade_id = t.id
            st.rerun()
        
        if cols[15].button("Edit", key=f"edit_{t.id}", use_container_width=True):
            st.session_state.edit_trade_id = t.id
            st.session_state[f"loaded_{t.id}"] = False
            st.switch_page("pages/1_Trade.py")
            
        if t.status == "Open":
            if cols[16].button("Close", key=f"close_{t.id}", use_container_width=True):
                st.session_state.close_trade_id = t.id
                st.switch_page("pages/5_Close Trade.py")
        else:
            if cols[16].button("Reopen", key=f"reopen_{t.id}", use_container_width=True):
                trade_to_reopen = db.query(Trade).filter(Trade.id == t.id).first()
                if trade_to_reopen:
                    trade_to_reopen.status = "Open"
                    txs_to_delete = [tx for tx in trade_to_reopen.transactions if tx.action != "Open"]
                    for tx in txs_to_delete:
                        db.delete(tx)
                    db.commit()
                    st.rerun()
            
        if st.session_state.expanded_trade_id == t.id:
            st.write("**Legs**")
            legs_df = []
            
            for leg in t.legs:
                legs_df.append({
                    "Action": leg.position,
                    "Quantity": leg.quantity if leg.quantity else 1,
                    "Type": leg.option_type,
                    "Strike": f"${leg.strike:.2f}",
                    "Price": f"${leg.price:.3f}",
                    "Delta": f"{leg.delta:.4f}",
                    "IV (%)": f"{leg.iv:.2f}",
                    "Expiry": leg.expiry,
                })
            st.table(pd.DataFrame(legs_df))
            
            st.write("**Metrics Comparison (Current vs. Opening)**")
            comp_cols = st.columns(5)
            
            # Opening stats
            open_up = f"${t.underlying_price_at_open:.2f}" if t.underlying_price_at_open else "N/A"
            open_pop = f"{t.probability_of_profit*100:.1f}%" if t.probability_of_profit is not None else "N/A"
            open_pol = f"{t.probability_of_loss*100:.1f}%" if t.probability_of_loss is not None else "N/A"
            open_pmp = f"{t.probability_max_profit*100:.1f}%" if t.probability_max_profit is not None else "N/A"
            open_pml = f"{t.probability_max_loss*100:.1f}%" if t.probability_max_loss is not None else "N/A"
            
            # Current stats from metrics dictionary calculated earlier
            curr_up = current_price
            
            if t.status == "Open" and metrics:
                curr_pop = f"{metrics.get('pop', 0)*100:.1f}%"
                curr_pol = f"{metrics.get('pol', 0)*100:.1f}%"
                curr_pmp = f"{metrics.get('pop_max_profit', 0)*100:.1f}%"
                curr_pml = f"{metrics.get('pop_max_loss', 0)*100:.1f}%"
            else:
                curr_pop = "N/A"
                curr_pol = "N/A"
                curr_pmp = "N/A"
                curr_pml = "N/A"
            
            def safe_delta(curr, open_val, is_currency=False, inverse=False):
                if curr != "N/A" and open_val != "N/A":
                    try:
                        c_val = float(curr.replace('$', '').replace('%', ''))
                        o_val = float(open_val.replace('$', '').replace('%', ''))
                        diff = c_val - o_val
                        color = "normal"
                        if inverse:
                            color = "inverse"
                        return f"{diff:.2f}" if is_currency else f"{diff:.1f}%"
                    except:
                        return None
                return None
                
            if t.status == "Open":
                comp_cols[0].metric("Underlying Price", curr_up, delta=safe_delta(curr_up, open_up, True))
            else:
                comp_cols[0].metric("Closing Price", curr_up)
                
            comp_cols[1].metric("Probability of Profit", curr_pop, delta=safe_delta(curr_pop, open_pop))
            comp_cols[2].metric("Probability of Loss", curr_pol, delta=safe_delta(curr_pol, open_pol, inverse=True), delta_color="inverse")
            comp_cols[3].metric("Prob. of Max Profit", curr_pmp, delta=safe_delta(curr_pmp, open_pmp))
            comp_cols[4].metric("Prob. of Max Loss", curr_pml, delta=safe_delta(curr_pml, open_pml, inverse=True), delta_color="inverse")
            
            st.write(f"*Opening values:* Price: {open_up} | POP: {open_pop} | POL: {open_pol} | Prob Max Profit: {open_pmp} | Prob Max Loss: {open_pml}")
            
            if t.idea_url:
                st.write(f"**Idea URL:** [{t.idea_url}]({t.idea_url})")

            # --- Copyable Trade Idea Feature ---
            idea_col1, idea_col2 = st.columns(2)
            
            if t.legs:
                first_leg = min(t.legs, key=lambda l: l.expiry)
                days_to_expiry = (first_leg.expiry - t.date_opened.date()).days
                if days_to_expiry <= 0:
                    days_to_expiry = 1
            else:
                days_to_expiry = 30
                
            term = days_to_expiry / 365.0
            ivs = [float(leg.iv) for leg in t.legs if leg.iv and float(leg.iv) > 0]
            avg_iv = (sum(ivs) / len(ivs)) / 100.0 if ivs else 0.3
            
            import numpy as np
            em_pct = avg_iv * np.sqrt(term)
            underlying_price = t.underlying_price_at_open if t.underlying_price_at_open else 100.0
            em_range_val = underlying_price * em_pct
            lower_bound = underlying_price - em_range_val
            upper_bound = underlying_price + em_range_val
            
            legs_formatted_list = []
            for leg in t.legs:
                action_str = "SELL" if leg.position in ["Short", "Sell"] else "BUY"
                qty_prefix = "-" if leg.position in ["Short", "Sell"] else "+"
                qty_val = leg.quantity if leg.quantity else 1
                leg_line = f"- {action_str} {qty_prefix}{qty_val} {t.ticker} {leg.expiry.strftime('%Y-%m-%d')} {float(leg.strike):.2f} {leg.option_type} @ ${float(leg.price):.3f} (Delta: {float(leg.delta):.4f}, IV: {float(leg.iv):.2f}%)"
                legs_formatted_list.append(leg_line)
            legs_text = "\n".join(legs_formatted_list)
            
            cost_suffix = "Net Credit" if display_cost >= 0 else "Net Debit"
            cost_str = f"${abs(display_cost):.2f} {cost_suffix}"
            pop_str = f"{t.probability_of_profit*100:.1f}%" if t.probability_of_profit is not None else "N/A"
            
            idea_text = f"{t.ticker} - {t.strategy_type or 'N/A'} ({days_to_expiry} DTE) @ {cost_str}\n" \
                        f"Ticker : {t.ticker}\n" \
                        f"Name : {t.underlying_name or 'N/A'}\n" \
                        f"Date Opened : {t.date_opened.strftime('%Y-%m-%d')}\n" \
                        f"Price of underlying at opening : {f'${t.underlying_price_at_open:.2f}' if t.underlying_price_at_open else 'N/A'}\n" \
                        f"Expected Move : ±{em_pct*100:.1f}% [{lower_bound:.2f},{upper_bound:.2f}]\n" \
                        f"Strategy : {t.strategy_type or 'N/A'}\n" \
                        f"Legs : \n" \
                        f"{legs_text}\n" \
                        f"Cost of trade : {cost_str}\n" \
                        f"Probability of profit : {pop_str}"
            
            # Formulate the JSON structure precisely as expected by the Pinescript
            import json
            sorted_strikes = sorted([float(leg.strike) for leg in t.legs if leg.strike])
            pinescript_json_dict = {
                "strategy": t.strategy_type or "N/A",
                "underlying_open": float(t.underlying_price_at_open) if t.underlying_price_at_open else 0.0,
                "premium": float(abs(display_cost)) / 100.0,
                "open_date": t.date_opened.strftime('%Y-%m-%d'),
                "expiry_date": first_leg.expiry.strftime('%Y-%m-%d') if t.legs else t.date_opened.strftime('%Y-%m-%d'),
                "expected_move": round(float(em_range_val), 2),
            }
            if t.probability_of_profit is not None:
                pinescript_json_dict["pop"] = round(float(t.probability_of_profit) * 100, 1)
            else:
                pinescript_json_dict["pop"] = 0.0
                
            for idx, strike in enumerate(sorted_strikes[:4], start=1):
                pinescript_json_dict[f"strike{idx}"] = strike
                
            pinescript_json_str = json.dumps(pinescript_json_dict, indent=2)

            with idea_col1:
                st.write("**Copyable Trade Idea**")
                st.code(idea_text, language="text")

            with idea_col2:
                st.write("**TradingView Pine Script JSON**")
                st.code(pinescript_json_str, language="json")
            # ------------------------------------
            
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
