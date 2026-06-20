import streamlit as st
import pandas as pd
from datetime import datetime
from src.db import SessionLocal
from src.models import Trade, Transaction

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

st.markdown(f"""
#### Underlying
<div style='display: flex; gap: 40px; margin-bottom: 15px; font-size: 1.1rem;'>
    <div style='display: flex; flex-direction: column;'><b>Ticker</b> <span>{trade.ticker}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Name</b> <span>{trade.underlying_name}</span></div>
</div>

#### Position
<div style='display: flex; gap: 40px; font-size: 1.1rem;'>
    <div style='display: flex; flex-direction: column;'><b>Strategy</b> <span>{trade.strategy_type}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Date opened</b> <span>{trade.date_opened.strftime('%Y-%m-%d')}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Cost of trade</b> <span>${display_cost:.2f}</span></div>
</div>
""", unsafe_allow_html=True)

st.divider()

st.subheader("Closing Information")

with st.form("close_trade_form"):
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    
    close_date = fcol1.date_input("Close Date", value=datetime.today())
    
    close_type = fcol2.selectbox("Type of Close", [
        "Closing for profit",
        "Closing for loss",
        "Rolling",
        "Expired",
        "Closed by broker"
    ])
    
    closing_price = fcol3.number_input("Closing Price (Net)", step=0.01, format="%.2f", help="Net credit received (+) or debit paid (-) to close")
    
    commission = fcol4.number_input("Closing Commission", value=0.0, step=0.01, format="%.2f")
    
    submit = st.form_submit_button("Submit Close")
    
    if submit:
        # Update trade status
        trade.status = close_type
        
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
