import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
from src.db import SessionLocal
from src.models import Trade, Transaction

st.set_page_config(page_title="Closed Trades Review", page_icon="📊", layout="wide")

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
title_col.title("Closed Trades Review")

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
            "Expected Direction": t.expected_direction if t.expected_direction else "N/A",
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
        @st.cache_data(ttl=86400)
        def get_sp500_data():
            ticker = yf.Ticker("^GSPC")
            df = ticker.history(period="max")
            if not df.empty:
                df.index = df.index.tz_localize(None)
            return df
            
        with st.spinner("Loading market data..."):
            sp500_df = get_sp500_data()
            
        period_return = 0.0
        ytd_return = 0.0
        if not sp500_df.empty:
            latest_close = sp500_df['Close'].iloc[-1]
            if date_filter == "All":
                if equity_data:
                    filter_start_date = min(d["Reference Date"] for d in equity_data)
                else:
                    filter_start_date = sp500_df.index[0].date()
            else:
                filter_start_date = start_date
                
            start_dt = pd.to_datetime(filter_start_date)
            mask = sp500_df.index >= start_dt
            if mask.any():
                start_close = sp500_df.loc[mask, 'Close'].iloc[0]
                period_return = ((latest_close - start_close) / start_close) * 100
                
            ytd_start_dt = pd.to_datetime(f"{datetime.today().year}-01-01")
            mask_ytd = sp500_df.index >= ytd_start_dt
            if mask_ytd.any():
                start_close_ytd = sp500_df.loc[mask_ytd, 'Close'].iloc[0]
                ytd_return = ((latest_close - start_close_ytd) / start_close_ytd) * 100
                
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
        
        total_cost = sum((d["Trade"].collateral or 0.0) for d in filtered_data)
        if total_cost == 0:
            total_cost = sum(d["Premium Paid"] for d in filtered_data)
            
        net_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0
        
        st.subheader("Key Metrics")
        
        def styled_metric(label, value, color="inherit", height="auto", val_size="1.6rem", center=False, help_text=None):
            align_style = "align-items: center; text-align: center;" if center else ""
            help_html = f'<span title="{help_text}" style="cursor: help; margin-left: 4px; display: inline-block; width: 14px; height: 14px; line-height: 14px; text-align: center; border-radius: 50%; border: 1px solid #aaa; font-size: 0.65rem; color: #aaa;">?</span>' if help_text else ""
            st.markdown(f"""
                <div style="height: {height}; display: flex; flex-direction: column; justify-content: center; {align_style} padding: 0.75rem; border-radius: 0.5rem; background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 0.5rem;">
                    <div style="font-size: 0.85rem; color: #aaa; margin-bottom: 0.2rem; display: flex; align-items: center; justify-content: {"center" if center else "flex-start"};">{label}{help_html}</div>
                    <div style="font-size: {val_size}; font-weight: 600; color: {color}; line-height: 1.2;">{value}</div>
                </div>
            """, unsafe_allow_html=True)
            
        def get_currency_color(val):
            return "#21c354" if val > 0 else "#ff4b4b" if val < 0 else "inherit"
            
        def get_batting_color(val):
            return "#ff4b4b" if val <= 50 else "#faca2b" if val <= 75 else "#21c354"
        
        col_left, col_right = st.columns([1, 4])
        with col_left:
            # Increased height slightly to perfectly match two rows of Streamlit columns + gaps
            styled_metric("Total Trades", total_trades, height="260px", val_size="5rem", center=True)
            
        with col_right:
            r1c1, r1c2, r1c3, r1c4 = st.columns(4)
            with r1c1:
                styled_metric("Batting Avg", f"{batting_avg:.1f}%", get_batting_color(batting_avg))
            with r1c2:
                styled_metric("Wins / Losses", f"{wins} / {losses}")
            with r1c3:
                styled_metric("Average Win", f"${avg_win:.2f}", get_currency_color(avg_win))
            with r1c4:
                styled_metric("Average Loss", f"${avg_loss:.2f}", get_currency_color(avg_loss))
            
            r2c1, r2c2, r2c3, r2c4 = st.columns(4)
            with r2c1:
                styled_metric("Premium Collected", f"${total_prem_col:.2f}", get_currency_color(total_prem_col))
            with r2c2:
                styled_metric("Premium Paid", f"${total_prem_paid:.2f}", "#ff4b4b")
            with r2c3:
                styled_metric("Total Commission", f"${total_comm:.2f}", "#ff4b4b")
            with r2c4:
                styled_metric("Net PnL", f"${total_pnl:.2f}", get_currency_color(total_pnl), help_text="Total premium collected minus total premium paid and commissions.")
                
            r3c1, r3c2, r3c3, r3c4 = st.columns(4)
            with r3c1:
                styled_metric("Net Portfolio Cost", f"${total_cost:,.2f}", help_text="Sum of collateral used for the trades. If collateral is not recorded, falls back to sum of premium paid.")
            with r3c2:
                styled_metric("Net PnL (%)", f"{net_pnl_pct:+.2f}%", get_currency_color(net_pnl_pct), help_text="Net PnL divided by Net Portfolio Cost.")
            with r3c3:
                styled_metric(f"S&P 500 Return ({date_filter})", f"{period_return:+.2f}%", get_currency_color(period_return))
            with r3c4:
                alpha = net_pnl_pct - period_return
                styled_metric("Alpha (vs S&P 500)", f"{alpha:+.2f}%", get_currency_color(alpha), help_text="Difference between Net PnL (%) and S&P 500 Return")
        
        st.divider()
        
        st.subheader("Detailed Breakdown")
        
        st.write("Analyze Performance By:")
        if "breakdown_by" not in st.session_state:
            st.session_state.breakdown_by = "Expected Direction"
            
        btn_cols = st.columns(7)
        if btn_cols[0].button("Expected Direction", use_container_width=True, type="primary" if st.session_state.breakdown_by == "Expected Direction" else "secondary"):
            st.session_state.breakdown_by = "Expected Direction"
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
            
        st.dataframe(styled_df, width='stretch', hide_index=True)
        
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
            
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No timeline data to display equity curve.")
            
        st.divider()

        tooltip_text = (
            "| Tier | Bullish | Bearish | Neutral | High Volatility |\n"
            "|---|---|---|---|---|\n"
            "| **Very Right** | > +5% | < -5% | ±1% | > ±10% |\n"
            "| **Right** | 0% to +5% | -5% to 0% | ±1% to ±2% | ±5% to ±10% |\n"
            "| **Wrong** | -5% to 0% | 0% to +5% | ±2% to ±5% | ±2% to ±5% |\n"
            "| **Very Wrong** | < -5% | > +5% | > ±5% | < ±2% |"
        )
        st.subheader("Expected Direction Analysis", help=tooltip_text)
        st.write("Analyze if you were right about the Expected Direction based on the Underlying Price at Open vs Close.")
        
        # Analyze directions
        direction_stats = {
            "Very Right": {"count": 0, "trades": []},
            "Right": {"count": 0, "trades": []},
            "Wrong": {"count": 0, "trades": []},
            "Very Wrong": {"count": 0, "trades": []},
            "N/A (Missing Data)": {"count": 0, "trades": []}
        }
        
        for t_dict in filtered_data:
            trade = t_dict["Trade"]
            direction = trade.expected_direction
            
            # Clean string like "Bullish ↗" to just "Bullish"
            if direction:
                if "Bullish" in direction: direction = "Bullish"
                elif "Bearish" in direction: direction = "Bearish"
                elif "Neutral" in direction: direction = "Neutral"
                elif "High volatility" in direction: direction = "High volatility"
            else:
                direction = "N/A"
                
            open_p = trade.underlying_price_at_open
            close_p = getattr(trade, 'underlying_price_at_close', None)
            
            if open_p is None or close_p is None or direction == "N/A":
                direction_stats["N/A (Missing Data)"]["count"] += 1
                direction_stats["N/A (Missing Data)"]["trades"].append(t_dict)
                continue
                
            pct_change = (close_p - open_p) / open_p
            
            tier = "Unknown"
            if direction == "Bullish":
                if pct_change > 0.05:
                    tier = "Very Right"
                elif 0 < pct_change <= 0.05:
                    tier = "Right"
                elif -0.05 <= pct_change <= 0:
                    tier = "Wrong"
                elif pct_change < -0.05:
                    tier = "Very Wrong"
            elif direction == "Bearish":
                if pct_change < -0.05:
                    tier = "Very Right"
                elif -0.05 <= pct_change < 0:
                    tier = "Right"
                elif 0 <= pct_change <= 0.05:
                    tier = "Wrong"
                elif pct_change > 0.05:
                    tier = "Very Wrong"
            elif direction == "Neutral":
                if -0.01 <= pct_change <= 0.01:
                    tier = "Very Right"
                elif (-0.02 <= pct_change < -0.01) or (0.01 < pct_change <= 0.02):
                    tier = "Right"
                elif (-0.05 <= pct_change < -0.02) or (0.02 < pct_change <= 0.05):
                    tier = "Wrong"
                elif pct_change < -0.05 or pct_change > 0.05:
                    tier = "Very Wrong"
            elif direction == "High volatility":
                if pct_change < -0.10 or pct_change > 0.10:
                    tier = "Very Right"
                elif (-0.10 <= pct_change < -0.05) or (0.05 < pct_change <= 0.10):
                    tier = "Right"
                elif (-0.05 <= pct_change < -0.02) or (0.02 < pct_change <= 0.05):
                    tier = "Wrong"
                elif -0.02 <= pct_change <= 0.02:
                    tier = "Very Wrong"
            else:
                tier = "N/A (Missing Data)"
                
            if tier != "Unknown":
                direction_stats[tier]["count"] += 1
                direction_stats[tier]["trades"].append(t_dict)
                
        # Display Stats
        stat_cols = st.columns(5)
        colors = {"Very Right": "#21c354", "Right": "#6ee7b7", "Wrong": "#fca5a5", "Very Wrong": "#ff4b4b", "N/A (Missing Data)": "#a1a1aa"}
        
        stat_keys = ["Very Right", "Right", "Wrong", "Very Wrong", "N/A (Missing Data)"]
        for idx, key in enumerate(stat_keys):
            with stat_cols[idx]:
                st.markdown(f"""
                <div style="padding: 1rem; border-radius: 0.5rem; background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); text-align: center;">
                    <div style="font-size: 1.2rem; font-weight: bold; color: {colors[key]};">{key}</div>
                    <div style="font-size: 2rem; font-weight: bold; margin-top: 0.5rem;">{direction_stats[key]["count"]}</div>
                </div>
                """, unsafe_allow_html=True)
                
        st.write("")
        st.write("### View Trades by Tier")
        
        st.write("Select Tier to view trades:")
        if "selected_tier" not in st.session_state:
            st.session_state.selected_tier = "Very Right"
            
        tier_btn_cols = st.columns(5)
        if tier_btn_cols[0].button("Very Right", use_container_width=True, type="primary" if st.session_state.selected_tier == "Very Right" else "secondary", key="tier_very_right"):
            st.session_state.selected_tier = "Very Right"
            st.rerun()
        if tier_btn_cols[1].button("Right", use_container_width=True, type="primary" if st.session_state.selected_tier == "Right" else "secondary", key="tier_right"):
            st.session_state.selected_tier = "Right"
            st.rerun()
        if tier_btn_cols[2].button("Wrong", use_container_width=True, type="primary" if st.session_state.selected_tier == "Wrong" else "secondary", key="tier_wrong"):
            st.session_state.selected_tier = "Wrong"
            st.rerun()
        if tier_btn_cols[3].button("Very Wrong", use_container_width=True, type="primary" if st.session_state.selected_tier == "Very Wrong" else "secondary", key="tier_very_wrong"):
            st.session_state.selected_tier = "Very Wrong"
            st.rerun()
        if tier_btn_cols[4].button("N/A (Missing Data)", use_container_width=True, type="primary" if st.session_state.selected_tier == "N/A (Missing Data)" else "secondary", key="tier_na"):
            st.session_state.selected_tier = "N/A (Missing Data)"
            st.rerun()
            
        selected_tier = st.session_state.selected_tier
        trades_to_show = direction_stats[selected_tier]["trades"]
        
        if not trades_to_show:
            st.info(f"No trades in the '{selected_tier}' tier.")
        else:
            header_cols = st.columns([1, 2, 1.5, 2, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5])
            header_cols[0].markdown("<span style='font-weight: bold; font-size: 14px;'>#</span>", unsafe_allow_html=True)
            header_cols[1].markdown("<span style='font-weight: bold; font-size: 14px;'>Date Opened</span>", unsafe_allow_html=True)
            header_cols[2].markdown("<span style='font-weight: bold; font-size: 14px;'>Ticker</span>", unsafe_allow_html=True)
            header_cols[3].markdown("<span style='font-weight: bold; font-size: 14px;'>Expected Direction</span>", unsafe_allow_html=True)
            header_cols[4].markdown("<span style='font-weight: bold; font-size: 14px;'>Open $</span>", unsafe_allow_html=True)
            header_cols[5].markdown("<span style='font-weight: bold; font-size: 14px;'>Close $</span>", unsafe_allow_html=True)
            header_cols[6].markdown("<span style='font-weight: bold; font-size: 14px;'>% Change</span>", unsafe_allow_html=True)
            header_cols[7].markdown("<span style='font-weight: bold; font-size: 14px;'>Final PnL</span>", unsafe_allow_html=True)
            header_cols[8].markdown("<span style='font-weight: bold; font-size: 14px;'>Status</span>", unsafe_allow_html=True)
            header_cols[9].markdown("<span style='font-weight: bold; font-size: 14px;'>Action</span>", unsafe_allow_html=True)
            
            # Use an aggressive negative margin to collapse Streamlit's default vertical gaps
            st.markdown("<div style='margin-top: -45px; margin-bottom: -20px;'><hr></div>", unsafe_allow_html=True)

            for t_dict in trades_to_show:
                t = t_dict["Trade"]
                pnl = t_dict["PnL"]
                open_p = t.underlying_price_at_open
                close_p = getattr(t, 'underlying_price_at_close', None)
                pct_change = ((close_p - open_p) / open_p * 100) if open_p and close_p else 0
                
                cols = st.columns([1, 2, 1.5, 2, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5])
                cols[0].write(t.trade_number)
                cols[1].write(t.date_opened.strftime("%Y-%m-%d"))
                cols[2].write(t.ticker)
                cols[3].write(t.expected_direction)
                cols[4].write(f"${open_p:.2f}" if open_p else "N/A")
                cols[5].write(f"${close_p:.2f}" if close_p else "N/A")
                cols[6].write(f"{pct_change:+.2f}%" if open_p and close_p else "N/A")
                
                pnl_color = "#21c354" if pnl > 0 else "#ff4b4b" if pnl < 0 else "inherit"
                cols[7].markdown(f"<span style='color: {pnl_color}; font-weight: bold;'>${pnl:.2f}</span>", unsafe_allow_html=True)
                
                cols[8].write(t.status)
                if cols[9].button("ℹ️ Details", key=f"details_tier_{t.id}", use_container_width=True):
                    st.session_state.details_trade_id = t.id
                    st.switch_page("pages/12_Trade_Details.py")
                
                st.markdown("<hr style='margin:0.25rem 0; opacity: 0.3'>", unsafe_allow_html=True)

        st.divider()
        st.subheader("Periodic Performance")
        
        df_perf = pd.DataFrame(equity_data)
        if not df_perf.empty:
            df_perf["Reference Date"] = pd.to_datetime(df_perf["Reference Date"])
            df_perf["Year"] = df_perf["Reference Date"].dt.year
            df_perf["Month_period"] = df_perf["Reference Date"].dt.to_period("M")
            
            def get_sp500_return(start_date, end_date):
                if sp500_df.empty: return 0.0
                mask = (sp500_df.index.date >= start_date) & (sp500_df.index.date <= end_date)
                if mask.any():
                    start_close = sp500_df.loc[mask, 'Close'].iloc[0]
                    end_close = sp500_df.loc[mask, 'Close'].iloc[-1]
                    if start_close > 0:
                        return ((end_close - start_close) / start_close) * 100
                return 0.0

            combined_data = []
            today = datetime.today()
            first_trade_month = df_perf["Reference Date"].min().replace(day=1)
            month_range = pd.date_range(start=first_trade_month, end=today, freq='MS')
            
            for year, year_group in df_perf.groupby("Year"):
                prem_col = year_group["Premium Collected"].sum()
                prem_paid = year_group["Premium Paid"].sum()
                comm = year_group["Commission"].sum()
                net_pnl = year_group["PnL"].sum()
                cost = sum((t.collateral or 0.0) for t in year_group["Trade"])
                if cost == 0:
                    cost = prem_paid
                net_pnl_pct = (net_pnl / cost * 100) if cost > 0 else 0.0
                
                start_date = pd.Timestamp(year=year, month=1, day=1).date()
                end_date = pd.Timestamp(year=year, month=12, day=31).date()
                if year == today.year:
                    end_date = today.date()
                
                sp500_ret = get_sp500_return(start_date, end_date)
                alpha = net_pnl_pct - sp500_ret
                
                combined_data.append({
                    "Period": str(year),
                    "Premium Collected": prem_col,
                    "Premium Paid": prem_paid,
                    "Total Commission": comm,
                    "Net Portfolio Cost": cost,
                    "Net PnL": net_pnl,
                    "Net PnL (%)": net_pnl_pct,
                    "S&P 500 Return": sp500_ret,
                    "Alpha (vs S&P 500)": alpha
                })
                
                year_months = [dt for dt in month_range if dt.year == year]
                for dt in year_months:
                    period = pd.Period(dt, freq='M')
                    group = df_perf[df_perf["Month_period"] == period]
                    
                    prem_col = group["Premium Collected"].sum() if not group.empty else 0.0
                    prem_paid = group["Premium Paid"].sum() if not group.empty else 0.0
                    comm = group["Commission"].sum() if not group.empty else 0.0
                    net_pnl = group["PnL"].sum() if not group.empty else 0.0
                    cost = sum((t.collateral or 0.0) for t in group["Trade"]) if not group.empty else 0.0
                    if cost == 0:
                        cost = prem_paid
                    net_pnl_pct = (net_pnl / cost * 100) if cost > 0 else 0.0
                    
                    start_date = dt.date()
                    end_date = (dt + pd.DateOffset(months=1) - pd.DateOffset(days=1)).date()
                    if period.year == today.year and period.month == today.month:
                        end_date = today.date()
                        
                    sp500_ret = get_sp500_return(start_date, end_date)
                    alpha = net_pnl_pct - sp500_ret
                    
                    combined_data.append({
                        "Period": dt.strftime("└ %b"),
                        "Premium Collected": prem_col,
                        "Premium Paid": prem_paid,
                        "Total Commission": comm,
                        "Net Portfolio Cost": cost,
                        "Net PnL": net_pnl,
                        "Net PnL (%)": net_pnl_pct,
                        "S&P 500 Return": sp500_ret,
                        "Alpha (vs S&P 500)": alpha
                    })

            def style_perf_dataframe(df):
                def style_currency_perf(val):
                    try:
                        v = float(str(val).replace('$', '').replace(',', ''))
                        if v > 0: return "color: #21c354; font-weight: bold;"
                        elif v < 0: return "color: #ff4b4b; font-weight: bold;"
                        return ""
                    except: return ""

                def style_pct_perf(val):
                    try:
                        v = float(str(val).replace('%', '').replace('+', ''))
                        if v > 0: return "color: #21c354; font-weight: bold;"
                        elif v < 0: return "color: #ff4b4b; font-weight: bold;"
                        return ""
                    except: return ""
                    
                def style_period(val):
                    if not str(val).startswith("└"):
                        return "font-weight: bold;"
                    return ""
                    
                format_dict = {
                    "Premium Collected": "${:,.2f}",
                    "Premium Paid": "${:,.2f}",
                    "Total Commission": "${:,.2f}",
                    "Net Portfolio Cost": "${:,.2f}",
                    "Net PnL": "${:,.2f}",
                    "Net PnL (%)": "{:+.2f}%",
                    "S&P 500 Return": "{:+.2f}%",
                    "Alpha (vs S&P 500)": "{:+.2f}%"
                }
                
                styled = df.style.format(format_dict)
                
                try:
                    styled = styled.map(style_currency_perf, subset=["Net PnL"]).map(style_pct_perf, subset=["Net PnL (%)", "S&P 500 Return", "Alpha (vs S&P 500)"]).map(style_period, subset=["Period"])
                except AttributeError:
                    styled = styled.applymap(style_currency_perf, subset=["Net PnL"]).applymap(style_pct_perf, subset=["Net PnL (%)", "S&P 500 Return", "Alpha (vs S&P 500)"]).applymap(style_period, subset=["Period"])
                    
                return styled

            st.dataframe(style_perf_dataframe(pd.DataFrame(combined_data)), width='stretch', hide_index=True)
        else:
            st.info("No data available for periodic performance.")

        st.divider()
        st.subheader("S&P 500 Performance")
            
        if not sp500_df.empty:
            latest_close = sp500_df['Close'].iloc[-1]
                
            st.markdown("#### Market Context")
            col_m1, col_m2 = st.columns(2)
            
            with col_m1:
                styled_metric("S&P 500 Return (YTD)", f"{ytd_return:+.2f}%", get_currency_color(ytd_return))
                
            with col_m2:
                styled_metric("S&P 500 Current Price", f"${latest_close:,.2f}")
                
            sp500_df['YearMonth'] = sp500_df.index.to_period('M')
            monthly_df = sp500_df.groupby('YearMonth')['Close'].last().to_frame()
            monthly_df['Return'] = monthly_df['Close'].pct_change() * 100
            monthly_df = monthly_df.dropna()
            monthly_df.index = monthly_df.index.to_timestamp()
            
            hist_df = monthly_df[monthly_df.index.year >= 1980].copy()
            hist_df['Month'] = hist_df.index.month
            monthly_avg = hist_df.groupby('Month')['Return'].mean().reset_index()
            month_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
            monthly_avg['Month Name'] = monthly_avg['Month'].map(month_names)
            monthly_avg['Color'] = monthly_avg['Return'].apply(lambda x: '#21c354' if x > 0 else '#ff4b4b')
            
            fig_hist = px.bar(monthly_avg, x='Month Name', y='Return', 
                              title='Historical Avg Monthly Return (Since 1980)',
                              labels={'Return': 'Average Return (%)', 'Month Name': ''},
                              color='Color', color_discrete_map='identity')
            fig_hist.update_xaxes(categoryorder='array', categoryarray=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
            fig_hist.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20), height=300)
            
            last_12 = monthly_df.tail(12).copy()
            last_12['Month Year'] = last_12.index.strftime('%b %Y')
            last_12['Color'] = last_12['Return'].apply(lambda x: '#21c354' if x > 0 else '#ff4b4b')
            
            fig_12m = px.bar(last_12, x='Month Year', y='Return',
                             title='Last 12 Months Performance',
                             labels={'Return': 'Return (%)', 'Month Year': ''},
                             color='Color', color_discrete_map='identity')
            fig_12m.update_xaxes(categoryorder='array', categoryarray=last_12['Month Year'].tolist())
            fig_12m.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20), height=300)

            st.write("")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.plotly_chart(fig_hist, use_container_width=True)
            with col_c2:
                st.plotly_chart(fig_12m, use_container_width=True)

db.close()
