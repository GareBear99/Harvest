#!/usr/bin/env python3
"""Accurate 7-day backtest using real 1-minute data."""

import json
from datetime import datetime
from collections import defaultdict

print('=' * 80)
print('HARVEST - 7-DAY ACCURATE BACKTEST')
print('=' * 80)

# Load minute data
print('\nLoading 1-minute data...')
with open('data/minute_data_7days.json', 'r') as f:
    data = json.load(f)

candles = data['candles']
print(f'Loaded {len(candles):,} 1-minute candles')
print(f'Period: {data["start_time"][:10]} to {data["end_time"][:10]}')

# Starting capital
capital = 10.0
print(f'Starting capital: ${capital:.2f}')

# Strategy configurations
strategies = {
    'ER-90': {
        'tp_pct': 1.0,
        'sl_pct': 0.75,
        'position_pct': 0.95,
        'check_every_minutes': 60,  # Check once per hour
        'signals': 0
    },
    'SCALPER': {
        'tp_pct': 0.4,
        'sl_pct': 0.3,
        'position_pct': 0.95,
        'check_every_minutes': 5,  # Check every 5 minutes
        'signals': 0
    },
    'MOMENTUM': {
        'tp_pct': 0.7,
        'sl_pct': 0.4,
        'position_pct': 0.95,
        'check_every_minutes': 15,  # Check every 15 minutes
        'signals': 0
    }
}

# Simulate trades
print(f'\n{"=" * 80}')
print('SIMULATING TRADES')
print('=' * 80)

trades = []
current_equity = capital

# Price movement analysis for signal generation
for i in range(len(candles)):
    candle = candles[i]
    price = candle['close']
    timestamp = datetime.fromisoformat(candle['timestamp'])
    
    # Check each strategy on its interval
    for strategy_name, params in strategies.items():
        # Only check at intervals
        if i % params['check_every_minutes'] != 0:
            continue
        
        # Simple signal generation based on price movements
        # Look at recent 5-minute change
        if i >= 5:
            recent_prices = [candles[j]['close'] for j in range(i-5, i+1)]
            price_change = ((recent_prices[-1] / recent_prices[0]) - 1) * 100
            
            # Generate signal based on momentum
            signal = None
            if abs(price_change) > 0.3:  # Some movement detected
                if price_change > 0:
                    signal = 'LONG'
                else:
                    signal = 'SHORT'
            
            if signal:
                # Simulate trade
                position_size = current_equity * params['position_pct']
                tp_price = price * (1 + params['tp_pct']/100 if signal == 'LONG' else 1 - params['tp_pct']/100)
                sl_price = price * (1 - params['sl_pct']/100 if signal == 'LONG' else 1 + params['sl_pct']/100)
                
                # Look ahead to see if TP or SL hit (simplified)
                trade_result = None
                exit_price = None
                exit_time = None
                
                for j in range(i+1, min(i+60, len(candles))):  # Check next 60 minutes
                    future_candle = candles[j]
                    high = future_candle['high']
                    low = future_candle['low']
                    
                    if signal == 'LONG':
                        if high >= tp_price:
                            trade_result = 'WIN'
                            exit_price = tp_price
                            exit_time = datetime.fromisoformat(future_candle['timestamp'])
                            break
                        elif low <= sl_price:
                            trade_result = 'LOSS'
                            exit_price = sl_price
                            exit_time = datetime.fromisoformat(future_candle['timestamp'])
                            break
                    else:  # SHORT
                        if low <= tp_price:
                            trade_result = 'WIN'
                            exit_price = tp_price
                            exit_time = datetime.fromisoformat(future_candle['timestamp'])
                            break
                        elif high >= sl_price:
                            trade_result = 'LOSS'
                            exit_price = sl_price
                            exit_time = datetime.fromisoformat(future_candle['timestamp'])
                            break
                
                if trade_result:
                    # Calculate P&L
                    if trade_result == 'WIN':
                        pnl = position_size * (params['tp_pct'] / 100)
                    else:
                        pnl = -position_size * (params['sl_pct'] / 100)
                    
                    current_equity += pnl
                    
                    trades.append({
                        'strategy': strategy_name,
                        'entry_time': timestamp,
                        'exit_time': exit_time,
                        'side': signal,
                        'entry_price': price,
                        'exit_price': exit_price,
                        'result': trade_result,
                        'pnl': pnl,
                        'equity_after': current_equity
                    })
                    
                    params['signals'] += 1

# Results
print(f'\nSimulation complete!')
print(f'\nTotal trades executed: {len(trades)}')

# Strategy breakdown
for strategy_name, params in strategies.items():
    strategy_trades = [t for t in trades if t['strategy'] == strategy_name]
    wins = [t for t in strategy_trades if t['result'] == 'WIN']
    losses = [t for t in strategy_trades if t['result'] == 'LOSS']
    
    if strategy_trades:
        win_rate = len(wins) / len(strategy_trades) * 100
        total_pnl = sum(t['pnl'] for t in strategy_trades)
        
        print(f'\n{strategy_name}:')
        print(f'  Trades: {len(strategy_trades)}')
        print(f'  Wins: {len(wins)} | Losses: {len(losses)}')
        print(f'  Win Rate: {win_rate:.1f}%')
        print(f'  P&L: ${total_pnl:+.4f}')

print(f'\n{"=" * 80}')
print('FINAL RESULTS')
print('=' * 80)

total_pnl = current_equity - capital
total_return = (total_pnl / capital) * 100
wins = [t for t in trades if t['result'] == 'WIN']
losses = [t for t in trades if t['result'] == 'LOSS']

print(f'\nStarting capital: ${capital:.2f}')
print(f'Ending capital: ${current_equity:.2f}')
print(f'Total P&L: ${total_pnl:+.4f}')
print(f'Total return: {total_return:+.2f}%')

if trades:
    print(f'\nTrade stats:')
    print(f'  Total: {len(trades)}')
    print(f'  Wins: {len(wins)} ({len(wins)/len(trades)*100:.1f}%)')
    print(f'  Losses: {len(losses)} ({len(losses)/len(trades)*100:.1f}%)')
    print(f'  Average per trade: ${total_pnl/len(trades):+.4f}')

# Daily breakdown
days_traded = 7
daily_avg = total_pnl / days_traded
print(f'\nDaily average: ${daily_avg:+.4f} ({(daily_avg/capital)*100:+.2f}%)')

# Project forward
print(f'\n{"=" * 80}')
print('PROJECTIONS')
print('=' * 80)

print(f'\nIf these results continue:')
print(f'  Weekly: ${daily_avg * 5:+.2f}')
print(f'  Monthly: ${daily_avg * 20:+.2f}')

if daily_avg > 0:
    days_to_double = capital / daily_avg
    print(f'  Days to double: {int(days_to_double)}')

print('=' * 80)
