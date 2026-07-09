import streamlit as st
import pandas as pd
from datetime import datetime
from src.db import SessionLocal
from src.models import Trade, Transaction
from src.market_data import get_ticker_info

st.set_page_config(page_title="Close Trade", page_icon="✖", layout="wide")
st.title("Close Trade")

if "close_trade_id" not in st.session_state:
    st.warning("No trade selected. Please go to the Journal and select a trade to close.")
    if st.button("Go to Journal"):
        st.switch_page("pages/2_Journal.py")
    st.stop()

trade_id = st.session_state.close_trade_id

db = SessionLocal()
trade = db.query(Trade).filter(Trade.id == trade_id).first()

if not trade:
    st.error("Trade not found.")
    st.stop()

# Display basic trade info (read-only)
open_tx = next((tx for tx in trade.transactions if tx.action == "Open"), None)
raw_cost = open_tx.price if open_tx else 0.0
display_cost = -raw_cost

def format_currency(val):
    return f"${val:.2f}" if val is not None else "N/A"

def format_percentage(val):
    return f"{val*100:.1f}%" if val is not None else "N/A"

def format_string(val):
    return str(val) if val is not None else "N/A"

ticker_info = get_ticker_info(trade.ticker)
current_price_str = "N/A"
if ticker_info and ticker_info.get("current_price"):
    current_price_str = format_currency(float(ticker_info["current_price"]))

st.markdown(f"""
#### Underlying
<div style='display: flex; gap: 40px; margin-bottom: 15px; font-size: 1.1rem;'>
    <div style='display: flex; flex-direction: column;'><b>Ticker</b> <span>{trade.ticker}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Name</b> <span>{format_string(trade.underlying_name)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Price at Open</b> <span>{format_currency(trade.underlying_price_at_open)}</span></div>
    <div style='display: flex; flex-direction: column;'><b style='color: #4da6ff;'>Current Price</b> <span style='color: #4da6ff; font-weight: bold;'>{current_price_str}</span></div>
</div>

#### Position
<div style='display: flex; flex-wrap: wrap; gap: 40px; margin-bottom: 15px; font-size: 1.1rem;'>
    <div style='display: flex; flex-direction: column;'><b>Strategy</b> <span>{format_string(trade.strategy_type)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Date opened</b> <span>{trade.date_opened.strftime('%Y-%m-%d')}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Cost of trade</b> <span>{format_currency(display_cost)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Collateral</b> <span>{format_currency(trade.collateral)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Category</b> <span>{format_string(trade.category)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Expected Direction</b> <span>{format_string(trade.expected_direction)}</span></div>
</div>

#### Probabilities & Metrics
<div style='display: flex; flex-wrap: wrap; gap: 40px; margin-bottom: 15px; font-size: 1.1rem;'>
    <div style='display: flex; flex-direction: column;'><b>Max Profit</b> <span>{format_currency(trade.max_profit)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Max Loss</b> <span>{format_currency(trade.max_loss)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>POP</b> <span>{format_percentage(trade.probability_of_profit)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>POL</b> <span>{format_percentage(trade.probability_of_loss)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>P(Max Profit)</b> <span>{format_percentage(trade.probability_max_profit)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>P(Max Loss)</b> <span>{format_percentage(trade.probability_max_loss)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Expected Value</b> <span>{format_currency(trade.expected_value)}</span></div>
</div>
""", unsafe_allow_html=True)

if trade.idea_url:
    st.markdown(f"**Idea URL:** [{trade.idea_url}]({trade.idea_url})")

st.markdown("#### Position Legs")
legs_data = []
for leg in trade.legs:
    legs_data.append({
        "Action": leg.position,
        "Quantity": leg.quantity if leg.quantity else 1,
        "Type": leg.option_type,
        "Strike": f"${leg.strike:.2f}",
        "Price": f"${leg.price:.3f}",
        "Delta": f"{leg.delta:.4f}",
        "IV (%)": f"{leg.iv:.2f}",
        "Expiry": leg.expiry,
    })
st.table(pd.DataFrame(legs_data))

st.divider()

st.subheader("Closing Information")

with st.form("close_trade_form"):
    fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns(5)
    
    close_date = fcol1.date_input("Close Date", value=datetime.today())
    
    close_type = fcol2.selectbox("Type of Close", [
        "Closing for profit",
        "Closing for loss",
        "Closed by stop-loss",
        "Rolling",
        "Expired",
        "Closed by broker"
    ])
    
    closing_price = fcol3.number_input("Closing Price (Net)", step=0.01, format="%.2f", help="Net credit received (+) or debit paid (-) to close")
    
    commission = fcol4.number_input("Closing Commission", value=0.0, step=0.01, format="%.2f")
    
    underlying_price_at_close = fcol5.number_input("Underlying Price", value=None, step=0.01, format="%.2f", help="Price of the underlying asset when closing")
    
    submit = st.form_submit_button("Submit Close")
    
    if submit:
        # Update trade status
        trade.status = close_type
        if underlying_price_at_close is not None:
            trade.underlying_price_at_close = underlying_price_at_close
        
        # Add closing transaction
        new_tx = Transaction(
            trade_id=trade.id,
            date=close_date,
            action=close_type,
            quantity=1, # simplified
            price=closing_price,
            commission=commission
        )
        db.add(new_tx)
        db.commit()
        
        st.success("Trade closed successfully!")
        st.session_state.close_trade_id = None
        st.switch_page("pages/2_Journal.py")

db.close()
