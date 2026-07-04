import streamlit as st
import pandas as pd
import numpy as np
import math

# Page setup
st.set_page_config(page_title="Probabilities", page_icon="🎲", layout="wide")

st.title("Probabilities Dashboard")
st.write("Analyze trading streak probabilities, explore probability models, and understand key math metrics used in options trading.")

# Tabs for organization
tab1, tab2 = st.tabs(["🎯 Streak Probability Analyzer", "📚 Educational Guide (Math & Models)"])

# -----------------------------------------------------------------------------
# TAB 1: STREAK PROBABILITY ANALYZER
# -----------------------------------------------------------------------------
with tab1:
    st.header("Loser Streak Probability Calculator")
    st.write(
        "A common pitfall in trading is underestimating the probability of consecutive losses (drawdowns), "
        "even with a high win-rate strategy. Use this analyzer to visualize and compute the probability of "
        "experiencing a consecutive losing streak over a sequence of trades."
    )

    # Sidebar / Top inputs
    col_input1, col_input2, col_input3 = st.columns(3)
    with col_input1:
        win_rate_input = st.number_input(
            "Strategy Strike Rate (Win %):",
            min_value=0.0,
            max_value=100.0,
            value=75.0,
            step=1.0,
            help="The historical or expected win rate of your trading strategy."
        )
    with col_input2:
        max_consec_losses = st.slider(
            "Max Consecutive Losses to Display (Columns):",
            min_value=10,
            max_value=20,
            value=15,
            step=1,
            help="Define the maximum length of consecutive losing streak to analyze."
        )
    with col_input3:
        custom_trades = st.number_input(
            "Add a custom trade sequence length:",
            min_value=1,
            max_value=10000,
            value=150,
            step=10,
            help="Quickly calculate probabilities for a specific number of trades of your choice."
        )

    # Core Math function for exact streak probability using Recurrence Relation
    def get_loser_streak_prob(n, k, win_rate_frac):
        if k <= 0:
            return 1.0
        if n < k:
            return 0.0
        if win_rate_frac >= 1.0:
            return 0.0
        if win_rate_frac <= 0.0:
            return 1.0
            
        p = 1.0 - win_rate_frac
        q = win_rate_frac
        
        # We use the recurrence relation:
        # A[i] is the probability of NOT getting k consecutive losses in i trials.
        # A[i] = sum_{j=1}^{k} p^(j-1) * q * A[i-j]
        A = [1.0] * (n + 1)
        
        # Pre-calculate coeffs: p^(j-1) * q
        coeffs = [(p ** (j - 1)) * q for j in range(1, k + 1)]
        
        for i in range(k, n + 1):
            val = 0.0
            for j in range(1, k + 1):
                val += coeffs[j - 1] * A[i - j]
            A[i] = val
            
        return 1.0 - A[n]

    # List of default trade sequence sizes (N values)
    standard_n_vals = [1, 10, 20, 30, 40, 50, 100, 200, 500, 1000]
    
    # Add custom trade count if it is not already in the list
    n_vals = sorted(list(set(standard_n_vals + [custom_trades])))

    # Define columns representing # consecutive losses (K values)
    k_vals = list(range(2, max_consec_losses + 1))

    # Calculate values
    win_rate_frac = win_rate_input / 100.0
    
    grid_data = []
    for n in n_vals:
        row = {"N": int(n)}
        for k in k_vals:
            prob = get_loser_streak_prob(n, k, win_rate_frac)
            row[str(k)] = prob
        grid_data.append(row)

    df = pd.DataFrame(grid_data)
    df.set_index("N", inplace=True)

    # Style the dataframe like the linked Excel spreadsheet
    # Red for low probability (below 10%), Green for higher probability (10% and above)
    def style_probability_grid(val):
        # We assume the value is a float representing the probability
        try:
            val_pct = val * 100.0
            if val_pct == 0.0:
                # 0% cells are styled red
                return 'background-color: #ffc7ce; color: #9c0006; text-align: right; font-weight: normal; padding: 3px 6px; font-size: 0.85rem;'
            elif val_pct >= 10.0:
                # Green styling for probabilities 10% and above
                return 'background-color: #c6efce; color: #006100; text-align: right; font-weight: 500; padding: 3px 6px; font-size: 0.85rem;'
            else:
                # Red styling for probabilities below 10%
                return 'background-color: #ffc7ce; color: #9c0006; text-align: right; padding: 3px 6px; font-size: 0.85rem;'
        except Exception:
            return 'text-align: right; padding: 3px 6px; font-size: 0.85rem;'

    # Apply formatting and styling
    try:
        styled_df = df.style.format("{:.2%}")\
                           .map(style_probability_grid)\
                           .set_table_styles([
                               {"selector": "th", "props": [("background-color", "#333333"), ("color", "white"), ("text-align", "center"), ("font-weight", "bold"), ("padding", "4px 8px"), ("font-size", "0.85rem")]},
                               {"selector": "td", "props": [("border", "1px solid #dddddd")]}
                           ])
    except AttributeError:
        styled_df = df.style.format("{:.2%}")\
                           .applymap(style_probability_grid)\
                           .set_table_styles([
                               {"selector": "th", "props": [("background-color", "#333333"), ("color", "white"), ("text-align", "center"), ("font-weight", "bold"), ("padding", "4px 8px"), ("font-size", "0.85rem")]},
                               {"selector": "td", "props": [("border", "1px solid #dddddd")]}
                           ])

    st.subheader(f"Loser Streak Probabilities Table (Strike Rate: {win_rate_input:.2f}%)")
    st.write(
        "The table below shows the exact probability of hitting **at least** a certain number of consecutive losses "
        "(columns) within a given number of trades (rows). Green cells indicate a probability of $\\ge 10.00\\%$, "
        "while red cells indicate a probability of $< 10.00\\%$."
    )
    
    # Render the styled table
    st.table(styled_df)

    st.info(
        f"💡 **Key Insight**: Notice how quickly the probability of a losing streak increases as your sample size of trades grows. "
        f"Even with an expected strike rate of **{win_rate_input:.2f}%**, you have a **{get_loser_streak_prob(100, 2, win_rate_frac):.2%}** chance of hitting a **2-loss streak** and a **{get_loser_streak_prob(100, 5, win_rate_frac):.2%}** chance of a "
        f"**5-loss streak** within 100 trades. Risk management and proper sizing are essential to survive these inevitable drawdowns!"
    )

    # Quick interactive calculator
    st.divider()
    st.subheader("🔮 Instant Run Calculator")
    col_calc1, col_calc2, col_calc3 = st.columns(3)
    with col_calc1:
        calc_trades = st.number_input("Number of Trades (Sample size):", min_value=1, value=50, step=1)
    with col_calc2:
        calc_streak = st.number_input("Consecutive Losses (Streak):", min_value=1, value=4, step=1)
    with col_calc3:
        calc_win_rate = st.slider("Strike Rate / Win Rate (%):", min_value=0.0, max_value=100.0, value=75.0, step=1.0)

    calc_prob = get_loser_streak_prob(calc_trades, calc_streak, calc_win_rate / 100.0)
    
    st.metric(
        label=f"Probability of experiencing at least {calc_streak} consecutive losses in {calc_trades} trades at {calc_win_rate:.2f}% win rate",
        value=f"{calc_prob:.4%}"
    )

# -----------------------------------------------------------------------------
# TAB 2: EDUCATIONAL GUIDE
# -----------------------------------------------------------------------------
with tab2:
    st.header("Quantitative Modeling & Options Mathematics")
    st.write(
        "This section details the theoretical models, formulas, and integration algorithms used "
        "to calculate advanced metrics (such as PoP, EV, and streak probabilities) throughout the application."
    )

    # Math details
    st.markdown("""
    ---
    ### 1. Probability Models & Stock Price Distributions
    Options payoff is non-linear and highly path-dependent. To model the asset's price distribution at expiration, we assume that stock prices follow a **Geometric Brownian Motion (GBM)**. This implies that the logarithm of the stock price at expiration $t$ is normally distributed (i.e., stock prices are **log-normally distributed**).

    Using the `scipy.stats.norm` mathematical engine, we compute the Probability Density Function (PDF) of the stock price at expiration using:
    """)

    st.latex(r"\mu = \ln(S_0) + \left(r - \frac{1}{2}\sigma^2\right) \cdot t")
    st.latex(r"\sigma_{dist} = \sigma \cdot \sqrt{t}")

    st.markdown(r"""
    Where:
    - $S_0$: Current spot price of the underlying asset
    - $r$: Risk-free interest rate (fixed at $5\%$)
    - $\sigma$: Volatility parameter, calculated as the weighted average Implied Volatility (IV) of all position legs
    - $t$: Time to option maturity in years, calculated as $\text{DTE} / 365$

    #### Probability Density Function (PDF)
    The probability density of the asset reaching price $S$ at expiration is given by:
    """)

    st.latex(r"f(S) = \frac{1}{S \sigma_{dist} \sqrt{2\pi}} e^{-\frac{(\ln(S) - \mu)^2}{2\sigma_{dist}^2}}")

    st.markdown("""
    ---
    ### 2. Probability of Profit (PoP)
    The **Probability of Profit (PoP)** represents the total theoretical probability that the strategy will result in a net credit/profit at expiration. It is computed by integrating the log-normal probability density function over all stock prices where the payoff is strictly positive:
    """)

    st.latex(r"\text{PoP} = \int_{S: \text{Payoff}(S) > 0} f(S) \, dS")

    st.markdown("""
    #### Numerical Integration Implementation
    Since options strategies can have multiple legs and complex payoff diagrams, the application uses **Riemann sum numerical integration**:
    """)

    st.latex(r"\text{PoP} \approx \sum_{S: \text{Payoff}(S) > 0} f(S) \cdot \Delta S")

    st.markdown(r"""
    - **Grid Generation**: The system dynamically creates a dense grid of $10,000$ points spanning from $1\%$ to $400\%$ of the current underlying spot price.
    - **Resolution ($\Delta S$)**: The width of each slice is the difference between consecutive price grid points.
    - **Evaluation**: For each price point, the strategy's exact expiration net payoff is evaluated. If the payoff is $> 0$, the area of the probability slice $f(S) \cdot \Delta S$ is added to the PoP sum.

    ---
    ### 3. Expected Value (EV)
    The **Expected Value (EV)** of a trade is the sum of all possible outcomes weighted by their respective probability of occurrence. It represents the average amount a trader can expect to win or lose per trade if the exact same trade was repeated thousands of times.
    """)

    st.latex(r"\text{EV} = \int_{0}^{\infty} \text{Payoff}(S) \cdot f(S) \, dS")

    st.markdown("""
    Using our numerical Riemann grid, the expected value is integrated as:
    """)

    st.latex(r"\text{EV} \approx \sum_{i=1}^{10000} \text{Payoff}(S_i) \cdot f(S_i) \cdot \Delta S")

    st.markdown(r"""
    A positive Expected Value ($\text{EV} > 0$) indicates a **mathematical edge**, while a negative EV suggests the strategy is a net loser over a long run, regardless of win rate.
    """)

    st.markdown(r"""
    ---
    ### 4. Streak Probability Mathematics
    To calculate the probability of experiencing at least $k$ consecutive losses in $N$ independent trials with win probability $q$ (and loss probability $p = 1 - q$), we use an **exact recurrence relation** rather than a simplified binomial or Poisson approximation.

    Let $A(n, k)$ be the probability of **not** encountering $k$ consecutive failures in $n$ trials.
    
    #### Recurrence Formula
    - For $n < k$: $A(n, k) = 1$ (it is impossible to have $k$ consecutive losses in fewer than $k$ trades).
    - For $n \ge k$:
    """)

    st.latex(r"A(n, k) = \sum_{j=1}^{k} p^{j-1} \cdot q \cdot A(n-j, k)")

    st.markdown(r"""
    Where:
    - $q$: Probability of a single success (Strike Rate)
    - $p$: Probability of a single failure ($1 - q$)
    - $p^{j-1} \cdot q$: The probability of starting with $j-1$ consecutive failures followed by a single success.

    #### Probability of experiencing a streak
    Once the non-streak probability $A(n, k)$ is determined, the probability of encountering **at least one** losing streak of length $k$ or more is:
    """)

    st.latex(r"\text{Probability of Streak} = 1 - A(N, k)")

    st.markdown("""
    This dynamic algorithm is implemented natively in the dashboard, ensuring absolute mathematical precision down to the smallest decimal place.
    """)
