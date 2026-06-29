import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from src.db import SessionLocal
from src.models import Trade, Transaction

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# Custom CSS to make the page more vertically compact
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    hr {
        margin: 1.5em 0px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Setup layout for title and filters on the same row
title_col, f_col1, f_col2 = st.columns([1.5, 1, 1.5], vertical_alignment="bottom")
title_col.title("Performance Dashboard")

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
    
    # Date Interval Filter
    date_options = ["Last 7 days", "Last month", "Last 3 Months", "Last Year", "YTD", "All"]
    # Select index 2 for "Last 3 Months"
    date_filter = f_col1.selectbox("Date Interval", date_options, index=2, label_visibility="collapsed")
    
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
        
    # Status Filter Note
    f_col2.info("Showing data for Closed Trades only.", icon="ℹ️")
    
    st.divider()
    
    filtered_data = []
    equity_data = []
    for t in all_trades:
        # Permanently filter for closed trades only
        if t.status == "Open":
            continue
            
        stats = analyze_trade(t)
        
        # Determine reference date
        ref_date = stats['close_date'] if stats['close_date'] else t.date_opened.date()
        
        trade_dict = {
            "Trade": t,
            "Reference Date": ref_date,
            "Month": t.date_opened.strftime("%b %Y"),
            "Month Opened": t.date_opened.strftime("%B"),
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
        }
        
        # Always add to equity data
        equity_data.append(trade_dict)
            
        # Apply Date filter for key metrics and detailed breakdown
        if ref_date < start_date:
            continue
            
        filtered_data.append(trade_dict)
        
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
        
        def styled_metric(label, value, color="inherit"):
            st.markdown(f"""
                <div style="padding: 0.75rem; border-radius: 0.5rem; background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 0.5rem;">
                    <div style="font-size: 0.85rem; color: #aaa; margin-bottom: 0.2rem;">{label}</div>
                    <div style="font-size: 1.6rem; font-weight: 600; color: {color}; line-height: 1.2;">{value}</div>
                </div>
            """, unsafe_allow_html=True)
            
        def get_currency_color(val):
            return "#21c354" if val > 0 else "#ff4b4b" if val < 0 else "inherit"
            
        def get_batting_color(val):
            return "#ff4b4b" if val <= 50 else "#faca2b" if val <= 75 else "#21c354"
        
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            styled_metric("Total Trades", total_trades)
        with m2:
            styled_metric("Batting Avg", f"{batting_avg:.1f}%", get_batting_color(batting_avg))
        with m3:
            styled_metric("Wins / Losses", f"{wins} / {losses}")
        with m4:
            styled_metric("Average Win", f"${avg_win:.2f}", get_currency_color(avg_win))
        with m5:
            styled_metric("Average Loss", f"${avg_loss:.2f}", get_currency_color(avg_loss))
        
        m6, m7, m8, m9, m10 = st.columns(5)
        with m6:
            st.empty() # First column is now empty to center the row visually
        with m7:
            styled_metric("Total Commission", f"${total_comm:.2f}", get_currency_color(total_comm))
        with m8:
            styled_metric("Premium Collected", f"${total_prem_col:.2f}", get_currency_color(total_prem_col))
        with m9:
            styled_metric("Premium Paid", f"${total_prem_paid:.2f}", get_currency_color(total_prem_paid))
        with m10:
            styled_metric("Net PnL", f"${total_pnl:.2f}", get_currency_color(total_pnl))
        
        st.divider()
        
        st.subheader("Detailed Breakdown")
        
        st.write("Analyze Performance By:")
        if "breakdown_by" not in st.session_state:
            st.session_state.breakdown_by = "Expected Move"
            
        btn_cols = st.columns(7)
        if btn_cols[0].button("Expected Move", use_container_width=True, type="primary" if st.session_state.breakdown_by == "Expected Move" else "secondary"):
            st.session_state.breakdown_by = "Expected Move"
            st.rerun()
        if btn_cols[1].button("Strategy Type", use_container_width=True, type="primary" if st.session_state.breakdown_by == "Strategy Type" else "secondary"):
            st.session_state.breakdown_by = "Strategy Type"
            st.rerun()
        if btn_cols[2].button("Category", use_container_width=True, type="primary" if st.session_state.breakdown_by == "Category" else "secondary"):
            st.session_state.breakdown_by = "Category"
            st.rerun()
        if btn_cols[3].button("DTE Category", use_container_width=True, type="primary" if st.session_state.breakdown_by == "DTE Category" else "secondary"):
            st.session_state.breakdown_by = "DTE Category"
            st.rerun()
        if btn_cols[4].button("Type of Close", use_container_width=True, type="primary" if st.session_state.breakdown_by == "Type of Close" else "secondary"):
            st.session_state.breakdown_by = "Type of Close"
            st.rerun()
        if btn_cols[5].button("Month", use_container_width=True, type="primary" if st.session_state.breakdown_by == "Month" else "secondary"):
            st.session_state.breakdown_by = "Month"
            st.rerun()
        if btn_cols[6].button("Month Opened", use_container_width=True, type="primary" if st.session_state.breakdown_by == "Month Opened" else "secondary"):
            st.session_state.breakdown_by = "Month Opened"
            st.rerun()
            
        breakdown_by = st.session_state.breakdown_by
            
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
        
        # Fill any potential NaN values with 0
        grouped.fillna({
            "Trades": 0, "Wins": 0, "Losses": 0, 
            "Total_PnL": 0.0, "Avg_Win": 0.0, "Avg_Loss": 0.0
        }, inplace=True)
        
        # Calculate Batting Avg safely
        grouped["Batting Avg"] = grouped.apply(
            lambda row: f"{(row['Wins'] / row['Trades'] * 100):.1f}%" if row['Trades'] > 0 else "0.0%", 
            axis=1
        )
        
        # Formatting for display
        grouped["Total PnL"] = grouped["Total_PnL"].apply(lambda x: f"${float(x):.2f}")
        grouped["Avg Win"] = grouped["Avg_Win"].apply(lambda x: f"${float(x):.2f}")
        grouped["Avg Loss"] = grouped["Avg_Loss"].apply(lambda x: f"${float(x):.2f}")
        
        # Select columns to display
        display_df = grouped[[breakdown_by, "Trades", "Batting Avg", "Wins", "Losses", "Avg Win", "Avg Loss", "Total PnL"]]
        
        def style_batting(val):
            try:
                v = float(val.strip('%'))
                color = "#ff4b4b" if v <= 50 else "#faca2b" if v <= 75 else "#21c354"
                return f"color: {color}; font-weight: bold;"
            except:
                return ""

        def style_currency(val):
            try:
                v = float(str(val).replace('$', '').replace(',', ''))
                if v > 0:
                    return "color: #21c354; font-weight: bold;"
                elif v < 0:
                    return "color: #ff4b4b; font-weight: bold;"
                else:
                    return ""
            except:
                return ""

        # Apply styles
        try:
            styled_df = display_df.style.map(style_batting, subset=["Batting Avg"]).map(style_currency, subset=["Avg Win", "Avg Loss", "Total PnL"])
        except AttributeError:
            styled_df = display_df.style.applymap(style_batting, subset=["Batting Avg"]).applymap(style_currency, subset=["Avg Win", "Avg Loss", "Total PnL"])
            
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        st.divider()

        st.subheader("Equity Curve (All-Time)")
        # Prepare Equity Curve Data using unfiltered equity_data
        df_equity = pd.DataFrame([{ "Date": d["Reference Date"], "PnL": d["PnL"] } for d in equity_data])
        df_equity.sort_values(by="Date", inplace=True)
        # Combine PnL for trades closed/opened on the same date
        df_equity = df_equity.groupby("Date").sum().reset_index()
        df_equity["Cumulative PnL"] = df_equity["PnL"].cumsum()
        
        if not df_equity.empty:
            # Convert Date to datetime for proper offset calculations
            df_equity["Date"] = pd.to_datetime(df_equity["Date"])
            
            first_date = df_equity["Date"].min()
            last_date = df_equity["Date"].max()
            # Ensure the graph shows at least 1 year span
            end_date = max(last_date, first_date + pd.DateOffset(years=1))

            fig = px.line(df_equity, x="Date", y="Cumulative PnL", markers=True, 
                          title="Cumulative PnL Over Time",
                          labels={"Cumulative PnL": "Cumulative Net PnL ($)"},
                          color_discrete_sequence=["#21c354"]) # Using a pleasant green
            
            fig.update_layout(
                yaxis_tickprefix="$", 
                hovermode="x unified",
                font=dict(size=14), # Increase overall font size for readability
                margin=dict(l=20, r=20, t=40, b=20),
                height=350 # Force a slightly smaller height to save space
            )
            
            # Format x-axis to Month Year and set range
            fig.update_xaxes(
                tickformat="%b %Y",
                range=[first_date, end_date]
            )
            
            # Fill area below the line with a softer semi-transparent color
            fig.update_traces(fill='tozeroy', fillcolor='rgba(33, 195, 84, 0.2)')
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No timeline data to display equity curve.")

db.close()
