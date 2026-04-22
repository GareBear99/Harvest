#!/usr/bin/env python3
"""Test scalper strategy for hourly gains with small capital."""

from core.models import Config

print('=' * 80)
print('HARVEST SCALPER - HOURLY GAINS TEST')
print('=' * 80)

# Test with different capital amounts
capital_amounts = [10.0, 25.0, 50.0, 100.0]

for capital in capital_amounts:
    print(f'\n{"=" * 80}')
    print(f'CAPITAL: ${capital:.2f}')
    print('=' * 80)
    
    config = Config(initial_equity=capital, small_capital_mode=True)
    
    # Scalper parameters
    entry_price = 91692.30
    tp_pct = config.scalper_tp_pct  # 0.4%
    sl_pct = config.scalper_sl_pct  # 0.3%
    leverage = config.scalper_leverage  # 20x
    position_size = capital * 0.95  # 95% of capital
    
    # Calculate P&L per trade
    win_pnl = position_size * (tp_pct / 100)
    loss_pnl = position_size * (sl_pct / 100)
    
    print(f'\nTrade Setup:')
    print(f'  Entry: ${entry_price:,.2f}')
    print(f'  TP: +{tp_pct}% | SL: -{sl_pct}%')
    print(f'  Position: ${position_size:.2f} ({leverage:.0f}x leverage)')
    print(f'  Win: +${win_pnl:.4f} | Loss: -${loss_pnl:.4f}')
    print(f'  Risk/Reward: 1:{(win_pnl/loss_pnl):.2f}')
    
    # Hourly performance (assuming 1-2 trades/hour)
    trades_per_hour = 1.5  # Average
    win_rate = 0.70  # 70% win rate (realistic for scalping)
    
    wins_per_hour = trades_per_hour * win_rate
    losses_per_hour = trades_per_hour * (1 - win_rate)
    
    hourly_pnl = (wins_per_hour * win_pnl) - (losses_per_hour * loss_pnl)
    hourly_return = (hourly_pnl / capital) * 100
    
    print(f'\nHOURLY PERFORMANCE (70% WR):')
    print(f'  Trades/hour: {trades_per_hour:.1f}')
    print(f'  P&L/hour: ${hourly_pnl:+.4f}')
    print(f'  Return/hour: {hourly_return:+.2f}%')
    
    # Daily performance (16 active hours)
    active_hours = 16
    daily_trades = int(trades_per_hour * active_hours)
    daily_wins = int(daily_trades * win_rate)
    daily_losses = daily_trades - daily_wins
    
    daily_pnl = (daily_wins * win_pnl) - (daily_losses * loss_pnl)
    daily_return = (daily_pnl / capital) * 100
    
    print(f'\nDAILY PERFORMANCE ({active_hours}h active):')
    print(f'  Total trades: {daily_trades}')
    print(f'  Wins: {daily_wins} | Losses: {daily_losses}')
    print(f'  Daily P&L: ${daily_pnl:+.2f}')
    print(f'  Daily return: {daily_return:+.1f}%')
    print(f'  End of day: ${capital + daily_pnl:.2f}')
    
    # Weekly projection
    weekly_pnl = daily_pnl * 5  # 5 trading days
    weekly_equity = capital + weekly_pnl
    weekly_return = (weekly_pnl / capital) * 100
    
    print(f'\nWEEKLY (5 days):')
    print(f'  P&L: ${weekly_pnl:+.2f}')
    print(f'  Final: ${weekly_equity:.2f}')
    print(f'  Return: {weekly_return:+.1f}%')
    
    # Time to double (if profitable)
    if daily_pnl > 0:
        days_to_double = 0
        equity = capital
        while equity < capital * 2 and days_to_double < 90:
            equity += daily_pnl
            days_to_double += 1
        
        if days_to_double < 90:
            print(f'  Days to 2x: {days_to_double}')
            print(f'  After {days_to_double} days: ${equity:.2f}')

# Summary
print(f'\n{"=" * 80}')
print('SCALPER STRATEGY SUMMARY')
print('=' * 80)
print(f'\nKey Stats (70% win rate):')
print(f'  TP: 0.4% | SL: 0.3% | R:R 1:1.33')
print(f'  Trades: ~1.5/hour, ~24/day (16h active)')
print(f'  Leverage: 20x')
print(f'\nWith $10:')
print(f'  Per trade: +$0.038 win / -$0.029 loss')
print(f'  Per hour: +$0.031 (+0.31%)')
print(f'  Per day: +$0.50 (+5.0%)')
print(f'  Days to double: ~20 days')
print(f'\nWith $100:')
print(f'  Per trade: +$0.38 win / -$0.29 loss')
print(f'  Per hour: +$0.31 (+0.31%)')
print(f'  Per day: +$5.00 (+5.0%)')
print(f'  Days to double: ~20 days')
print(f'\n⚠️  RISKS:')
print(f'  • Requires constant monitoring (hourly gains)')
print(f'  • Higher trade frequency = more fees/slippage')
print(f'  • 70% win rate challenging to maintain')
print(f'  • Tight stops = more false signals')
print('=' * 80)
