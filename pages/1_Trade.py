import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from src.market_data import get_ticker_info
from src.options_math import generate_payoff_chart, calculate_metrics
from src.db import SessionLocal
from src.models import Trade, Leg, Transaction

def toggle_action(i):
    current = st.session_state[f"action_val_{i}"]
    st.session_state[f"action_val_{i}"] = "Buy" if current == "Sell" else "Sell"

def toggle_type(i):
    current = st.session_state[f"type_val_{i}"]
    st.session_state[f"type_val_{i}"] = "Call" if current == "Put" else "Put"

st.set_page_config(page_title="Trade Entry", page_icon="📝", layout="wide")

db = SessionLocal()

trade_to_edit = None
if "edit_trade_id" in st.session_state and st.session_state.edit_trade_id:
    st.title("Edit Trade Entry")
    trade_to_edit = db.query(Trade).filter(Trade.id == st.session_state.edit_trade_id).first()
    if trade_to_edit and not st.session_state.get(f"loaded_{trade_to_edit.id}"):
        st.session_state[f"loaded_{trade_to_edit.id}"] = True
        st.session_state["ticker_val"] = trade_to_edit.ticker
        st.session_state["name_val"] = trade_to_edit.underlying_name
        st.session_state["strategy_val"] = trade_to_edit.strategy_type
        st.session_state["move_val"] = trade_to_edit.expected_move
        st.session_state["url_val"] = trade_to_edit.idea_url
        st.session_state["date_val"] = trade_to_edit.date_opened
        st.session_state["num_legs"] = len(trade_to_edit.legs) or 2
        for i, leg in enumerate(trade_to_edit.legs):
            st.session_state[f"action_val_{i}"] = leg.position
            st.session_state[f"type_val_{i}"] = leg.option_type
            st.session_state[f"strike_{i}"] = leg.strike
            st.session_state[f"expiry_{i}"] = leg.expiry
else:
    st.title("New Trade Entry")

col1, col2 = st.columns(2)

with col1:
    ticker = st.text_input("Underlying Ticker", value=st.session_state.get("ticker_val", "MU")).upper()
    if ticker:
        with st.spinner("Fetching data..."):
            info = get_ticker_info(ticker)
        
        name = st.text_input("Name of Underlying", value=st.session_state.get("name_val", info['name']))
        
        cat_options = ["Stock", "ETF", "Index", "Futures", "Forex", "Crypto"]
        default_cat = info['category'].capitalize() if info['category'].capitalize() in cat_options else "Stock"
        category = st.selectbox("Category", cat_options, index=cat_options.index(default_cat))
        
        current_price = st.number_input("Underlying Price", value=float(info['current_price']) if info.get('current_price') else 1151.38, format="%.2f")
        
        strat_options = ["Bull put spread", "Bear call spread", "Iron condor", "Long call", "Long put", "Custom"]
        def_strat = st.session_state.get("strategy_val", "Bull put spread")
        strat_idx = strat_options.index(def_strat) if def_strat in strat_options else 0
        strategy_type = st.selectbox("Strategy Type", strat_options, index=strat_idx)

with col2:
    move_options = ["Bullish ↗", "Neutral →", "Bearish ↘", "High volatility"]
    def_move = st.session_state.get("move_val", "Bullish ↗")
    move_idx = move_options.index(def_move) if def_move in move_options else 0
    expected_move = st.selectbox("Expected Move", move_options, index=move_idx)
    
    idea_url = st.text_input("Idea URL", value=st.session_state.get("url_val", ""))
    date_opened = st.date_input("Date Opened", value=st.session_state.get("date_val", datetime.today()))

st.subheader("Options")

# Inject Custom CSS script via components.html
components.html("""
<script>
const observer = new MutationObserver(() => {
    const buttons = window.parent.document.querySelectorAll('.stButton button');
    buttons.forEach(b => {
        // Base styling for these specific toggle buttons
        if (['Buy', 'Sell', 'Call', 'Put'].includes(b.innerText)) {
            b.style.borderWidth = '1px';
            b.style.borderStyle = 'solid';
            b.style.borderRadius = '6px';
            b.style.boxShadow = 'none';
            b.style.minHeight = '40px';
            
            // Fix internal p tag font weight
            let p = b.querySelector('p');
            if (p) {
                p.style.fontWeight = '600';
            }

            if (b.innerText === 'Buy' || b.innerText === 'Call') {
                b.style.backgroundColor = '#e6f4ea';
                b.style.color = '#137333';
                b.style.borderColor = '#ceead6';
            } else if (b.innerText === 'Sell' || b.innerText === 'Put') {
                b.style.backgroundColor = '#fce8e6';
                b.style.color = '#c5221f';
                b.style.borderColor = '#fad2cf';
            }
        }
    });
});
observer.observe(window.parent.document.body, {childList: true, subtree: true});
</script>
""", height=0, width=0)

num_legs = st.number_input("Number of Legs", min_value=1, max_value=8, value=st.session_state.get("num_legs", 2), key="num_legs")

col_btn1, col_btn2 = st.columns([2, 10])
if col_btn1.button("Pull Live Data for All Legs"):
    with st.spinner("Fetching live data from Yahoo Finance..."):
        from src.market_data import get_live_option_leg_data
        from src.options_math import calculate_bs_delta
        for i in range(num_legs):
            strike = st.session_state.get(f"strike_input_{i}") or st.session_state.get(f"strike_{i}")
            expiry = st.session_state.get(f"expiry_input_{i}") or st.session_state.get(f"expiry_{i}")
            opt_type = st.session_state.get(f"type_val_{i}", "Put")
            
            if expiry and strike and ticker:
                expiry_str = pd.to_datetime(expiry).strftime('%Y-%m-%d')
                data = get_live_option_leg_data(ticker, expiry_str, float(strike), opt_type)
                if data:
                    action = st.session_state.get(f"action_val_{i}", "Buy")
                    bid = data.get('bid', 0.0)
                    ask = data.get('ask', 0.0)
                    
                    if action == "Sell" and bid > 0:
                        price = bid
                    elif action == "Buy" and ask > 0:
                        price = ask
                    else:
                        price = data.get('lastPrice', 0.0)
                        
                    iv_dec = data.get('impliedVolatility', 0.0)
                    iv_pct = iv_dec * 100
                    
                    st.session_state[f"price_{i}"] = price
                    st.session_state[f"iv_{i}"] = iv_pct
                    
                    # Calculate Delta
                    T = (pd.to_datetime(expiry) - pd.Timestamp.now().normalize()).days / 365.0
                    if T <= 0: T = 0.001
                    delta = calculate_bs_delta(current_price, float(strike), T, 0.05, iv_dec, opt_type)
                    st.session_state[f"delta_{i}"] = delta
    st.rerun()

legs_data = []

hcol0, hcol1, hcol2, hcol3, hcol4, hcol5, hcol6, hcol7, hcol8 = st.columns([0.8, 1.2, 1, 2.5, 1.5, 1.2, 1.5, 1.5, 1.5])
hcol1.write("**Action**")
hcol2.write("**Qty**")
hcol3.write("**Expiration Date**")
hcol4.write("**Strike**")
hcol5.write("**Type**")
hcol6.write("**Price**")
hcol7.write("**Delta**")
hcol8.write("**IV (%)**")

for i in range(num_legs):
    col0, col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.8, 1.2, 1, 2.5, 1.5, 1.2, 1.5, 1.5, 1.5])
    col0.markdown(f"<div style='padding-top:10px; font-weight:bold;'>{ticker}</div>", unsafe_allow_html=True)
    
    if f"action_val_{i}" not in st.session_state:
        st.session_state[f"action_val_{i}"] = "Sell" if i == 0 else "Buy"
    if f"type_val_{i}" not in st.session_state:
        st.session_state[f"type_val_{i}"] = "Put"
        
    action = st.session_state[f"action_val_{i}"]
    col1.button(action, key=f"action_btn_{i}", on_click=toggle_action, args=(i,), use_container_width=True)
    
    qty = col2.number_input("Qty", min_value=1, value=1, key=f"qty_{i}", label_visibility="collapsed")
    
    default_expiry = st.session_state.get(f"expiry_{i}", datetime(2026, 7, 17))
    expiry = col3.date_input("Expiry", value=default_expiry, key=f"expiry_input_{i}", label_visibility="collapsed")
    
    default_strike = st.session_state.get(f"strike_{i}", 840.0 if i==0 else 760.0)
    strike = col4.number_input("Strike", value=float(default_strike), step=1.0, format="%.2f", key=f"strike_input_{i}", label_visibility="collapsed")
    
    opt_type = st.session_state[f"type_val_{i}"]
    col5.button(opt_type, key=f"type_btn_{i}", on_click=toggle_type, args=(i,), use_container_width=True)
    
    price = col6.number_input("Price", value=26.23 if i==0 else 15.75, step=0.01, format="%.2f", key=f"price_{i}", label_visibility="collapsed")
    delta = col7.number_input("Delta", value=-0.13 if i==0 else -0.08, step=0.01, format="%.2f", key=f"delta_{i}", label_visibility="collapsed")
    iv = col8.number_input("IV", value=111.54 if i==0 else 117.19, step=0.01, format="%.2f", key=f"iv_{i}", label_visibility="collapsed")
    
    legs_data.append({
        "action": action,
        "qty": qty,
        "expiry": expiry,
        "strike": strike,
        "type": opt_type,
        "price": price,
        "delta": delta,
        "iv": iv
    })

# Format strategy text
st.markdown(f"#### {strategy_type}")
for leg in legs_data:
    color = "red" if leg['action'] == "Sell" else "green"
    sign = "-" if leg['action'] == "Sell" else "+"
    formatted_date = leg['expiry'].strftime("%b %d, %Y")
    st.markdown(f"<span style='color:{color}; font-weight:bold;'>{leg['action'].upper()} {sign}{leg['qty']} {ticker} {formatted_date} {leg['strike']:.2f} {leg['type'].lower()} @${leg['price']:.2f}</span>", unsafe_allow_html=True)

st.divider()

if ticker and current_price > 0:
    fig = generate_payoff_chart(legs_data, current_price, ticker)
    st.plotly_chart(fig, width='stretch')
    
    metrics = calculate_metrics(legs_data, current_price)
    
    total_contracts = sum(leg['qty'] for leg in legs_data)
    commissions = total_contracts * 0.65
    
    net_cost = sum((leg['price'] * 100 * leg['qty'] * (1 if leg['action'] == 'Buy' else -1)) for leg in legs_data)
    
    max_loss = metrics.get('max_loss', 0)
    if max_loss == float('-inf'):
        collateral = "Infinite"
        collateral_val = 0.0
    else:
        # Collateral only applies if a premium is received/collected (Net Credit, net_cost < 0)
        collateral_val = abs(max_loss) * 1.6 if (max_loss < 0 and net_cost < 0) else 0.0
        collateral = f"${collateral_val:.2f}"

        
    st.header("Results")
    
    st.subheader("Stock")
    scol1, scol2 = st.columns(2)
    scol1.metric("Stock current price", f"${current_price:.2f}", help="The current market price of the underlying asset.")
    
    bes = metrics.get('breakevens', [])
    be_str = ", ".join([f"${b:.2f}" for b in bes]) if bes else "N/A"
    scol2.metric("Breakeven price", be_str, help="The price(s) at which the strategy neither makes nor loses money at expiration.")
    
    st.subheader("Trade Details")
    tcol1, tcol2, tcol3, tcol4 = st.columns(4)
    # Cost of Trade logic: net_cost is negative for debit (paid) and positive for credit (received).
    tcol1.metric("Cost of trade", f"${-net_cost:.2f}", help="Total cost of the transaction. Positive if premium is received, negative if premium is paid.")
    tcol2.metric("Collateral amount", collateral, help="Calculated as Maximum Loss * 1.6")
    
    mp = metrics.get('max_profit', 0)
    mp_str = f"${mp:.2f}" if mp != float('inf') else "Infinite"
    tcol3.metric("Maximum profit", mp_str, help="The maximum potential profit of the strategy.")
    
    ml = metrics.get('max_loss', 0)
    ml_str = f"${ml:.2f}" if ml != float('-inf') else "Infinite"
    tcol4.metric("Maximum loss", ml_str, help="The maximum potential loss of the strategy.")
    
    st.subheader("Probability analysis")
    pcol1, pcol2, pcol3 = st.columns(3)
    pcol1.metric("Probability of profit", f"{metrics.get('pop', 0)*100:.1f}%", help="The theoretical probability of making at least $0.01 on this trade at expiration.")
    pcol2.metric("Probability of max profit", f"{metrics.get('pop_max_profit', 0)*100:.1f}%", help="The theoretical probability of achieving the maximum profit at expiration.")
    pcol3.metric("Probability of max loss", f"{metrics.get('pop_max_loss', 0)*100:.1f}%", help="The theoretical probability of hitting the maximum loss at expiration.")
    
    st.subheader("Risk reward analysis")
    rcol1, rcol2, rcol3 = st.columns(3)
    ev = metrics.get('ev', 0)
    rcol1.metric("Expected value (EV)", f"${ev:.2f}", help="The mathematically expected profit or loss per trade if executed many times.")
    
    er = metrics.get('er', 0)
    rcol2.metric("Expected return", f"{er*100:.1f}%", help="Expected Value divided by Maximum Risk.")
    
    rr = metrics.get('rr', 0)
    rr_str = f"{rr:.2f}" if rr != float('inf') else "Infinite"
    rcol3.metric("Risk to reward ratio", rr_str, help="Ratio of Maximum Loss to Maximum Profit.")
    
    st.subheader("Others")
    ocol1 = st.columns(1)[0]
    ocol1.metric("Commissions", f"${commissions:.2f}", help="Calculated as $0.65 per contract.")
    
    st.divider()
    
    btn_label = "Update Trade" if trade_to_edit else "Save Trade"
    if st.button(btn_label):
        # We need a consolidated cost if someone wants to track it
        cost = net_cost
        
        if trade_to_edit:
            trade_to_edit.ticker = ticker
            trade_to_edit.underlying_name = name
            trade_to_edit.category = category
            trade_to_edit.strategy_type = strategy_type
            trade_to_edit.expected_move = expected_move
            trade_to_edit.idea_url = idea_url
            trade_to_edit.date_opened = date_opened
            trade_to_edit.collateral = float(collateral_val)
            
            trade_to_edit.underlying_price_at_open = float(current_price)
            trade_to_edit.probability_of_profit = float(metrics.get('pop', 0))
            trade_to_edit.probability_max_profit = float(metrics.get('pop_max_profit', 0))
            trade_to_edit.probability_max_loss = float(metrics.get('pop_max_loss', 0))
            trade_to_edit.max_profit = float(metrics.get('max_profit', 0)) if metrics.get('max_profit', 0) != float('inf') else None
            trade_to_edit.max_loss = float(metrics.get('max_loss', 0)) if metrics.get('max_loss', 0) != float('-inf') else None
            trade_to_edit.expected_value = float(metrics.get('ev', 0))
            
            db.query(Leg).filter(Leg.trade_id == trade_to_edit.id).delete()
            open_tx = db.query(Transaction).filter(Transaction.trade_id == trade_to_edit.id, Transaction.action == "Open").first()
            if open_tx:
                open_tx.price = float(cost)
                open_tx.commission = float(commissions)
                open_tx.date = date_opened
                
            target_trade_id = trade_to_edit.id
            db.commit()
            st.success("Trade updated successfully!")
            st.session_state.edit_trade_id = None
        else:
            new_trade = Trade(
                ticker=ticker,
                underlying_name=name,
                category=category,
                strategy_type=strategy_type,
                expected_move=expected_move,
                idea_url=idea_url,
                date_opened=date_opened,
                collateral=float(collateral_val),
                underlying_price_at_open=float(current_price),
                probability_of_profit=float(metrics.get('pop', 0)),
                probability_max_profit=float(metrics.get('pop_max_profit', 0)),
                probability_max_loss=float(metrics.get('pop_max_loss', 0)),
                max_profit=float(metrics.get('max_profit', 0)) if metrics.get('max_profit', 0) != float('inf') else None,
                max_loss=float(metrics.get('max_loss', 0)) if metrics.get('max_loss', 0) != float('-inf') else None,
                expected_value=float(metrics.get('ev', 0))
            )
            db.add(new_trade)
            db.commit()
            db.refresh(new_trade)
            target_trade_id = new_trade.id
            
            new_transaction = Transaction(
                trade_id=target_trade_id,
                date=date_opened,
                action="Open",
                quantity=1,
                price=float(cost),
                commission=float(commissions)
            )
            db.add(new_transaction)
            db.commit()
            st.success("Trade saved successfully!")
            
        for leg in legs_data:
            new_leg = Leg(
                trade_id=target_trade_id,
                strike=float(leg['strike']),
                expiry=leg['expiry'],
                option_type=leg['type'],
                position=leg['action']
            )
            db.add(new_leg)
            
        db.commit()

db.close()
