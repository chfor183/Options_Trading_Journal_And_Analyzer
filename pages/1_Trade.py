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

@st.dialog("Extract Multi-Leg Strategy Help", width="large")
def show_multi_help():
    import os
    from PIL import Image
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_path = os.path.join(base_dir, "assets", "Multileg_tutorial.png")
        img = Image.open(img_path)
        st.image(img, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading tutorial image: {e}")
    st.markdown("""
    **How to use Extract Multi-Leg Strategy:**
    1. Open your **Interactive Brokers Desktop App**.
    2. View the multi-leg order/trade confirmation.
    3. Take a screenshot of the area shown in the image above (e.g., using Windows Snipping Tool `Win + Shift + S`).
    4. Click the **Extract Multi-Leg Strategy** button to automatically paste and parse it!
    """)

@st.dialog("Extract Single Contract Details Help", width="large")
def show_single_help():
    import os
    from PIL import Image
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_path = os.path.join(base_dir, "assets", "Singleleg_tutorial.png")
        img = Image.open(img_path)
        st.image(img, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading tutorial image: {e}")
    st.markdown("""
    **How to use Extract Single Contract Details:**
    1. Open your **Interactive Brokers Desktop App**.
    2. View the single contract details.
    3. Take a screenshot of the area shown in the image above (e.g., using Windows Snipping Tool `Win + Shift + S`).
    4. Click the **Extract Single Contract Details** button to automatically paste and parse it!
    """)

st.set_page_config(page_title="Trade Entry", page_icon="📝", layout="wide")

# Initialize default session state values safely
if "num_legs" not in st.session_state:
    st.session_state["num_legs"] = 2

db = SessionLocal()

trade_to_edit = None
if "edit_trade_id" in st.session_state and st.session_state.edit_trade_id:
    st.title("Edit Trade Entry")
    trade_to_edit = db.query(Trade).filter(Trade.id == st.session_state.edit_trade_id).first()
    if trade_to_edit and not st.session_state.get(f"loaded_{trade_to_edit.id}"):
        st.session_state[f"loaded_{trade_to_edit.id}"] = True
        st.session_state["ticker_val"] = trade_to_edit.ticker
        st.session_state["name_val"] = trade_to_edit.underlying_name
        st.session_state["last_ticker"] = trade_to_edit.ticker
        st.session_state["strategy_val"] = trade_to_edit.strategy_type
        st.session_state["move_val"] = trade_to_edit.expected_move
        st.session_state["url_val"] = trade_to_edit.idea_url
        st.session_state["date_val"] = trade_to_edit.date_opened
        st.session_state["num_legs"] = len(trade_to_edit.legs) or 2
        for i, leg in enumerate(trade_to_edit.legs):
            st.session_state[f"action_val_{i}"] = leg.position
            st.session_state[f"qty_{i}"] = leg.quantity if leg.quantity else 1
            st.session_state[f"type_val_{i}"] = leg.option_type
            st.session_state[f"strike_{i}"] = leg.strike
            st.session_state[f"price_{i}"] = float(leg.price)
            st.session_state[f"delta_{i}"] = float(leg.delta)
            st.session_state[f"iv_{i}"] = float(leg.iv)
            st.session_state[f"expiry_{i}"] = leg.expiry
else:
    st.title("New Trade Entry")

st.write("### 📸 Auto-Fill from Clipboard")
st.info("💡 **Note:** This OCR feature is designed **only for the Interactive Brokers Desktop App**.")
st.write("Take a screenshot of your broker's trade confirmation, then click one of the buttons below to paste it.")

# Use compact, native columns for the action and help buttons
col_btn1, col_help1, col_btn2, col_help2, _ = st.columns([2.6, 0.5, 2.8, 0.5, 5.6])

with col_btn1:
    btn_multi = st.button("Extract Multi-Leg Strategy", type="primary", use_container_width=True)
with col_help1:
    if st.button("❓", key="multi_help", use_container_width=True, help="Show Multi-Leg Screenshot Tutorial"):
        show_multi_help()

with col_btn2:
    btn_single = st.button("Extract Single Contract Details", use_container_width=True)
with col_help2:
    if st.button("❓", key="single_help", use_container_width=True, help="Show Single Contract Screenshot Tutorial"):
        show_single_help()

if btn_multi or btn_single:
    with st.spinner("Reading clipboard and extracting text with OCR..."):
        from src.ocr_parser import parse_trade_image, parse_single_leg_image
        from PIL import ImageGrab, Image
        
        img = ImageGrab.grabclipboard()
        
        if img is None:
            st.error("No image found on your clipboard. Please take a screenshot first (e.g., using Snipping Tool).")
        else:
            if isinstance(img, list):
                try:
                    img = Image.open(img[0])
                except Exception as e:
                    st.error("Found files in clipboard but could not load as an image.")
                    img = None
            
            if img:
                if btn_multi:
                    result = parse_trade_image(img)
                else:
                    result = parse_single_leg_image(img)
                    
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state["ticker_val"] = result["ticker"]
                    legs = result["legs"]
                    st.session_state["num_legs"] = len(legs)
                    for i, leg in enumerate(legs):
                        st.session_state[f"action_val_{i}"] = leg["action"]
                        st.session_state[f"qty_{i}"] = leg["qty"]
                        st.session_state[f"type_val_{i}"] = leg["type"]
                        st.session_state[f"strike_input_{i}"] = leg["strike"]
                        st.session_state[f"strike_{i}"] = leg["strike"]
                        try:
                            parsed_date = datetime.strptime(leg["expiry"], "%Y-%m-%d").date()
                            st.session_state[f"expiry_input_{i}"] = parsed_date
                            st.session_state[f"expiry_{i}"] = parsed_date
                        except:
                            pass # Let it fallback to default if parsing failed
                        st.session_state[f"price_{i}"] = 0.0 # Force pulling live data or manual entry
                        st.session_state[f"delta_{i}"] = 0.0
                    st.rerun()
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("<span style='color: #a1a1aa; font-weight: bold; font-size: 14px;'>Underlying Ticker</span>", unsafe_allow_html=True)
    ticker = st.text_input("Underlying Ticker", value=st.session_state.get("ticker_val", "GLD"), label_visibility="collapsed").upper()
    if ticker:
        with st.spinner("Fetching data..."):
            info = get_ticker_info(ticker)
        
        # Check if the ticker has changed to fetch and update name_val
        if "last_ticker" not in st.session_state or st.session_state["last_ticker"] != ticker:
            st.session_state["last_ticker"] = ticker
            st.session_state["name_val"] = "SPDR Gold Shares" if ticker == "GLD" else info['name']
        
        st.markdown("<span style='color: #a1a1aa; font-weight: bold; font-size: 14px;'>Name of Underlying</span>", unsafe_allow_html=True)
        name = st.text_input("Name of Underlying", value=st.session_state.get("name_val", "SPDR Gold Shares" if ticker == "GLD" else info['name']), label_visibility="collapsed")
        
        cat_options = ["Stock", "ETF", "Index", "Futures", "Forex", "Crypto"]
        default_cat = "ETF" if ticker == "GLD" else (info['category'].capitalize() if info['category'].capitalize() in cat_options else "Stock")
        st.markdown("<span style='color: #60a5fa; font-weight: bold; font-size: 14px;'>Category</span>", unsafe_allow_html=True)
        category = st.selectbox("Category", cat_options, index=cat_options.index(default_cat), label_visibility="collapsed")
        
        st.markdown("<span style='color: #a1a1aa; font-weight: bold; font-size: 14px;'>Underlying Price</span>", unsafe_allow_html=True)
        current_price = st.number_input("Underlying Price", value=float(373.63) if ticker == "GLD" else (float(info['current_price']) if info.get('current_price') else 1151.38), format="%.2f", label_visibility="collapsed")
        
        strat_options = [
            "Bull Put Spread (credit)",
            "Bear Call Spread (credit)",
            "Bull Call Spread (debit)",
            "Bear Put Spread (debit)",
            "Iron Condor (debit)",
            "Short Iron Condor (credit)",
            "Long Call (debit)",
            "Long Put (debit)",
            "Covered Call (credit)",
            "Cash-Secured Put (credit)",
            "Custom"
        ]
        def_strat = st.session_state.get("strategy_val", "Bull Put Spread (credit)" if ticker == "GLD" else "Bull Put Spread (credit)")
        strat_idx = strat_options.index(def_strat) if def_strat in strat_options else 0
        st.markdown("<span style='color: #60a5fa; font-weight: bold; font-size: 14px;'>Strategy Type</span>", unsafe_allow_html=True)
        strategy_type = st.selectbox("Strategy Type", strat_options, index=strat_idx, label_visibility="collapsed")

with col2:
    move_options = ["Bullish ↗", "Neutral →", "Bearish ↘", "High volatility"]
    def_move = st.session_state.get("move_val", "Bullish ↗" if ticker == "GLD" else "Bullish ↗")
    move_idx = move_options.index(def_move) if def_move in move_options else 0
    st.markdown("<span style='color: #60a5fa; font-weight: bold; font-size: 14px;'>Expected Move</span>", unsafe_allow_html=True)
    expected_move = st.selectbox("Expected Move", move_options, index=move_idx, label_visibility="collapsed")
    
    st.markdown("<span style='color: #60a5fa; font-weight: bold; font-size: 14px;'>Idea URL</span>", unsafe_allow_html=True)
    idea_url = st.text_input("Idea URL", value=st.session_state.get("url_val", ""), label_visibility="collapsed")
    
    st.markdown("<span style='color: #60a5fa; font-weight: bold; font-size: 14px;'>Date Opened</span>", unsafe_allow_html=True)
    date_opened = st.date_input("Date Opened", value=st.session_state.get("date_val", datetime(2026, 6, 26) if ticker == "GLD" else datetime.today()), label_visibility="collapsed")

st.subheader("Options")

# Inject Custom CSS script via components.html
components.html("""
<script>
const observer = new MutationObserver(() => {
    const parentDoc = window.parent.document;
    
    // Inject stylesheet if it doesn't exist
    if (!parentDoc.getElementById('custom-trade-styles')) {
        const styleEl = parentDoc.createElement('style');
        styleEl.id = 'custom-trade-styles';
        styleEl.textContent = `
            .fixed-save-button {
                position: fixed !important;
                bottom: 24px !important;
                right: 24px !important;
                width: 190px !important;
                z-index: 99999 !important;
                background-color: #2e7d32 !important; /* Nice Material green 800 */
                color: #ffffff !important;
                border: 1px solid #1b5e20 !important;
                border-radius: 8px !important;
                padding: 10px 24px !important;
                font-weight: 600 !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
                transition: background-color 0.2s, transform 0.1s !important;
            }
            .fixed-save-button:hover {
                background-color: #1b5e20 !important;
                transform: scale(1.03) !important;
                cursor: pointer !important;
            }
            .fixed-save-button:active {
                transform: scale(0.97) !important;
            }
            .fixed-save-button p {
                color: #ffffff !important;
                font-weight: 600 !important;
            }
        `;
        parentDoc.head.appendChild(styleEl);
    }

    const buttons = parentDoc.querySelectorAll('.stButton button');
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
        
        // Style Save/Update Trade buttons
        if (['Save Trade', 'Update Trade'].includes(b.innerText)) {
            b.classList.add('fixed-save-button');
        }
    });
});
observer.observe(window.parent.document.body, {childList: true, subtree: true});
</script>
""", height=0, width=0)

st.markdown("<span style='color: #a1a1aa; font-weight: bold; font-size: 14px;'>Number of Legs</span>", unsafe_allow_html=True)
num_legs = st.number_input("Number of Legs", min_value=1, max_value=8, key="num_legs", label_visibility="collapsed")

col_btn1, col_btn2 = st.columns([2, 10])
if col_btn1.button("Pull Live Data for All Legs"):
    with st.spinner("Fetching live data from Barchart..."):
        from src.market_data import get_barchart_live_option_leg_data
        from src.options_math import calculate_bs_delta
        for i in range(num_legs):
            strike = st.session_state.get(f"strike_input_{i}") or st.session_state.get(f"strike_{i}")
            expiry = st.session_state.get(f"expiry_input_{i}") or st.session_state.get(f"expiry_{i}")
            opt_type = st.session_state.get(f"type_val_{i}", "Put")
            
            if expiry and strike and ticker:
                expiry_str = pd.to_datetime(expiry).strftime('%Y-%m-%d')
                data = get_barchart_live_option_leg_data(ticker, expiry_str, float(strike), opt_type)
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
    # Removed st.rerun() because it aborts the run and destroys widget state below

legs_data = []

hcol0, hcol1, hcol2, hcol3, hcol4, hcol5, hcol6, hcol7, hcol8 = st.columns([0.8, 1.2, 1, 2.5, 1.5, 1.2, 1.5, 1.5, 1.5])
hcol1.markdown("<span style='color: #a1a1aa; font-weight: bold; font-size: 14px;'>Action</span>", unsafe_allow_html=True)
hcol2.markdown("<span style='color: #60a5fa; font-weight: bold; font-size: 14px;'>Qty</span>", unsafe_allow_html=True)
hcol3.markdown("<span style='color: #a1a1aa; font-weight: bold; font-size: 14px;'>Expiration Date</span>", unsafe_allow_html=True)
hcol4.markdown("<span style='color: #a1a1aa; font-weight: bold; font-size: 14px;'>Strike</span>", unsafe_allow_html=True)
hcol5.markdown("<span style='color: #a1a1aa; font-weight: bold; font-size: 14px;'>Type</span>", unsafe_allow_html=True)
hcol6.markdown("<span style='color: #60a5fa; font-weight: bold; font-size: 14px;'>Price</span>", unsafe_allow_html=True)
hcol7.markdown("<span style='color: #a1a1aa; font-weight: bold; font-size: 14px;'>Delta</span>", unsafe_allow_html=True)
hcol8.markdown("<span style='color: #a1a1aa; font-weight: bold; font-size: 14px;'>IV (%)</span>", unsafe_allow_html=True)

for i in range(num_legs):
    col0, col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.8, 1.2, 1, 2.5, 1.5, 1.2, 1.5, 1.5, 1.5])
    col0.markdown(f"<div style='padding-top:10px; font-weight:bold;'>{ticker}</div>", unsafe_allow_html=True)
    
    if f"action_val_{i}" not in st.session_state:
        st.session_state[f"action_val_{i}"] = "Sell" if i == 0 else "Buy"
    if f"type_val_{i}" not in st.session_state:
        st.session_state[f"type_val_{i}"] = "Put"
        
    action = st.session_state[f"action_val_{i}"]
    col1.button(action, key=f"action_btn_{i}", on_click=toggle_action, args=(i,), use_container_width=True)
    
    # Initialize session state values dynamically to prevent duplicate default values warning
    if f"qty_{i}" not in st.session_state:
        st.session_state[f"qty_{i}"] = 1
    qty = col2.number_input("Qty", min_value=1, key=f"qty_{i}", label_visibility="collapsed")
    
    if f"expiry_input_{i}" not in st.session_state:
        st.session_state[f"expiry_input_{i}"] = st.session_state.get(f"expiry_{i}", datetime(2026, 7, 17))
    expiry = col3.date_input("Expiry", key=f"expiry_input_{i}", label_visibility="collapsed")
    
    if f"strike_input_{i}" not in st.session_state:
        st.session_state[f"strike_input_{i}"] = float(st.session_state.get(f"strike_{i}", 355.0 if i==0 else 345.0))
    strike = col4.number_input("Strike", step=1.0, format="%.2f", key=f"strike_input_{i}", label_visibility="collapsed")
    
    opt_type = st.session_state[f"type_val_{i}"]
    col5.button(opt_type, key=f"type_btn_{i}", on_click=toggle_type, args=(i,), use_container_width=True)
    
    if f"price_{i}" not in st.session_state:
        st.session_state[f"price_{i}"] = 3.541 if i==0 else 2.248
    price = col6.number_input("Price", step=0.001, format="%.3f", key=f"price_{i}", label_visibility="collapsed")
    
    if f"delta_{i}" not in st.session_state:
        st.session_state[f"delta_{i}"] = -0.1956 if i==0 else -0.1129
    delta = col7.number_input("Delta", step=0.0001, format="%.4f", key=f"delta_{i}", label_visibility="collapsed")
    
    if f"iv_{i}" not in st.session_state:
        st.session_state[f"iv_{i}"] = 27.31 if i==0 else 29.28
    iv = col8.number_input("IV", step=0.01, format="%.2f", key=f"iv_{i}", label_visibility="collapsed")
    
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
    st.markdown(f"<span style='color:{color}; font-weight:bold;'>{leg['action'].upper()} {sign}{leg['qty']} {ticker} {formatted_date} {leg['strike']:.2f} {leg['type'].lower()} @${leg['price']:.3f}</span>", unsafe_allow_html=True)

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
    be_str = ", ".join([f"&#36;{b:.2f}" for b in bes]) if bes else "N/A"
    scol2.metric("Breakeven price", be_str, help="The price(s) at which the strategy neither makes nor loses money at expiration.")
    
    st.subheader("Trade Details")
    tcol1, tcol2, tcol3, tcol4, tcol5 = st.columns(5)
    # Cost of Trade logic: net_cost is negative for debit (paid) and positive for credit (received).
    tcol1.metric("Cost of trade", f"${-net_cost:.2f}", help="Total cost of the transaction. Positive if premium is received, negative if premium is paid.")
    tcol2.metric("Collateral amount", collateral, help="Calculated as Maximum Loss * 1.6")
    
    mp = metrics.get('max_profit', 0)
    mp_str = f"${mp:.2f}" if mp != float('inf') else "Infinite"
    tcol3.metric("Maximum profit", mp_str, help="The maximum potential profit of the strategy.")
    
    ml = metrics.get('max_loss', 0)
    ml_str = f"${ml:.2f}" if ml != float('-inf') else "Infinite"
    tcol4.metric("Maximum loss", ml_str, help="The maximum potential loss of the strategy.")
    
    if ml == 0:
        roi_str = "Infinite"
    elif mp == float('inf') or ml == float('-inf'):
        roi_str = "N/A"
    else:
        roi_str = f"{abs(mp / ml) * 100:.2f}%"
    tcol5.metric("ROI", roi_str, help="Calculated as Abs(Max profit / Max loss).")
    
    st.subheader("Probability analysis")
    pcol1, pcol2, pcol3, pcol4 = st.columns(4)
    pcol1.metric("Probability of profit", f"{metrics.get('pop', 0)*100:.1f}%", help="The theoretical probability of making at least $0.01 on this trade at expiration.")
    pcol2.metric("Probability of loss", f"{metrics.get('pol', 0)*100:.1f}%", help="The theoretical probability of losing money on this trade at expiration.")
    pcol3.metric("Probability of max profit", f"{metrics.get('pop_max_profit', 0)*100:.1f}%", help="The theoretical probability of achieving the maximum profit at expiration.")
    pcol4.metric("Probability of max loss", f"{metrics.get('pop_max_loss', 0)*100:.1f}%", help="The theoretical probability of hitting the maximum loss at expiration.")
    
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
            trade_to_edit.probability_of_loss = float(metrics.get('pol', 0))
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
            st.session_state[f"loaded_{trade_to_edit.id}"] = False
            st.session_state.edit_trade_id = None
        else:
            active_portfolio_id = st.session_state.get("active_portfolio_id")
            if not active_portfolio_id:
                st.error("No active portfolio selected. Please select a portfolio in the sidebar.")
                st.stop()
                
            from sqlalchemy import func
            max_num = db.query(func.max(Trade.trade_number)).filter(Trade.portfolio_id == active_portfolio_id).scalar()
            next_trade_num = (max_num or 0) + 1
            
            new_trade = Trade(
                portfolio_id=active_portfolio_id,
                trade_number=next_trade_num,
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
                probability_of_loss=float(metrics.get('pol', 0)),
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
                position=leg['action'],
                quantity=leg['qty'],
                price=float(leg['price']),
                delta=float(leg['delta']),
                iv=float(leg['iv'])
            )
            db.add(new_leg)
            
        db.commit()
        st.switch_page("pages/2_Journal.py")

db.close()
