import streamlit as st
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go

# Page setup

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

    st.markdown(r"""
    ---
    ### 2. Price Distribution Comparison
    To visualize how Time to Expiration (DTE) affects the probability distribution of the underlying stock price, we can compare a short-term option (e.g., **DTE 10**) and a long-term option (e.g., **DTE 100**).
    
    Over a shorter time frame, there is less time for the price to diffuse, creating a tall, narrow probability density. Over a longer time frame, the price has more time to move, which flattens and widens the distribution, shifting the peak (mode) to the left due to the log-normal asymmetry.

    #### Lognormal Distribution Statistics
    Due to the asymmetric shape of the log-normal distribution, key statistical metrics of central tendency and dispersion diverge as time to expiration ($t$) increases:
    - **Mean (Expected Value)**: $E[S] = S_0 e^{r t}$. This is the risk-neutral expected value of the asset price at expiration, which drifts upward over time at the risk-free interest rate $r$.
    - **Median (50th Percentile)**: $\text{Median} = e^{\mu} = S_0 e^{(r - \frac{1}{2}\sigma^2) t}$. Exactly $50\%$ of the potential outcomes fall below this price, and $50\%$ above.
    - **Mode (Peak Density)**: $\text{Mode} = e^{\mu - \sigma_{dist}^2} = S_0 e^{(r - \frac{3}{2}\sigma^2) t}$. This is the single most probable price at expiration, represented by the peak of the probability density curve.
    - **Standard Deviation (Price SD)**: $\text{SD} = E[S] \sqrt{e^{\sigma_{dist}^2} - 1} = S_0 e^{r t} \sqrt{e^{\sigma^2 t} - 1}$. This measures absolute price dispersion in dollar terms.
    """)

    # Interactive Controls
    st.write("#### ⚙️ Configure Distribution Parameters")
    col_dist1, col_dist2, col_dist3 = st.columns(3)
    with col_dist1:
        spot_price_dist = st.number_input(
            "Underlying Spot Price ($S_0$):",
            min_value=1.0,
            max_value=10000.0,
            value=100.0,
            step=5.0,
            key="dist_spot"
        )
    with col_dist2:
        iv_dist = st.slider(
            "Implied Volatility (Annualized IV %):",
            min_value=5.0,
            max_value=150.0,
            value=25.0,
            step=1.0,
            key="dist_iv"
        ) / 100.0
    with col_dist3:
        r_dist = st.slider(
            "Risk-Free Interest Rate (%):",
            min_value=0.0,
            max_value=15.0,
            value=5.0,
            step=0.5,
            key="dist_r"
        ) / 100.0

    col_dte1, col_dte2 = st.columns(2)
    with col_dte1:
        dte_short = st.slider(
            "Short-term DTE (DTE 1):",
            min_value=1,
            max_value=365,
            value=10,
            step=1,
            key="dist_dte_short"
        )
    with col_dte2:
        dte_long = st.slider(
            "Long-term DTE (DTE 2):",
            min_value=1,
            max_value=365,
            value=100,
            step=1,
            key="dist_dte_long"
        )

    show_lines = st.multiselect(
        "🎯 Select statistical markers to overlay on the chart:",
        options=["Mean", "Median", "Mode", "1-SD Range (Exact)"],
        default=["1-SD Range (Exact)"],
        key="dist_show_lines",
        help="Overlay vertical lines or shaded regions for the chosen statistical measures of both distributions on the chart."
    )

    # Calculate distributions
    t_short = dte_short / 365.0
    t_long = dte_long / 365.0

    # We want a dynamic price grid that covers both distributions nicely.
    # The long-term distribution will have a wider variance.
    # Standard deviation of log-price for long term:
    sigma_log_long = iv_dist * math.sqrt(t_long)
    mu_log_long = math.log(spot_price_dist) + (r_dist - 0.5 * iv_dist**2) * t_long

    # Standard deviation of log-price for short term:
    sigma_log_short = iv_dist * math.sqrt(t_short)
    mu_log_short = math.log(spot_price_dist) + (r_dist - 0.5 * iv_dist**2) * t_short

    # Exact metrics for overlays
    mean_short = spot_price_dist * math.exp(r_dist * t_short)
    median_short = math.exp(mu_log_short)
    mode_short = math.exp(mu_log_short - sigma_log_short**2)
    exact_lower_short = math.exp(mu_log_short - sigma_log_short)
    exact_upper_short = math.exp(mu_log_short + sigma_log_short)

    mean_long = spot_price_dist * math.exp(r_dist * t_long)
    median_long = math.exp(mu_log_long)
    mode_long = math.exp(mu_log_long - sigma_log_long**2)
    exact_lower_long = math.exp(mu_log_long - sigma_log_long)
    exact_upper_long = math.exp(mu_log_long + sigma_log_long)
    
    # Cover 4 standard deviations on each side of the long-term distribution
    # to capture virtually the entire density.
    grid_min = max(1.0, math.exp(mu_log_long - 4 * sigma_log_long))
    grid_max = math.exp(mu_log_long + 4 * sigma_log_long)
    
    price_grid = np.linspace(grid_min, grid_max, 1000)

    # Function to compute exact lognormal PDF
    def get_lognormal_pdf(s, s0, sigma, t, r):
        if t <= 0 or sigma <= 0 or s0 <= 0:
            return np.zeros_like(s)
        mu = np.log(s0) + (r - 0.5 * sigma**2) * t
        sigma_dist = sigma * np.sqrt(t)
        # Avoid division by zero
        s_safe = np.where(s <= 0, 1e-5, s)
        pdf = (1.0 / (s_safe * sigma_dist * np.sqrt(2 * np.pi))) * np.exp(-((np.log(s_safe) - mu)**2) / (2 * sigma_dist**2))
        return pdf

    pdf_short = get_lognormal_pdf(price_grid, spot_price_dist, iv_dist, t_short, r_dist)
    pdf_long = get_lognormal_pdf(price_grid, spot_price_dist, iv_dist, t_long, r_dist)

    # Create the Plotly chart
    fig_dist = go.Figure()

    # Plot short-term distribution
    fig_dist.add_trace(go.Scatter(
        x=price_grid,
        y=pdf_short,
        mode='lines',
        name=f"Short-term (DTE {dte_short})",
        line=dict(color='#1f77b4', width=3),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.15)'
    ))

    # Plot long-term distribution
    fig_dist.add_trace(go.Scatter(
        x=price_grid,
        y=pdf_long,
        mode='lines',
        name=f"Long-term (DTE {dte_long})",
        line=dict(color='#ff7f0e', width=3),
        fill='tozeroy',
        fillcolor='rgba(255, 127, 14, 0.15)'
    ))

    # Add vertical line for Spot Price
    fig_dist.add_vline(
        x=spot_price_dist,
        line_dash="dash",
        line_color="#7f7f7f",
        annotation_text="Current Spot Price",
        annotation_position="top right",
        annotation_y=0.95
    )

    # Statistical overlays
    if "Mean" in show_lines:
        fig_dist.add_vline(
            x=mean_short,
            line_dash="dash",
            line_color="rgba(31, 119, 180, 0.8)",
            annotation_text=f"Mean (S): ${mean_short:.1f}",
            annotation_position="top right",
            annotation_y=0.85
        )
        fig_dist.add_vline(
            x=mean_long,
            line_dash="dash",
            line_color="rgba(255, 127, 14, 0.8)",
            annotation_text=f"Mean (L): ${mean_long:.1f}",
            annotation_position="top right",
            annotation_y=0.45
        )

    if "Median" in show_lines:
        fig_dist.add_vline(
            x=median_short,
            line_dash="dot",
            line_color="rgba(31, 119, 180, 0.8)",
            annotation_text=f"Med (S): ${median_short:.1f}",
            annotation_position="top left",
            annotation_y=0.75
        )
        fig_dist.add_vline(
            x=median_long,
            line_dash="dot",
            line_color="rgba(255, 127, 14, 0.8)",
            annotation_text=f"Med (L): ${median_long:.1f}",
            annotation_position="top left",
            annotation_y=0.35
        )

    if "Mode" in show_lines:
        fig_dist.add_vline(
            x=mode_short,
            line_dash="dashdot",
            line_color="rgba(31, 119, 180, 0.8)",
            annotation_text=f"Mode (S): ${mode_short:.1f}",
            annotation_position="top left",
            annotation_y=0.65
        )
        fig_dist.add_vline(
            x=mode_long,
            line_dash="dashdot",
            line_color="rgba(255, 127, 14, 0.8)",
            annotation_text=f"Mode (L): ${mode_long:.1f}",
            annotation_position="top left",
            annotation_y=0.25
        )

    if "1-SD Range (Exact)" in show_lines:
        # Shaded region for Short-term 1-SD Range
        fig_dist.add_vrect(
            x0=exact_lower_short,
            x1=exact_upper_short,
            fillcolor="rgba(31, 119, 180, 0.04)",
            line=dict(color="rgba(31, 119, 180, 0.25)", width=1, dash="dot"),
            annotation_text="Short 1-SD",
            annotation_position="inside top left"
        )
        # Shaded region for Long-term 1-SD Range
        fig_dist.add_vrect(
            x0=exact_lower_long,
            x1=exact_upper_long,
            fillcolor="rgba(255, 127, 14, 0.04)",
            line=dict(color="rgba(255, 127, 14, 0.25)", width=1, dash="dot"),
            annotation_text="Long 1-SD",
            annotation_position="inside top right"
        )

    fig_dist.update_layout(
        title=dict(
            text=f"Log-Normal Stock Price Probability Density at Expiration (Spot: ${spot_price_dist})",
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Stock Price ($)",
        yaxis_title="Probability Density",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_dist, use_container_width=True)

    # Metrics comparison tables
    # Calculate exact statistics
    def calc_stats(s0, sigma, t, r, dte):
        mu_log = math.log(s0) + (r - 0.5 * sigma**2) * t
        sigma_log = sigma * math.sqrt(t)
        
        # Exact 1-SD range
        exact_lower = math.exp(mu_log - sigma_log)
        exact_upper = math.exp(mu_log + sigma_log)
        
        # Linear/Symmetric expected move
        expected_move = s0 * sigma * math.sqrt(t)
        linear_lower = s0 - expected_move
        linear_upper = s0 + expected_move
        
        # Peak of distribution (Mode)
        mode = math.exp(mu_log - sigma_log**2)
        # Median of distribution (50th Percentile)
        median = math.exp(mu_log)
        # Expected value (Mean of lognormal is e^(mu + sigma^2/2) = s0 * e^(rt))
        mean = s0 * math.exp(r * t)
        # Standard deviation of the log-normal price distribution in dollars ($)
        price_sd_dollar = mean * math.sqrt(math.exp(sigma_log**2) - 1)
        
        return {
            "DTE": dte,
            "Mode (Peak)": f"\\${mode:.2f}",
            "Median (50% Prob)": f"\\${median:.2f}",
            "Mean (Expected Value)": f"\\${mean:.2f}",
            "Price Std Dev ($)": f"\\${price_sd_dollar:.2f}",
            "Log-Price Std Dev (σ_dist)": f"{sigma_log:.4f}",
            "Expected Move (±1 SD)": f"±\\${expected_move:.2f}",
            "Standard Linear 1-SD Range": f"\\${linear_lower:.2f} - \\${linear_upper:.2f}",
            "Exact Log-Normal 1-SD Range": f"\\${exact_lower:.2f} - \\${exact_upper:.2f}"
        }

    stats_short = calc_stats(spot_price_dist, iv_dist, t_short, r_dist, dte_short)
    stats_long = calc_stats(spot_price_dist, iv_dist, t_long, r_dist, dte_long)

    df_stats = pd.DataFrame([stats_short, stats_long]).set_index("DTE")

    st.subheader("📊 Distribution Comparison Metrics Table")
    st.write(
        "Below is a comparison of key metrics derived from both distributions. Note how the "
        "**Exact Log-Normal 1-SD Range** is asymmetric, reflecting that stock prices cannot fall below \\$0 "
        "but have theoretically unlimited upside, whereas the standard linear approximation assumes a symmetric normal distribution."
    )
    st.table(df_stats)

    st.info(
        "💡 **Key Insights & Trader Application**:\n\n"
        f"1. **Peak Shifting & Central Tendency Divergence**: Notice that for the longer-term DTE {dte_long} distribution, the Mode (Peak) is at "
        f"**{stats_long['Mode (Peak)']}**, the Median (50% probability) is at **{stats_long['Median (50% Prob)']}**, and the Mean (Expected Value) is at **{stats_long['Mean (Expected Value)']}**. "
        f"Even though the spot price is **\\${spot_price_dist:.2f}**, the most probable outcome (Mode) shifts to the left, while the mean drifts upwards. "
        "This is a direct mathematical consequence of the log-normal distribution asymmetry: the right tail is unbounded, dragging the Mean above the Median and Mode.\n\n"
        f"2. **Standard Deviation & Volatility**: The absolute standard deviation of the price at expiration scales with time. "
        f"For DTE {dte_short}, the price standard deviation is only **{stats_short['Price Std Dev ($)']}**, whereas for DTE {dte_long} it increases to **{stats_long['Price Std Dev ($)']}**. "
        "This shows how uncertainty expands non-linearly with longer durations.\n\n"
        f"3. **Premium Decay (Theta)**: Over the first 265 days (going from DTE 365 to DTE 100), the distribution widens slowly. "
        "But as we transition from **DTE 100 to DTE 10**, the distribution dramatically narrows and spikes. This rapid concentration of probability "
        "corresponds to the non-linear acceleration of **Theta decay** as expiration approaches.\n\n"
        f"4. **Probability of Profit (PoP)**: This widening of the probability density explains why selling out-of-the-money options "
        "with higher DTE has a wider safety buffer (more price movement is required to breach the strikes) but also why "
        "short DTE options can yield rapid profit if the price remains stable."
    )

    st.markdown("""
    ---
    ### 3. Probability of Profit (PoP)
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
    - **// Evaluation**: For each price point, the strategy's exact expiration net payoff is evaluated. If the payoff is $> 0$, the area of the probability slice $f(S) \cdot \Delta S$ is added to the PoP sum.

    ---
    ### 4. Expected Value (EV)
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
    ### 5. Streak Probability Mathematics
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
