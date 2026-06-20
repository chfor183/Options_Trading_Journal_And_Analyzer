import streamlit as st
import pandas as pd
from src.db import SessionLocal
from src.models import Trade

st.set_page_config(page_title="Trading Journal", page_icon="📓", layout="wide")
st.title("Trading Journal")

db = SessionLocal()

trades = db.query(Trade).all()

if trades:
    data = []
    for t in trades:
        # Calculate current status, total PnL etc here in the future
        data.append({
            "ID": t.id,
            "Date": t.date_opened,
            "Ticker": t.ticker,
            "Strategy": t.strategy_type,
            "Expected Move": t.expected_move,
            "Collateral": t.collateral
        })
    df = pd.DataFrame(data)
    st.dataframe(df, width='stretch')
    
    st.subheader("Manage Trades")
    trade_id_to_delete = st.number_input("Enter Trade ID to Delete", min_value=0, step=1)
    if st.button("Delete Trade"):
        if trade_id_to_delete > 0:
            trade = db.query(Trade).filter(Trade.id == trade_id_to_delete).first()
            if trade:
                db.delete(trade)
                db.commit()
                st.success(f"Trade {trade_id_to_delete} deleted!")
                st.rerun()
            else:
                st.error("Trade not found.")
else:
    st.info("No trades found in the journal.")

db.close()
