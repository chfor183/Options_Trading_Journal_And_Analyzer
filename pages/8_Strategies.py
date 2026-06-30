import streamlit as st
import pandas as pd

st.set_page_config(page_title="Option Strategies", page_icon="📈", layout="wide")
st.title("📈 Option Strategies")

# Define the tabs: Summary, Details, and Barchart Filters
tabs = st.tabs(["📋 Strategies Summary", "🔍 Strategies Details", "🔎 Barchart Filters"])

with tabs[0]:
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
                <td>Go further out in expiration (e.g., 45-60 DTE) for less maintenance work and proportional yield if you wish to hold.</td>
            </tr>
            <tr>
                <td><b>Wheel Strategy</b><br><span class="badge badge-credit">Credit</span></td>
                <td><b>Cash-Secured Put</b></td>
                <td>Collecting premium based on probability of profit. Farming Theta decay. Looking to buy underlying at a key strike point or rolling over.</td>
                <td>15 - 60 Days</td>
                <td>OTM (Low delta, typically &lt;= 0.30)</td>
                <td>Go further out in expiration for less work and steady proportional yield. Be happy to own the underlying.</td>
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

with tabs[1]:
    st.subheader("Detailed Strategy Configurations")
    
    # We will use selectbox or expanders to explore each strategy cleanly
    strat_details = st.selectbox("Select Strategy to Explore", [
        "Bull Call Spread [Debit]",
        "Bear Put Spread [Debit]",
        "Bear Call Spread [Credit]",
        "Bull Put Spread [Credit]",
        "Short Iron Condor",
        "Long Iron Condor"
    ])
    
    st.write("---")
    
    if strat_details == "Bull Call Spread [Debit]":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Strategy Summary")
            st.markdown("""
            - **Description**: Buy a low-strike Call option and Sell a higher-strike Call option with the same expiration.
            - **Market Outlook**: Bullish on the underlying asset (Upward directional trend).
            - **Reason to Use**: Reduces the capital cost and lowers the break-even point compared to buying a naked Call.
            - **Losing Conditions**: Underlyings moving sideways or downwards.
            - **Max Risk**: Premium paid (debit).
            - **Max Reward**: `(Difference between strikes * 100) - Premium paid`
            - **Margin Requirement**: Yes (requires margin account to sell the short leg).
            """)
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
            - **Description**: Buy a high-strike Put option and Sell a lower-strike Put option with the same expiration.
            - **Market Outlook**: Bearish on the underlying asset (Downward directional trend).
            - **Reason to Use**: Reduces the capital outlay and lowers the break-even point compared to buying a naked Put.
            - **Losing Conditions**: Underlyings moving sideways or upwards.
            - **Max Risk**: Premium paid (debit).
            - **Max Reward**: `(Difference between strikes * 100) - Premium paid`
            - **Margin Requirement**: Yes (requires margin account to sell the short leg).
            """)
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
            - **Description**: Sell a lower-strike Call option and Buy a higher-strike Call option with the same expiration.
            - **Market Outlook**: Bearish to Neutral on the underlying asset (Downward trend or Sideways consolidation).
            - **Reason to Use**: Collect upfront premium and restrict maximum risk with the bought long Call protective wing.
            - **Losing Conditions**: Sharp, aggressive upward price breakouts.
            - **Max Risk**: `(Difference between strikes * 100) - Premium received`
            - **Max Reward**: Premium received (net credit).
            - **Margin Requirement**: Yes.
            """)
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
                  - *Changed Outlook*: Close and invert/convert to a neutral or bullish spread.
                """)

    elif strat_details == "Bull Put Spread [Credit]":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Strategy Summary")
            st.markdown("""
            - **Description**: Sell a higher-strike Put option and Buy a lower-strike Put option with the same expiration.
            - **Market Outlook**: Bullish to Neutral on the underlying asset (Upward trend or Sideways consolidation).
            - **Reason to Use**: Collect upfront credit premium and limit capital risk with the bought long Put protection.
            - **Losing Conditions**: Sharp, aggressive downward price sell-offs.
            - **Max Risk**: `(Difference between strikes * 100) - Premium received`
            - **Max Reward**: Premium received (net credit).
            - **Margin Requirement**: Yes.
            """)
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
                  - *Changed Outlook*: Close and invert/convert to a bearish or neutral configuration.
                """)

    elif strat_details == "Short Iron Condor":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Strategy Summary")
            st.markdown("""
            - **Description**: Simultaneously sell an OTM Call Spread (Bear Call) and sell an OTM Put Spread (Bull Put).
            - **Market Outlook**: Neutral/Range-bound. We want the underlying stock to consolidate sideways between the short Put and short Call strikes.
            - **Reason to Use**: Collect high upfront net credit by taking advantage of double-sided premium decay.
            - **Losing Conditions**: Large, aggressive breakout or breakdown moves in either direction.
            - **Max Risk**: `(Difference between strikes * 100) - Premium received` (for the wider of the two wings).
            - **Max Reward**: Premium received (net credit).
            - **Margin Requirement**: Yes.
            """)
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

    elif strat_details == "Long Iron Condor":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Strategy Summary")
            st.markdown("""
            - **Description**: Simultaneously buy an ITM/ATM Call Spread and buy an ITM/ATM Put Spread. (Or conversely, buy OTM wings and sell inner ATM strikes).
            - **Market Outlook**: Highly Volatile / Expecting a massive breakout or breakdown.
            - **Reason to Use**: Anticipate a major directional explosion while capping maximum potential risk to a small premium paid. Often used right before high-impact events like earnings.
            - **Losing Conditions**: Underlying asset consolidates sideways within the narrow inner strike bounds.
            - **Max Risk**: Premium paid (net debit).
            - **Max Reward**: `(Strike Width * 100) - Premium paid`
            - **Margin Requirement**: No (the bought wings fully cover margin risk).
            """)
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

with tabs[2]:
    st.subheader("🔎 Barchart Option Filters")
    st.write("Saved queries and filter constraints to run on Barchart.com or other scanners to source premium setups.")
    
    # Keeping it empty for now as requested
    st.info("No filters currently configured. Add criteria to build automated trade scanners.")
