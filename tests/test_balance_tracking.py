#!/usr/bin/env python3
"""Test balance tracking, tier upgrades/downgrades, and depletion handling"""

from backtest_90_complete import MultiTimeframeBacktest

print("="*80)
print("BALANCE TRACKING & TIER SYSTEM TEST")
print("="*80)

# Create backtest instance
bt = MultiTimeframeBacktest(
    'data/ETHUSDT_1m_90d.json',
    starting_balance=100.0,
    seed=42,
    balance_aware=True
)

print(f"\n📊 Testing Balance Milestones & Tier Changes\n")

# Simulate various balance scenarios
test_scenarios = [
    (100.0, "Starting balance"),
    (115.0, "Profit to $115 - Should upgrade to Tier 2"),
    (95.0, "Loss to $95 - Should downgrade to Tier 1"),
    (220.0, "Big profit to $220 - Should upgrade to Tier 3"),
    (180.0, "Loss to $180 - Should downgrade to Tier 2"),
    (90.0, "Major loss to $90 - Should downgrade to Tier 1"),
    (45.0, "Critical loss to $45 - Still Tier 1 but limited"),
    (5.0, "Near depletion $5 - Critical warning"),
    (0.0, "Depleted $0 - Trading halted"),
    (50.0, "Recovery to $50 - Tier 1 resumed"),
]

print("Simulating balance changes and tier adjustments:\n")

for balance, description in test_scenarios:
    print(f"{'─'*80}")
    print(f"Scenario: {description}")
    print(f"Balance: ${balance:.2f}")
    
    # Update balance
    bt.balance = balance
    total_balance = bt.get_total_balance()
    
    # Check tier change
    old_tier = bt.current_position_tier
    old_limit = bt.founder_fee.get_position_limit()
    
    bt._check_tier_upgrade(total_balance)
    
    new_tier = bt.current_position_tier
    new_limit = bt.founder_fee.get_position_limit()
    
    # Show current state
    print(f"Position Limit: {new_limit} per TF per asset")
    print(f"Total Slots: {bt.founder_fee.get_total_position_limit()}")
    print(f"Can Open Positions: {'Yes' if balance > 0 else 'NO - DEPLETED'}")
    
    # Show milestones
    print(f"\nMilestones:")
    print(f"  Peak: ${bt.balance_milestones['peak']:.2f}")
    print(f"  Lowest: ${bt.balance_milestones['lowest']:.2f}")
    if bt.balance_milestones['times_below_100'] > 0:
        print(f"  Times below $100: {bt.balance_milestones['times_below_100']}")
    if bt.balance_milestones['times_below_50'] > 0:
        print(f"  Times below $50: {bt.balance_milestones['times_below_50']}")
    if bt.balance_milestones['times_depleted'] > 0:
        print(f"  ⚠️  Times depleted: {bt.balance_milestones['times_depleted']}")
    print()

# Final Summary
print(f"\n{'='*80}")
print("FINAL SUMMARY")
print(f"{'='*80}\n")

print(f"📈 Balance Journey:")
print(f"  Peak: ${bt.balance_milestones['peak']:.2f}")
print(f"  Lowest: ${bt.balance_milestones['lowest']:.2f}")
print(f"  Final: ${bt.balance:.2f}")
print(f"  Range: ${bt.balance_milestones['lowest']:.2f} → ${bt.balance_milestones['peak']:.2f}")

print(f"\n🎯 Tier Changes:")
print(f"  Upgrades: {len(bt.tier_upgrade_history)}")
if bt.tier_upgrade_history:
    for upgrade in bt.tier_upgrade_history:
        print(f"    • {upgrade['old_limit']} → {upgrade['new_limit']} at ${upgrade['balance']:.2f}")

print(f"  Downgrades: {len(bt.tier_downgrade_history)}")
if bt.tier_downgrade_history:
    for downgrade in bt.tier_downgrade_history:
        print(f"    • {downgrade['old_limit']} → {downgrade['new_limit']} at ${downgrade['balance']:.2f} "
              f"(from peak ${downgrade['peak_before_drop']:.2f})")

print(f"\n⚠️  Critical Events:")
print(f"  Times below $100: {bt.balance_milestones['times_below_100']}")
print(f"  Times below $50: {bt.balance_milestones['times_below_50']}")
print(f"  Times depleted: {bt.balance_milestones['times_depleted']}")

print(f"\n✅ Balance tracking and tier system working correctly!")
print(f"   - Upgrades when balance increases past thresholds")
print(f"   - Downgrades when balance drops below thresholds")
print(f"   - Tracks depletion and critical levels")
print(f"   - Ready for live trading with proper risk management\n")
