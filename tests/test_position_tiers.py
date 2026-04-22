#!/usr/bin/env python3
"""Quick test of position tier integration"""

import signal
from backtest_90_complete import MultiTimeframeBacktest

# Set 60 second timeout
signal.alarm(60)

print("Testing position tier integration with $100 starting balance...\n")

# Create backtest
bt = MultiTimeframeBacktest(
    'data/ETHUSDT_1m_90d.json',
    starting_balance=100.0,
    seed=42,
    balance_aware=True
)

print(f"\nInitial state:")
print(f"  Position limit: {bt.founder_fee.get_position_limit()} per TF per asset")
print(f"  Total slots: {bt.founder_fee.get_total_position_limit()}")
print(f"  Balance: ${bt.balance:.2f}")

# Run only first 5000 minutes (about 3.5 days) for quick test
print(f"\nRunning backtest (first 5000 minutes)...")
print(f"{'='*80}\n")

# Print initial setup
print(f"MULTI-TIMEFRAME BACKTEST: {bt.symbol}")
print(f"Timeframes: {', '.join(bt.active_timeframes)}")
print(f"Starting Balance: ${bt.starting_balance:.2f}")
print(f"{'='*80}\n")

# Run for 5000 minutes
for i in range(min(5000, len(bt.candles))):
    bt.processing_manager.process_minute(i, bt)
    
    # Print tier upgrades as they happen (already handled in _check_tier_upgrade)
    if i % 1000 == 0:
        print(f"\n[Progress: {i}/5000 minutes] Balance: ${bt.get_total_balance():.2f}, "
              f"Tier: {bt.current_position_tier}, Active positions: {len(bt.active_positions)}")

# Print results
print(f"\n{'='*80}")
print("QUICK TEST RESULTS")
print(f"{'='*80}\n")

total_balance = bt.get_total_balance()
print(f"Final Balance: ${total_balance:.2f}")
print(f"Final Tier: {bt.current_position_tier}")
print(f"Final Position Limit: {bt.founder_fee.get_position_limit()} per TF per asset")
print(f"Final Total Slots: {bt.founder_fee.get_total_position_limit()}")
print(f"Max Concurrent Positions: {bt.max_concurrent_positions}")
print(f"Total Trades: {len(bt.all_trades)}")

if bt.tier_upgrade_history:
    print(f"\nTier Upgrades:")
    for upgrade in bt.tier_upgrade_history:
        print(f"  {upgrade['old_limit']} → {upgrade['new_limit']} at ${upgrade['balance']:.2f} "
              f"({upgrade['total_slots']} slots)")

print("\n✅ Position tier integration test complete!")
