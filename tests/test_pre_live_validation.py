#!/usr/bin/env python3
"""
Pre-Live Trading Validation Script
Tests all critical balance points, tier transitions, and edge cases
"""

import sys
from core.balance_aware_strategy import get_balance_aware_strategy, Asset
from core.founder_fee_manager import FounderFeeManager

print("="*80)
print("HARVEST BOT - PRE-LIVE VALIDATION TEST")
print("="*80)
print("\nTesting all critical balance points and tier transitions\n")

strategy = get_balance_aware_strategy()
founder_fee = FounderFeeManager(mode='BACKTEST')

# Critical balance points to test
test_balances = [
    0,    # Depleted
    5,    # Critical low
    10,   # Minimum viable
    20,   # Tier 2
    30,   # Tier 3
    40,   # Tier 4  
    50,   # Tier 5
    74,   # Just below BTC
    75,   # BTC activation
    99,   # Just below position tier
    100,  # Position tier baseline
    109,  # Tier 1 positions
    110,  # Tier 2 positions upgrade
    111,  # After tier 2 upgrade
    209,  # Tier 2 positions high
    210,  # Tier 3 positions upgrade
    211,  # After tier 3 upgrade
]

results = []

print(f"{'Balance':<10} {'Timeframes':<30} {'Assets':<15} {'Pos Limit':<12} {'Total Slots':<12} {'Status'}")
print("-" * 100)

for balance in test_balances:
    # Get tier info
    tier = strategy.get_tier(balance)
    active_tfs = strategy.get_active_timeframes(balance)
    active_assets = strategy.get_active_assets(balance)
    tier_desc = tier.description if tier else "Below Minimum ($10)"
    
    # Get position info (only for $100+)
    if balance >= 100:
        # Update founder fee manager
        founder_fee.check_and_collect(
            current_balance=balance,
            active_timeframes=['1m', '5m', '15m', '1h', '4h'],
            active_assets=['ETH', 'BTC'],
            mode='BACKTEST'
        )
        pos_limit = founder_fee.get_position_limit()
        total_slots = founder_fee.get_total_position_limit()
    else:
        pos_limit = 1
        total_slots = len(active_tfs) * len(active_assets) * pos_limit
    
    # Determine status
    if balance == 0:
        status = "⛔ DEPLETED"
    elif balance < 10:
        status = "🔴 CRITICAL"
    elif balance < 100:
        status = "🟡 BELOW BASELINE"
    elif balance >= 210:
        status = "✅ MAXED (Tier 3)"
    elif balance >= 110:
        status = "✅ UPGRADED (Tier 2)"
    else:
        status = "✅ BASELINE (Tier 1)"
    
    # Format timeframes
    tf_str = ', '.join(active_tfs) if active_tfs else "None"
    if len(tf_str) > 28:
        tf_str = tf_str[:25] + "..."
    
    # Format assets
    asset_str = ', '.join([a.name for a in active_assets])
    
    # Print row
    print(f"${balance:<9.0f} {tf_str:<30} {asset_str:<15} {pos_limit:<12} {total_slots:<12} {status}")
    
    # Store results
    results.append({
        'balance': balance,
        'timeframes': active_tfs,
        'assets': [a.name for a in active_assets],
        'pos_limit': pos_limit,
        'total_slots': total_slots,
        'tier_name': tier_desc
    })

# Validation checks
print("\n" + "="*80)
print("VALIDATION CHECKS")
print("="*80)

checks_passed = 0
checks_total = 0

def check(condition, description):
    global checks_passed, checks_total
    checks_total += 1
    if condition:
        checks_passed += 1
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description}")
        return False

# Check 1: $10 should have ETH only
r = results[test_balances.index(10)]
check(r['assets'] == ['ETH'] and r['timeframes'] == ['1m'], 
      "$10 balance: ETH only, 1m timeframe")

# Check 2: $20 should have both assets
r = results[test_balances.index(20)]
check(r['assets'] == ['ETH', 'BTC'], 
      "$20 balance: Both assets active")

# Check 3: $74 should have BTC (tier 5: $50-75)
r = results[test_balances.index(74)]
check('BTC' in r['assets'], 
      "$74 balance: BTC active (Tier 5)")

# Check 4: $75 should have BTC and all 5 TFs
r = results[test_balances.index(75)]
check('BTC' in r['assets'] and len(r['timeframes']) == 5, 
      "$75 balance: BTC + all 5 timeframes (Tier 6)")

# Check 5: $99 should have all TFs but not position tier system
r = results[test_balances.index(99)]
check(r['pos_limit'] == 1 and r['total_slots'] == 10,  # 5 TFs * 2 assets * 1
      "$99 balance: All TFs active, position tier not active yet (10 slots)")

# Check 6: $100 should have position tier baseline
r = results[test_balances.index(100)]
check(r['pos_limit'] == 1 and r['total_slots'] == 10,  # 5 TFs * 2 assets * 1
      "$100 balance: Position tier baseline (10 slots)")

# Check 7: $109 should still be tier 1
r = results[test_balances.index(109)]
check(r['pos_limit'] == 1 and r['total_slots'] == 10,
      "$109 balance: Still tier 1 (10 slots)")

# Check 8: $110 should upgrade to tier 2
r = results[test_balances.index(110)]
check(r['pos_limit'] == 2 and r['total_slots'] == 20,
      "$110 balance: Upgraded to tier 2 (20 slots)")

# Check 9: $111 should stay tier 2
r = results[test_balances.index(111)]
check(r['pos_limit'] == 2 and r['total_slots'] == 20,
      "$111 balance: Stays tier 2 (20 slots)")

# Check 10: $209 should still be tier 2
r = results[test_balances.index(209)]
check(r['pos_limit'] == 2 and r['total_slots'] == 20,
      "$209 balance: Still tier 2 (20 slots)")

# Check 11: $210 should upgrade to tier 3
r = results[test_balances.index(210)]
check(r['pos_limit'] == 3 and r['total_slots'] == 30,
      "$210 balance: Upgraded to tier 3 (30 slots - MAXED)")

# Check 12: $211 should stay tier 3
r = results[test_balances.index(211)]
check(r['pos_limit'] == 3 and r['total_slots'] == 30,
      "$211 balance: Stays tier 3 (30 slots - MAXED)")

# Check 13: All 5 timeframes at $100+
r = results[test_balances.index(100)]
check(len(r['timeframes']) == 5 and '4h' in r['timeframes'],
      "$100+ balance: All 5 timeframes active")

# Check 14: $0 should have no positions possible
r = results[test_balances.index(0)]
check(r['total_slots'] == 0,  # No timeframes or assets active
      "$0 balance: No positions (depleted)")

# Check 15: $5 should allow minimal trading
r = results[test_balances.index(5)]
check(r['total_slots'] == 0,  # Below $10 minimum
      "$5 balance: Below minimum ($10)")

# Summary
print("\n" + "="*80)
print(f"VALIDATION SUMMARY: {checks_passed}/{checks_total} CHECKS PASSED")
print("="*80)

if checks_passed == checks_total:
    print("\n✅ ALL VALIDATION CHECKS PASSED - SYSTEM READY FOR LIVE TESTING")
    sys.exit(0)
else:
    print(f"\n❌ {checks_total - checks_passed} CHECKS FAILED - REVIEW BEFORE LIVE TESTING")
    sys.exit(1)
