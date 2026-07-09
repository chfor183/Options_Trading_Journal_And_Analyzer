import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from src.db import SessionLocal
from src.models import Trade, Leg, Transaction
from src.market_data import get_ticker_info, get_barchart_live_option_leg_data
from src.options_math import calculate_metrics, calculate_payoff_array

st.set_page_config(page_title="Open Trades", page_icon="🔓", layout="wide")
st.title("🔓 Open Trades Review")

# 1. Database & Portfolio Session Setup
db = SessionLocal()

active_portfolio_id = st.session_state.get("active_portfolio_id")
if not active_portfolio_id:
    st.warning("No portfolio selected. Please select one from the sidebar.")
    db.close()
    st.stop()

# Query active portfolio trades that are "Open"
open_trades = (
    db.query(Trade)
    .filter(Trade.portfolio_id == active_portfolio_id, Trade.status == "Open")
    .order_by(Trade.date_opened.desc())
    .all()
)

if not open_trades:
    st.info("No open trades found in this portfolio. Go to the Trade tab to log a new position!")
    db.close()
    st.stop()

# 2. Helpers for live valuation and metrics calculations
def get_leg_current_price(ticker, expiry_date, strike, option_type, position, fallback_price):
    try:
        expiry_str = pd.to_datetime(expiry_date).strftime('%Y-%m-%d')
        leg_data = get_barchart_live_option_leg_data(ticker, expiry_str, strike, option_type)
        if leg_data:
            bid = leg_data.get('bid', 0.0)
            ask = leg_data.get('ask', 0.0)
            last = leg_data.get('lastPrice', 0.0)
            
            # To close a Short leg (Sell/Short), we must buy it back (pay Ask)
            if position in ["Sell", "Short"]:
                return ask if ask > 0 else (last if last > 0 else float(fallback_price))
            # To close a Long leg (Buy/Long), we must sell it (receive Bid)
            else:
                return bid if bid > 0 else (last if last > 0 else float(fallback_price))
    except Exception:
        pass
    return float(fallback_price)

# Pre-fetch and process live metrics for all open trades
processed_trades = []
total_entry_net_premium = 0.0
total_liquidation_value = 0.0
total_unrealized_pnl = 0.0
has_live_pricing_warning = False

with st.spinner("Fetching live market data and calculating valuations..."):
    for t in open_trades:
        open_tx = next((tx for tx in t.transactions if tx.action == "Open"), None)
        entry_price = open_tx.price if open_tx else 0.0
        entry_commission = open_tx.commission if open_tx else 0.0
        
        # Cash flow at entry (Net credit positive, net debit negative)
        entry_net_premium = -entry_price - entry_commission
        total_entry_net_premium += entry_net_premium
        
        # Live underlying ticker price info
        ticker_info = get_ticker_info(t.ticker)
        current_underlying_price = None
        if ticker_info and ticker_info.get("current_price"):
            current_underlying_price = float(ticker_info["current_price"])
            
        # Calculate current liquidation value of all option legs
        liquidation_value = 0.0
        legs_detail_list = []
        is_live = True
        
        for leg in t.legs:
            fallback = float(leg.price) if leg.price is not None else 0.0
            cur_price = get_leg_current_price(t.ticker, leg.expiry, leg.strike, leg.option_type, leg.position, fallback)
            
            if cur_price == fallback:
                # If we fell back on every leg, we label the pricing as non-live
                is_live = False
            
            qty = leg.quantity if leg.quantity else 1
            # Value to close: Sell leg is buy to close (negative cashflow); Buy leg is sell to close (positive cashflow)
            if leg.position in ["Buy", "Long"]:
                leg_val = cur_price * 100 * qty
            else:
                leg_val = -cur_price * 100 * qty
                
            liquidation_value += leg_val
            legs_detail_list.append({
                "leg": leg,
                "current_price": cur_price,
                "fallback_price": fallback,
                "value": leg_val
            })
            
        if not is_live:
            has_live_pricing_warning = True
            
        total_liquidation_value += liquidation_value
        unrealized_pnl = entry_net_premium + liquidation_value
        total_unrealized_pnl += unrealized_pnl
        
        # Calculate Profit Zone and Strikes proximity warning
        in_profit_zone = False
        is_near_strike = False
        near_strike_val = None
        
        if current_underlying_price is not None and t.legs:
            legs_for_payoff = []
            for leg in t.legs:
                legs_for_payoff.append({
                    "action": "Buy" if leg.position.lower() in ["buy", "long"] else "Sell",
                    "qty": leg.quantity if leg.quantity else 1,
                    "type": leg.option_type,
                    "strike": leg.strike,
                    "price": float(leg.price) if leg.price is not None else 0.0,
                    "expiry": pd.to_datetime(leg.expiry)
                })
            try:
                payoffs = calculate_payoff_array(legs_for_payoff, np.array([current_underlying_price]))
                if len(payoffs) > 0:
                    in_profit_zone = payoffs[0] > 0
            except Exception:
                pass
                
            # Check if current price is within 5% of any strike
            for leg in t.legs:
                if abs(current_underlying_price - leg.strike) / leg.strike <= 0.05:
                    is_near_strike = True
                    near_strike_val = leg.strike
                    break
        
        # Calculate days since opened and days remaining to expiry
        days_to_expiry = None
        if t.legs:
            min_expiry = min(leg.expiry for leg in t.legs)
            days_to_expiry = (min_expiry - datetime.now().date()).days

        processed_trades.append({
            "trade": t,
            "entry_net_premium": entry_net_premium,
            "liquidation_value": liquidation_value,
            "unrealized_pnl": unrealized_pnl,
            "current_underlying_price": current_underlying_price,
            "legs_details": legs_detail_list,
            "is_live_pricing": is_live,
            "in_profit_zone": in_profit_zone,
            "is_near_strike": is_near_strike,
            "near_strike_val": near_strike_val,
            "days_to_expiry": days_to_expiry
        })

# Sort processed_trades by days_to_expiry left ascending (non-option trades or None goes last)
processed_trades.sort(key=lambda x: (x["days_to_expiry"] is None, x["days_to_expiry"]))

# Calculate trades expiring within 7 days
expiring_within_7_days = sum(
    1 for p in processed_trades 
    if p["days_to_expiry"] is not None and 0 <= p["days_to_expiry"] <= 7
)

if has_live_pricing_warning:
    st.info("💡 Some option chain prices are showing entry values because live options data is currently unavailable (e.g. off-market hours or rate limits).")

# 3. Key Summary Cards
mcol1, mcol1_sub, mcol2, mcol3, mcol4 = st.columns([1, 1.2, 1.2, 1.2, 1.4])
mcol1.metric("Active Trades", len(open_trades))
mcol1_sub.metric("Trades Expiring ≤ 7d", expiring_within_7_days, help="Trades expiring within the next 7 days.")

# Display net portfolio premium at open
premium_label = "Net Portfolio Cost" if total_entry_net_premium < 0 else "Net Portfolio Credit"
mcol2.metric(premium_label, f"${abs(total_entry_net_premium):,.2f}")

# Display current liquidation value
liq_label = "Liquidation Value"
mcol3.metric(liq_label, f"${total_liquidation_value:,.2f}", help="Current estimated net cash to close all positions.")

# Display combined unrealized P&L
pnl_color = "green" if total_unrealized_pnl >= 0 else "red"
pnl_prefix = "+" if total_unrealized_pnl >= 0 else ""

if total_entry_net_premium != 0:
    total_pnl_pct = (total_unrealized_pnl / abs(total_entry_net_premium)) * 100
    pnl_pct_str = f" ({pnl_prefix}{total_pnl_pct:.2f}%)"
else:
    pnl_pct_str = ""

mcol4.markdown(
    f"""
    <div style="background-color: {'rgba(40, 167, 69, 0.1)' if total_unrealized_pnl >= 0 else 'rgba(220, 53, 69, 0.1)'}; 
                padding: 10px; border-radius: 8px; text-align: center; border: 1px solid {'#28a745' if total_unrealized_pnl >= 0 else '#dc3545'}">
        <span style="font-size: 0.85rem; color: #6c757d; font-weight: bold; text-transform: uppercase;">Unrealized Portfolio P&L</span><br/>
        <span style="font-size: 1.8rem; color: {'#28a745' if total_unrealized_pnl >= 0 else '#dc3545'}; font-weight: bold;">
            {pnl_prefix}${total_unrealized_pnl:,.2f}{pnl_pct_str}
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# 4. Filters & Controls for the Open Trades listing
# Initialize keys in session state for resetting filters
if "ot_filter_ticker" not in st.session_state:
    st.session_state.ot_filter_ticker = ""
if "ot_filter_strategy" not in st.session_state:
    st.session_state.ot_filter_strategy = "All"
if "ot_filter_type" not in st.session_state:
    st.session_state.ot_filter_type = "All"
if "ot_filter_health" not in st.session_state:
    st.session_state.ot_filter_health = "All"
if "ot_filter_zone" not in st.session_state:
    st.session_state.ot_filter_zone = "All"

def reset_open_trades_filters():
    st.session_state.ot_filter_ticker = ""
    st.session_state.ot_filter_strategy = "All"
    st.session_state.ot_filter_type = "All"
    st.session_state.ot_filter_health = "All"
    st.session_state.ot_filter_zone = "All"

fcol1, fcol2, fcol3, fcol4, fcol5, fcol6 = st.columns([1, 1, 1, 1, 1, 0.9])
filter_ticker = fcol1.text_input("🔍 Filter by Ticker symbol", key="ot_filter_ticker").upper().strip()
strategy_options = ["All"] + sorted(list(set(p["trade"].strategy_type for p in processed_trades)))
filter_strategy = fcol2.selectbox("📈 Filter by Strategy", strategy_options, key="ot_filter_strategy")
filter_type = fcol3.selectbox("💰 Filter by Debit/Credit", ["All", "Debit", "Credit"], key="ot_filter_type")
filter_health = fcol4.selectbox("📊 Filter by Health", ["All", "Doing Well", "In The Red"], key="ot_filter_health")
filter_zone = fcol5.selectbox("🎯 Filter by Profit Zone", ["All", "In Profit Zone", "Out of Profit Zone", "Profit Zone Irrelevant"], key="ot_filter_zone")

# Reset button vertical alignment helper
fcol6.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
if fcol6.button("Reset filters", key="ot_reset_btn", type="primary", use_container_width=True, on_click=reset_open_trades_filters):
    pass

# Apply filters
filtered_processed = [
    p for p in processed_trades
    if (not filter_ticker or filter_ticker in p["trade"].ticker.upper()) and
       (filter_strategy == "All" or p["trade"].strategy_type == filter_strategy) and
       (filter_type == "All" or 
        (filter_type == "Debit" and p["trade"].strategy_type and "debit" in p["trade"].strategy_type.lower()) or 
        (filter_type == "Credit" and p["trade"].strategy_type and "credit" in p["trade"].strategy_type.lower())) and
       (filter_health == "All" or 
        (filter_health == "Doing Well" and p["unrealized_pnl"] >= 0) or 
        (filter_health == "In The Red" and p["unrealized_pnl"] < 0)) and
       (filter_zone == "All" or
        (filter_zone == "In Profit Zone" and not (p["trade"].strategy_type and "debit" in p["trade"].strategy_type.lower()) and p["in_profit_zone"]) or
        (filter_zone == "Out of Profit Zone" and not (p["trade"].strategy_type and "debit" in p["trade"].strategy_type.lower()) and not p["in_profit_zone"]) or
        (filter_zone == "Profit Zone Irrelevant" and p["trade"].strategy_type and "debit" in p["trade"].strategy_type.lower()))
]

if not filtered_processed:
    st.info("No open trades match the chosen filters.")
    db.close()
    st.stop()

# 5. Open Positions Grid / Accordion-Cards
st.subheader("Active Positions")

for idx, p in enumerate(filtered_processed):
    t = p["trade"]
    upnl = p["unrealized_pnl"]
    is_profit = upnl >= 0
    pnl_class = "success" if is_profit else "danger"
    pnl_symbol = "📈 Profit" if is_profit else "📉 Loss"
    color_hex = "#28a745" if is_profit else "#dc3545"
    bg_hex = "rgba(40, 167, 69, 0.05)" if is_profit else "rgba(220, 53, 69, 0.05)"
    
    is_debit = "debit" in t.strategy_type.lower()
    
    # Calculate days since opened and days remaining to expiry
    days_since_open = (datetime.now().date() - t.date_opened.date()).days
    opened_date_str = t.date_opened.strftime('%Y-%m-%d')
    opened_badge = f'<span style="font-size: 0.95rem; color: #ced4da; margin-left: 15px; font-family: sans-serif;">🗓️ Opened: <b style="color: #f8f9fa;">{opened_date_str}</b></span>'
    days_ago_text = f"{days_since_open} day ago" if days_since_open == 1 or days_since_open == 0 else f"{days_since_open} days ago"
    days_ago_badge = f'<span style="background-color: rgba(173, 181, 189, 0.15); color: #dee2e6; padding: 3px 8px; border-radius: 4px; font-size: 0.85rem; margin-left: 10px; font-weight: bold; border: 1px solid rgba(173, 181, 189, 0.3);">📅 {days_ago_text}</span>'
    
    if t.legs:
        # Initial DTE of trade at open
        first_leg_open = min(t.legs, key=lambda l: l.expiry)
        dte_at_open_val = (first_leg_open.expiry - t.date_opened.date()).days
        if dte_at_open_val <= 0:
            dte_at_open_val = 1
        
        initial_dte_badge = f'<span style="background-color: rgba(0, 123, 255, 0.15); color: #339af0; padding: 3px 8px; border-radius: 4px; font-size: 0.85rem; margin-left: 10px; font-weight: bold; border: 1px solid rgba(0, 123, 255, 0.3);">⏱️ {dte_at_open_val} DTE at Open</span>'
        
        days_to_expiry = p["days_to_expiry"]
        if days_to_expiry < 0:
            expiry_badge = f'<span style="background-color: rgba(220, 53, 69, 0.15); color: #ff6b6b; padding: 3px 8px; border-radius: 4px; font-size: 0.85rem; margin-left: 10px; font-weight: bold; border: 1px solid rgba(220, 53, 69, 0.3);">⏳ Expired</span>'
        else:
            if is_debit:
                if days_to_expiry <= 30:
                    badge_color = "#ff6b6b"
                    badge_bg = "rgba(220, 53, 69, 0.15)"
                    badge_border = "rgba(220, 53, 69, 0.3)"
                elif days_to_expiry <= 60:
                    badge_color = "#fcc419"
                    badge_bg = "rgba(255, 193, 7, 0.15)"
                    badge_border = "rgba(255, 193, 7, 0.3)"
                else:
                    badge_color = "#51cf66"
                    badge_bg = "rgba(40, 167, 69, 0.15)"
                    badge_border = "rgba(40, 167, 69, 0.3)"
            else:
                if days_to_expiry <= 3:
                    badge_color = "#ff6b6b"
                    badge_bg = "rgba(220, 53, 69, 0.15)"
                    badge_border = "rgba(220, 53, 69, 0.3)"
                elif days_to_expiry <= 7:
                    badge_color = "#fcc419"
                    badge_bg = "rgba(255, 193, 7, 0.15)"
                    badge_border = "rgba(255, 193, 7, 0.3)"
                else:
                    badge_color = "#51cf66"
                    badge_bg = "rgba(40, 167, 69, 0.15)"
                    badge_border = "rgba(40, 167, 69, 0.3)"
                    
            expiry_badge = f'<span style="background-color: {badge_bg}; color: {badge_color}; padding: 3px 8px; border-radius: 4px; font-size: 0.85rem; margin-left: 10px; font-weight: bold; border: 1px solid {badge_border};">⏳ {days_to_expiry} DTE left</span>'
            
        time_details_html = f"{opened_badge}{initial_dte_badge}{days_ago_badge}{expiry_badge}"
    else:
        time_details_html = f"{opened_badge}{days_ago_badge}"
        
    # Retrieve Profit Zone and Strikes proximity warning from processed dictionary
    in_profit_zone = p["in_profit_zone"]
    is_near_strike = p["is_near_strike"]
    near_strike_val = p["near_strike_val"]
    current_underlying_price = p["current_underlying_price"]
                
    if is_debit:
        zone_banner = "Profit Zone Irrelevant"
        zone_color = "#6c757d" # Grey
    elif in_profit_zone:
        if is_near_strike:
            zone_banner = f"⚠️ PROFIT ZONE (NEAR ${near_strike_val:.2f})"
            zone_color = "#ffc107" # Yellow
        else:
            zone_banner = "✅ IN PROFIT ZONE"
            zone_color = "#28a745" # Green
    else:
        zone_banner = "❌ OUT OF PROFIT ZONE"
        zone_color = "#dc3545" # Red
    
    # Calculate current PoP and the change from PoP at open
    current_pop = 0.0
    change_pop = 0.0
    if t.legs:
        cp = current_underlying_price if current_underlying_price is not None else t.underlying_price_at_open
        if cp:
            curr_legs_for_math = []
            for leg in t.legs:
                fallback = float(leg.price) if leg.price is not None else 0.0
                cur_price = get_leg_current_price(t.ticker, leg.expiry, leg.strike, leg.option_type, leg.position, fallback)
                curr_legs_for_math.append({
                    "action": leg.position,
                    "qty": leg.quantity if leg.quantity else 1,
                    "type": leg.option_type,
                    "strike": leg.strike,
                    "price": cur_price,
                    "expiry": pd.to_datetime(leg.expiry),
                    "iv": float(leg.iv) if leg.iv is not None else 30.0
                })
            try:
                curr_metrics = calculate_metrics(curr_legs_for_math, cp)
                current_pop = float(curr_metrics.get('pop', 0))
                open_pop = float(t.probability_of_profit or 0)
                change_pop = current_pop - open_pop
            except Exception:
                pass

    # Calculate underlying movement
    underlying_desc = "N/A"
    if current_underlying_price is not None and t.underlying_price_at_open:
        diff = current_underlying_price - t.underlying_price_at_open
        pct_diff = (diff / t.underlying_price_at_open) * 100
        sign = "+" if diff >= 0 else ""
        underlying_desc = f"${current_underlying_price:.2f} ({sign}${diff:.2f} / {sign}{pct_diff:.2f}%)"
    elif t.underlying_price_at_open:
        underlying_desc = f"${t.underlying_price_at_open:.2f} (Entry)"

    # Build Trade Status Label for Quick Visual Health Assessment
    entry_net = p['entry_net_premium']
    liq_val = p['liquidation_value']
    pct_suffix = ""
    if entry_net != 0:
        pct_val = (abs(liq_val) / abs(entry_net)) * 100
        pct_diff = abs(pct_val - 100)
        pct_suffix = f" | {pct_diff:.2f}%"

    if is_profit:
        status_banner = f"🟢 DOING WELL ({pnl_symbol} +${abs(upnl):,.2f}{pct_suffix})"
    else:
        status_banner = f"🔴 IN THE RED ({pnl_symbol} -${abs(upnl):,.2f}{pct_suffix})"

    # Render trade card
    with st.container():
        # Cleanly format the header banner using custom HTML
        st.markdown(
            f"""
            <div style="border-left: 5px solid {color_hex}; padding: 15px; border-radius: 6px; margin-bottom: 20px; border-top: 1px solid #ddd; border-right: 1px solid #ddd; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div>
                    <span style="font-size: 1.4rem; font-weight: bold; color: white;">#{t.trade_number or idx+1} {t.ticker}</span>
                    <span style="background-color: #f1f3f5; color: #495057; padding: 3px 8px; border-radius: 4px; font-size: 0.85rem; margin-left: 10px; font-weight: bold;">{t.strategy_type}</span>
                    {time_details_html}
                </div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <div style="font-size: 0.9rem; font-weight: bold; color: {zone_color}; padding: 4px 10px; border-radius: 4px; border: 1px solid {zone_color}; background-color: rgba(0,0,0,0.2);">
                        {zone_banner}
                    </div>
                    <div style="font-size: 0.9rem; font-weight: bold; color: {color_hex}; padding: 5px 11px; border-radius: 4px; border: 1px solid {color_hex}; background-color: rgba(0,0,0,0.2);">
                        {status_banner}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Information details layout
        cc1, cc2, cc3 = st.columns([1.5, 1.5, 1])
        
        with cc1:
            # Format and color Underlying Movement
            if current_underlying_price is not None and t.underlying_price_at_open:
                diff = current_underlying_price - t.underlying_price_at_open
                pct_diff = (diff / t.underlying_price_at_open) * 100
                diff_color = "#28a745" if diff >= 0 else "#dc3545"
                diff_sign = "+" if diff >= 0 else ""
                underlying_html = f"<span style='font-weight: bold;'>${current_underlying_price:.2f}</span> <span style='color: {diff_color}; font-weight: bold;'>({diff_sign}${diff:.2f} / {diff_sign}{pct_diff:.2f}%)</span>"
            elif t.underlying_price_at_open:
                underlying_html = f"<span style='font-weight: bold;'>${t.underlying_price_at_open:.2f}</span> <span style='color: #6c757d; font-weight: bold;'>(Entry)</span>"
            else:
                underlying_html = "<span style='font-weight: bold;'>N/A</span>"
            
            # Format and color PoP Change
            pop_color = "#28a745" if change_pop >= 0 else "#dc3545"
            pop_sign = "+" if change_pop >= 0 else ""
            pop_html = f"<span style='font-weight: bold;'>{current_pop*100:.1f}%</span> <span style='color: {pop_color}; font-weight: bold;'>({pop_sign}{change_pop*100:.1f}%)</span>"
            
            # Format and color Expected Direction
            expected_direction_text = t.expected_direction or "N/A"
            if "bullish" in expected_direction_text.lower():
                direction_color = "#28a745"  # Green
            elif "bearish" in expected_direction_text.lower():
                direction_color = "#dc3545"  # Red
            elif "neutral" in expected_direction_text.lower():
                direction_color = "#ffc107"  # Yellow
            else:
                direction_color = "inherit"
            direction_html = f"<span style='color: {direction_color}; font-weight: bold;'>{expected_direction_text}</span>"
            
            # Render Column 1 as a single block-level HTML element to prevent Markdown escaping
            st.markdown(f"""
            <div style="font-size: 1rem; line-height: 2.0; font-family: inherit; color: inherit;">
                <div style="margin-bottom: 6px;">📈 <b>Underlying Ticker Price:</b> {underlying_html}</div>
                <div style="margin-bottom: 6px;">🎯 <b>PoP (Current & Change):</b> {pop_html}</div>
                <div style="margin-bottom: 6px;">🔮 <b>Expected Direction:</b> {direction_html}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with cc2:
            # Format and color Net Position Cost
            entry_net = p['entry_net_premium']
            cost_color = "#28a745" if entry_net >= 0 else "#dc3545"
            cost_sign = "+" if entry_net >= 0 else "-"
            cost_html = f"<span style='color: {cost_color}; font-weight: bold;'>{cost_sign}${abs(entry_net):,.2f}</span>"
            
            # Format and color Current Liquidation Value
            liq_val = p['liquidation_value']
            liq_color = "#28a745" if liq_val >= 0 else "#dc3545"
            liq_sign = "+" if liq_val >= 0 else ""
            
            if entry_net != 0:
                pct_val = (abs(liq_val) / abs(entry_net)) * 100
                # Determine if it's a credit strategy
                is_credit = False
                if p["trade"].strategy_type:
                    strat_lower = p["trade"].strategy_type.lower()
                    if "credit" in strat_lower:
                        is_credit = True
                    elif "debit" in strat_lower:
                        is_credit = False
                    else:
                        is_credit = (entry_net > 0)
                else:
                    is_credit = (entry_net > 0)
                
                # Colors: green if <= 100% for credit, red if > 100%
                # Debit: green if >= 100%, red if < 100%
                if is_credit:
                    pct_color = "#28a745" if pct_val <= 100 else "#dc3545"
                else:
                    pct_color = "#28a745" if pct_val >= 100 else "#dc3545"
                    
                pct_diff = abs(pct_val - 100)
                pct_html = f" <span style='color: {pct_color}; font-weight: bold;'>({pct_diff:.2f}%)</span>"
            else:
                pct_html = ""
                
            liq_html = f"<span style='color: {liq_color}; font-weight: bold;'>{liq_sign}${liq_val:,.2f}</span>{pct_html}"
            
            # Format Collateral Held
            col_val = t.collateral or 0.0
            
            # Render Column 2 as a single block-level HTML element to prevent Markdown escaping
            st.markdown(f"""
            <div style="font-size: 1rem; line-height: 2.0; font-family: inherit; color: inherit;">
                <div style="margin-bottom: 6px;">💰 <b>Net Position Cost:</b> {cost_html}</div>
                <div style="margin-bottom: 6px;">🏦 <b>Current Liquidation Value:</b> {liq_html}</div>
                <div style="margin-bottom: 6px;">🛡️ <b>Collateral Held:</b> <span style="font-weight: bold; color: #17a2b8;">${col_val:,.2f}</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with cc3:
            # Action controls
            col_url, col_details = st.columns(2)
            
            with col_url:
                if t.idea_url:
                    st.link_button("🔗 View Trade Idea", t.idea_url, use_container_width=True)
                else:
                    st.button("🔗 No Idea URL", disabled=True, use_container_width=True, key=f"no_url_{t.id}")
            
            with col_details:
                if st.button("ℹ️ Details", key=f"details_btn_{t.id}", use_container_width=True):
                    st.session_state.details_trade_id = t.id
                    st.switch_page("pages/12_Trade_Details.py")
                
            # Edit / Close buttons side-by-side or stacked
            col_act1, col_act2 = st.columns(2)
            if col_act1.button("✏️ Edit", key=f"edit_btn_{t.id}", use_container_width=True):
                st.session_state.edit_trade_id = t.id
                st.session_state[f"loaded_{t.id}"] = False
                st.switch_page("pages/1_Trade.py")
                
            if col_act2.button("✖ Close", key=f"close_btn_{t.id}", use_container_width=True):
                st.session_state.close_trade_id = t.id
                st.switch_page("pages/5_Close Trade.py")
        
        # Option legs details expander
        with st.expander("🔍 View Option Legs & Metrics"):
            # Legs summary table
            legs_table_data = []
            for item in p["legs_details"]:
                leg = item["leg"]
                is_leg_live = p["is_live_pricing"]
                status_suffix = "" if is_leg_live else " (Entry Fallback)"
                entry_p = float(leg.price) if leg.price is not None else 0.0
                curr_p = item["current_price"]
                price_diff = curr_p - entry_p
                diff_sign = "+" if price_diff >= 0 else ""
                legs_table_data.append({
                    "Action": leg.position,
                    "Qty": leg.quantity,
                    "Type": leg.option_type,
                    "Strike": f"${leg.strike:.2f}",
                    "Expiry": leg.expiry,
                    "Entry Price": f"${entry_p:.3f}",
                    "Current Price": f"${curr_p:.3f}{status_suffix}",
                    "Price Difference": f"{diff_sign}${price_diff:.3f}"
                })
            st.table(pd.DataFrame(legs_table_data))

        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

db.close()
