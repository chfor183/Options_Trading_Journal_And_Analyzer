import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Option Strategies", page_icon="📈", layout="wide")
st.title("📈 Option Strategies")

# Define the tabs: Options Theory, Summary, Details, and Barchart Filters
tabs = st.tabs(["📈 Options Theory", "📋 Strategies Summary", "🔍 Strategies Details", "🔎 Barchart Filters"])

with tabs[0]:
    st.subheader("📈 Options Pricing & Theta Decay")
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.markdown("""
        ### ⏳ Intrinsic vs. Extrinsic Value
        Every option premium is made of two components:
        $$\\text{Total Premium} = \\text{Intrinsic Value} + \\text{Extrinsic Value}$$

        - **Intrinsic Value (Real value):** The amount by which an option is in-the-money.
          - For a Call: $\\max(0, S - K)$
          - For a Put: $\\max(0, K - S)$
        - **Extrinsic Value (Time & Volatility value):** The "hope" premium that decays towards zero as expiration approaches. Represented by Theta ($\\theta$).

        #### ⚡ Core Pricing Concepts
        - **Credit (Premium Sellers):** Farm Theta decay. Sell OTM options to capture extrinsic value.
        - **Debit (Premium Buyers):** Gain high-delta leverage. Buy deep ITM options to minimize decay.

        #### 🎯 Option Moneyness Profiles
        <table style="width:100%; border-collapse: collapse; font-size: 0.85rem; line-height: 1.2; margin-top: 4px;">
            <tr style="border-bottom: 1px solid rgba(128,128,128,0.3); font-weight: bold; color: #888;">
                <th style="text-align: left; padding: 3px 5px;">Moneyness</th>
                <th style="text-align: left; padding: 3px 5px;">Delta Range</th>
                <th style="text-align: left; padding: 3px 5px;">Risk Profile</th>
            </tr>
            <tr style="border-bottom: 1px solid rgba(128,128,128,0.15);">
                <td style="padding: 3px 5px;"><b>OTM</b> (Out of The Money)</td>
                <td style="padding: 3px 5px;"><b>10 - 30</b> Delta</td>
                <td style="padding: 3px 5px;">Low risk to <b>SELL</b></td>
            </tr>
            <tr style="border-bottom: 1px solid rgba(128,128,128,0.15);">
                <td style="padding: 3px 5px;"><b>ATM</b> (At The Money)</td>
                <td style="padding: 3px 5px;"><b>40 - 60</b> Delta</td>
                <td style="padding: 3px 5px;">High risk to buy/sell</td>
            </tr>
            <tr>
                <td style="padding: 3px 5px;"><b>ITM</b> (In The Money)</td>
                <td style="padding: 3px 5px;"><b>70 - 90</b> Delta</td>
                <td style="padding: 3px 5px;">Low risk to <b>BUY</b></td>
            </tr>
        </table>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("### 📉 The Theta Decay Curve")
        
        # Curve function: y = 100 * (x / 120) ** 0.42 fits the profile of the graph
        t_days = np.linspace(120, 0, 200)
        ext_val = 100 * (t_days / 120) ** 0.42
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=t_days, 
            y=ext_val, 
            mode='lines', 
            fill='tozeroy',
            fillcolor='rgba(255, 75, 75, 0.08)',
            line=dict(color='#ff4b4b', width=4.5),
            name='Extrinsic Premium'
        ))
        
        fig.update_layout(
            title="Option Extrinsic Value vs. Days to Expiration (DTE)",
            xaxis_title="Time Remaining Until Expiration Date (Days)",
            yaxis_title="Percent of Premium Remaining (%)",
            xaxis=dict(
                autorange="reversed",  # 120 on the left, 0 on the right
                gridcolor='rgba(128,128,128,0.15)',
                tickvals=[120, 90, 60, 30, 0],
                ticktext=["120 Days", "90 Days", "60 Days", "30 Days", "0 Days"]
            ),
            yaxis=dict(
                gridcolor='rgba(128,128,128,0.15)',
                range=[0, 105],
                tickvals=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                ticktext=["0%", "10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%", "100%"]
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            height=380,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        # Gridlines matching the image divisions (120, 90, 60, 30)
        for val in [90, 60, 30]:
            fig.add_vline(x=val, line_dash="solid", line_color="rgba(128,128,128,0.25)", line_width=1)
            
        # Add labels matching the annotations in the picture.
        fig.add_annotation(x=105, y=96, text="120 to 90 Days<br>(Least impact)", showarrow=True, arrowhead=1, arrowcolor="#0066cc", font=dict(size=9))
        fig.add_annotation(x=75, y=86, text="90 to 60 Days<br>(Slightly greater)", showarrow=True, arrowhead=1, arrowcolor="#0066cc", font=dict(size=9))
        fig.add_annotation(x=45, y=73, text="60 to 30 Days<br>(Greater still)", showarrow=True, arrowhead=1, arrowcolor="#0066cc", font=dict(size=9))
        fig.add_annotation(x=15, y=48, text="Under 30 Days<br>(Most rapid)", showarrow=True, arrowhead=1, arrowcolor="#0066cc", font=dict(size=9), ax=30, ay=-50)
        
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Notice how extrinsic value decays exponentially. As an option seller, the sweet spot to capture the premium acceleration is around 30 to 45 DTE.")

with tabs[1]:
    st.subheader("Option Strategies Reference Table")
    st.write("A structured overview of primary credit and debit options strategies, key variables, and execution comments.")
    
    # Custom CSS to enable clean cell wrapping, column sizing, and professional look
    st.markdown("""
    <style>
        .strategies-table {
            width: 100%;
            border-collapse: collapse;
            font-family: inherit;
            margin: 10px 0;
            font-size: 0.95rem;
        }
        .strategies-table th {
            background-color: #2e7d32;
            color: white;
            text-align: left;
            padding: 10px;
            font-weight: bold;
            border: 1px solid #ddd;
        }
        .strategies-table td {
            padding: 10px;
            border: 1px solid #ddd;
            vertical-align: top;
            line-height: 1.4;
        }
        .strategies-table tr:nth-child(even) {
            background-color: rgba(128,128,128,0.05);
        }
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.78rem;
            font-weight: bold;
            text-transform: uppercase;
        }
        .badge-credit {
            background-color: rgba(40, 167, 69, 0.15);
            color: #28a745;
            border: 1px solid rgba(40, 167, 69, 0.25);
        }
        .badge-debit {
            background-color: rgba(23, 162, 184, 0.15);
            color: #17a2b8;
            border: 1px solid rgba(23, 162, 184, 0.25);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Let's write the table in clean HTML so columns wrap beautifully and respect width constraints
    html_table = """
    <table class="strategies-table">
        <thead>
            <tr>
                <th style="width: 15%">Category</th>
                <th style="width: 15%">Strategy</th>
                <th style="width: 30%">Technique & Core Mechanics</th>
                <th style="width: 12%">Time to Expiry</th>
                <th style="width: 13%">Moneyness</th>
                <th style="width: 15%">Comment</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><b>Wheel Strategy</b><br><span class="badge badge-credit">Credit</span></td>
                <td><b>Covered Call</b></td>
                <td>Collecting premium based on probability of profit. Farming Theta decay. Looking to sell underlying at a key strike point or rolling over.</td>
                <td>15 - 60 Days</td>
                <td>OTM (Low delta, typically &lt;= 0.30)</td>
                <td>Go further out in expiration (e.g., 45-60 DTE) for less maintenance work and proportional yield. You want to close your position in the underlying.</td>
            </tr>
            <tr>
                <td><b>Wheel Strategy</b><br><span class="badge badge-credit">Credit</span></td>
                <td><b>Cash-Secured Put</b></td>
                <td>Collecting premium based on probability of profit. Farming Theta decay. Looking to buy underlying at a key strike point or rolling over.</td>
                <td>15 - 60 Days</td>
                <td>OTM (Low delta, typically &lt;= 0.30)</td>
                <td>Go further out in expiration for less work and steady proportional yield. You want to own the underlying.</td>
            </tr>
            <tr>
                <td><b>Credit Spread</b><br><span class="badge badge-credit">Credit</span></td>
                <td><b>Bull Put Spread</b></td>
                <td>Collecting premium based on probability of profit. Farming Theta decay. Sell outer put and buy deeper put to define risk.</td>
                <td>15 - 60 Days</td>
                <td>OTM (Low delta, typically &lt;= 0.25)</td>
                <td>Go further out in expiration for less work and proportional yield if support holds.</td>
            </tr>
            <tr>
                <td><b>Credit Spread</b><br><span class="badge badge-credit">Credit</span></td>
                <td><b>Bear Call Spread</b></td>
                <td>Collecting premium based on probability of profit. Farming Theta decay. Sell outer call and buy deeper call to define risk.</td>
                <td>15 - 60 Days</td>
                <td>OTM (Low delta, typically &lt;= 0.25)</td>
                <td>Go further out in expiration for less work and proportional yield if resistance holds.</td>
            </tr>
            <tr>
                <td><b>Debit</b><br><span class="badge badge-debit">Debit</span></td>
                <td><b>LEAPS Call / Put</b></td>
                <td>Capitalizing on a predefined large directional move up or down. Farming intrinsic value. Reduces Theta decay drag.</td>
                <td>6 Months - 1+ Years</td>
                <td>Deep ITM (High delta, typically &gt;= 0.70)</td>
                <td>Profit on move with less capital and not owning shares. Close as soon as decent profit targets are met.</td>
            </tr>
            <tr>
                <td><b>Debit Spread</b><br><span class="badge badge-debit">Debit</span></td>
                <td><b>Bull Call Spread</b></td>
                <td>Same as LEAPS, but requires less capital and profits are capped. Buy lower call and sell higher call.</td>
                <td>6 Months - 1+ Years</td>
                <td>ATM or ITM (Average delta, 0.40 - 0.60)</td>
                <td>Cheap Leaps. The short leg offsets decay but caps the maximum upside.</td>
            </tr>
            <tr>
                <td><b>Debit Spread</b><br><span class="badge badge-debit">Debit</span></td>
                <td><b>Bear Put Spread</b></td>
                <td>Same as LEAPS, but requires less capital and profits are capped. Buy higher put and sell lower put.</td>
                <td>6 Months - 1+ Years</td>
                <td>ATM or ITM (Average delta, 0.40 - 0.60)</td>
                <td>Cheap Leaps. Ideal for capturing downward moves in high-priced stocks with controlled risk.</td>
            </tr>
            <tr>
                <td><b>High Volatility</b><br><span class="badge badge-credit">Credit</span></td>
                <td><b>Short Iron Butterfly</b></td>
                <td>Maximizing premium collected based on tight price ranges. Farming Theta decay. Sell ATM Straddle and buy OTM protective wings.</td>
                <td>15 - 60 Days</td>
                <td>ATM Core (High ATM delta, low wing delta)</td>
                <td>Demands a lot of attention (high maintenance). Highest risk but highest potential reward.</td>
            </tr>
            <tr>
                <td><b>High Volatility</b><br><span class="badge badge-credit">Credit</span></td>
                <td><b>Short Iron Condor</b></td>
                <td>Maximizing premium collected based on range-bound price channels. Farming Theta decay. Sell OTM Put spread and OTM Call spread.</td>
                <td>15 - 60 Days</td>
                <td>OTM Wings (Low delta, typically &lt;= 0.20)</td>
                <td>Demands a lot of attention (high maintenance). Less risk than Iron Butterfly but similar.</td>
            </tr>
        </tbody>
    </table>
    """
    
    st.markdown(html_table, unsafe_allow_html=True)

with tabs[2]:
    st.subheader("Detailed Strategy Configurations")
    
    # Helper to generate payoff plot data
    def get_payoff_data(strategy):
        S = np.linspace(80, 120, 200)
        y_expiry = None
        y_t0 = None
        current_price = 100
        break_evens = []
        
        if strategy == "Long Call [Debit]":
            K = 100
            P = 5
            y_expiry = np.maximum(0, S - K) - P
            y_t0 = np.log(1 + np.exp(0.35 * (S - K))) / 0.35 - P
            break_evens = [105]
            
        elif strategy == "Long Put [Debit]":
            K = 100
            P = 5
            y_expiry = np.maximum(0, K - S) - P
            y_t0 = np.log(1 + np.exp(0.35 * (K - S))) / 0.35 - P
            break_evens = [95]
            
        elif strategy == "Covered Call [Credit]":
            current_price = 95
            S = np.linspace(75, 115, 200)
            y_expiry = (S - 95) - np.maximum(0, S - 100) + 5
            y_t0 = (S - 95) + 5 - (np.log(1 + np.exp(0.35 * (S - 100))) / 0.35)
            break_evens = [90]
            
        elif strategy == "Cash-Secured Put [Credit]":
            K = 100
            P = 5
            y_expiry = -np.maximum(0, K - S) + P
            y_t0 = P - (np.log(1 + np.exp(0.35 * (K - S))) / 0.35)
            break_evens = [95]
            
        elif strategy == "Bull Call Spread [Debit]":
            K1, K2 = 95, 105
            D = 5
            y_expiry = np.maximum(0, S - K1) - np.maximum(0, S - K2) - D
            y_t0 = (np.log(1 + np.exp(0.35 * (S - K1))) / 0.35) - (np.log(1 + np.exp(0.35 * (S - K2))) / 0.35) - D
            break_evens = [100]
            
        elif strategy == "Bear Put Spread [Debit]":
            K1, K2 = 95, 105
            D = 5
            y_expiry = np.maximum(0, K2 - S) - np.maximum(0, K1 - S) - D
            y_t0 = (np.log(1 + np.exp(0.35 * (K2 - S))) / 0.35) - (np.log(1 + np.exp(0.35 * (K1 - S))) / 0.35) - D
            break_evens = [100]
            
        elif strategy == "Bear Call Spread [Credit]":
            K1, K2 = 100, 105
            C = 2
            y_expiry = -np.maximum(0, S - K1) + np.maximum(0, S - K2) + C
            y_t0 = C - (np.log(1 + np.exp(0.35 * (S - K1))) / 0.35) + (np.log(1 + np.exp(0.35 * (S - K2))) / 0.35)
            break_evens = [102]
            
        elif strategy == "Bull Put Spread [Credit]":
            K1, K2 = 95, 100
            C = 2
            y_expiry = -np.maximum(0, K2 - S) + np.maximum(0, K1 - S) + C
            y_t0 = C - (np.log(1 + np.exp(0.35 * (K2 - S))) / 0.35) + (np.log(1 + np.exp(0.35 * (K1 - S))) / 0.35)
            break_evens = [98]
            
        elif strategy == "Short Iron Condor [Credit]":
            y_expiry = -np.maximum(0, 95 - S) + np.maximum(0, 90 - S) - np.maximum(0, S - 105) + np.maximum(0, S - 110) + 2
            y_t0 = 2 - (np.log(1 + np.exp(0.35 * (95 - S))) / 0.35) + (np.log(1 + np.exp(0.35 * (90 - S))) / 0.35) - (np.log(1 + np.exp(0.35 * (S - 105))) / 0.35) + (np.log(1 + np.exp(0.35 * (S - 110))) / 0.35)
            break_evens = [93, 107]
            
        elif strategy == "Long Iron Condor [Debit]":
            y_expiry = np.maximum(0, 95 - S) - np.maximum(0, 90 - S) + np.maximum(0, S - 105) - np.maximum(0, S - 110) - 2
            y_t0 = -2 + (np.log(1 + np.exp(0.35 * (95 - S))) / 0.35) - (np.log(1 + np.exp(0.35 * (90 - S))) / 0.35) + (np.log(1 + np.exp(0.35 * (S - 105))) / 0.35) - (np.log(1 + np.exp(0.35 * (S - 110))) / 0.35)
            break_evens = [93, 107]
            
        return S, y_expiry, y_t0, current_price, break_evens

    def plot_payoff(strategy_name, S, y_expiry, y_t0, current_price, break_evens):
        fig = go.Figure()
        
        # Add red/green background fills split exactly at y=0
        # Over 0 PnL (Green fill)
        fig.add_trace(go.Scatter(
            x=[S[0], S[-1]],
            y=[0, 0],
            fill=None,
            mode='lines',
            line=dict(color='rgba(0,0,0,0)'),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Fill above 0 (Green)
        fig.add_trace(go.Scatter(
            x=S,
            y=np.maximum(0, y_expiry),
            fill='tonexty',
            fillcolor='rgba(40, 167, 69, 0.08)',
            mode='lines',
            line=dict(color='rgba(0,0,0,0)'),
            name='Profit Zone',
            showlegend=True,
            hoverinfo='skip'
        ))
        
        # Fill below 0 (Red)
        fig.add_trace(go.Scatter(
            x=S,
            y=np.minimum(0, y_expiry),
            fill='tozeroy',
            fillcolor='rgba(220, 53, 69, 0.08)',
            mode='lines',
            line=dict(color='rgba(0,0,0,0)'),
            name='Loss Zone',
            showlegend=True,
            hoverinfo='skip'
        ))

        fig.add_hline(y=0, line_color="rgba(128, 128, 128, 0.4)", line_width=1.5, line_dash="solid")
        
        # Plot expiration payoff - thick teal line
        fig.add_trace(go.Scatter(
            x=S,
            y=y_expiry,
            mode='lines',
            line=dict(color='#00cc96', width=3.5),
            name='At Expiration'
        ))
        
        # Plot T+0 payoff - dashed blue curve
        fig.add_trace(go.Scatter(
            x=S,
            y=y_t0,
            mode='lines',
            line=dict(color='#3b82f6', width=2, dash='dash'),
            name='Current (T+0)'
        ))
        
        # Current stock price marker
        if current_price is not None:
            y_curr = np.interp(current_price, S, y_t0)
            fig.add_trace(go.Scatter(
                x=[current_price],
                y=[y_curr],
                mode='markers',
                marker=dict(color='#9ca3af', size=11, line=dict(color='white', width=1.5)),
                name='Current Stock Price',
                showlegend=False
            ))
            fig.add_vline(x=current_price, line_color="rgba(156, 163, 175, 0.5)", line_width=1.5, line_dash="dash")
            fig.add_annotation(
                x=current_price,
                y=y_curr,
                text=f"Current: ${current_price:.2f}",
                showarrow=True,
                arrowhead=1,
                arrowcolor="#9ca3af",
                ax=40,
                ay=-35,
                font=dict(size=10, color="#9ca3af"),
                bgcolor="rgba(17, 24, 39, 0.8)",
                bordercolor="rgba(156, 163, 175, 0.5)",
                borderwidth=1,
                borderpad=4
            )
            
        fig.update_layout(
            title=dict(
                text=f"📊 {strategy_name} Payoff Profile",
                font=dict(size=13, color="white")
            ),
            xaxis_title="Underlying Price ($)",
            yaxis_title="Profit / Loss ($)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=350,  # Increased height by 25% (from 280 to 350)
            margin=dict(l=40, r=20, t=45, b=25),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=9)
            ),
            xaxis=dict(gridcolor='rgba(128,128,128,0.15)', zeroline=False),
            yaxis=dict(gridcolor='rgba(128,128,128,0.15)', zeroline=False)
        )
        return fig

    # Selectbox updated with Credit/Debit tags and 4 new basic strategies
    strat_details = st.selectbox("Select Strategy to Explore", [
        "Long Call [Debit]",
        "Long Put [Debit]",
        "Covered Call [Credit]",
        "Cash-Secured Put [Credit]",
        "Bull Call Spread [Debit]",
        "Bear Put Spread [Debit]",
        "Bear Call Spread [Credit]",
        "Bull Put Spread [Credit]",
        "Short Iron Condor [Credit]",
        "Long Iron Condor [Debit]"
    ])
    
    st.write("---")
    
    # Render selected strategy configurations
    if strat_details == "Long Call [Debit]":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Strategy Summary")
            st.markdown("""
            | Parameter | Detail |
            | :--- | :--- |
            | **Description** | Buy a standard Call option with a chosen strike and expiration. |
            | **Market Outlook** | Strongly Bullish (expecting a sharp upward breakout). |
            | **Reason to Use** | High leveraged upside potential with strictly capped risk. |
            | **Losing Conditions** | Sideways movement, price decrease, or severe time decay / implied volatility contraction. |
            | **Max Risk** | Premium paid (debit). |
            | **Max Reward** | Unlimited as the underlying stock price rises. |
            | **Margin Required** | No. |
            """)
            S_data, y_exp, y_t0, curr, bes = get_payoff_data("Long Call [Debit]")
            fig = plot_payoff("Long Call [Debit]", S_data, y_exp, y_t0, curr, bes)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("### 📜 Rules & Execution Guidelines")
            with st.container(border=True):
                st.markdown("**Stock Selection Rules**")
                st.markdown("""
                - Underlying trading near technical breakouts, support levels, or experiencing highly bullish catalyst schedules.
                - Focus on highly liquid names with tight bid-ask spreads (e.g. SPY, QQQ, large caps).
                """)
                st.markdown("**Risk Management**")
                st.markdown("""
                - Restrict size to **2% - 5% of total capital max**.
                - Buy further out in expiration (60-90+ Days to Expiration) to buffer against immediate Theta decay.
                """)
                st.markdown("**Exit & Take Profit Strategies**")
                st.markdown("""
                - *Take Profit*: Target closing at 50% - 100% option appreciation, or if momentum stalls.
                - *Exit for Loss*: Cut losses if the trend breaks key horizontal support. Avoid holding into the last 30 DTE.
                """)

    elif strat_details == "Long Put [Debit]":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Strategy Summary")
            st.markdown("""
            | Parameter | Detail |
            | :--- | :--- |
            | **Description** | Buy a standard Put option with a chosen strike and expiration. |
            | **Market Outlook** | Strongly Bearish (expecting a sharp correction or breakdown). |
            | **Reason to Use** | Highly leveraged downside exposure with defined risk (an excellent hedge). |
            | **Losing Conditions** | Stock consolidates flat, rallies, or IV crushes. |
            | **Max Risk** | Premium paid (debit). |
            | **Max Reward** | Strike Price minus Premium paid (stock falls to zero). |
            | **Margin Required** | No. |
            """)
            S_data, y_exp, y_t0, curr, bes = get_payoff_data("Long Put [Debit]")
            fig = plot_payoff("Long Put [Debit]", S_data, y_exp, y_t0, curr, bes)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("### 📜 Rules & Execution Guidelines")
            with st.container(border=True):
                st.markdown("**Stock Selection Rules**")
                st.markdown("""
                - Weak macro sectors, stocks breaking below multi-month support, or as systemic market portfolio hedges.
                """)
                st.markdown("**Risk Management**")
                st.markdown("""
                - Position size limited to **2% - 5% max**.
                - Avoid buying during historically high Implied Volatility (IV Rank > 70%) to protect against IV crush.
                """)
                st.markdown("**Exit & Take Profit Strategies**")
                st.markdown("""
                - *Take Profit*: Close out on sharp, swift downswings as volatility expansion will artificially pump the Put premiums.
                - *Exit for Loss*: Cut loss if the stock reverses and consolidates above resistance.
                """)

    elif strat_details == "Covered Call [Credit]":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Strategy Summary")
            st.markdown("""
            | Parameter | Detail |
            | :--- | :--- |
            | **Description** | Buy/own 100 shares of stock and sell 1 Out-of-the-Money Call option against them. |
            | **Market Outlook** | Neutral to Mildly Bullish. |
            | **Reason to Use** | Generate consistent passive income, reducing the effective cost basis of the shares. |
            | **Losing Conditions** | Severe stock drop (share losses exceed premium), or stock surges past the strike (gains capped). |
            | **Max Risk** | Stock purchase price minus Call premium received. |
            | **Max Reward** | (Strike Price - Purchase Price) * 100 + Premium received |
            | **Margin Required** | No (covered by shares). |
            """)
            S_data, y_exp, y_t0, curr, bes = get_payoff_data("Covered Call [Credit]")
            fig = plot_payoff("Covered Call [Credit]", S_data, y_exp, y_t0, curr, bes)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("### 📜 Rules & Execution Guidelines")
            with st.container(border=True):
                st.markdown("**Stock Selection Rules**")
                st.markdown("""
                - High-quality, stable dividend payers, blue-chips, or index ETFs you want to hold long-term.
                """)
                st.markdown("**Risk Management**")
                st.markdown("""
                - Sell Call strikes at **30 Delta or lower** to balance collection sizing with low probability of assignment.
                - Focus on **30 - 45 DTE** to exploit accelerating decay.
                """)
                st.markdown("**Exit & Take Profit Strategies**")
                st.markdown("""
                - *Take Profit*: Let contract expire worthless to capture 100% premium, or buy back cheap (< 10% value) and sell a new month.
                - *If Assigned*: Allow shares to be called away, locking in max profit, and transition to selling cash-secured puts.
                """)

    elif strat_details == "Cash-Secured Put [Credit]":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Strategy Summary")
            st.markdown("""
            | Parameter | Detail |
            | :--- | :--- |
            | **Description** | Sell an Out-of-the-Money Put option while holding enough cash to buy 100 shares if assigned. |
            | **Market Outlook** | Neutral to Mildly Bullish. |
            | **Reason to Use** | Earn yield/premium while waiting to acquire premium stocks at a discounted entry price. |
            | **Losing Conditions** | The stock price collapses dramatically below the strike. |
            | **Max Risk** | Strike Price minus Put premium collected (substantial but safer than owning stock outright). |
            | **Max Reward** | Put premium collected (net credit). |
            | **Margin Required** | Cash-secured. |
            """)
            S_data, y_exp, y_t0, curr, bes = get_payoff_data("Cash-Secured Put [Credit]")
            fig = plot_payoff("Cash-Secured Put [Credit]", S_data, y_exp, y_t0, curr, bes)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("### 📜 Rules & Execution Guidelines")
            with st.container(border=True):
                st.markdown("**Stock Selection Rules**")
                st.markdown("""
                - Grade-A companies or broad market indexes that you actively desire to own in your long-term portfolio.
                """)
                st.markdown("**Risk Management**")
                st.markdown("""
                - Sell at **30 Delta or lower** with **30 - 45 DTE** to capture optimal extrinsic decay premium.
                """)
                st.markdown("**Exit & Take Profit Strategies**")
                st.markdown("""
                - *Take Profit*: Buy back and close the position at **50% - 70% of max profit** to eliminate tail risk and recycle capital.
                - *If Assigned*: Accept the 100 shares of stock at the discount strike, and initiate **The Wheel** by selling Covered Calls.
                """)

    elif strat_details == "Bull Call Spread [Debit]":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Strategy Summary")
            st.markdown("""
            | Parameter | Detail |
            | :--- | :--- |
            | **Description** | Buy a low-strike Call option and Sell a higher-strike Call option with the same expiration. |
            | **Market Outlook** | Bullish on the underlying asset (Upward directional trend). |
            | **Reason to Use** | Reduces the capital cost and lowers the break-even point compared to buying a naked Call. |
            | **Losing Conditions** | Underlyings moving sideways or downwards. |
            | **Max Risk** | Premium paid (debit). |
            | **Max Reward** | (Difference between strikes * 100) - Premium paid |
            | **Margin Required** | Yes (requires margin account to sell the short leg). |
            """)
            S_data, y_exp, y_t0, curr, bes = get_payoff_data("Bull Call Spread [Debit]")
            fig = plot_payoff("Bull Call Spread [Debit]", S_data, y_exp, y_t0, curr, bes)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("### 📜 Rules & Execution Guidelines")
            with st.container(border=True):
                st.markdown("**Stock Selection Rules**")
                st.markdown("""
                - Underlying trading near its long-term support or all-time lows.
                - High Delta on the long leg (>= 45%).
                - Implied Volatility (IV) between 30% and 90%.
                - High trading volume & tight spreads.
                - Robust market capitalization to avoid illiquidity.
                """)
                
                st.markdown("**Risk Management**")
                st.markdown("""
                - *Strike Width*: Larger spreads equal less structural capping (more potential profit) but higher premium paid.
                - *Delta*: Lower delta long leg equals more execution risk.
                - Limit trade size to **5% - 10% of total portfolio capital max**.
                - Avoid trading during Ex-Dividend weeks, or exit 2 days prior to prevent early assignment on the short call.
                - Always cross-reference upcoming earnings announcements.
                """)
                
                st.markdown("**Exit & Take Profit Strategies**")
                st.markdown("""
                - *Exit for Loss*: If the underlying moves down/sideways, close early to preserve capital, or wait for a technical correction depending on remaining DTE.
                - *Take Profit*: Close when the underlying approaches the short strike, near expiration, or when 50-70% of max value is achieved.
                - *Follow Up*: Repeat the trade or flip strategies based on new technical opportunities.
                """)

    elif strat_details == "Bear Put Spread [Debit]":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Strategy Summary")
            st.markdown("""
            | Parameter | Detail |
            | :--- | :--- |
            | **Description** | Buy a high-strike Put option and Sell a lower-strike Put option with the same expiration. |
            | **Market Outlook** | Bearish on the underlying asset (Downward directional trend). |
            | **Reason to Use** | Reduces the capital outlay and lowers the break-even point compared to buying a naked Put. |
            | **Losing Conditions** | Underlyings moving sideways or upwards. |
            | **Max Risk** | Premium paid (debit). |
            | **Max Reward** | (Difference between strikes * 100) - Premium paid |
            | **Margin Required** | Yes (requires margin account to sell the short leg). |
            """)
            S_data, y_exp, y_t0, curr, bes = get_payoff_data("Bear Put Spread [Debit]")
            fig = plot_payoff("Bear Put Spread [Debit]", S_data, y_exp, y_t0, curr, bes)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("### 📜 Rules & Execution Guidelines")
            with st.container(border=True):
                st.markdown("**Stock Selection Rules**")
                st.markdown("""
                - Underlying trading near major resistance or multi-year highs.
                - High Delta on the long leg (>= 45%).
                - Implied Volatility (IV) between 30% and 90%.
                - High trading volume & tight spreads.
                - Strong market capitalization.
                """)
                
                st.markdown("**Risk Management**")
                st.markdown("""
                - *Strike Width*: Larger spreads equal more potential profit but higher capital cost.
                - *Delta*: Lower delta on the long put equals higher probability of loss.
                - Limit trade size to **5% - 10% of total portfolio capital max**.
                - Check for upcoming dividend distributions and exit schedules.
                - Monitor earnings releases carefully.
                """)
                
                st.markdown("**Exit & Take Profit Strategies**")
                st.markdown("""
                - *Exit for Loss*: If the stock turns up or stays flat, cut losses early, or hold for a technical retracement.
                - *Take Profit*: Close near expiration or when the price approaches the short (lower) put strike.
                - *Follow Up*: Re-enter if the downward momentum continues, or shift strategies if support is reached.
                """)

    elif strat_details == "Bear Call Spread [Credit]":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Strategy Summary")
            st.markdown("""
            | Parameter | Detail |
            | :--- | :--- |
            | **Description** | Sell a lower-strike Call option and Buy a higher-strike Call option with the same expiration. |
            | **Market Outlook** | Bearish to Neutral on the underlying asset (Downward trend or Sideways consolidation). |
            | **Reason to Use** | Collect upfront premium and restrict maximum risk with the bought long Call protective wing. |
            | **Losing Conditions** | Sharp, aggressive upward price breakouts. |
            | **Max Risk** | (Difference between strikes * 100) - Premium received |
            | **Max Reward** | Premium received (net credit). |
            | **Margin Required** | Yes. |
            """)
            S_data, y_exp, y_t0, curr, bes = get_payoff_data("Bear Call Spread [Credit]")
            fig = plot_payoff("Bear Call Spread [Credit]", S_data, y_exp, y_t0, curr, bes)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("### 📜 Rules & Execution Guidelines")
            with st.container(border=True):
                st.markdown("**Stock Selection Rules**")
                st.markdown("""
                - Underlying trading near strong technical resistance or all-time highs.
                - Low Delta on the short leg (<= 25%).
                - Implied Volatility (IV) elevated (30% to 90%) to capture higher credit premium.
                - Liquid option volume and tight bid-ask spreads.
                - High-quality market capitalization.
                """)
                
                st.markdown("**Risk Management**")
                st.markdown("""
                - *Strike Width*: Larger spreads increase maximum risk but collect more initial credit.
                - *Delta*: Lower delta short call increases probability of success but collects less premium.
                - Limit allocation to **5% - 10% of portfolio capital per trade**.
                - Do not trade during Ex-Dividend weeks to eliminate dividend-assignment risk on the short call.
                - Ensure no major corporate earnings are scheduled during the trade's duration.
                """)
                
                st.markdown("**Exit & Take Profit Strategies**")
                st.markdown("""
                - *Exit for Loss*: Close or roll the spread if the underlying price approaches or breaches the short call strike.
                - *Take Profit*: Let expire worthless to collect 100% max profit, or close early at 50% - 80% decay to release margin.
                - *Follow Up*:
                  - *Same Outlook*: Close and roll up (higher strikes) or roll over (further expiration).
                  - *Changed Outlook*: Close or invert/convert to a neutral or bullish spread.
                """)

    elif strat_details == "Bull Put Spread [Credit]":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Strategy Summary")
            st.markdown("""
            | Parameter | Detail |
            | :--- | :--- |
            | **Description** | Sell a higher-strike Put option and Buy a lower-strike Put option with the same expiration. |
            | **Market Outlook** | Bullish to Neutral on the underlying asset (Upward trend or Sideways consolidation). |
            | **Reason to Use** | Collect upfront credit premium and limit capital risk with the bought long Put protection. |
            | **Losing Conditions** | Sharp, aggressive downward price sell-offs. |
            | **Max Risk** | (Difference between strikes * 100) - Premium received |
            | **Max Reward** | Premium received (net credit). |
            | **Margin Required** | Yes. |
            """)
            S_data, y_exp, y_t0, curr, bes = get_payoff_data("Bull Put Spread [Credit]")
            fig = plot_payoff("Bull Put Spread [Credit]", S_data, y_exp, y_t0, curr, bes)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("### 📜 Rules & Execution Guidelines")
            with st.container(border=True):
                st.markdown("**Stock Selection Rules**")
                st.markdown("""
                - Underlying trading near major horizontal support levels or all-time lows.
                - Low Delta on the short leg (<= 25%).
                - Elevated Implied Volatility (30% to 90%) to pump up premium.
                - High volume and market capitalisation.
                """)
                
                st.markdown("**Risk Management**")
                st.markdown("""
                - *Strike Width*: Wider spreads increase maximum risk but offer a higher net credit.
                - *Delta*: Lower delta on the short put decreases risk of assignment.
                - Limit trade allocation to **5% - 10% of portfolio max**.
                - Guard against early assignment risk by checking ex-dividend calendars.
                - Verify earnings calendars.
                """)
                
                st.markdown("**Exit & Take Profit Strategies**")
                st.markdown("""
                - *Exit for Loss*: Roll or close the spread if the underlying price collapses near the short put strike.
                - *Take Profit*: Allow the spread to expire worthless, or buy back the spread at 50% - 80% profit.
                - *Follow Up*:
                  - *Same Outlook*: Roll down (collecting more credit) or roll over (extending time).
                  - *Changed Outlook*: Close or invert/convert to a bearish or neutral configuration.
                """)

    elif strat_details == "Short Iron Condor [Credit]":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Strategy Summary")
            st.markdown("""
            | Parameter | Detail |
            | :--- | :--- |
            | **Description** | Simultaneously sell an OTM Call Spread (Bear Call) and sell an OTM Put Spread (Bull Put). |
            | **Market Outlook** | Neutral / Range-bound. We want the underlying stock to consolidate sideways between the short Put and short Call strikes. |
            | **Reason to Use** | Collect high upfront net credit by taking advantage of double-sided premium decay. |
            | **Losing Conditions** | Large, aggressive breakout or breakdown moves in either direction. |
            | **Max Risk** | (Difference between strikes * 100) - Premium received (for the wider of the two wings) |
            | **Max Reward** | Premium received (net credit). |
            | **Margin Required** | Yes. |
            """)
            S_data, y_exp, y_t0, curr, bes = get_payoff_data("Short Iron Condor [Credit]")
            fig = plot_payoff("Short Iron Condor [Credit]", S_data, y_exp, y_t0, curr, bes)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("### 📜 Rules & Execution Guidelines")
            with st.container(border=True):
                st.markdown("**Core Setup Rules**")
                st.markdown("""
                - Select a highly liquid underlying index or stock trading in a well-defined consolidation channel.
                - Sell short strikes at the 15-20 Delta range (80%+ theoretical probability of success).
                - Buy protective wings 5 to 10 points out on both sides to limit structural risk.
                - Target 30 - 45 days to expiration to capture accelerating Theta decay.
                """)
                
                st.markdown("**Active Risk Management**")
                st.markdown("""
                - Avoid trading through high-risk binary events like corporate earnings or major FOMC releases.
                - If one wing is tested, you can roll the untested side closer to the underlying price to collect additional credit.
                - Limit overall Iron Condor exposure to **10% of total portfolio capital max**.
                """)
                
                st.markdown("**Exit & Profit Strategy**")
                st.markdown("""
                - *Profit Target*: Buy back and close the entire iron condor when you capture **50% of the maximum credit received**.
                - Let options expire worthless only if the underlying price remains perfectly centered and stable.
                """)

    elif strat_details == "Long Iron Condor [Debit]":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Strategy Summary")
            st.markdown("""
            | Parameter | Detail |
            | :--- | :--- |
            | **Description** | Simultaneously buy an ITM/ATM Call Spread and buy an ITM/ATM Put Spread. (Or conversely, buy OTM wings and sell inner ATM strikes). |
            | **Market Outlook** | Highly Volatile / Expecting a massive breakout or breakdown. |
            | **Reason to Use** | Anticipate a major directional explosion while capping maximum potential risk to a small premium paid. Often used right before high-impact events like earnings. |
            | **Losing Conditions** | Underlying asset consolidates sideways within the narrow inner strike bounds. |
            | **Max Risk** | Premium paid (net debit). |
            | **Max Reward** | (Strike Width * 100) - Premium paid |
            | **Margin Required** | No (the bought wings fully cover margin risk). |
            """)
            S_data, y_exp, y_t0, curr, bes = get_payoff_data("Long Iron Condor [Debit]")
            fig = plot_payoff("Long Iron Condor [Debit]", S_data, y_exp, y_t0, curr, bes)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("### 📜 Rules & Execution Guidelines")
            with st.container(border=True):
                st.markdown("**Core Setup Rules**")
                st.markdown("""
                - Target stocks with very cheap Implied Volatility (IV) relative to upcoming expected volatility.
                - Look for massive historical movers prior to highly anticipated announcements.
                - Select tight inner strike widths to lower the break-even move threshold.
                """)
                
                st.markdown("**Management & Exit**")
                st.markdown("""
                - *Take Profit*: Close as soon as the price breaks outside the wings and premium surges. Avoid holding too close to expiration as decay will eat into profits.
                - *Max Loss*: If the stock consolidates flat post-event, accept the loss and close out remaining premium.
                """)

with tabs[3]:
    st.subheader("🔎 Barchart Option Filters")
    st.write("Saved queries and filter constraints to run on Barchart.com or other scanners to source premium setups.")
    
    # Keeping it empty for now as requested
    st.info("No filters currently configured. Add criteria to build automated trade scanners.")
