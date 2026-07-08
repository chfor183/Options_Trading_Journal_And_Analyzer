import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.market_data import get_dcf_financial_data

# Set Streamlit page config
st.set_page_config(page_title="DCF Evaluation", page_icon="💵", layout="wide")

# Custom Compact CSS
st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        padding-bottom: 0px !important;
    }
    .metric-card {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #334155;
        text-align: center;
        min-height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# CORE DCF VALUATION ENGINE
# -------------------------------------------------------------
def run_dcf_model(
    fcf_base_m: float,       # Base FCF in Millions
    shares_m: float,         # Shares outstanding in Millions
    cash_m: float,           # Cash in Millions
    debt_m: float,           # Debt in Millions
    growth_rate: float,      # Initial Growth Rate (Year 1)
    terminal_growth: float,  # Terminal Growth Rate (perpetual)
    discount_rate: float,    # Discount Rate / WACC
    decay_pattern: str = "Continuous (Decay from Year 2)",
    x_val: float = 0.0       # Fixed percentage points (fraction) added or subtracted each year starting in Year 2
) -> dict:
    # 1. Project Growth Rates for 10 Years
    growths = []
    if "Add X% each year" in decay_pattern:
        for t in range(1, 11):
            growths.append(growth_rate + (t - 1) * x_val)
    elif "Remove X% each year" in decay_pattern:
        for t in range(1, 11):
            growths.append(growth_rate - (t - 1) * x_val)
    else:
        if decay_pattern == "Continuous (Decay from Year 2)":
            decay_start_year = 2
        elif decay_pattern == "Keep Stable (Entire 10 Years)":
            decay_start_year = 11
        else:
            decay_start_year = 6

        for t in range(1, 11):
            if t < decay_start_year:
                # Stable initial growth rate
                growths.append(growth_rate)
            else:
                # Linear decay from decay_start_year to Year 10 down to terminal_growth
                if 10 - decay_start_year <= 0:
                    # If decay starts at Year 10, or is stable throughout (e.g. decay_start_year >= 11)
                    growths.append(terminal_growth)
                else:
                    fraction = (t - decay_start_year) / (10 - decay_start_year)
                    g_t = growth_rate - fraction * (growth_rate - terminal_growth)
                    growths.append(g_t)
            
    # 2. Project Free Cash Flows (Millions)
    fcf_projections = []
    current_fcf = fcf_base_m
    for t in range(1, 11):
        next_fcf = current_fcf * (1 + growths[t-1])
        fcf_projections.append(next_fcf)
        current_fcf = next_fcf
        
    # 3. Discount cash flows to Present Value (PV)
    pv_fcfs = []
    for t in range(1, 11):
        pv = fcf_projections[t-1] / ((1 + discount_rate) ** t)
        pv_fcfs.append(pv)
        
    # 4. Calculate Terminal Value
    fcf_10 = fcf_projections[-1]
    safe_discount_rate = max(discount_rate, terminal_growth + 0.005)
    terminal_value = (fcf_10 * (1 + terminal_growth)) / (safe_discount_rate - terminal_growth)
    pv_terminal_value = terminal_value / ((1 + discount_rate) ** 10)
    
    # 5. Totals
    enterprise_value = sum(pv_fcfs) + pv_terminal_value
    equity_value = enterprise_value + cash_m - debt_m
    intrinsic_value = equity_value / shares_m if shares_m > 0 else 0.0
    
    return {
        "growths": growths,
        "fcf_projections": fcf_projections,
        "pv_fcfs": pv_fcfs,
        "terminal_value": terminal_value,
        "pv_terminal_value": pv_terminal_value,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "intrinsic_value": max(0.0, intrinsic_value)
    }

def solve_implied_growth(
    fcf_base_m: float,
    current_price: float,
    shares_m: float,
    cash_m: float,
    debt_m: float,
    terminal_growth: float,
    discount_rate: float,
    decay_pattern: str = "Continuous (Decay from Year 2)",
    x_val: float = 0.0
) -> float:
    # Solves for growth_rate such that intrinsic_value == current_price
    if fcf_base_m <= 0 or current_price <= 0 or shares_m <= 0:
        return None
        
    low = -0.90
    high = 3.0
    
    # Verify bounds
    val_low = run_dcf_model(fcf_base_m, shares_m, cash_m, debt_m, low, terminal_growth, discount_rate, decay_pattern, x_val)["intrinsic_value"]
    val_high = run_dcf_model(fcf_base_m, shares_m, cash_m, debt_m, high, terminal_growth, discount_rate, decay_pattern, x_val)["intrinsic_value"]
    
    if current_price <= val_low:
        return low
    if current_price >= val_high:
        return high
        
    for _ in range(100):
        mid = (low + high) / 2.0
        val_mid = run_dcf_model(fcf_base_m, shares_m, cash_m, debt_m, mid, terminal_growth, discount_rate, decay_pattern, x_val)["intrinsic_value"]
        
        if abs(val_mid - current_price) < 0.01:
            return mid
            
        if val_mid < current_price:
            low = mid
        else:
            high = mid
            
    return (low + high) / 2.0
            
    return (low + high) / 2.0


# -------------------------------------------------------------
# CALLBACKS FOR REACTIVE RESET & MOVEMENT
# -------------------------------------------------------------
def on_base_growth_change():
    if "base_growth_slider" in st.session_state and "spread_slider" in st.session_state:
        base_val = st.session_state.base_growth_slider
        spread_val = st.session_state.spread_slider
        st.session_state.con_growth_val = base_val - spread_val
        st.session_state.agg_growth_val = base_val + spread_val

def on_spread_change():
    if "base_growth_slider" in st.session_state and "spread_slider" in st.session_state:
        base_val = st.session_state.base_growth_slider
        spread_val = st.session_state.spread_slider
        st.session_state.con_growth_val = base_val - spread_val
        st.session_state.agg_growth_val = base_val + spread_val


# -------------------------------------------------------------
# USER INTERFACE SETUP
# -------------------------------------------------------------
st.title("💵 Discounted Cash Flow (DCF) Evaluation")
st.markdown("Assess a stock's intrinsic value using a **10-Year Free Cash Flow** model and reverse-engineer market expectations.")

# Ticker selection bar
ticker_input = st.text_input("Enter Ticker Symbol:", value="MSFT").strip().upper()

if ticker_input:
    # Fetch live data
    with st.spinner(f"Fetching financial data for {ticker_input}..."):
        raw_data = get_dcf_financial_data(ticker_input)
        
    if raw_data.get("current_price", 0.0) == 0.0 and len(raw_data.get("fcf_history", {})) == 0:
        st.error(f"Could not load data for '{ticker_input}'. Please verify the ticker and try again.")
    else:
        # Convert raw large integers to Millions of USD
        shares_m = raw_data["shares_outstanding"] / 1_000_000.0
        cash_m = raw_data["total_cash"] / 1_000_000.0
        debt_m = raw_data["total_debt"] / 1_000_000.0
        current_price = raw_data["current_price"]
        beta = raw_data["beta"]
        
        # Calculate historical FCF in Millions
        fcf_hist_m = {}
        for date_str, val in raw_data["fcf_history"].items():
            fcf_hist_m[date_str] = val / 1_000_000.0
            
        # Get starting FCF default (most recent historical, or fallback)
        default_fcf_base_m = list(fcf_hist_m.values())[-1] if fcf_hist_m else 1000.0
        
        # Get decay start year from session state or default to determine consensus growth
        decay_pattern = st.session_state.get("decay_pattern_selectbox", "Continuous (Decay from Year 2)")
        decay_x_increment = st.session_state.get("decay_x_increment", 2.0)
        current_x_val = decay_x_increment / 100.0 if "each year to" in decay_pattern else 0.0

        # Fetch the current slider values or defaults to calculate consensus growth dynamically
        current_discount = st.session_state.get("discount_rate_slider", 8.0) / 100.0
        current_terminal = st.session_state.get("terminal_growth_slider", 3.0) / 100.0

        # Calculate implied consensus growth rate from Wall Street Target Mean Price
        target_mean_val = raw_data.get("target_mean")
        if target_mean_val and target_mean_val > 0 and default_fcf_base_m > 0:
            consensus_growth = solve_implied_growth(
                fcf_base_m=default_fcf_base_m,
                current_price=target_mean_val,
                shares_m=shares_m,
                cash_m=cash_m,
                debt_m=debt_m,
                terminal_growth=current_terminal,
                discount_rate=current_discount,
                decay_pattern=decay_pattern,
                x_val=current_x_val
            )
            if consensus_growth is None or consensus_growth <= -0.90 or consensus_growth >= 3.0:
                consensus_growth = 0.10
        else:
            consensus_growth = 0.10
            
        # Check if discount rate, terminal growth, decay pattern, or increment has changed since the last execution
        discount_changed = False
        terminal_changed = False
        decay_changed = False
        increment_changed = False
        
        if "prev_discount_rate" in st.session_state and st.session_state.prev_discount_rate != current_discount:
            discount_changed = True
        if "prev_terminal_growth" in st.session_state and st.session_state.prev_terminal_growth != current_terminal:
            terminal_changed = True
        if "prev_decay_pattern" in st.session_state and st.session_state.prev_decay_pattern != decay_pattern:
            decay_changed = True
        if "prev_decay_x_increment" in st.session_state and st.session_state.prev_decay_x_increment != decay_x_increment:
            increment_changed = True
            
        st.session_state.prev_discount_rate = current_discount
        st.session_state.prev_terminal_growth = current_terminal
        st.session_state.prev_decay_pattern = decay_pattern
        st.session_state.prev_decay_x_increment = decay_x_increment
        
        if discount_changed or terminal_changed or decay_changed or increment_changed:
            st.session_state.base_growth_slider = float(round(consensus_growth * 100.0, 1))
            st.session_state.spread_slider = 5.0
            st.session_state.con_growth_val = float(round(consensus_growth * 100.0 - 5.0, 1))
            st.session_state.agg_growth_val = float(round(consensus_growth * 100.0 + 5.0, 1))

        # State tracking: Force reset starting session state keys when ticker changes
        if "last_ticker_symbol" not in st.session_state or st.session_state.last_ticker_symbol != ticker_input:
            st.session_state.last_ticker_symbol = ticker_input
            
            # Explicitly pre-populate clean defaults for the newly selected ticker
            st.session_state.discount_rate_slider = 8.0
            st.session_state.terminal_growth_slider = 3.0
            st.session_state.decay_pattern_selectbox = "Continuous (Decay from Year 2)"
            st.session_state.decay_x_increment = 2.0
            st.session_state.base_growth_slider = float(round(consensus_growth * 100.0, 1))
            st.session_state.spread_slider = 5.0
            st.session_state.con_growth_val = float(round(consensus_growth * 100.0 - 5.0, 1))
            st.session_state.agg_growth_val = float(round(consensus_growth * 100.0 + 5.0, 1))
            
            st.session_state.prev_discount_rate = 0.08
            st.session_state.prev_terminal_growth = 0.03
            st.session_state.prev_decay_pattern = "Continuous (Decay from Year 2)"
            st.session_state.prev_decay_x_increment = 2.0
            
            st.rerun()
        
        # --- UI LAYOUT ---
        col_inputs, col_results = st.columns([1, 2], gap="large")
        
        # -------------------------------------------------------------
        # LEFT COLUMN: VALUATION CONTROLS
        # -------------------------------------------------------------
        with col_inputs:
            st.subheader("🛠️ Valuation Inputs")
            
            # Expander 1: Core Financial Overrides
            with st.expander("💼 Financial Parameters (Millions USD)", expanded=False):
                user_fcf_base_m = st.number_input(
                    "Starting Free Cash Flow (FCF_0)",
                    value=float(default_fcf_base_m),
                    format="%.2f",
                    help="The base cash flow from which projections start. Pre-populated with the latest annual Free Cash Flow."
                )
                if user_fcf_base_m <= 0:
                    st.warning("⚠️ Starting FCF is negative or zero. DCF modeling is highly sensitive to negative starting values. Consider using a positive normalized or average FCF instead.")
                    
                user_shares_m = st.number_input(
                    "Shares Outstanding (Millions)",
                    value=float(shares_m),
                    min_value=0.1,
                    format="%.2f",
                    help="Total outstanding common shares."
                )
                user_cash_m = st.number_input(
                    "Cash & Short Term Investments (Millions)",
                    value=float(cash_m),
                    format="%.2f",
                    help="Total cash on balance sheet to add to Enterprise Value."
                )
                user_debt_m = st.number_input(
                    "Total Debt (Millions)",
                    value=float(debt_m),
                    format="%.2f",
                    help="Total short-term and long-term debt to subtract from Enterprise Value."
                )
                
            st.markdown("**Core Rates (Applies to Base Scenario):**")
            
            user_discount_percent = st.slider(
                "Discount Rate (%)",
                min_value=4.0,
                max_value=20.0,
                value=float(st.session_state.get("discount_rate_slider", 8.0)),
                step=0.1,
                key="discount_rate_slider",
                help="The rate used to discount future cash flows. Higher discount rate lowers valuation."
            )
            user_discount_rate = user_discount_percent / 100.0
            
            user_terminal_growth_percent = st.slider(
                "Terminal Growth Rate (%)",
                min_value=0.5,
                max_value=5.0,
                value=float(st.session_state.get("terminal_growth_slider", 3.0)),
                step=0.1,
                key="terminal_growth_slider",
                help="The rate at which the company is assumed to grow forever after Year 10. Typically matches long-term inflation/GDP growth."
            )
            user_terminal_growth = user_terminal_growth_percent / 100.0

            if user_discount_rate <= user_terminal_growth:
                st.error("❌ Discount Rate must be strictly greater than Terminal Growth Rate to maintain mathematical sanity.")
                
            # Expander 3: Scenario Growth Setup
            with st.expander("🎭 Scenario Growth Presets", expanded=True):
                st.caption(f"Wall Street Consensus Growth Estimate: **{consensus_growth * 100:.1f}%**")
                
                # Base Growth input
                base_growth_percent = st.slider(
                    "Initial FCF Growth Rate (%)",
                    min_value=-30.0,
                    max_value=120.0, # Expanded range to accommodate hyper-growth expectations
                    value=float(st.session_state.get("base_growth_slider", float(round(consensus_growth * 100.0, 1)))),
                    step=0.5,
                    key="base_growth_slider",
                    on_change=on_base_growth_change,
                    help="Starting growth rate for Year 1. Future years decay continuously towards your perpetual Terminal Growth Rate."
                )
                base_growth_rate = base_growth_percent / 100.0

                # Spread Slider (+-% from base case)
                spread_val = st.slider(
                    "Scenario Growth Spread (+/- % from Base Case)",
                    min_value=0.5,
                    max_value=25.0,
                    value=float(st.session_state.get("spread_slider", 5.0)),
                    step=0.5,
                    key="spread_slider",
                    on_change=on_spread_change,
                    help="Sets the percentage point offset for Conservative (Base minus Spread) and Aggressive (Base plus Spread) scenarios."
                )

                # Control for FCF Growth Rate decay start year or keeping it stable
                decay_option = st.selectbox(
                    "Growth Rate Decay Pattern",
                    options=[
                        "Continuous (Decay from Year 2)",
                        "Keep Stable (Entire 10 Years)",
                        "Delayed (Decay starts in Year 6)",
                        "Add X% each year to the Initial FCF Growth Rate",
                        "Remove X% each year to the Initial FCF Growth Rate"
                    ],
                    key="decay_pattern_selectbox",
                    help="Determine when the initial growth rate starts decaying linearly toward the Perpetual Terminal Growth Rate. Or choose to add/remove a fixed percentage of growth each year starting in Year 2."
                )

                # Show 2 digit float input box only if required by chosen pattern
                decay_x_val = 0.0
                if "each year to" in decay_option:
                    decay_x_increment = st.number_input(
                        "Yearly Adjust Amount (X%)",
                        min_value=0.0,
                        max_value=50.0,
                        value=float(st.session_state.get("decay_x_increment", 2.0)),
                        step=0.01,
                        format="%.2f",
                        key="decay_x_increment",
                        help="Enter the percentage point change to add or remove sequentially starting in Year 2."
                    )
                    decay_x_val = decay_x_increment / 100.0
                else:
                    decay_x_val = 0.0
                
                # Derive final growth rates
                con_growth = (base_growth_percent - spread_val) / 100.0
                agg_growth = (base_growth_percent + spread_val) / 100.0

        # -------------------------------------------------------------
        # RIGHT COLUMN: RESULTS & CHARTS
        # -------------------------------------------------------------
        with col_results:
            st.subheader(f"📊 {raw_data['name']} ({ticker_input}) Valuation")
            
            # Metric Card Header row
            raw_rec = raw_data["recommendation"]
            clean_rec = str(raw_rec).replace("_", " ").title() if raw_rec else "N/A"
            rec_color = "#22c55e" if "buy" in clean_rec.lower() else ("#ef4444" if "sell" in clean_rec.lower() else "#eab308")
            
            summary_cols = st.columns(4)
            with summary_cols[0]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">${current_price:,.2f}</div>
                    <div class="metric-label">Current Price</div>
                </div>
                """, unsafe_allow_html=True)
            with summary_cols[1]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: {rec_color};">{clean_rec}</div>
                    <div class="metric-label">Analyst Recommendation</div>
                </div>
                """, unsafe_allow_html=True)
            with summary_cols[2]:
                ws_mean_display = f"${raw_data['target_mean']:.2f}" if raw_data.get("target_mean") else "N/A"
                analyst_count_display = f"({raw_data['analyst_count']} analysts)" if raw_data.get("analyst_count") else "(0 analysts)"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{ws_mean_display}</div>
                    <div class="metric-label">Wall Street Target Mean<br><span style="font-size: 0.75rem; color: #64748b;">{analyst_count_display}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with summary_cols[3]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{beta:,.2f}</div>
                    <div class="metric-label">Beta Coefficient</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- CALCULATE SCENARIOS ---
            ws_target_price = raw_data.get("target_mean") if raw_data.get("target_mean") and raw_data.get("target_mean") > 0 else current_price
            ws_growth = solve_implied_growth(
                fcf_base_m=user_fcf_base_m,
                current_price=ws_target_price,
                shares_m=user_shares_m,
                cash_m=user_cash_m,
                debt_m=user_debt_m,
                terminal_growth=user_terminal_growth,
                discount_rate=user_discount_rate,
                decay_pattern=decay_option,
                x_val=decay_x_val
            )
            if ws_growth is None:
                ws_growth = consensus_growth

            con_res = run_dcf_model(user_fcf_base_m, user_shares_m, user_cash_m, user_debt_m, con_growth, user_terminal_growth, user_discount_rate, decay_pattern=decay_option, x_val=decay_x_val)
            base_res = run_dcf_model(user_fcf_base_m, user_shares_m, user_cash_m, user_debt_m, base_growth_rate, user_terminal_growth, user_discount_rate, decay_pattern=decay_option, x_val=decay_x_val)
            ws_res = run_dcf_model(user_fcf_base_m, user_shares_m, user_cash_m, user_debt_m, ws_growth, user_terminal_growth, user_discount_rate, decay_pattern=decay_option, x_val=decay_x_val)
            agg_res = run_dcf_model(user_fcf_base_m, user_shares_m, user_cash_m, user_debt_m, agg_growth, user_terminal_growth, user_discount_rate, decay_pattern=decay_option, x_val=decay_x_val)
            
            # Calculate Margin of Safety
            def get_mos(intrinsic, current):
                if current <= 0: return 0.0
                return (intrinsic - current) / current * 100.0
                
            con_mos = get_mos(con_res["intrinsic_value"], current_price)
            base_mos = get_mos(base_res["intrinsic_value"], current_price)
            ws_mos = get_mos(ws_res["intrinsic_value"], current_price)
            agg_mos = get_mos(agg_res["intrinsic_value"], current_price)
            
            # Scenario Metrics Grid
            result_cols = st.columns(4)
            with result_cols[0]:
                mos_color = "green" if con_mos >= 0 else "red"
                st.markdown(f"""
                <div class="metric-card" style="border-top: 4px solid #ef4444;">
                    <div class="metric-label">CONSERVATIVE INTRINSIC VALUE</div>
                    <div class="metric-value" style="color: #ef4444;">${con_res["intrinsic_value"]:,.2f}</div>
                    <div class="metric-label" style="color: {mos_color};">Margin of Safety: <b>{con_mos:+.1f}%</b></div>
                </div>
                """, unsafe_allow_html=True)
            with result_cols[1]:
                mos_color = "green" if base_mos >= 0 else "red"
                st.markdown(f"""
                <div class="metric-card" style="border-top: 4px solid #3b82f6;">
                    <div class="metric-label">BASE CASE INTRINSIC VALUE</div>
                    <div class="metric-value" style="color: #3b82f6;">${base_res["intrinsic_value"]:,.2f}</div>
                    <div class="metric-label" style="color: {mos_color};">Margin of Safety: <b>{base_mos:+.1f}%</b></div>
                </div>
                """, unsafe_allow_html=True)
            with result_cols[2]:
                mos_color = "green" if agg_mos >= 0 else "red"
                st.markdown(f"""
                <div class="metric-card" style="border-top: 4px solid #22c55e;">
                    <div class="metric-label">AGGRESSIVE INTRINSIC VALUE</div>
                    <div class="metric-value" style="color: #22c55e;">${agg_res["intrinsic_value"]:,.2f}</div>
                    <div class="metric-label" style="color: {mos_color};">Margin of Safety: <b>{agg_mos:+.1f}%</b></div>
                </div>
                """, unsafe_allow_html=True)
            with result_cols[3]:
                mos_color = "green" if ws_mos >= 0 else "red"
                st.markdown(f"""
                <div class="metric-card" style="border-top: 4px solid #eab308;">
                    <div class="metric-label">WALL STREET INTRINSIC VALUE</div>
                    <div class="metric-value" style="color: #eab308;">${ws_res["intrinsic_value"]:,.2f}</div>
                    <div class="metric-label" style="color: {mos_color};">Margin of Safety: <b>{ws_mos:+.1f}%</b></div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- DETAIL TABLE ---
            st.markdown("### 📋 Scenario Comparison Details")
            comparison_df = pd.DataFrame({
                "Parameter": [
                    "Starting FCF",
                    "Initial Growth (Y1)",
                    "Terminal Growth Rate",
                    "Discount Rate",
                    "Enterprise Value",
                    "Cash (+)",
                    "Debt (-)",
                    "Equity Value",
                    "Shares Outstanding",
                    "Intrinsic Value",
                    "Margin of Safety",
                    "Valuation Assessment"
                ],
                "Conservative": [
                    f"${user_fcf_base_m:,.2f} M",
                    f"{con_growth*100:.1f}%",
                    f"{user_terminal_growth*100:.1f}%",
                    f"{user_discount_rate*100:.1f}%",
                    f"${con_res['enterprise_value']:,.1f} M",
                    f"${user_cash_m:,.1f} M",
                    f"${user_debt_m:,.1f} M",
                    f"${con_res['equity_value']:,.1f} M",
                    f"{user_shares_m:,.1f} M",
                    f"${con_res['intrinsic_value']:,.2f}",
                    f"{con_mos:+.1f}%",
                    "Undervalued" if con_mos >= 15 else ("Fairly Valued" if abs(con_mos) < 15 else "Overvalued")
                ],
                "Base Case": [
                    f"${user_fcf_base_m:,.2f} M",
                    f"{base_growth_rate*100:.1f}%",
                    f"{user_terminal_growth*100:.1f}%",
                    f"{user_discount_rate*100:.1f}%",
                    f"${base_res['enterprise_value']:,.1f} M",
                    f"${user_cash_m:,.1f} M",
                    f"${user_debt_m:,.1f} M",
                    f"${base_res['equity_value']:,.1f} M",
                    f"{user_shares_m:,.1f} M",
                    f"${base_res['intrinsic_value']:,.2f}",
                    f"{base_mos:+.1f}%",
                    "Undervalued" if base_mos >= 15 else ("Fairly Valued" if abs(base_mos) < 15 else "Overvalued")
                ],
                "Aggressive": [
                    f"${user_fcf_base_m:,.2f} M",
                    f"{agg_growth*100:.1f}%",
                    f"{user_terminal_growth*100:.1f}%",
                    f"{user_discount_rate*100:.1f}%",
                    f"${agg_res['enterprise_value']:,.1f} M",
                    f"${user_cash_m:,.1f} M",
                    f"${user_debt_m:,.1f} M",
                    f"${agg_res['equity_value']:,.1f} M",
                    f"{user_shares_m:,.1f} M",
                    f"${agg_res['intrinsic_value']:,.2f}",
                    f"{agg_mos:+.1f}%",
                    "Undervalued" if agg_mos >= 15 else ("Fairly Valued" if abs(agg_mos) < 15 else "Overvalued")
                ],
                "Wall Street": [
                    f"${user_fcf_base_m:,.2f} M",
                    f"{ws_growth*100:.1f}%" if ws_growth is not None else "N/A",
                    f"{user_terminal_growth*100:.1f}%",
                    f"{user_discount_rate*100:.1f}%",
                    f"${ws_res['enterprise_value']:,.1f} M",
                    f"${user_cash_m:,.1f} M",
                    f"${user_debt_m:,.1f} M",
                    f"${ws_res['equity_value']:,.1f} M",
                    f"{user_shares_m:,.1f} M",
                    f"${ws_res['intrinsic_value']:,.2f}",
                    f"{ws_mos:+.1f}%",
                    "Undervalued" if ws_mos >= 15 else ("Fairly Valued" if abs(ws_mos) < 15 else "Overvalued")
                ]
            })
            st.dataframe(comparison_df.set_index("Parameter"), use_container_width=True, height=460)
            
        # --- END OF TWO-COLUMN LAYOUT ---
        # Close the column context. Sub-components below this will automatically render taking the ENTIRE page width.
        st.markdown("<br><hr>", unsafe_allow_html=True)
        
        # --- SECTION 1: PRICE TARGET VS INTRINSIC VALUES BAR CHART (FULL WIDTH) ---
        st.markdown("### 🎯 Value Comparison Chart")
        
        labels = ["Conservative Value", "Base Case Value", "Aggressive Value", "Wall Street Target"]
        values = [con_res["intrinsic_value"], base_res["intrinsic_value"], agg_res["intrinsic_value"], ws_res["intrinsic_value"]]
        colors = ["#ef4444", "#3b82f6", "#22c55e", "#eab308"]
        
        fig_prices = go.Figure()
        
        # Add intrinsic value bars
        fig_prices.add_trace(go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            width=0.35,
            text=[f"${v:,.2f}" for v in values],
            textposition='auto',
            name="Intrinsic Value"
        ))
        
        # Current price horizontal reference line
        fig_prices.add_shape(type="line",
            x0=-0.5, y0=current_price, x1=3.5, y1=current_price,
            line=dict(color="#ffffff", width=2, dash="dash"),
            name="Current Price"
        )
        fig_prices.add_annotation(
            x=0.5, y=current_price,
            text=f"<b>Current Price: ${current_price:,.2f}</b>",
            showarrow=False,
            yshift=12,
            font=dict(color="#ffffff", size=11)
        )
        
        # Wall Street Mean Target horizontal line
        if raw_data["target_mean"]:
            ws_mean = raw_data["target_mean"]
            fig_prices.add_shape(type="line",
                x0=-0.5, y0=ws_mean, x1=3.5, y1=ws_mean,
                line=dict(color="#eab308", width=2, dash="dot"),
                name="Wall Street Target Mean"
            )
            fig_prices.add_annotation(
                x=2.5, y=ws_mean,
                text=f"<b>Wall Street Target Mean: ${ws_mean:,.2f}</b>",
                showarrow=False,
                yshift=12,
                font=dict(color="#eab308", size=11)
            )
            
        fig_prices.update_layout(
            margin=dict(l=20, r=20, t=10, b=10),
            height=320,
            template="plotly_dark",
            yaxis=dict(title="Stock Price ($)", gridcolor="#334155"),
            xaxis=dict(gridcolor="#334155")
        )
        st.plotly_chart(fig_prices, use_container_width=True)
        
        # --- SECTION 2: ANNUAL PROJECTIONS FLOW TABULAR VIEW (FULL WIDTH) ---
        st.markdown("### 🗓️ Annual FCF Projection & Present Value (PV) Flow")
        
        # Construct a row index for each of the 10 years, terminal value, and total sum
        years_list = [f"Year {t}" for t in range(1, 11)] + ["Terminal Value", "Total"]
        
        flow_df = pd.DataFrame({
            "Year": years_list,
            # Growth Rates
            "Con Growth Rate": [f"{g * 100:.1f}%" for g in con_res["growths"]] + ["", ""],
            "Base Growth Rate": [f"{g * 100:.1f}%" for g in base_res["growths"]] + ["", ""],
            "Agg Growth Rate": [f"{g * 100:.1f}%" for g in agg_res["growths"]] + ["", ""],
            "WS Growth Rate": [f"{g * 100:.1f}%" for g in ws_res["growths"]] + ["", ""],
            # FCF Projections
            "Con Projected FCF": [f"${val:,.2f} M" for val in con_res["fcf_projections"]] + [
                f"${con_res['terminal_value']:,.2f} M",
                f"${sum(con_res['fcf_projections']) + con_res['terminal_value']:,.2f} M"
            ],
            "Base Projected FCF": [f"${val:,.2f} M" for val in base_res["fcf_projections"]] + [
                f"${base_res['terminal_value']:,.2f} M",
                f"${sum(base_res['fcf_projections']) + base_res['terminal_value']:,.2f} M"
            ],
            "Agg Projected FCF": [f"${val:,.2f} M" for val in agg_res["fcf_projections"]] + [
                f"${agg_res['terminal_value']:,.2f} M",
                f"${sum(agg_res['fcf_projections']) + agg_res['terminal_value']:,.2f} M"
            ],
            "WS Projected FCF": [f"${val:,.2f} M" for val in ws_res["fcf_projections"]] + [
                f"${ws_res['terminal_value']:,.2f} M",
                f"${sum(ws_res['fcf_projections']) + ws_res['terminal_value']:,.2f} M"
            ],
            # PV of FCFs
            "Con PV of FCF": [f"${val:,.2f} M" for val in con_res["pv_fcfs"]] + [
                f"${con_res['pv_terminal_value']:,.2f} M",
                f"${con_res['enterprise_value']:,.2f} M"
            ],
            "Base PV of FCF": [f"${val:,.2f} M" for val in base_res["pv_fcfs"]] + [
                f"${base_res['pv_terminal_value']:,.2f} M",
                f"${base_res['enterprise_value']:,.2f} M"
            ],
            "Agg PV of FCF": [f"${val:,.2f} M" for val in agg_res["pv_fcfs"]] + [
                f"${agg_res['pv_terminal_value']:,.2f} M",
                f"${agg_res['enterprise_value']:,.2f} M"
            ],
            "WS PV of FCF": [f"${val:,.2f} M" for val in ws_res["pv_fcfs"]] + [
                f"${ws_res['pv_terminal_value']:,.2f} M",
                f"${ws_res['enterprise_value']:,.2f} M"
            ]
        })

        def style_rows(row):
            if row["Year"] == "Terminal Value":
                return ["background-color: #1e293b; font-weight: bold; color: #3b82f6;"] * len(row)
            elif row["Year"] == "Total":
                return ["background-color: #0f172a; font-weight: bold; color: #10b981;"] * len(row)
            return [""] * len(row)

        styled_flow_df = flow_df.style.apply(style_rows, axis=1)

        # Map column widths to small sizes so that the entire table fits full width without horizontal scrolling
        col_config = {
            "Year": st.column_config.TextColumn("Year", width=110),
            "Con Growth Rate": st.column_config.TextColumn("Con Growth", width=85),
            "Base Growth Rate": st.column_config.TextColumn("Base Growth", width=85),
            "Agg Growth Rate": st.column_config.TextColumn("Agg Growth", width=85),
            "WS Growth Rate": st.column_config.TextColumn("WS Growth", width=85),
            "Con Projected FCF": st.column_config.TextColumn("Con FCF", width=105),
            "Base Projected FCF": st.column_config.TextColumn("Base FCF", width=105),
            "Agg Projected FCF": st.column_config.TextColumn("Agg FCF", width=105),
            "WS Projected FCF": st.column_config.TextColumn("WS FCF", width=105),
            "Con PV of FCF": st.column_config.TextColumn("Con PV", width=105),
            "Base PV of FCF": st.column_config.TextColumn("Base PV", width=105),
            "Agg PV of FCF": st.column_config.TextColumn("Agg PV", width=105),
            "WS PV of FCF": st.column_config.TextColumn("WS PV", width=105)
        }

        st.dataframe(
            styled_flow_df,
            use_container_width=True,
            hide_index=True,
            height=490,  # High enough to accommodate 12 rows + headers perfectly without vertical scrollbar
            column_config=col_config
        )


