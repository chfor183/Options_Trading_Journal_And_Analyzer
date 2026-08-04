import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from src.db import SessionLocal
from src.models import Trade, Transaction
from src.market_data import get_ticker_info, get_barchart_live_option_leg_data

st.markdown("<h3 style='margin-top: -15px; padding-top: 0; margin-bottom: 10px;'>Close Trade</h3>", unsafe_allow_html=True)

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

def format_currency(val):
    return f"${val:.2f}" if val is not None else "N/A"

def format_percentage(val):
    return f"{val*100:.1f}%" if val is not None else "N/A"

def format_string(val):
    return str(val) if val is not None else "N/A"

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

# Calculate Current Liquidation Value
entry_price = open_tx.price if open_tx else 0.0
entry_commission = open_tx.commission if open_tx else 0.0
entry_net_premium = -entry_price - entry_commission

liquidation_value = 0.0
for leg in trade.legs:
    fallback = float(leg.price) if leg.price is not None else 0.0
    cur_price = get_leg_current_price(trade.ticker, leg.expiry, leg.strike, leg.option_type, leg.position, fallback)
    qty = leg.quantity if leg.quantity else 1
    if leg.position in ["Buy", "Long"]:
        leg_val = cur_price * 100 * qty
    else:
        leg_val = -cur_price * 100 * qty
    liquidation_value += leg_val

unrealized_pnl = entry_net_premium + liquidation_value
if entry_net_premium != 0:
    pnl_pct = (unrealized_pnl / abs(entry_net_premium)) * 100
    pnl_pct_str = f"{pnl_pct:+.2f}%"
else:
    pnl_pct_str = "0.00%"

ticker_info = get_ticker_info(trade.ticker)
current_price_str = "N/A"
if ticker_info and ticker_info.get("current_price"):
    current_price_str = format_currency(float(ticker_info["current_price"]))

st.markdown(f"""
<style>
.compact-section {{ margin-bottom: 12px; font-size: 1.0rem; }}
.compact-header {{ margin: 5px 0 6px 0; font-size: 1.1rem; font-weight: 600; color: #a1a1aa; }}
.flex-row {{ display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 12px; }}
.flex-col {{ display: flex; flex-direction: column; }}
.compact-table {{ border-collapse: collapse; width: 100%; margin-bottom: 12px; font-size: 0.95rem; }}
.compact-table th, .compact-table td {{ padding: 4px 8px; text-align: left; border-bottom: 1px solid #333; }}
.compact-table th {{ color: #a1a1aa; font-weight: 600; }}
.block-container {{ padding-top: 2rem; padding-bottom: 1rem; }}
</style>

<div class="compact-section">
<h5 class="compact-header">Underlying</h5>
<div class="flex-row">
<div class="flex-col"><b>Trade #</b> <span>{trade.id}</span></div>
<div class="flex-col"><b>Ticker</b> <span>{trade.ticker}</span></div>
<div class="flex-col"><b>Name</b> <span>{format_string(trade.underlying_name)}</span></div>
<div class="flex-col"><b>Price at Open</b> <span>{format_currency(trade.underlying_price_at_open)}</span></div>
<div class="flex-col"><b style='color: #4da6ff;'>Current Price</b> <span style='color: #4da6ff; font-weight: bold;'>{current_price_str}</span></div>
</div>

<h5 class="compact-header">Position</h5>
<div class="flex-row">
<div class="flex-col"><b>Strategy</b> <span>{format_string(trade.strategy_type)}</span></div>
<div class="flex-col"><b>Date opened</b> <span>{trade.date_opened.strftime('%Y-%m-%d')}</span></div>
<div class="flex-col"><b>Cost of trade</b> <span>{format_currency(display_cost)}</span></div>
<div class="flex-col"><b>Collateral</b> <span>{format_currency(trade.collateral)}</span></div>
<div class="flex-col"><b>Category</b> <span>{format_string(trade.category)}</span></div>
<div class="flex-col"><b>Expected Direction</b> <span>{format_string(trade.expected_direction)}</span></div>
<div class="flex-col"><b>Current Liq. Value</b> <span>{format_currency(liquidation_value)} ({pnl_pct_str})</span></div>
</div>

<h5 class="compact-header">Probabilities & Metrics</h5>
<div class="flex-row">
<div class="flex-col"><b>Max Profit</b> <span>{format_currency(trade.max_profit)}</span></div>
<div class="flex-col"><b>Max Loss</b> <span>{format_currency(trade.max_loss)}</span></div>
<div class="flex-col"><b>POP</b> <span>{format_percentage(trade.probability_of_profit)}</span></div>
<div class="flex-col"><b>POL</b> <span>{format_percentage(trade.probability_of_loss)}</span></div>
<div class="flex-col"><b>P(Max Profit)</b> <span>{format_percentage(trade.probability_max_profit)}</span></div>
<div class="flex-col"><b>P(Max Loss)</b> <span>{format_percentage(trade.probability_max_loss)}</span></div>
<div class="flex-col"><b>Expected Value</b> <span>{format_currency(trade.expected_value)}</span></div>
</div>
</div>
""", unsafe_allow_html=True)

if trade.idea_url:
    st.markdown(f"<div style='margin-bottom: 12px; font-size: 1.0rem;'><b>Idea URL:</b> <a href='{trade.idea_url}'>{trade.idea_url}</a></div>", unsafe_allow_html=True)

table_html = "<table class='compact-table'><thead><tr><th>Action</th><th>Quantity</th><th>Type</th><th>Strike</th><th>Price</th><th>Delta</th><th>IV (%)</th><th>Expiry</th></tr></thead><tbody>"
for leg in trade.legs:
    table_html += f"<tr><td>{leg.position}</td><td>{leg.quantity if leg.quantity else 1}</td><td>{leg.option_type}</td><td>${leg.strike:.2f}</td><td>${leg.price:.3f}</td><td>{leg.delta:.4f}</td><td>{leg.iv:.2f}</td><td>{leg.expiry}</td></tr>"
table_html += "</tbody></table>"
st.markdown(f"<div class='compact-section'><h5 class='compact-header'>Position Legs</h5>{table_html}</div>", unsafe_allow_html=True)

st.markdown("<h5 style='margin: 15px 0 8px 0; font-size: 1.1rem; font-weight: 600; color: #a1a1aa;'>Closing Information</h5>", unsafe_allow_html=True)

total_quantity = sum(leg.quantity if leg.quantity else 1 for leg in trade.legs)
default_commission = float(total_quantity * 0.65)

default_underlying_price = None
if ticker_info and ticker_info.get("current_price"):
    cur_p = float(ticker_info["current_price"])
    if cur_p > 0:
        default_underlying_price = cur_p

with st.form("close_trade_form"):
    fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns(5)
    
    close_date = fcol1.date_input("Close Date", value=datetime.today())
    
    close_type = fcol2.selectbox("Type of Close", [
        "Closing for profit",
        "Closing for loss",
        "Closed by stop-loss",
        "Rolling",
        "Expired",
        "Closed by broker"
    ])
    
    closing_price = fcol3.number_input("Closing Price (Net)", value=float(liquidation_value), step=0.01, format="%.2f", help="Net credit received (+) or debit paid (-) to close")
    
    commission = fcol4.number_input("Closing Commission", value=default_commission, step=0.01, format="%.2f")
    
    underlying_price_at_close = fcol5.number_input("Underlying Price", value=default_underlying_price, step=0.01, format="%.2f", help="Price of the underlying asset when closing")
    
    submit = st.form_submit_button("Submit Close")
    
    if submit:
        # Update trade status
        trade.status = close_type
        if underlying_price_at_close is not None:
            trade.underlying_price_at_close = underlying_price_at_close
        
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
        
        st.toast("Trade closed successfully! 🎉", icon="✅")

# Inject Custom CSS script via components.html
components.html(r"""
<script>
const observer = new MutationObserver(() => {
    const parentDoc = window.parent.document;
    
    // Inject stylesheet if it does not exist
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

    const buttons = parentDoc.querySelectorAll('button');
    buttons.forEach(b => {
        // Style Save/Update Trade buttons
        const btnText = (b.innerText || b.textContent || '').trim();
        if (btnText === 'Submit Close' || btnText.includes('Submit Close')) {
            b.classList.add('fixed-save-button');
            if (!b.dataset.clickDisabled) {
                b.dataset.clickDisabled = "true";
                b.addEventListener('click', () => {
                    b.style.pointerEvents = 'none';
                    b.style.opacity = '0.7';
                    setTimeout(() => {
                        b.style.pointerEvents = 'auto';
                        b.style.opacity = '1';
                    }, 3000);
                });
            }
        }
    });
});
observer.observe(window.parent.document.body, { childList: true, subtree: true });
</script>
""", height=0, width=0)

db.close()
