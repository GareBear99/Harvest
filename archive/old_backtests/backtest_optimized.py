#!/usr/bin/env python3
"""Optimized backtest with real indicator logic on 7-day data."""

import json
import sys
sys.path.insert(0, '.')

from core.indicators_backtest import BacktestIndicators
from datetime import datetime

print('=' * 80)
print('HARVEST - OPTIMIZED BACKTEST (Real Indicators)')
print('=' * 80)

# Load minute data
print('\nLoading data...')
with open('data/minute_data_7days.json', 'r') as f:
    data = json.load(f)

minute_candles = data['candles']
print(f'Loaded {len(minute_candles):,} 1-minute candles')
print(f'Period: {data["start_time"][:10]} to {data["end_time"][:10]}')

# Aggregate to multiple timeframes
print('\nAggregating timeframes...')
candles_5m = BacktestIndicators.aggregate_candles(minute_candles, 5)
candles_15m = BacktestIndicators.aggregate_candles(minute_candles, 15)
candles_1h = BacktestIndicators.aggregate_candles(minute_candles, 60)
candles_4h = BacktestIndicators.aggregate_candles(minute_candles, 240)

print(f'5m candles: {len(candles_5m)}')
print(f'15m candles: {len(candles_15m)}')
print(f'1h candles: {len(candles_1h)}')
print(f'4h candles: {len(candles_4h)}')

# Starting capital
capital = 10.0
current_equity = capital
trades = []

print(f'\nStarting capital: ${capital:.2f}')

# Strategy parameters
strategies_config = {
    'ER-90': {
        'enabled': True,
        'tp_pct': 1.0,
        'sl_pct': 0.75,
        'position_pct': 0.95
    },
    'SCALPER': {
        'enabled': True,
        'tp_pct': 0.4,
        'sl_pct': 0.3,
        'position_pct': 0.95
    },
    'MOMENTUM': {
        'enabled': True,
        'tp_pct': 0.7,
        'sl_pct': 0.4,
        'position_pct': 0.95
    }
}

print(f'\n{"=" * 80}')
print('RUNNING OPTIMIZED BACKTEST')
print('=' * 80)

# Main backtest loop - check every 5 minutes
for i in range(50, len(candles_5m)):  # Start after warmup
    current_5m = candles_5m[:i+1]
    current_price = current_5m[-1]['close']
    timestamp_str = current_5m[-1]['timestamp']
    timestamp = datetime.fromisoformat(timestamp_str)
    
    # Get corresponding 15m, 1h, 4h data
    current_15m = [c for c in candles_15m if c['timestamp'] <= timestamp_str]
    current_1h = [c for c in candles_1h if c['timestamp'] <= timestamp_str]
    current_4h = [c for c in candles_4h if c['timestamp'] <= timestamp_str]
    
    if len(current_1h) < 20 or len(current_4h) < 10:
        continue
    
    # Classify regime
    regime = BacktestIndicators.classify_regime(current_4h)
    
    # Reduce position size in drawdown but don't skip entirely
    position_multiplier = 0.5 if regime == 'DRAWDOWN' else 1.0
    
    # ===== ER-90 STRATEGY =====
    if strategies_config['ER-90']['enabled'] and i % 12 == 0:  # Check every hour
        closes_5m = [c['close'] for c in current_5m[-50:]]
        closes_1h = [c['close'] for c in current_1h[-50:]]
        
        rsi_5m = BacktestIndicators.rsi(closes_5m, 5)
        rsi_1h = BacktestIndicators.rsi(closes_1h, 5)
        
        signal = None
        # LONG: Oversold on 5m (relaxed from 35 to 45)
        if rsi_5m < 45:
            signal = 'LONG'
        # SHORT: Overbought on 5m (relaxed from 65 to 55)
        elif rsi_5m > 55:
            signal = 'SHORT'
        
        if signal:  # Trade in all regimes
            params = strategies_config['ER-90']
            position_size = current_equity * params['position_pct'] * position_multiplier
            
            tp_price = current_price * (1 + params['tp_pct']/100 if signal == 'LONG' else 1 - params['tp_pct']/100)
            sl_price = current_price * (1 - params['sl_pct']/100 if signal == 'LONG' else 1 + params['sl_pct']/100)
            
            # Look ahead for exit
            exit_idx = min(i + 60, len(candles_5m))  # Check next 5 hours
            for j in range(i+1, exit_idx):
                future = candles_5m[j]
                
                if signal == 'LONG':
                    if future['high'] >= tp_price:
                        pnl = position_size * (params['tp_pct'] / 100)
                        current_equity += pnl
                        trades.append({
                            'strategy': 'ER-90', 'side': signal, 'result': 'WIN',
                            'entry': current_price, 'exit': tp_price, 'pnl': pnl
                        })
                        break
                    elif future['low'] <= sl_price:
                        pnl = -position_size * (params['sl_pct'] / 100)
                        current_equity += pnl
                        trades.append({
                            'strategy': 'ER-90', 'side': signal, 'result': 'LOSS',
                            'entry': current_price, 'exit': sl_price, 'pnl': pnl
                        })
                        break
                else:  # SHORT
                    if future['low'] <= tp_price:
                        pnl = position_size * (params['tp_pct'] / 100)
                        current_equity += pnl
                        trades.append({
                            'strategy': 'ER-90', 'side': signal, 'result': 'WIN',
                            'entry': current_price, 'exit': tp_price, 'pnl': pnl
                        })
                        break
                    elif future['high'] >= sl_price:
                        pnl = -position_size * (params['sl_pct'] / 100)
                        current_equity += pnl
                        trades.append({
                            'strategy': 'ER-90', 'side': signal, 'result': 'LOSS',
                            'entry': current_price, 'exit': sl_price, 'pnl': pnl
                        })
                        break
    
    # ===== SCALPER STRATEGY =====
    if strategies_config['SCALPER']['enabled']:
        closes_5m = [c['close'] for c in current_5m[-30:]]
        
        if len(closes_5m) >= 20:
            rsi_7 = BacktestIndicators.rsi(closes_5m, 7)
            ema_20 = BacktestIndicators.ema(closes_5m, 20)
            vol_avg = BacktestIndicators.volume_average(current_5m[-10:], 10)
            current_vol = current_5m[-1]['volume']
            
            # RSI crossing 50 + price near EMA + volume (relaxed)
            price_near_ema = abs(current_price - ema_20) / current_price < 0.005  # Relaxed from 0.002
            volume_ok = current_vol >= vol_avg * 0.5  # Relaxed from 0.8
            
            rsi_prev = BacktestIndicators.rsi(closes_5m[:-1], 7)
            
            signal = None
            if rsi_prev < 50 and rsi_7 >= 50 and price_near_ema and volume_ok:
                signal = 'LONG'
            elif rsi_prev > 50 and rsi_7 <= 50 and price_near_ema and volume_ok:
                signal = 'SHORT'
            
            if signal:
                params = strategies_config['SCALPER']
                position_size = current_equity * params['position_pct'] * position_multiplier
                
                tp_price = current_price * (1 + params['tp_pct']/100 if signal == 'LONG' else 1 - params['tp_pct']/100)
                sl_price = current_price * (1 - params['sl_pct']/100 if signal == 'LONG' else 1 + params['sl_pct']/100)
                
                # Look ahead
                exit_idx = min(i + 12, len(candles_5m))  # Next hour
                for j in range(i+1, exit_idx):
                    future = candles_5m[j]
                    
                    if signal == 'LONG':
                        if future['high'] >= tp_price:
                            pnl = position_size * (params['tp_pct'] / 100)
                            current_equity += pnl
                            trades.append({
                                'strategy': 'SCALPER', 'side': signal, 'result': 'WIN',
                                'entry': current_price, 'exit': tp_price, 'pnl': pnl
                            })
                            break
                        elif future['low'] <= sl_price:
                            pnl = -position_size * (params['sl_pct'] / 100)
                            current_equity += pnl
                            trades.append({
                                'strategy': 'SCALPER', 'side': signal, 'result': 'LOSS',
                                'entry': current_price, 'exit': sl_price, 'pnl': pnl
                            })
                            break
                    else:  # SHORT
                        if future['low'] <= tp_price:
                            pnl = position_size * (params['tp_pct'] / 100)
                            current_equity += pnl
                            trades.append({
                                'strategy': 'SCALPER', 'side': signal, 'result': 'WIN',
                                'entry': current_price, 'exit': tp_price, 'pnl': pnl
                            })
                            break
                        elif future['high'] >= sl_price:
                            pnl = -position_size * (params['sl_pct'] / 100)
                            current_equity += pnl
                            trades.append({
                                'strategy': 'SCALPER', 'side': signal, 'result': 'LOSS',
                                'entry': current_price, 'exit': sl_price, 'pnl': pnl
                            })
                            break
    
    # ===== MOMENTUM STRATEGY =====
    if strategies_config['MOMENTUM']['enabled'] and i % 3 == 0:  # Check every 15min
        if len(current_5m) >= 30 and len(current_15m) >= 20:
            closes_5m = [c['close'] for c in current_5m[-30:]]
            closes_15m = [c['close'] for c in current_15m[-20:]]
            
            # EMA crossover on 5m
            crossover = BacktestIndicators.detect_ema_crossover(closes_5m, 9, 21)
            
            # RSI neutral zone (relaxed)
            rsi_5m = BacktestIndicators.rsi(closes_5m, 14)
            rsi_neutral = 40 <= rsi_5m <= 70  # Relaxed from 45-65
            
            # 15m trend confirmation
            ema_15m = BacktestIndicators.ema(closes_15m, 20)
            
            signal = None
            if crossover == 'bullish' and rsi_neutral and current_price > ema_15m:
                signal = 'LONG'
            elif crossover == 'bearish' and rsi_neutral and current_price < ema_15m:
                signal = 'SHORT'
            
            if signal:  # Trade in all regimes
                params = strategies_config['MOMENTUM']
                position_size = current_equity * params['position_pct'] * position_multiplier
                
                tp_price = current_price * (1 + params['tp_pct']/100 if signal == 'LONG' else 1 - params['tp_pct']/100)
                sl_price = current_price * (1 - params['sl_pct']/100 if signal == 'LONG' else 1 + params['sl_pct']/100)
                
                # Look ahead
                exit_idx = min(i + 24, len(candles_5m))  # Next 2 hours
                for j in range(i+1, exit_idx):
                    future = candles_5m[j]
                    
                    if signal == 'LONG':
                        if future['high'] >= tp_price:
                            pnl = position_size * (params['tp_pct'] / 100)
                            current_equity += pnl
                            trades.append({
                                'strategy': 'MOMENTUM', 'side': signal, 'result': 'WIN',
                                'entry': current_price, 'exit': tp_price, 'pnl': pnl
                            })
                            break
                        elif future['low'] <= sl_price:
                            pnl = -position_size * (params['sl_pct'] / 100)
                            current_equity += pnl
                            trades.append({
                                'strategy': 'MOMENTUM', 'side': signal, 'result': 'LOSS',
                                'entry': current_price, 'exit': sl_price, 'pnl': pnl
                            })
                            break
                    else:  # SHORT
                        if future['low'] <= tp_price:
                            pnl = position_size * (params['tp_pct'] / 100)
                            current_equity += pnl
                            trades.append({
                                'strategy': 'MOMENTUM', 'side': signal, 'result': 'WIN',
                                'entry': current_price, 'exit': tp_price, 'pnl': pnl
                            })
                            break
                        elif future['high'] >= sl_price:
                            pnl = -position_size * (params['sl_pct'] / 100)
                            current_equity += pnl
                            trades.append({
                                'strategy': 'MOMENTUM', 'side': signal, 'result': 'LOSS',
                                'entry': current_price, 'exit': sl_price, 'pnl': pnl
                            })
                            break

# Results
print(f'\n{"=" * 80}')
print('RESULTS')
print('=' * 80)

total_pnl = current_equity - capital
total_return = (total_pnl / capital) * 100

print(f'\nTotal trades: {len(trades)}')

# Per-strategy breakdown
for strategy_name in ['ER-90', 'SCALPER', 'MOMENTUM']:
    strategy_trades = [t for t in trades if t['strategy'] == strategy_name]
    if strategy_trades:
        wins = [t for t in strategy_trades if t['result'] == 'WIN']
        losses = [t for t in strategy_trades if t['result'] == 'LOSS']
        win_rate = len(wins) / len(strategy_trades) * 100
        total_pnl_strat = sum(t['pnl'] for t in strategy_trades)
        
        print(f'\n{strategy_name}:')
        print(f'  Trades: {len(strategy_trades)}')
        print(f'  Wins: {len(wins)} | Losses: {len(losses)}')
        print(f'  Win Rate: {win_rate:.1f}%')
        print(f'  P&L: ${total_pnl_strat:+.4f}')

wins = [t for t in trades if t['result'] == 'WIN']
losses = [t for t in trades if t['result'] == 'LOSS']

print(f'\n{"=" * 80}')
print('FINAL PERFORMANCE')
print('=' * 80)

print(f'\nStarting: ${capital:.2f}')
print(f'Ending: ${current_equity:.2f}')
print(f'Total P&L: ${total_pnl:+.4f}')
print(f'Total Return: {total_return:+.2f}%')

if trades:
    print(f'\nWin Rate: {len(wins)/len(trades)*100:.1f}%')
    print(f'Avg per trade: ${total_pnl/len(trades):+.4f}')

daily_avg = total_pnl / 7
print(f'\nDaily average: ${daily_avg:+.4f} ({(daily_avg/capital)*100:+.2f}%)')

print(f'\nProjections:')
print(f'  Weekly: ${daily_avg * 5:+.2f}')
print(f'  Monthly: ${daily_avg * 20:+.2f}')
if daily_avg > 0:
    print(f'  Days to double: {int(capital / daily_avg)}')

print('=' * 80)
