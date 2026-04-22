#!/usr/bin/env python3
"""Test HARVEST system with $10 starting capital."""

from core.models import Config, ExecutionIntent, Engine, Side
from datetime import datetime

print('=' * 80)
print('HARVEST - $10 CAPITAL TEST')
print('=' * 80)

# Initialize with $10
initial_capital = 10.0
print(f'\nInitial Capital: ${initial_capital:.2f}')
print(f'Mode: Paper Trading (Simulated)')

# Simulate a typical ER-90 signal with optimized parameters
entry_price = 91692.30
# New optimized parameters: TP 1.0%, SL 0.75%
tp_pct = 1.0
sl_pct = 0.75
tp_price = entry_price * (1 + tp_pct / 100)
stop_price = entry_price * (1 - sl_pct / 100)
leverage = 15.0
position_size = 9.50  # ~95% of capital

print(f'\n--- TYPICAL ER-90 TRADE ---')
print(f'Entry: ${entry_price:,.2f}')
print(f'Stop Loss: ${stop_price:,.2f} ({((stop_price/entry_price - 1) * 100):.2f}%)')
print(f'Take Profit: ${tp_price:,.2f} ({((tp_price/entry_price - 1) * 100):.2f}%)')
print(f'Leverage: {leverage:.1f}x')
print(f'Position Size: ${position_size:.2f}')

# Calculate position details
margin_needed = position_size / leverage
stop_loss_pct = abs((stop_price / entry_price) - 1) * 100

print(f'\nMargin Required: ${margin_needed:.2f} ({(margin_needed/initial_capital)*100:.1f}% of capital)')
print(f'Stop Distance: {stop_loss_pct:.2f}%')

# WIN scenario
print(f'\n--- SCENARIO 1: WIN (TP Hit) ---')
win_pnl = position_size * ((tp_price / entry_price) - 1)
win_new_equity = initial_capital + win_pnl
print(f'P&L: ${win_pnl:.4f}')
print(f'New Equity: ${win_new_equity:.4f}')
print(f'Gain: {((win_new_equity/initial_capital - 1) * 100):.3f}%')

# LOSS scenario
print(f'\n--- SCENARIO 2: LOSS (SL Hit) ---')
loss_pnl = position_size * ((stop_price / entry_price) - 1)
loss_new_equity = initial_capital + loss_pnl
print(f'P&L: ${loss_pnl:.4f}')
print(f'New Equity: ${loss_new_equity:.4f}')
print(f'Loss: {((loss_new_equity/initial_capital - 1) * 100):.3f}%')

# Monthly projection
win_rate = 0.75  # 75% win rate
trades_per_month = 90  # 3 per day × 30 days
wins = int(trades_per_month * win_rate)
losses = trades_per_month - wins

print(f'\n--- MONTHLY PROJECTION (75% Win Rate) ---')
print(f'Trades/Month: {trades_per_month} (3/day)')
print(f'Expected Wins: {wins}')
print(f'Expected Losses: {losses}')

monthly_pnl = (wins * win_pnl) + (losses * loss_pnl)
final_equity = initial_capital + monthly_pnl
monthly_return = ((final_equity / initial_capital) - 1) * 100

print(f'\nTotal Monthly P&L: ${monthly_pnl:.2f}')
print(f'Final Equity: ${final_equity:.2f}')
print(f'Monthly Return: {monthly_return:.1f}%')

# Time to double
if final_equity > initial_capital:
    months_to_double = 0
    equity = initial_capital
    while equity < 20.0 and months_to_double < 36:
        equity += (equity * (monthly_return / 100))
        months_to_double += 1
    print(f'Months to Double: {months_to_double}')
    print(f'After {months_to_double} months: ${equity:.2f}')

print(f'\n' + '=' * 80)
print('✅ $10 Capital Test Complete')
print('=' * 80)
