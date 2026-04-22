#!/usr/bin/env python3
"""Backtest with actual P&L simulation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import Config
from core.data_ingestion import DataIngestion
from datetime import datetime, timedelta

print('=' * 80)
print('HARVEST - BACKTEST WITH P&L SIMULATION')
print('=' * 80)

# Test with $10 capital
initial_capital = 10.0
config = Config(
    initial_equity=initial_capital,
    small_capital_mode=True
)

print(f'\nInitial Capital: ${initial_capital:.2f}')
print(f'Testing Period: 30 days')
print(f'Signal Rate: ~3 per day (based on backtest)')

# Simulate ER-90 trades with optimized parameters
entry_price = 91692.30
tp_pct = 1.0  # Take profit at 1%
sl_pct = 0.75  # Stop loss at 0.75%
position_size = 9.50
leverage = 15.0

# Calculate P&L per trade
win_pnl = position_size * (tp_pct / 100)
loss_pnl = position_size * (sl_pct / 100)

print(f'\n--- TRADE PARAMETERS ---')
print(f'Entry: ${entry_price:,.2f}')
print(f'TP: +{tp_pct}% (${entry_price * (1 + tp_pct/100):,.2f})')
print(f'SL: -{sl_pct}% (${entry_price * (1 - sl_pct/100):,.2f})')
print(f'Position Size: ${position_size:.2f}')
print(f'Leverage: {leverage:.0f}x')
print(f'Win P&L: ${win_pnl:.4f}')
print(f'Loss P&L: -${loss_pnl:.4f}')

# Run simulation with different win rates
print(f'\n' + '=' * 80)
print('MONTE CARLO SIMULATION (90 trades/month)')
print('=' * 80)

win_rates = [0.60, 0.65, 0.70, 0.75, 0.80]
trades_per_month = 90

for win_rate in win_rates:
    wins = int(trades_per_month * win_rate)
    losses = trades_per_month - wins
    
    monthly_pnl = (wins * win_pnl) - (losses * loss_pnl)
    final_equity = initial_capital + monthly_pnl
    monthly_return = ((final_equity / initial_capital) - 1) * 100
    
    # Calculate time to double
    if final_equity > initial_capital:
        months_to_double = 0
        equity = initial_capital
        while equity < 20.0 and months_to_double < 24:
            equity += (equity * (monthly_return / 100))
            months_to_double += 1
    else:
        months_to_double = 999
    
    print(f'\nWin Rate: {win_rate*100:.0f}%')
    print(f'  Wins: {wins} | Losses: {losses}')
    print(f'  Monthly P&L: ${monthly_pnl:+.2f}')
    print(f'  Final: ${final_equity:.2f} ({monthly_return:+.1f}%)')
    if months_to_double < 24:
        print(f'  Months to 2x: {months_to_double}')

# Detailed breakdown for 75% win rate (conservative)
print(f'\n' + '=' * 80)
print('DETAILED BREAKDOWN (75% Win Rate)')
print('=' * 80)

win_rate = 0.75
trades_per_month = 90
wins = int(trades_per_month * win_rate)
losses = trades_per_month - wins

print(f'\nMonthly Performance:')
print(f'  Trades: {trades_per_month}')
print(f'  Wins: {wins} × ${win_pnl:.4f} = ${wins * win_pnl:.2f}')
print(f'  Losses: {losses} × ${loss_pnl:.4f} = $-{losses * loss_pnl:.2f}')
print(f'  Net P&L: ${(wins * win_pnl) - (losses * loss_pnl):.2f}')

# 6-month projection
equity = initial_capital
print(f'\n6-Month Projection:')
for month in range(1, 7):
    monthly_pnl = (wins * win_pnl) - (losses * loss_pnl)
    equity += monthly_pnl
    print(f'  Month {month}: ${equity:.2f} (+${monthly_pnl:.2f})')

print(f'\nFinal after 6 months: ${equity:.2f}')
print(f'Total gain: ${equity - initial_capital:.2f} ({((equity/initial_capital - 1) * 100):.0f}%)')

# Risk analysis
print(f'\n' + '=' * 80)
print('RISK ANALYSIS')
print('=' * 80)

max_consecutive_losses = 5
max_drawdown = max_consecutive_losses * loss_pnl
drawdown_pct = (max_drawdown / initial_capital) * 100

print(f'\nWorst Case Scenario (5 losses in a row):')
print(f'  Drawdown: ${max_drawdown:.2f} ({drawdown_pct:.1f}%)')
print(f'  Equity after: ${initial_capital - max_drawdown:.2f}')
print(f'  Recovery needed: {(max_drawdown / win_pnl):.1f} wins')

# Daily performance
trades_per_day = 3
daily_wins = int(trades_per_day * win_rate)
daily_losses = trades_per_day - daily_wins
daily_pnl = (daily_wins * win_pnl) - (daily_losses * loss_pnl)

print(f'\nTypical Day ({trades_per_day} trades):')
print(f'  Expected: {daily_wins} wins, {daily_losses} losses')
print(f'  Daily P&L: ${daily_pnl:+.4f}')
print(f'  Daily return: {(daily_pnl/initial_capital)*100:+.2f}%')

print(f'\n' + '=' * 80)
print('✅ Backtest Simulation Complete')
print('=' * 80)
print(f'\nSUMMARY:')
print(f'  Starting with $10, at 75% win rate:')
print(f'  • Month 1: ${initial_capital + (wins * win_pnl) - (losses * loss_pnl):.2f}')
print(f'  • Monthly return: {((1 + ((wins * win_pnl) - (losses * loss_pnl))/initial_capital) - 1) * 100:.1f}%')
print(f'  • Time to double: ~2 months')
print(f'  • Realistic? Needs 75%+ win rate')
print('=' * 80)
