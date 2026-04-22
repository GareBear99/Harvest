#!/usr/bin/env python3
"""Test all strategies combined for maximum gains."""

from core.models import Config

print('=' * 80)
print('HARVEST MULTI-STRATEGY - MAXIMUM FREQUENCY')
print('=' * 80)

capital = 10.0
config = Config(initial_equity=capital, small_capital_mode=True)

print(f'\nStarting Capital: ${capital:.2f}')
print(f'Mode: ALL STRATEGIES ACTIVE')

# Define all strategies with their parameters
strategies = {
    'ER-90': {
        'trades_per_day': 3,
        'win_rate': 0.75,
        'tp_pct': 1.0,
        'sl_pct': 0.75,
        'position_pct': 0.95
    },
    'SCALPER': {
        'trades_per_day': 24,
        'win_rate': 0.70,
        'tp_pct': 0.4,
        'sl_pct': 0.3,
        'position_pct': 0.95
    },
    'MOMENTUM': {
        'trades_per_day': 12,
        'win_rate': 0.72,
        'tp_pct': 0.7,
        'sl_pct': 0.4,
        'position_pct': 0.95
    }
}

print(f'\n{"=" * 80}')
print('STRATEGY BREAKDOWN')
print('=' * 80)

total_daily_trades = 0
combined_daily_pnl = 0

for name, params in strategies.items():
    position_size = capital * params['position_pct']
    
    # Calculate per-trade P&L
    win_pnl = position_size * (params['tp_pct'] / 100)
    loss_pnl = position_size * (params['sl_pct'] / 100)
    
    # Daily stats
    wins = int(params['trades_per_day'] * params['win_rate'])
    losses = params['trades_per_day'] - wins
    
    daily_pnl = (wins * win_pnl) - (losses * loss_pnl)
    daily_return = (daily_pnl / capital) * 100
    
    print(f'\n{name}:')
    print(f'  Trades/day: {params["trades_per_day"]}')
    print(f'  Win rate: {params["win_rate"]*100:.0f}%')
    print(f'  TP/SL: +{params["tp_pct"]}% / -{params["sl_pct"]}%')
    print(f'  Per trade: +${win_pnl:.4f} / -${loss_pnl:.4f}')
    print(f'  Daily P&L: ${daily_pnl:+.4f} ({daily_return:+.2f}%)')
    
    total_daily_trades += params['trades_per_day']
    combined_daily_pnl += daily_pnl

print(f'\n{"=" * 80}')
print('COMBINED PERFORMANCE')
print('=' * 80)

print(f'\nTotal trades/day: {total_daily_trades}')
print(f'Trades/hour (16h): {total_daily_trades/16:.1f}')

# Daily performance
daily_return = (combined_daily_pnl / capital) * 100
print(f'\nDaily Performance:')
print(f'  P&L: ${combined_daily_pnl:+.2f}')
print(f'  Return: {daily_return:+.1f}%')
print(f'  End of day: ${capital + combined_daily_pnl:.2f}')

# Hourly performance
hourly_pnl = combined_daily_pnl / 16
hourly_return = (hourly_pnl / capital) * 100
print(f'\nHourly Average:')
print(f'  P&L: ${hourly_pnl:+.4f}')
print(f'  Return: {hourly_return:+.2f}%')

# Weekly projection
weekly_pnl = combined_daily_pnl * 5
weekly_equity = capital + weekly_pnl
weekly_return = (weekly_pnl / capital) * 100

print(f'\nWeekly (5 days):')
print(f'  P&L: ${weekly_pnl:+.2f}')
print(f'  Final: ${weekly_equity:.2f}')
print(f'  Return: {weekly_return:+.1f}%')

# Monthly projection
monthly_pnl = combined_daily_pnl * 20  # 20 trading days
monthly_equity = capital + monthly_pnl
monthly_return = (monthly_pnl / capital) * 100

print(f'\nMonthly (20 days):')
print(f'  P&L: ${monthly_pnl:+.2f}')
print(f'  Final: ${monthly_equity:.2f}')
print(f'  Return: {monthly_return:+.1f}%')

# Time to double
if combined_daily_pnl > 0:
    days = 0
    equity = capital
    while equity < capital * 2 and days < 90:
        equity += combined_daily_pnl
        days += 1
    
    print(f'\nTime to Double:')
    print(f'  Days: {days}')
    print(f'  Weeks: {days/5:.1f}')
    print(f'  After {days} days: ${equity:.2f}')

# Test with different capital amounts
print(f'\n{"=" * 80}')
print('SCALING WITH CAPITAL')
print('=' * 80)

test_capitals = [10, 25, 50, 100]
for test_cap in test_capitals:
    scale_factor = test_cap / capital
    scaled_daily = combined_daily_pnl * scale_factor
    scaled_monthly = scaled_daily * 20
    
    print(f'\n${test_cap:.0f} capital:')
    print(f'  Daily: ${scaled_daily:+.2f} ({(scaled_daily/test_cap)*100:+.1f}%)')
    print(f'  Monthly: ${scaled_monthly:+.2f} ({(scaled_monthly/test_cap)*100:+.1f}%)')
    
    # Days to double
    if scaled_daily > 0:
        days = int(test_cap / scaled_daily)
        print(f'  Days to 2x: {days}')

print(f'\n{"=" * 80}')
print('⚠️  RISK WARNING')
print('=' * 80)
print(f'\nWith {total_daily_trades} trades/day:')
print(f'  • Requires ACTIVE monitoring every hour')
print(f'  • Fees: ~${total_daily_trades * 0.001 * capital:.2f}/day (0.1% per trade)')
print(f'  • Slippage reduces returns by ~15-25%')
print(f'  • Win rates are theoretical - need live testing')
print(f'  • Capital at risk: 100% on every trade (leveraged)')
print(f'\nRealistic daily return after fees/slippage:')
print(f'  Theoretical: {daily_return:+.1f}%')
print(f'  Realistic: {daily_return * 0.75:+.1f}%')
print(f'  Conservative: {daily_return * 0.5:+.1f}%')
print('=' * 80)
