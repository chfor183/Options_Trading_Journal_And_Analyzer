import streamlit as st
from src.db import init_db

st.set_page_config(
    page_title="Options Trading Journal",
    page_icon="📈",
    layout="wide",
)

# Custom stylized banner / header
st.markdown("""
<div style="background-color: rgba(0, 97, 252, 0.1); border-left: 5px solid #013382; padding: 20px; border-radius: 5px; margin-bottom: 25px;">
    <h1 style="margin: 0; color: #e0e0e0; font-family: inherit;">📈 Options Trading Journal & Analyzer</h1>
    <p style="margin: 8px 0 0 0; color: #b0b0b0; font-size: 1.1rem; line-height: 1.5;">
        Welcome to your advanced local options trading companion.<br>Track positions, model strategy payouts, audit setups, and build a consistent mathematical edge.
    </p>
</div>
""", unsafe_allow_html=True)

# Initialize database on startup
try:
    init_db()
    st.success("Database connected and initialized.")
except Exception as e:
    st.error(f"Failed to connect to the database. Ensure PostgreSQL is running. Error: {e}")

st.info("📅 **Calendar Spreads Not Supported:** Please note that calendar spreads (such as a Poor Man's Covered Call) are not currently supported as a single multi-leg entry. Each part of a calendar spread (having different expiration dates) should be entered and managed as a separate trade.")

st.divider()

# Options Basics Section
st.subheader("💡 Options Trading: The Core Basics")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("### 🎫 Options Contracts")
        st.markdown("""
        An option is a contract representing **100 shares** of an underlying stock. It is usually used to hedge risk or speculate on price movements. Options are derivatives, meaning their value is derived from the underlying asset (usually a stock or index).
        
        - **📞 Call Option**: The right to **BUY** a stock at a set strike price before expiration. You buy Calls when bullish; sell them when neutral/bearish.
        - **🛡️ Put Option**: The right to **SELL** a stock at a set strike price before expiration. You buy Puts when bearish; sell them when neutral/bullish.
        """)
        
    with st.container(border=True):
        st.markdown("### ⏳ How Options are Priced")
        st.markdown("""
        Every option's price (Premium) is split into two components:
        
        $$\\text{Premium} = \\text{Intrinsic Value} + \\text{Extrinsic Value}$$
        
        - **Intrinsic Value (Real value)**: How much the option is currently in-the-money (for Calls: Stock Price - Strike Price; for Puts: Strike Price - Stock Price).
        - **Extrinsic Value (Hope/Time value)**: The premium representing remaining days until expiration (**Theta**) and volatility levels (**Vega**). This value decays exponentially to $0.00 at expiration.
        """)

with col2:
    with st.container(border=True):
        st.markdown("### ⚖️ Bid, Ask & The Spread")
        st.markdown("""
        - **💵 Bid**: The highest price buyers are willing to pay. (You sell at the Bid).
        - **🏷️ Ask**: The lowest price sellers are willing to accept. (You buy at the Ask).
        - **↔️ Spread**: The difference between the Bid and Ask (`Ask - Bid`).
        
        **Why we want a TIGHT spread:**
        1. **Low Transaction Friction**: A narrow spread (such as \\$0.01 - $0.05) ensures you don't immediately lose substantial value upon entering a trade.
        2. **High Liquidity**: Tight spreads signify high trading volume and plenty of active participants, making it simple to exit or adjust your trade instantly at fair prices without taking a haircut.
        """)

    with st.container(border=True):
        st.markdown("### 🎛️ Essential Greek Metrics")
        st.markdown("""
        - **$\\Delta$ (Delta)**: Price sensitivity. Measures how much the premium moves per $1.00 move of the stock. (Also acts as a rough probability of finishing ITM).
        - **$\\theta$ (Theta)**: Time decay. The daily premium erosion. (Our best friend as option sellers).
        - **$\\nu$ (Vega)**: Volatility sensitivity. Measures premium changes per 1% change in Implied Volatility (IV).
        """)

st.divider()

