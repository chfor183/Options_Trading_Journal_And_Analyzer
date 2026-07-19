import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import norm

def calculate_bs_delta(S, K, T, r, sigma, option_type):
    if T <= 0 or sigma <= 0:
        if option_type.lower() == 'call':
            return 1.0 if S > K else 0.0
        else:
            return -1.0 if S < K else 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    if option_type.lower() == 'call':
        return norm.cdf(d1)
    else:
        return norm.cdf(d1) - 1.0

def calculate_payoff_array(legs, spot_prices):
    total_payoff = np.zeros_like(spot_prices)
    for leg in legs:
        multiplier = 1 if leg['action'].lower() == 'buy' else -1
        if leg['type'].lower() == 'call':
            payoff = np.maximum(0, spot_prices - leg['strike']) - leg['price']
        else:
            payoff = np.maximum(0, leg['strike'] - spot_prices) - leg['price']
        total_payoff += payoff * multiplier * leg['qty'] * 100
    return total_payoff

def generate_payoff_chart(legs, current_price, ticker="", open_price=None, current_price_label="Current Price", trade_date=None, show_current_em=True, show_open_em=True):
    if not legs:
        return go.Figure()
        
    strikes = [leg['strike'] for leg in legs]
    min_strike = min(strikes) if strikes else current_price
    max_strike = max(strikes) if strikes else current_price
    
    # Find exact breakeven points to determine custom chart boundaries
    # We find where payoff transitions from negative to positive or vice versa
    temp_prices = np.linspace(current_price * 0.05, current_price * 2.5, 5000)
    temp_payoffs = calculate_payoff_array(legs, temp_prices)
    crossings = np.where(np.diff(np.sign(temp_payoffs)))[0]
    bes = [temp_prices[zc] for zc in crossings]
    
    if bes:
        min_be, max_be = min(bes), max(bes)
        # Handle cases where breakevens are extremely close or equal to prevent flat bounds
        if max_be - min_be < 0.05 * current_price:
            lower_bound = max(0.0, min_be * 0.8)
            upper_bound = max_be * 1.2
        else:
            lower_bound = max(0.0, min_be * 0.8)
            upper_bound = max_be * 1.2
    else:
        # Default fallback to strikes if no breakeven crossings are found
        lower_bound = max(0.0, min_strike * 0.8)
        upper_bound = max_strike * 1.2

    # Calculate Expected Move range beforehand so we can use it for boundaries
    try:
        days_to_expiry = (pd.to_datetime(legs[0]['expiry']) - pd.Timestamp.now().normalize()).days
        if days_to_expiry <= 0: days_to_expiry = 1
    except:
        days_to_expiry = 30
        
    t = days_to_expiry / 365.0
    
    ivs = [leg.get('iv', 0) for leg in legs if leg.get('iv', 0) > 0]
    iv = np.mean(ivs) / 100.0 if ivs else 0.3
    
    expected_move = current_price * iv * np.sqrt(t)
    em_lower = current_price - expected_move
    em_upper = current_price + expected_move

    em_open_lower = None
    em_open_upper = None
    expected_move_open = None

    if trade_date and open_price:
        try:
            days_to_expiry_open = (pd.to_datetime(legs[0]['expiry']).date() - pd.to_datetime(trade_date).date()).days
            if days_to_expiry_open <= 0: days_to_expiry_open = 1
        except:
            days_to_expiry_open = 30
            
        t_open = days_to_expiry_open / 365.0
        expected_move_open = open_price * iv * np.sqrt(t_open)
        em_open_lower = open_price - expected_move_open
        em_open_upper = open_price + expected_move_open
        
        if show_open_em:
            lower_bound = min(lower_bound, em_open_lower * 0.95)
            upper_bound = max(upper_bound, em_open_upper * 1.05)

    # Ensure boundaries cover both current price and +/- 1 SD expected move
    if show_current_em:
        lower_bound = min(lower_bound, current_price * 0.95, em_lower * 0.95)
        upper_bound = max(upper_bound, current_price * 1.05, em_upper * 1.05)
        
    spot_prices = np.linspace(lower_bound, upper_bound, 1000)
    
    total_payoff = calculate_payoff_array(legs, spot_prices)
    
    fig = go.Figure()

    # Add Expected Move range with a premium semi-transparent blue
    if show_current_em:
        fig.add_vrect(
            x0=em_lower, x1=em_upper,
            fillcolor="rgba(59, 130, 246, 0.05)", opacity=1.0,
            layer="below", line_width=1, line_dash="dash", line_color="rgba(59, 130, 246, 0.35)"
        )
        
        # Beautiful non-overlapping box for the Expected Move metric
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            text=f"<b>Expected Move (±1 SD):</b> ±${expected_move:.2f} [${em_lower:.2f}, ${em_upper:.2f}]",
            showarrow=False,
            font=dict(size=12, color="#3b82f6", weight="bold"), # Bigger, bolder font
            align="left",
            bgcolor="rgba(15, 23, 42, 0.95)", # Darker, highly opaque slate background
            bordercolor="rgba(59, 130, 246, 0.8)", # Stronger border opacity
            borderwidth=1.5,
            borderpad=6
        )

    if show_open_em and em_open_lower is not None and em_open_upper is not None:
        fig.add_vrect(
            x0=em_open_lower, x1=em_open_upper,
            fillcolor="rgba(139, 92, 246, 0.05)", opacity=1.0,
            layer="below", line_width=1, line_dash="dash", line_color="rgba(139, 92, 246, 0.35)"
        )
        
        # Adjust y position based on whether the current EM is also displayed to prevent overlap
        y_pos = 0.88 if show_current_em else 0.98
        
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.02, y=y_pos,
            text=f"<b>Expected Move at Open (±1 SD):</b> ±${expected_move_open:.2f} [${em_open_lower:.2f}, ${em_open_upper:.2f}]",
            showarrow=False,
            font=dict(size=12, color="#8b5cf6", weight="bold"),
            align="left",
            bgcolor="rgba(15, 23, 42, 0.95)",
            bordercolor="rgba(139, 92, 246, 0.8)",
            borderwidth=1.5,
            borderpad=6
        )
    
    # Add fill above and below 0
    fig.add_trace(go.Scatter(
        x=spot_prices,
        y=np.where(total_payoff > 0, total_payoff, 0),
        fill='tozeroy',
        fillcolor='rgba(113, 203, 187, 0.8)', # Teal green
        line=dict(color='rgba(113, 203, 187, 1)', width=2),
        name='Profit'
    ))
    
    fig.add_trace(go.Scatter(
        x=spot_prices,
        y=np.where(total_payoff <= 0, total_payoff, 0),
        fill='tozeroy',
        fillcolor='rgba(255, 153, 153, 0.8)', # Light red
        line=dict(color='rgba(255, 100, 100, 1)', width=2),
        name='Loss'
    ))
    
    # Find breakeven crossings for annotations
    zero_crossings = np.where(np.diff(np.sign(total_payoff)))[0]
    bes_list = [spot_prices[zc] for zc in zero_crossings]
    
    # Determine default anchor alignments based on relation to breakeven points
    cp_anchor = "left"
    be_anchor = "right"
    if bes_list:
        avg_be = np.mean(bes_list)
        if current_price < avg_be:
            cp_anchor = "right"
            be_anchor = "left"
        else:
            cp_anchor = "left"
            be_anchor = "right"

    fig.add_vline(x=current_price, line_dash="dot", line_color="#0066cc")
    # Annotate current/close price at the top of the chart to prevent overlap
    fig.add_annotation(
        x=current_price, y=0.85, yref="paper",
        text=f"<b>{current_price_label}: {current_price:.2f}</b>", 
        textangle=90, showarrow=False, 
        xanchor=cp_anchor, yanchor="middle",
        font=dict(size=12, color="#3b82f6", weight="bold"), # Bigger, bolder font matching theme
        bgcolor="rgba(15, 23, 42, 0.95)", # Highly opaque background
        bordercolor="#3b82f6", borderwidth=1.5, borderpad=5
    )
    
    if open_price is not None:
        fig.add_vline(x=open_price, line_dash="dot", line_color="#8b5cf6")
        fig.add_annotation(
            x=open_price, y=0.02, yref="paper",
            text=f"<b>Open price: {open_price:.2f}</b>", 
            textangle=90, showarrow=False, 
            xanchor="right" if open_price > current_price else "left", yanchor="bottom",
            font=dict(size=12, color="#8b5cf6", weight="bold"),
            bgcolor="rgba(15, 23, 42, 0.95)",
            bordercolor="#8b5cf6", borderwidth=1.5, borderpad=5
        )
    
    # Breakevens annotated at the bottom of the chart
    for i_zc, be_price in enumerate(bes_list):
        fig.add_vline(x=be_price, line_dash="dot", line_color="red")
        
        # Determine specific anchor per breakeven if there are multiple, or fall back to general rule
        specific_be_anchor = be_anchor
        if len(bes_list) > 1:
            specific_be_anchor = "right" if be_price < current_price else "left"
            
        fig.add_annotation(
            x=be_price, y=0.15 + (i_zc * 0.1), yref="paper",
            text=f"<b>Breakeven: {be_price:.2f}</b>", 
            textangle=90, showarrow=False, 
            xanchor=specific_be_anchor, yanchor="middle",
            font=dict(size=12, color="#ef4444", weight="bold"), # Bigger, bolder red font
            bgcolor="rgba(15, 23, 42, 0.95)", # Highly opaque background
            bordercolor="#ef4444", borderwidth=1.5, borderpad=5
        )

    fig.add_hline(y=0, line_color="black", line_width=1)
    
    fig.update_layout(
        xaxis_title=f"{ticker} Price ($)" if ticker else "Underlying Price ($)",
        yaxis_title="Expected Profit & Loss ($)",
        template="plotly_white",
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    return fig

def calculate_metrics(legs, current_price):
    if not legs:
        return {}
        
    spot_prices = np.linspace(current_price * 0.01, current_price * 4, 10000)
    payoff = calculate_payoff_array(legs, spot_prices)
    
    max_profit = np.max(payoff)
    max_loss = np.min(payoff)
    
    if payoff[-1] > payoff[-2] + 0.01:
        max_profit = float('inf')
    if payoff[-1] < payoff[-2] - 0.01:
        max_loss = float('-inf')
    if payoff[0] > payoff[1] + 0.01:
        max_profit = float('inf')
    if payoff[0] < payoff[1] - 0.01:
        max_loss = float('-inf')
        
    zero_crossings = np.where(np.diff(np.sign(payoff)))[0]
    breakevens = [spot_prices[zc] for zc in zero_crossings]
    
    try:
        days_to_expiry = (pd.to_datetime(legs[0]['expiry']) - pd.Timestamp.now().normalize()).days
        if days_to_expiry <= 0: days_to_expiry = 1
    except:
        days_to_expiry = 30
        
    t = days_to_expiry / 365.0
    
    ivs = [leg.get('iv', 0) for leg in legs if leg.get('iv', 0) > 0]
    iv = np.mean(ivs) / 100.0 if ivs else 0.3
    
    r = 0.05
    
    mu = np.log(current_price) + (r - 0.5 * iv**2) * t
    sigma = iv * np.sqrt(t)
    
    dx = spot_prices[1] - spot_prices[0]
    pdf = (1 / (spot_prices * sigma * np.sqrt(2 * np.pi))) * np.exp(- (np.log(spot_prices) - mu)**2 / (2 * sigma**2))
    
    pop = np.sum(pdf[payoff > 0]) * dx
    pol = np.sum(pdf[payoff < 0]) * dx
    
    if max_profit != float('inf'):
        pop_max_profit = np.sum(pdf[np.isclose(payoff, max_profit, atol=2)]) * dx
    else:
        pop_max_profit = 0
        
    if max_loss != float('-inf'):
        pop_max_loss = np.sum(pdf[np.isclose(payoff, max_loss, atol=2)]) * dx
    else:
        pop_max_loss = 0
        
    ev = np.sum(pdf * payoff) * dx
    
    risk = abs(max_loss) if max_loss != float('-inf') else float('inf')
    er = ev / risk if risk != 0 else 0
    # User requested risk to reward ratio (Risk / Reward)
    rr = risk / max_profit if max_profit != 0 else float('inf')
    
    # Calculate Expected Move % using 1 std dev
    expected_move_pct = sigma

    return {
        "max_profit": max_profit,
        "max_loss": max_loss,
        "breakevens": breakevens,
        "pop": pop,
        "pol": pol,
        "pop_max_profit": pop_max_profit,
        "pop_max_loss": pop_max_loss,
        "ev": ev,
        "er": er,
        "rr": rr,
        "expected_move_pct": expected_move_pct
    }
