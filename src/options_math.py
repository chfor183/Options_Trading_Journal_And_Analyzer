import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import norm

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

def generate_payoff_chart(legs, current_price, ticker=""):
    if not legs:
        return go.Figure()
        
    strikes = [leg['strike'] for leg in legs]
    min_strike = min(strikes) if strikes else current_price
    max_strike = max(strikes) if strikes else current_price
    
    lower_bound = max(0, min_strike * 0.5)
    upper_bound = max_strike * 1.5
    spot_prices = np.linspace(lower_bound, upper_bound, 1000)
    
    total_payoff = calculate_payoff_array(legs, spot_prices)
    
    fig = go.Figure()
    
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
    
    fig.add_vline(x=current_price, line_dash="dot", line_color="#0066cc")
    # Annotate current price
    fig.add_annotation(x=current_price, y=0, text=f"Current Price: {current_price:.2f}", textangle=90, showarrow=False, xanchor="left", yanchor="bottom", yshift=10)
    
    # Breakevens
    zero_crossings = np.where(np.diff(np.sign(total_payoff)))[0]
    for zc in zero_crossings:
        be_price = spot_prices[zc]
        fig.add_vline(x=be_price, line_dash="dot", line_color="red")
        fig.add_annotation(x=be_price, y=0, text=f"Breakeven: {be_price:.2f}", textangle=90, showarrow=False, xanchor="right", yanchor="bottom", yshift=10)

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
    
    return {
        "max_profit": max_profit,
        "max_loss": max_loss,
        "breakevens": breakevens,
        "pop": pop,
        "pop_max_profit": pop_max_profit,
        "pop_max_loss": pop_max_loss,
        "ev": ev,
        "er": er,
        "rr": rr
    }
