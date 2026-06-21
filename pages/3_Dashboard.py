import streamlit as st
import pandas as pd
import plotly.express as px
from src.db import SessionLocal
from src.models import Trade, Transaction

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("Performance Dashboard")

db = SessionLocal()

active_portfolio_id = st.session_state.get("active_portfolio_id")
if active_portfolio_id:
    trades = db.query(Trade).filter(Trade.portfolio_id == active_portfolio_id).all()
    transactions = db.query(Transaction).join(Trade).filter(Trade.portfolio_id == active_portfolio_id).all()
else:
    trades = []
    transactions = []
    st.warning("No portfolio selected. Please select one from the sidebar.")

if not trades and active_portfolio_id:
    st.info("Not enough data to display dashboard. Add some trades first!")
elif trades:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trades", len(trades))
    with col2:
        # Placeholder for win rate
        st.metric("Win Rate", "0%")
    with col3:
        st.metric("Total Commissions", sum(t.commission for t in transactions))
    with col4:
        # Placeholder for PnL
        st.metric("Total PnL", "$0.00")
        
    st.subheader("Equity Curve (Placeholder)")
    # We will build a real equity curve later based on closed trades
    st.line_chart([0, 10, 5, 20, 15, 30])
    
db.close()
