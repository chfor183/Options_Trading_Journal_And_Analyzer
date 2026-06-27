import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from src.db import SessionLocal
from src.models import Trade, Transaction

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("Performance Dashboard")

def get_dte_category(dte):
    if dte <= 0:
        return "0 DTE"
    elif 1 <= dte <= 3:
        return "1-3 DTE"
    elif 4 <= dte <= 7:
        return "4-7 DTE"
    elif 8 <= dte <= 20:
        return "8-20 DTE"
    elif 21 <= dte <= 60:
        return "21-60 DTE"
    elif 61 <= dte <= 200:
        return "61-200 DTE"
    else:
        return "201+ DTE"

def analyze_trade(trade):
    pnl = 0.0
    premium_collected = 0.0
    premium_paid = 0.0
    total_commission = 0.0
    close_date = None
    
    for tx in trade.transactions:
        total_commission += tx.commission
        if tx.action == "Open":
            pnl -= tx.price
            if tx.price > 0:
                premium_paid += tx.price
            else:
                premium_collected += abs(tx.price)
        else:
            pnl += tx.price
            if tx.price > 0:
                premium_collected += tx.price
            else:
                premium_paid += abs(tx.price)
            
            if close_date is None or tx.date > close_date:
                close_date = tx.date
                
    pnl -= total_commission
    
    dte = 0
    if trade.legs:
        first_leg = min(trade.legs, key=lambda l: l.expiry)
        dte = (first_leg.expiry - trade.date_opened.date()).days
            
    return {
        "pnl": pnl,
        "premium_collected": premium_collected,
        "premium_paid": premium_paid,
        "total_commission": total_commission,
        "close_date": close_date.date() if close_date else None,
        "dte_category": get_dte_category(dte),
        "is_winner": pnl > 0,
        "is_loser": pnl < 0
    }

db = SessionLocal()

active_portfolio_id = st.session_state.get("active_portfolio_id")
if active_portfolio_id:
    all_trades = db.query(Trade).filter(Trade.portfolio_id == active_portfolio_id).all()
else:
    all_trades = []
    st.warning("No portfolio selected. Please select one from the sidebar.")

if not all_trades and active_portfolio_id:
    st.info("Not enough data to display dashboard. Add some trades first!")
elif all_trades:
    
    st.sidebar.header("Filters")
    
    # Date Interval Filter
    date_options = ["Last 7 days", "Last month", "Last 3 Months", "Last Year", "YTD", "All"]
    # Select index 2 for "Last 3 Months"
    date_filter = st.sidebar.selectbox("Date Interval", date_options, index=2)
    
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
        
    # Status Filter
    status_filter = st.sidebar.selectbox("Trade Status", ["Both", "All Closed Trades", "All Open Trades"])
    
    filtered_data = []
    for t in all_trades:
        stats = analyze_trade(t)
        
        # Determine reference date
        if t.status == "Open":
            ref_date = t.date_opened.date()
        else:
            ref_date = stats['close_date'] if stats['close_date'] else t.date_opened.date()
            
        # Apply Date filter
        if ref_date < start_date:
            continue
            
        # Apply Status filter
        if status_filter == "All Closed Trades" and t.status == "Open":
            continue
        if status_filter == "All Open Trades" and t.status != "Open":
            continue
            
        filtered_data.append({
            "Trade": t,
            "Reference Date": ref_date,
            "PnL": stats["pnl"],
            "Premium Collected": stats["premium_collected"],
            "Premium Paid": stats["premium_paid"],
            "Commission": stats["total_commission"],
            "Expected Move": t.expected_move if t.expected_move else "N/A",
            "Strategy Type": t.strategy_type if t.strategy_type else "N/A",
            "Category": t.category if t.category else "N/A",
            "DTE Category": stats["dte_category"],
            "Type of Close": t.status,
            "Is Winner": stats["is_winner"],
            "Is Loser": stats["is_loser"]
        })
        
    if not filtered_data:
        st.warning("No trades match the selected filters.")
    else:
        # Calculate Aggregates
        total_trades = len(filtered_data)
        wins = sum(1 for d in filtered_data if d["Is Winner"])
        losses = sum(1 for d in filtered_data if d["Is Loser"])
        batting_avg = (wins / total_trades * 100) if total_trades > 0 else 0
        
        winning_pnls = [d["PnL"] for d in filtered_data if d["Is Winner"]]
        losing_pnls = [d["PnL"] for d in filtered_data if d["Is Loser"]]
        avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0
        avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0
        
        total_comm = sum(d["Commission"] for d in filtered_data)
        total_prem_col = sum(d["Premium Collected"] for d in filtered_data)
        total_prem_paid = sum(d["Premium Paid"] for d in filtered_data)
        total_pnl = sum(d["PnL"] for d in filtered_data)
        
        st.subheader("Key Metrics")
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Trades", total_trades)
        m2.metric("Batting Avg", f"{batting_avg:.1f}%")
        m3.metric("Wins / Losses", f"{wins} / {losses}")
        m4.metric("Average Win", f"${avg_win:.2f}")
        m5.metric("Average Loss", f"${avg_loss:.2f}")
        
        m6, m7, m8, m9, m10 = st.columns(5)
        m6.metric("Total Commission", f"${total_comm:.2f}")
        m7.metric("Premium Collected", f"${total_prem_col:.2f}")
        m8.metric("Premium Paid", f"${total_prem_paid:.2f}")
        m9.metric("Net PnL", f"${total_pnl:.2f}")
        
        st.divider()
        
        st.subheader("Equity Curve")
        # Prepare Equity Curve Data
        df_equity = pd.DataFrame([{ "Date": d["Reference Date"], "PnL": d["PnL"] } for d in filtered_data])
        df_equity.sort_values(by="Date", inplace=True)
        # Combine PnL for trades closed/opened on the same date
        df_equity = df_equity.groupby("Date").sum().reset_index()
        df_equity["Cumulative PnL"] = df_equity["PnL"].cumsum()
        
        if not df_equity.empty:
            # We want to start the curve at 0 on the earliest date - 1 day, or just plot what we have
            fig = px.line(df_equity, x="Date", y="Cumulative PnL", markers=True, 
                          title="Cumulative PnL Over Time",
                          labels={"Cumulative PnL": "Cumulative Net PnL ($)"})
            fig.update_layout(yaxis_tickprefix="$", hovermode="x unified")
            # Fill area below the line
            fig.update_traces(fill='tozeroy')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No timeline data to display equity curve.")
            
        st.divider()
        
        st.subheader("Detailed Breakdown")
        
        breakdown_by = st.selectbox("Analyze Performance By:", 
            ["Expected Move", "Strategy Type", "Category", "DTE Category", "Type of Close"])
            
        # Group data
        df_all = pd.DataFrame(filtered_data)
        
        grouped = df_all.groupby(breakdown_by).agg(
            Trades=("Trade", "count"),
            Wins=("Is Winner", "sum"),
            Losses=("Is Loser", "sum"),
            Total_PnL=("PnL", "sum"),
            Avg_Win=("PnL", lambda x: x[x > 0].mean() if len(x[x > 0]) > 0 else 0),
            Avg_Loss=("PnL", lambda x: x[x < 0].mean() if len(x[x < 0]) > 0 else 0)
        ).reset_index()
        
        grouped["Batting Avg"] = (grouped["Wins"] / grouped["Trades"] * 100).round(1).astype(str) + "%"
        
        # Formatting for display
        grouped["Total PnL"] = grouped["Total_PnL"].apply(lambda x: f"${x:.2f}")
        grouped["Avg Win"] = grouped["Avg_Win"].apply(lambda x: f"${x:.2f}")
        grouped["Avg Loss"] = grouped["Avg_Loss"].apply(lambda x: f"${x:.2f}")
        
        # Select columns to display
        display_df = grouped[[breakdown_by, "Trades", "Batting Avg", "Wins", "Losses", "Avg Win", "Avg Loss", "Total PnL"]]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)

db.close()
