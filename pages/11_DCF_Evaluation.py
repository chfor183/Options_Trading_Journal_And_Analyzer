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
    growth_rate: float,      # Stage 1 Growth Rate (Years 1-5)
    terminal_growth: float,  # Terminal Growth Rate (perpetual)
    discount_rate: float,    # Discount Rate / WACC
) -> dict:
    # 1. Project Growth Rates for 10 Years
    growths = []
    for t in range(1, 11):
        if t <= 5:
            growths.append(growth_rate)
        else:
            # Stage 2: Linear Taper from growth_rate to terminal_growth
            taper_factor = (t - 5) / 5.0
            g_t = growth_rate - taper_factor * (growth_rate - terminal_growth)
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
) -> float:
    # Solves for growth_rate such that intrinsic_value == current_price
    if fcf_base_m <= 0 or current_price <= 0 or shares_m <= 0:
        return None
        
    low = -0.90
    high = 3.0
    
    # Verify bounds
    val_low = run_dcf_model(fcf_base_m, shares_m, cash_m, debt_m, low, terminal_growth, discount_rate)["intrinsic_value"]
    val_high = run_dcf_model(fcf_base_m, shares_m, cash_m, debt_m, high, terminal_growth, discount_rate)["intrinsic_value"]
    
    if current_price <= val_low:
        return low
    if current_price >= val_high:
        return high
        
    for _ in range(100):
        mid = (low + high) / 2.0
        val_mid = run_dcf_model(fcf_base_m, shares_m, cash_m, debt_m, mid, terminal_growth, discount_rate)["intrinsic_value"]
        
        if abs(val_mid - current_price) < 0.01:
            return mid
            
        if val_mid < current_price:
            low = mid
        else:
            high = mid
            
    return (low + high) / 2.0


# -------------------------------------------------------------
# USER INTERFACE SETUP
# -------------------------------------------------------------
st.title("💵 Discounted Cash Flow (DCF) Evaluation")
st.markdown("Assess a stock's intrinsic value using a **10-Year 2-Stage Free Cash Flow** model and reverse-engineer market expectations.")

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
        
        # Suggested growth rates based on analyst consensus (default to 10% if missing)
        consensus_growth = raw_data["earnings_growth"] or raw_data["revenue_growth"] or 0.10
        
        # --- UI LAYOUT ---
        col_inputs, col_results = st.columns([1, 2], gap="large")
        
        # -------------------------------------------------------------
        # LEFT COLUMN: VALUATION CONTROLS
        # -------------------------------------------------------------
        with col_inputs:
            st.subheader("🛠️ Valuation Inputs")
            
            # Expander 1: Core Financial Overrides
            with st.expander("💼 Financial Parameters (Millions USD)", expanded=True):
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
                
            # Expander 2: WACC & CAPM Estimator
            with st.expander("🧬 Discount Rate (WACC) Calculator", expanded=False):
                st.markdown("**Capital Asset Pricing Model (CAPM) Inputs:**")
                risk_free_rate = st.slider("Risk-Free Rate (%)", min_value=1.0, max_value=10.0, value=4.20, step=0.05, help="Typically the yield on 10-year US Treasury bonds.") / 100.0
                equity_risk_premium = st.slider("Equity Risk Premium (ERP) (%)", min_value=3.0, max_value=8.0, value=5.50, step=0.1, help="Expected market return minus risk-free rate.") / 100.0
                user_beta = st.number_input("Beta (Risk Coefficient)", value=float(beta), min_value=0.1, max_value=5.0, step=0.05, help="Measures historical volatility relative to the index.")
                
                # Cost of Equity
                cost_of_equity = risk_free_rate + (user_beta * equity_risk_premium)
                st.write(f"**Cost of Equity (Re):** {cost_of_equity*100:.2f}%")
                
                st.markdown("---")
                st.markdown("**Cost of Debt Inputs:**")
                cost_of_debt = st.slider("Cost of Debt (%)", min_value=1.0, max_value=15.0, value=5.0, step=0.1) / 100.0
                tax_rate = st.slider("Corporate Tax Rate (%)", min_value=0.0, max_value=40.0, value=21.0, step=1.0) / 100.0
                after_tax_debt_cost = cost_of_debt * (1 - tax_rate)
                st.write(f"**After-Tax Cost of Debt:** {after_tax_debt_cost*100:.2f}%")
                
                st.markdown("---")
                st.markdown("**Capital Weights:**")
                # Equity Market Value = Share Price * Outstanding Shares
                market_equity_m = current_price * user_shares_m
                total_capital_m = market_equity_m + user_debt_m
                
                if total_capital_m > 0:
                    weight_equity = market_equity_m / total_capital_m
                    weight_debt = user_debt_m / total_capital_m
                else:
                    weight_equity = 1.0
                    weight_debt = 0.0
                    
                st.write(f"**Market Equity Value:** ${market_equity_m:,.2f} M ({weight_equity*100:.1f}%)")
                st.write(f"**Debt Value:** ${user_debt_m:,.2f} M ({weight_debt*100:.1f}%)")
                
                calculated_wacc = (weight_equity * cost_of_equity) + (weight_debt * after_tax_debt_cost)
                st.success(f"**Calculated WACC:** {calculated_wacc*100:.2f}%")
                
                apply_calculated_wacc = st.checkbox("Use Calculated WACC as base Discount Rate", value=True)
                
            # Standing Discount and Terminal Growth Rates
            discount_base = calculated_wacc if apply_calculated_wacc else 0.08
            
            st.markdown("**Core Rates (Applies to Base Scenario):**")
            user_discount_rate = st.slider(
                "Discount Rate / Base WACC (%)",
                min_value=4.0,
                max_value=20.0,
                value=float(round(discount_base * 100.0, 2)),
                step=0.1,
                help="The rate used to discount future cash flows. Higher discount rate lowers valuation."
            ) / 100.0
            
            user_terminal_growth = st.slider(
                "Terminal Growth Rate (%)",
                min_value=0.5,
                max_value=5.0,
                value=2.50,
                step=0.1,
                help="The rate at which the company is assumed to grow forever after Year 10. Typically matches long-term inflation/GDP growth."
            ) / 100.0
            
            if user_discount_rate <= user_terminal_growth:
                st.error("❌ Discount Rate must be strictly greater than Terminal Growth Rate to maintain mathematical sanity.")
                
            # Expander 3: Scenario Growth Setup
            with st.expander("🎭 Scenario Growth Presets", expanded=True):
                st.caption(f"Wall Street Consensus Growth Estimate: **{consensus_growth * 100:.1f}%**")
                
                # Base Growth input
                base_growth_rate = st.slider(
                    "Base FCF Growth Rate (Years 1-5) (%)",
                    min_value=-30.0,
                    max_value=60.0,
                    value=float(round(consensus_growth * 100.0, 1)),
                    step=0.5,
                    help="Growth rate for the first 5 years under standard expectations."
                ) / 100.0
                
                # Conservative Inputs
                st.markdown("**Conservative Preset Overrides:**")
                con_col1, con_col2 = st.columns(2)
                with con_col1:
                    # Narrowed: 80% of Base growth (was 60%)
                    con_growth = st.number_input("Growth Rate (%)", value=float(round(base_growth_rate * 0.8 * 100, 1)), format="%.1f", key="con_growth") / 100.0
                with con_col2:
                    # Narrowed: +0.5% on discount rate (was +1.5%)
                    con_discount = st.number_input("Discount Rate (%)", value=float(round((user_discount_rate + 0.005) * 100, 1)), format="%.1f", key="con_discount") / 100.0
                    
                # Aggressive Inputs
                st.markdown("**Aggressive Preset Overrides:**")
                agg_col1, agg_col2 = st.columns(2)
                with agg_col1:
                    # Narrowed: 1.15x of Base growth (was 1.3x)
                    agg_growth = st.number_input("Growth Rate (%)", value=float(round(base_growth_rate * 1.15 * 100, 1)), format="%.1f", key="agg_growth") / 100.0
                with agg_col2:
                    # Narrowed: -0.5% on discount rate (was -1.0%)
                    agg_discount = st.number_input("Discount Rate (%)", value=float(max(4.0, round((user_discount_rate - 0.005) * 100, 1))), format="%.1f", key="agg_discount") / 100.0

        # -------------------------------------------------------------
        # RIGHT COLUMN: RESULTS & CHARTS
        # -------------------------------------------------------------
        with col_results:
            st.subheader(f"📊 {raw_data['name']} ({ticker_input}) Valuation")
            
            # Metric Card Header row
            rec_color = "#22c55e" if "buy" in raw_data["recommendation"].lower() else ("#ef4444" if "sell" in raw_data["recommendation"].lower() else "#eab308")
            
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
                    <div class="metric-value" style="color: {rec_color};">{raw_data["recommendation"]}</div>
                    <div class="metric-label">Analyst Recommendation</div>
                </div>
                """, unsafe_allow_html=True)
            with summary_cols[2]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">${raw_data["target_mean"] or "N/A"}</div>
                    <div class="metric-label">Wall Street Target Mean ({raw_data["analyst_count"] or 0} analysts)</div>
                </div>
                """, unsafe_allow_html=True)
            with summary_cols[3]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{user_beta:,.2f}</div>
                    <div class="metric-label">Beta Coefficient</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- CALCULATE SCENARIOS ---
            con_res = run_dcf_model(user_fcf_base_m, user_shares_m, user_cash_m, user_debt_m, con_growth, user_terminal_growth, con_discount)
            base_res = run_dcf_model(user_fcf_base_m, user_shares_m, user_cash_m, user_debt_m, base_growth_rate, user_terminal_growth, user_discount_rate)
            agg_res = run_dcf_model(user_fcf_base_m, user_shares_m, user_cash_m, user_debt_m, agg_growth, user_terminal_growth, agg_discount)
            
            # Calculate Margin of Safety
            def get_mos(intrinsic, current):
                if current <= 0: return 0.0
                return (intrinsic - current) / current * 100.0
                
            con_mos = get_mos(con_res["intrinsic_value"], current_price)
            base_mos = get_mos(base_res["intrinsic_value"], current_price)
            agg_mos = get_mos(agg_res["intrinsic_value"], current_price)
            
            # Scenario Metrics Grid
            result_cols = st.columns(3)
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
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- IMPLIED GROWTH (REVERSE DCF) ---
            implied_growth_raw = solve_implied_growth(
                fcf_base_m=user_fcf_base_m,
                current_price=current_price,
                shares_m=user_shares_m,
                cash_m=user_cash_m,
                debt_m=user_debt_m,
                terminal_growth=user_terminal_growth,
                discount_rate=user_discount_rate
            )
            
            if implied_growth_raw is not None:
                st.info(
                    f"🕵️ **Reverse DCF Analysis:** To justify the current market price of **${current_price:,.2f}**, the market is pricing in an "
                    f"implied Free Cash Flow annual growth rate of **{implied_growth_raw * 100:.2f}%** for the next 5 years (assuming a "
                    f"{user_discount_rate*100:.1f}% discount rate and {user_terminal_growth*100:.1f}% terminal growth). "
                    f"\n\n*If you expect {raw_data['name']} to grow faster than **{implied_growth_raw * 100:.2f}%** per year, the stock is historically undervalued.*"
                )
            else:
                st.info("🕵️ **Reverse DCF Analysis:** Implied growth calculation requires a positive starting Free Cash Flow.")
                
            # --- DETAIL TABLE ---
            st.markdown("### 📋 Scenario Comparison Details")
            comparison_df = pd.DataFrame({
                "Parameter": [
                    "Starting FCF",
                    "Growth Rate (Y1-5)",
                    "Terminal Growth Rate",
                    "Discount Rate",
                    "Enterprise Value",
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
                    f"{con_discount*100:.1f}%",
                    f"${con_res['enterprise_value']:,.1f} M",
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
                    f"{agg_discount*100:.1f}%",
                    f"${agg_res['enterprise_value']:,.1f} M",
                    f"${agg_res['equity_value']:,.1f} M",
                    f"{user_shares_m:,.1f} M",
                    f"${agg_res['intrinsic_value']:,.2f}",
                    f"{agg_mos:+.1f}%",
                    "Undervalued" if agg_mos >= 15 else ("Fairly Valued" if abs(agg_mos) < 15 else "Overvalued")
                ]
            })
            st.dataframe(comparison_df.set_index("Parameter"), use_container_width=True)
            
            # --- CHART 1: PLOTLY FREE CASH FLOW PROJECTIONS ---
            st.markdown("### 📈 10-Year Free Cash Flow Projections")
            
            # Build FCF timeline (Historical + Projected)
            hist_dates = list(fcf_hist_m.keys())
            hist_vals = list(fcf_hist_m.values())
            
            # Extract last historical year as integer
            if hist_dates:
                try:
                    last_year = int(hist_dates[-1].split("-")[0])
                except:
                    last_year = 2025
            else:
                last_year = 2025
                
            # Create friendly string-based categorical x-axis labels
            hist_x = [f"{d.split('-')[0]} (Hist)" for d in hist_dates]
            proj_x = [f"{last_year + t} (Y{t})" for t in range(1, 11)]
            
            # Fallback if no history
            if not hist_x:
                hist_x = ["Base (Est)"]
                hist_vals = [user_fcf_base_m]
                
            fig_fcf = go.Figure()
            
            # Plot historical FCF as a solid bar series
            fig_fcf.add_trace(go.Bar(
                x=hist_x,
                y=hist_vals,
                name="Historical FCF",
                marker_color="#475569",
                opacity=0.85
            ))
            
            # Historical last year link line
            last_hist_label = hist_x[-1]
            last_hist_val = hist_vals[-1]
            
            # Combine link point + projections
            x_line = [last_hist_label] + proj_x
            y_con = [last_hist_val] + con_res["fcf_projections"]
            y_base = [last_hist_val] + base_res["fcf_projections"]
            y_agg = [last_hist_val] + agg_res["fcf_projections"]
            
            fig_fcf.add_trace(go.Scatter(
                x=x_line, y=y_con, name="Conservative Projection",
                line=dict(color="#ef4444", width=3, dash="dash")
            ))
            
            fig_fcf.add_trace(go.Scatter(
                x=x_line, y=y_base, name="Base Case Projection",
                line=dict(color="#3b82f6", width=4)
            ))
            
            fig_fcf.add_trace(go.Scatter(
                x=x_line, y=y_agg, name="Aggressive Projection",
                line=dict(color="#22c55e", width=3, dash="dot")
            ))
            
            fig_fcf.update_layout(
                margin=dict(l=20, r=20, t=10, b=10),
                height=350,
                template="plotly_dark",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(gridcolor="#334155"),
                yaxis=dict(title="FCF (Millions USD)", gridcolor="#334155")
            )
            st.plotly_chart(fig_fcf, use_container_width=True)
            
            # --- CHART 2: PRICE TARGET VS INTRINSIC VALUES BAR CHART ---
            st.markdown("### 🎯 Value Comparison Chart")
            
            labels = ["Conservative Value", "Base Case Value", "Aggressive Value"]
            values = [con_res["intrinsic_value"], base_res["intrinsic_value"], agg_res["intrinsic_value"]]
            colors = ["#ef4444", "#3b82f6", "#22c55e"]
            
            fig_prices = go.Figure()
            
            # Add intrinsic value bars
            fig_prices.add_trace(go.Bar(
                x=labels,
                y=values,
                marker_color=colors,
                width=0.4,
                text=[f"${v:,.2f}" for v in values],
                textposition='auto',
                name="Intrinsic Value"
            ))
            
            # Current price horizontal reference line
            fig_prices.add_shape(type="line",
                x0=-0.5, y0=current_price, x1=2.5, y1=current_price,
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
                    x0=-0.5, y0=ws_mean, x1=2.5, y1=ws_mean,
                    line=dict(color="#eab308", width=2, dash="dot"),
                    name="Wall Street Target Mean"
                )
                fig_prices.add_annotation(
                    x=1.8, y=ws_mean,
                    text=f"<b>Wall Street Target Mean: ${ws_mean:,.2f}</b>",
                    showarrow=False,
                    yshift=12,
                    font=dict(color="#eab308", size=11)
                )
                
            fig_prices.update_layout(
                margin=dict(l=20, r=20, t=10, b=10),
                height=300,
                template="plotly_dark",
                yaxis=dict(title="Stock Price ($)", gridcolor="#334155"),
                xaxis=dict(gridcolor="#334155")
            )
            st.plotly_chart(fig_prices, use_container_width=True)
            
            # --- EDUCATIONAL FOOTNOTE ---
            with st.expander("📚 How to read the Discounted Cash Flow model parameters?", expanded=False):
                st.markdown("""
                * **Starting Free Cash Flow ($FCF_0$)**: This is the cash generated by the business that is free to be distributed to debt and equity holders. It is computed as `Cash Flow from Operations - Capital Expenditures`.
                * **Discount Rate / WACC**: The Weighted Average Cost of Capital reflects the blended cost of debt and equity capital. A higher discount rate represents higher risk or opportunity cost and dramatically lowers present value valuation.
                * **Terminal Growth Rate**: The perpetual growth rate assumed for the business after Year 10. This must strictly be lower than the discount rate and is usually set near the long-term rate of GDP growth or inflation (2.0% - 3.0%).
                * **2-Stage Tapering**: Years 1-5 use your input high-growth Stage 1. Years 6-10 smoothly taper that growth down linearly to your Terminal Growth Rate. This mimics the real-life competitive cycle of maturing companies.
                * **Margin of Safety (MoS)**: The discount of the current stock price relative to its intrinsic value. A value of **+20%** means the stock is trading 20% below our calculated fair value, suggesting a margin of safety for investment.
                """)
