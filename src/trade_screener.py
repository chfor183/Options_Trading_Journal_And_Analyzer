import pandas as pd
import numpy as np
from datetime import datetime
from src.market_data import get_option_chain_for_date, get_ticker_info
from src.options_math import calculate_metrics

def find_best_trades(ticker, strategy, expiry, min_oi, min_vol, min_pop, max_spread_pct, min_roi, min_er):
    chain = get_option_chain_for_date(ticker, expiry)
    calls = chain.get('calls', pd.DataFrame())
    puts = chain.get('puts', pd.DataFrame())

    if calls.empty and puts.empty:
        return []

    if not calls.empty:
        calls['volume'] = calls['volume'].fillna(0)
        calls['openInterest'] = calls['openInterest'].fillna(0)
        calls_f = calls[(calls['volume'] >= min_vol) & (calls['openInterest'] >= min_oi)].sort_values('strike').reset_index(drop=True)
    else:
        calls_f = pd.DataFrame()

    if not puts.empty:
        puts['volume'] = puts['volume'].fillna(0)
        puts['openInterest'] = puts['openInterest'].fillna(0)
        puts_f = puts[(puts['volume'] >= min_vol) & (puts['openInterest'] >= min_oi)].sort_values('strike').reset_index(drop=True)
    else:
        puts_f = pd.DataFrame()

    info = get_ticker_info(ticker)
    current_price = info.get('current_price', 0)
    if current_price <= 0:
        return []

    parsed_expiry = datetime.strptime(expiry, "%Y-%m-%d").date()

    def make_leg(row, action, opt_type):
        bid = float(row['bid']) if pd.notna(row['bid']) else 0.0
        ask = float(row['ask']) if pd.notna(row['ask']) else 0.0
        last = float(row.get('lastPrice', 0.0))
        
        price = bid if action == 'Sell' and bid > 0 else (
                ask if action == 'Buy' and ask > 0 else last
        )
        return {
            'action': action,
            'qty': 1,
            'type': opt_type,
            'strike': float(row['strike']),
            'price': price,
            'bid': bid,
            'ask': ask,
            'iv': float(row['impliedVolatility']) * 100 if pd.notna(row['impliedVolatility']) else 0.0,
            'expiry': parsed_expiry,
            'delta': 0.0,
            'volume': int(row['volume']) if pd.notna(row.get('volume')) else 0,
            'oi': int(row['openInterest']) if pd.notna(row.get('openInterest')) else 0
        }

    combinations = []

    if strategy in ["Long Call (debit)", "Covered Call (credit)"]:
        action = "Buy" if "Long" in strategy else "Sell"
        for _, row in calls_f.iterrows():
            combinations.append([make_leg(row, action, "Call")])
            
    elif strategy in ["Long Put (debit)", "Cash-Secured Put (credit)"]:
        action = "Buy" if "Long" in strategy else "Sell"
        for _, row in puts_f.iterrows():
            combinations.append([make_leg(row, action, "Put")])

    elif strategy == "Bull Put Spread (credit)":
        for i in range(len(puts_f)):
            for w in range(1, min(15, len(puts_f) - i)):
                sell_leg = make_leg(puts_f.iloc[i+w], "Sell", "Put")
                buy_leg = make_leg(puts_f.iloc[i], "Buy", "Put")
                combinations.append([sell_leg, buy_leg])
                        
    elif strategy == "Bear Call Spread (credit)":
        for i in range(len(calls_f)):
            for w in range(1, min(15, len(calls_f) - i)):
                sell_leg = make_leg(calls_f.iloc[i], "Sell", "Call")
                buy_leg = make_leg(calls_f.iloc[i+w], "Buy", "Call")
                combinations.append([sell_leg, buy_leg])
                        
    elif strategy == "Bull Call Spread (debit)":
        for i in range(len(calls_f)):
            for w in range(1, min(15, len(calls_f) - i)):
                buy_leg = make_leg(calls_f.iloc[i], "Buy", "Call")
                sell_leg = make_leg(calls_f.iloc[i+w], "Sell", "Call")
                combinations.append([buy_leg, sell_leg])
                    
    elif strategy == "Bear Put Spread (debit)":
        for i in range(len(puts_f)):
            for w in range(1, min(15, len(puts_f) - i)):
                buy_leg = make_leg(puts_f.iloc[i+w], "Buy", "Put")
                sell_leg = make_leg(puts_f.iloc[i], "Sell", "Put")
                combinations.append([buy_leg, sell_leg])
                    
    elif "Iron Condor" in strategy:
        is_credit = "Short" in strategy
        put_spreads = []
        for i in range(len(puts_f)):
            for w in range(1, min(15, len(puts_f) - i)):
                leg1 = make_leg(puts_f.iloc[i+w], "Sell" if is_credit else "Buy", "Put")
                leg2 = make_leg(puts_f.iloc[i], "Buy" if is_credit else "Sell", "Put")
                if leg1['strike'] < current_price:
                    # Pre-filter for minimal estimated premium viability
                    net_est = ((leg1['bid'] + leg1['ask'])/2) - ((leg2['bid'] + leg2['ask'])/2)
                    if net_est > 0.05:
                        put_spreads.append([leg1, leg2])
        call_spreads = []
        for i in range(len(calls_f)):
            for w in range(1, min(15, len(calls_f) - i)):
                leg1 = make_leg(calls_f.iloc[i], "Sell" if is_credit else "Buy", "Call")
                leg2 = make_leg(calls_f.iloc[i+w], "Buy" if is_credit else "Sell", "Call")
                if leg1['strike'] > current_price:
                    # Pre-filter for minimal estimated premium viability
                    net_est = ((leg1['bid'] + leg1['ask'])/2) - ((leg2['bid'] + leg2['ask'])/2)
                    if net_est > 0.05:
                        call_spreads.append([leg1, leg2])
        
        for ps in put_spreads:
            for cs in call_spreads:
                # Require wings to not overlap
                if ps[0]['strike'] < cs[0]['strike']:
                    # Iron Condors are almost always traded with symmetrical widths
                    width_p = abs(ps[0]['strike'] - ps[1]['strike'])
                    width_c = abs(cs[0]['strike'] - cs[1]['strike'])
                    if abs(width_p - width_c) < 0.01:
                        condor = ps + cs
                        combinations.append(condor)

    # To prevent combinatorial explosion and freezing, sample evenly across 
    # the chain if we exceed 2,000 viable combinations.
    if len(combinations) > 2000:
        step = len(combinations) // 2000
        combinations = combinations[::step][:2000]

    valid_trades = []
    for legs in combinations:
        total_spread = sum(max(0, l['ask'] - l['bid']) for l in legs)
        gross_mid = sum(((l['ask'] + l['bid']) / 2) for l in legs)
        net_mid = sum(((l['ask'] + l['bid'])/2) * (1 if l['action'] == 'Buy' else -1) for l in legs)
        
        if abs(net_mid) < 0.01 or gross_mid <= 0: 
            continue
            
        spread_pct = total_spread / abs(net_mid)
        gross_spread_pct = total_spread / gross_mid
        
        if spread_pct > (max_spread_pct / 100.0):
            continue
            
        # VERY FAST PRE-FILTER: Estimate max loss and ROI algebraically 
        # to skip the 10,000-point array math for doomed trades.
        max_loss_est = 0
        max_profit_est = 0
        
        if strategy in ["Bull Put Spread (credit)", "Bear Call Spread (credit)"]:
            width = abs(legs[0]['strike'] - legs[1]['strike'])
            max_loss_est = width - abs(net_mid)
            max_profit_est = abs(net_mid)
        elif strategy in ["Bull Call Spread (debit)", "Bear Put Spread (debit)"]:
            width = abs(legs[0]['strike'] - legs[1]['strike'])
            max_loss_est = abs(net_mid)
            max_profit_est = width - abs(net_mid)
        elif "Iron Condor" in strategy:
            width_p = abs(legs[0]['strike'] - legs[1]['strike'])
            width_c = abs(legs[2]['strike'] - legs[3]['strike'])
            if "Short" in strategy:
                max_loss_est = max(width_p, width_c) - abs(net_mid)
                max_profit_est = abs(net_mid)
            else:
                max_loss_est = abs(net_mid)
                max_profit_est = max(width_p, width_c) - abs(net_mid)
            
        if max_loss_est > 0:
            roi_est = (max_profit_est / max_loss_est) * 100
            # If the best-case mathematical ROI is less than the user's minimum, skip it!
            if min_roi > 0 and roi_est < min_roi * 0.95:
                continue
            
        try:
            metrics = calculate_metrics(legs, current_price)
            pop = metrics.get('pop', 0) * 100
            if pop < min_pop:
                continue
                
            er = metrics.get('er', 0)
            
            # Basic sanity checks
            max_loss = metrics.get('max_loss', 0)
            max_profit = metrics.get('max_profit', 0)
            if max_loss == 0 and max_profit == 0:
                continue
                
            if max_loss == 0:
                roi = float('inf')
            elif max_profit == float('inf') and max_loss != float('-inf'):
                roi = float('inf')
            elif max_loss == float('-inf'):
                roi = 0.0
            else:
                roi = abs(max_profit / max_loss) * 100
                
            if min_roi > 0 and roi < min_roi:
                continue
                
            er_pct = er * 100
            if min_er > 0 and er_pct < min_er:
                continue
            
            valid_trades.append({
                'legs': legs,
                'pop': pop,
                'er': er,
                'spread_pct': spread_pct * 100,
                'gross_spread_pct': gross_spread_pct * 100,
                'metrics': metrics,
                'underlying_price': current_price,
                'expected_move': [
                    current_price * (1 - metrics.get('expected_move_pct', 0)),
                    current_price * (1 + metrics.get('expected_move_pct', 0))
                ],
                'volume': sum(l.get('volume', 0) for l in legs),
                'oi': min((l.get('oi', 0) for l in legs), default=0)
            })
        except Exception as e:
            continue

    valid_trades.sort(key=lambda x: (x['pop'], x['er']), reverse=True)
    return valid_trades[:5]