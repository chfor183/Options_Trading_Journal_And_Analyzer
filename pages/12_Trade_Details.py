import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import json
import numpy as np

from src.db import SessionLocal
from src.models import Trade, Transaction
from src.market_data import get_ticker_info, get_barchart_live_option_leg_data
from src.options_math import calculate_metrics, generate_payoff_chart


def get_leg_current_price(ticker, expiry_date, strike, option_type, position, fallback_price):
    try:
        expiry_str = pd.to_datetime(expiry_date).strftime('%Y-%m-%d')
        leg_data = get_barchart_live_option_leg_data(ticker, expiry_str, strike, option_type)
        if leg_data:
            bid = leg_data.get('bid', 0.0)
            ask = leg_data.get('ask', 0.0)
            last = leg_data.get('lastPrice', 0.0)
            
            if position in ["Sell", "Short"]:
                return ask if ask > 0 else (last if last > 0 else float(fallback_price))
            else:
                return bid if bid > 0 else (last if last > 0 else float(fallback_price))
    except Exception:
        pass
    return float(fallback_price)

st.title("Trade Details")

if "details_trade_id" not in st.session_state or st.session_state.details_trade_id is None:
    st.warning("No trade selected. Please go to the Journal and select a trade to view details.")
    if st.button("Go to Journal"):
        st.switch_page("pages/2_Journal.py")
    st.stop()

trade_id = st.session_state.details_trade_id

db = SessionLocal()
trade = db.query(Trade).filter(Trade.id == trade_id).first()

if not trade:
    st.error("Trade not found.")
    if st.button("Go to Journal"):
        st.switch_page("pages/2_Journal.py")
    st.stop()

def format_currency(val):
    return f"${val:.2f}" if val is not None else "N/A"

def format_percentage(val):
    return f"{val*100:.1f}%" if val is not None else "N/A"

def format_string(val):
    return str(val) if val is not None else "N/A"

# --- Metrics Calculations ---
open_tx = next((tx for tx in trade.transactions if tx.action == "Open"), None)
raw_cost = open_tx.price if open_tx else 0.0
display_cost = -raw_cost

pnl = 0.0
total_commission = 0.0
for tx in trade.transactions:
    if tx.action == "Open":
        pnl += -tx.price - tx.commission
    else:
        pnl += tx.price - tx.commission
    total_commission += tx.commission

ticker_info = get_ticker_info(trade.ticker)
current_price_str = "N/A"
if ticker_info and ticker_info.get("current_price"):
    current_price_str = format_currency(float(ticker_info["current_price"]))

close_dates = [tx for tx in trade.transactions if tx.action != "Open"]
close_date_str = max([tx.date for tx in close_dates]).strftime('%Y-%m-%d') if close_dates else "Not Closed"

# Current Liquidation Value or Final Value
is_open = trade.status == "Open"
value_label = "Current Liquidation Value" if is_open else "Final Value"
val_pct_str = ""

if is_open:
    current_liquidation_value = 0.0
    for leg in trade.legs:
        fallback = float(leg.price) if leg.price is not None else 0.0
        cur_price = get_leg_current_price(trade.ticker, leg.expiry, leg.strike, leg.option_type, leg.position, fallback)
        qty = leg.quantity if leg.quantity else 1
        if leg.position in ["Buy", "Long"]:
            leg_val = cur_price * 100 * qty
        else:
            leg_val = -cur_price * 100 * qty
        current_liquidation_value += leg_val
    
    val_amount = current_liquidation_value
else:
    val_amount = sum((tx.price - tx.commission) for tx in close_dates)

val_pct = 0.0
pos_return_dollars = pnl + val_amount
if pnl != 0:
    val_pct = (pos_return_dollars / abs(pnl)) * 100
    val_pct_str = f"{format_currency(pos_return_dollars)}({'+' if val_pct > 0 else ''}{val_pct:.2f}%)"
else:
    val_pct_str = f"{format_currency(pos_return_dollars)}(N/A)"

val_sign = "+" if val_amount > 0 else ""
val_display_str = f"<span>{val_sign}{format_currency(val_amount)}</span>"

pct_color = "#28a745" if pos_return_dollars > 0 else "#dc3545" if pos_return_dollars < 0 else "inherit"
pct_display_str = f"<span style='color:{pct_color}; font-weight:bold;'>{val_pct_str}</span>"

st.markdown(f"### {trade.ticker} - {format_string(trade.underlying_name)}")

st.markdown(f"""
#### General Information
<div style='display: flex; flex-wrap: wrap; gap: 40px; margin-bottom: 25px; font-size: 1.1rem; background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);'>
    <div style='display: flex; flex-direction: column;'><b>Trade Status</b> <span>{trade.status}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Strategy</b> <span>{format_string(trade.strategy_type)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Category</b> <span>{format_string(trade.category)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Expected Direction</b> <span>{format_string(trade.expected_direction)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Date Opened</b> <span>{trade.date_opened.strftime('%Y-%m-%d')}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Date Closed</b> <span>{close_date_str}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Trade Number</b> <span>{trade.trade_number if trade.trade_number else 'N/A'}</span></div>
</div>

#### Financial & Market Data
<div style='display: flex; flex-wrap: nowrap; justify-content: space-between; gap: 15px; margin-bottom: 25px; font-size: 0.95rem; background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);'>
    <div style='display: flex; flex-direction: column;'><b>Cost of Trade</b> <span>{format_currency(display_cost)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Collateral</b> <span>{format_currency(trade.collateral)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Total Commissions</b> <span>{format_currency(total_commission)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Net PnL</b> <span>{format_currency(pnl)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>{value_label}</b> {val_display_str}</div>
    <div style='display: flex; flex-direction: column;'><b>Position Return</b> {pct_display_str}</div>
    <div style='display: flex; flex-direction: column;'><b>Underlying Price at Open</b> <span>{format_currency(trade.underlying_price_at_open)}</span></div>
    <div style='display: flex; flex-direction: column;'><b>Underlying Price at Close</b> <span>{format_currency(trade.underlying_price_at_close)}</span></div>
    <div style='display: flex; flex-direction: column;'><b style='color: #4da6ff;'>Current Market Price</b> <span style='color: #4da6ff; font-weight: bold;'>{current_price_str}</span></div>
</div>
""", unsafe_allow_html=True)

if trade.idea_url:
    st.write(f"**Idea URL:** [{trade.idea_url}]({trade.idea_url})")

st.divider()

st.subheader("Metrics Comparison (Current vs. Opening)")

# Calculate current metrics
current_metrics = {}
legs_for_math = []
legs_for_chart = []
cp = float(ticker_info["current_price"]) if ticker_info and ticker_info.get("current_price") else (trade.underlying_price_at_open if trade.underlying_price_at_open else 100.0)

for leg in trade.legs:
    price = float(leg.price) if leg.price else 0.0
    iv = float(leg.iv) if leg.iv else 0.0
    expiry_str = pd.to_datetime(leg.expiry).strftime('%Y-%m-%d')
    if is_open:
        leg_data = get_barchart_live_option_leg_data(trade.ticker, expiry_str, leg.strike, leg.option_type)
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
        "action": "Buy" if leg.position in ["Buy", "Long"] else "Sell",
        "qty": leg.quantity if leg.quantity else 1,
        "type": leg.option_type,
        "strike": leg.strike,
        "price": price,
        "expiry": pd.to_datetime(leg.expiry),
        "iv": iv
    })
    legs_for_chart.append({
        "action": "Buy" if leg.position in ["Buy", "Long"] else "Sell",
        "qty": leg.quantity if leg.quantity else 1,
        "type": leg.option_type,
        "strike": leg.strike,
        "price": price,
        "expiry": pd.to_datetime(leg.expiry),
        "iv": iv,
        "delta": float(leg.delta) if leg.delta else 0.0
    })

if is_open:
    try:
        current_metrics = calculate_metrics(legs_for_math, cp)
    except Exception as e:
        pass

comp_cols = st.columns(5)

# Opening stats
open_up = f"${trade.underlying_price_at_open:.2f}" if trade.underlying_price_at_open else "N/A"
open_pop = f"{trade.probability_of_profit*100:.1f}%" if trade.probability_of_profit is not None else "N/A"
open_pol = f"{trade.probability_of_loss*100:.1f}%" if trade.probability_of_loss is not None else "N/A"
open_pmp = f"{trade.probability_max_profit*100:.1f}%" if trade.probability_max_profit is not None else "N/A"
open_pml = f"{trade.probability_max_loss*100:.1f}%" if trade.probability_max_loss is not None else "N/A"

# Current stats from metrics dictionary calculated earlier
curr_up = current_price_str

if is_open and current_metrics:
    curr_pop = f"{current_metrics.get('pop', 0)*100:.1f}%"
    curr_pol = f"{current_metrics.get('pol', 0)*100:.1f}%"
    curr_pmp = f"{current_metrics.get('pop_max_profit', 0)*100:.1f}%"
    curr_pml = f"{current_metrics.get('pop_max_loss', 0)*100:.1f}%"
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
    
if is_open:
    comp_cols[0].metric("Underlying Price", curr_up, delta=safe_delta(curr_up, open_up, True))
else:
    close_up = f"${trade.underlying_price_at_close:.2f}" if getattr(trade, 'underlying_price_at_close', None) is not None else "N/A"
    comp_cols[0].metric("Underlying Price", close_up, delta=safe_delta(close_up, open_up, True))
    
comp_cols[1].metric("Probability of Profit", curr_pop, delta=safe_delta(curr_pop, open_pop))
comp_cols[2].metric("Probability of Loss", curr_pol, delta=safe_delta(curr_pol, open_pol, inverse=True), delta_color="inverse")
comp_cols[3].metric("Prob. of Max Profit", curr_pmp, delta=safe_delta(curr_pmp, open_pmp))
comp_cols[4].metric("Prob. of Max Loss", curr_pml, delta=safe_delta(curr_pml, open_pml, inverse=True), delta_color="inverse")

st.markdown(f"*Opening values:* Price: {open_up} | POP: {open_pop} | POL: {open_pol} | Prob Max Profit: {open_pmp} | Prob Max Loss: {open_pml}")

st.divider()

if is_open:
    chart_price = cp
    price_label = "Current Price"
else:
    chart_price = float(trade.underlying_price_at_close) if getattr(trade, 'underlying_price_at_close', None) else cp
    price_label = "Close price"

open_price = float(trade.underlying_price_at_open) if trade.underlying_price_at_open else None

if trade.legs and chart_price > 0:
    if is_open:
        col_toggles = st.columns([1, 1, 2])
        show_current_em = col_toggles[0].toggle("Show Current Expected Move", value=True)
        show_open_em = col_toggles[1].toggle("Show Expected Move at Open", value=False)
    else:
        col_toggles = st.columns([1, 3])
        show_current_em = False
        show_open_em = col_toggles[0].toggle("Show Expected Move at Open", value=True)

    fig = generate_payoff_chart(legs_for_chart, chart_price, trade.ticker, open_price=open_price, current_price_label=price_label, trade_date=trade.date_opened, show_current_em=show_current_em, show_open_em=show_open_em)
    st.plotly_chart(fig, width='stretch')

st.subheader("Position Legs")
if trade.legs:
    legs_data = []
    for leg in trade.legs:
        legs_data.append({
            "Action": leg.position,
            "Quantity": leg.quantity if leg.quantity else 1,
            "Type": leg.option_type,
            "Strike": f"${leg.strike:.2f}",
            "Price": f"${leg.price:.3f}",
            "Delta": f"{leg.delta:.4f}",
            "IV": f"{leg.iv:.2f}%",
            "Expiry": leg.expiry,
        })
    st.table(pd.DataFrame(legs_data))
else:
    st.info("No legs found for this trade.")

st.divider()

st.subheader("Transaction History")
if trade.transactions:
    tx_data = []
    for tx in trade.transactions:
        # DB stores Open price as Cost (Positive for Debit, Negative for Credit).
        # We invert it to display as Cashflow (Positive for Credit, Negative for Debit) to match closing txs.
        disp_price = -tx.price if tx.action == "Open" else tx.price
        tx_data.append({
            "Date": tx.date.strftime('%Y-%m-%d %H:%M'),
            "Action": tx.action,
            "Quantity": tx.quantity,
            "Price": f"${disp_price:.2f}",
            "Commission": f"${tx.commission:.2f}"
        })
    st.table(pd.DataFrame(tx_data))
else:
    st.info("No transactions found.")

st.divider()

idea_col1, idea_col2 = st.columns(2)

if trade.legs:
    first_leg = min(trade.legs, key=lambda l: l.expiry)
    days_to_expiry = (first_leg.expiry - trade.date_opened.date()).days
    if days_to_expiry <= 0:
        days_to_expiry = 1
else:
    days_to_expiry = 30
    
term = days_to_expiry / 365.0
ivs = [float(leg.iv) for leg in trade.legs if leg.iv and float(leg.iv) > 0]
avg_iv = (sum(ivs) / len(ivs)) / 100.0 if ivs else 0.3

em_pct = avg_iv * np.sqrt(term)
underlying_price = trade.underlying_price_at_open if trade.underlying_price_at_open else 100.0
em_range_val = underlying_price * em_pct
lower_bound = underlying_price - em_range_val
upper_bound = underlying_price + em_range_val

legs_formatted_list = []
if trade.legs:
    for leg in trade.legs:
        action_str = "SELL" if leg.position in ["Short", "Sell"] else "BUY"
        qty_prefix = "-" if leg.position in ["Short", "Sell"] else "+"
        qty_val = leg.quantity if leg.quantity else 1
        leg_line = f"- {action_str} {qty_prefix}{qty_val} {trade.ticker} {leg.expiry.strftime('%Y-%m-%d')} {float(leg.strike):.2f} {leg.option_type} @ ${float(leg.price):.3f} (Delta: {float(leg.delta):.4f}, IV: {float(leg.iv):.2f}%)"
        legs_formatted_list.append(leg_line)
legs_text = "\n".join(legs_formatted_list) if trade.legs else "None"

cost_suffix = "Net Credit" if display_cost >= 0 else "Net Debit"
cost_str = f"${abs(display_cost):.2f} {cost_suffix}"
pop_str = f"{trade.probability_of_profit*100:.1f}%" if trade.probability_of_profit is not None else "N/A"

idea_text = f"{trade.ticker} - {trade.strategy_type or 'N/A'} ({days_to_expiry} DTE) @ {cost_str}\n" \
            f"Ticker : {trade.ticker}\n" \
            f"Name : {trade.underlying_name or 'N/A'}\n" \
            f"Date Opened : {trade.date_opened.strftime('%Y-%m-%d')}\n" \
            f"Price of underlying at opening : {f'${trade.underlying_price_at_open:.2f}' if trade.underlying_price_at_open else 'N/A'}\n" \
            f"Expected Move : ±{em_pct*100:.1f}% [{lower_bound:.2f},{upper_bound:.2f}]\n" \
            f"Strategy : {trade.strategy_type or 'N/A'}\n" \
            f"Legs : \n" \
            f"{legs_text}\n" \
            f"Cost of trade : {cost_str}\n" \
            f"Probability of profit : {pop_str}"

# Calculate Entry Breakevens for Pinescript
entry_legs = []
if trade.legs:
    for leg in trade.legs:
        entry_legs.append({
            "action": "Buy" if leg.position in ["Buy", "Long"] else "Sell",
            "qty": leg.quantity if leg.quantity else 1,
            "type": leg.option_type,
            "strike": leg.strike,
            "price": float(leg.price) if leg.price else 0.0,
            "expiry": pd.to_datetime(leg.expiry),
            "iv": float(leg.iv) if leg.iv else 0.0
        })
entry_metrics = calculate_metrics(entry_legs, float(trade.underlying_price_at_open) if trade.underlying_price_at_open else 100.0)
entry_bes = entry_metrics.get("breakevens", [])

# Formulate the JSON structure precisely as expected by the Pinescript
sorted_strikes = sorted([float(leg.strike) for leg in trade.legs if leg.strike]) if trade.legs else []
pinescript_json_dict = {
    "strategy": trade.strategy_type or "N/A",
    "underlying_open": float(trade.underlying_price_at_open) if trade.underlying_price_at_open else 0.0,
    "premium": float(abs(display_cost)) / 100.0,
    "open_date": trade.date_opened.strftime('%Y-%m-%d'),
    "expiry_date": first_leg.expiry.strftime('%Y-%m-%d') if trade.legs else trade.date_opened.strftime('%Y-%m-%d'),
    "expected_move": round(float(em_range_val), 2),
}
if trade.probability_of_profit is not None:
    pinescript_json_dict["pop"] = round(float(trade.probability_of_profit) * 100, 1)
else:
    pinescript_json_dict["pop"] = 0.0
    
for idx, strike in enumerate(sorted_strikes[:4], start=1):
    pinescript_json_dict[f"strike{idx}"] = strike
    
if len(entry_bes) >= 1:
    pinescript_json_dict["breakeven1"] = round(entry_bes[0], 2)
if len(entry_bes) >= 2:
    pinescript_json_dict["breakeven2"] = round(entry_bes[1], 2)

pinescript_json_str = json.dumps(pinescript_json_dict, indent=2)

with idea_col1:
    st.subheader("Copyable Trade Idea")
    st.code(idea_text, language="text")

with idea_col2:
    st.subheader("TradingView Pine Script JSON")
    st.code(pinescript_json_str, language="json")

st.divider()

db.close()
