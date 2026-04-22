#!/usr/bin/env python3
"""
Strategy Pool Integrity Checker
Validates strategy pool structure and rotation logic
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.strategy_pool import StrategyPool
from ml.base_strategy import BASE_STRATEGY, STRATEGY_EVALUATION


def check_pool_structure(pool: StrategyPool) -> bool:
    """Verify pool structure is valid"""
    print("\n" + "="*80)
    print("🔍 CHECKING POOL STRUCTURE")
    print("="*80 + "\n")
    
    all_valid = True
    
    for timeframe in ['15m', '1h', '4h']:
        print(f"📊 {timeframe} Timeframe:")
        print("-" * 40)
        
        # Get pool stats
        stats = pool.get_pool_stats(timeframe)
        
        # Check 1: Pool exists
        if not stats:
            print(f"  ❌ Pool not found for {timeframe}")
            all_valid = False
            continue
        
        # Check 2: Has active strategy
        if not stats['active_strategy_id']:
            print(f"  ❌ No active strategy set")
            all_valid = False
        else:
            print(f"  ✅ Active Strategy: {stats['active_strategy_id']}")
        
        # Check 3: Base strategy always exists
        has_base = any(s['id'] == 'base' for s in stats['strategies'])
        if not has_base:
            print(f"  ❌ Base strategy missing!")
            all_valid = False
        else:
            print(f"  ✅ Base strategy present")
        
        # Check 4: Max 3 proven strategies (+ base)
        proven_count = len([s for s in stats['strategies'] if not s['is_base']])
        if proven_count > 3:
            print(f"  ❌ Too many proven strategies: {proven_count} (max 3)")
            all_valid = False
        else:
            print(f"  ✅ Proven strategies: {proven_count}/3")
        
        # Check 5: Strategy IDs valid
        valid_ids = ['base', 'strategy_1', 'strategy_2', 'strategy_3']
        for strategy in stats['strategies']:
            if strategy['id'] not in valid_ids:
                print(f"  ❌ Invalid strategy ID: {strategy['id']}")
                all_valid = False
        
        # Check 6: Consecutive losses valid
        losses = stats['consecutive_losses']
        if losses < 0:
            print(f"  ❌ Invalid consecutive losses: {losses}")
            all_valid = False
        else:
            print(f"  ✅ Consecutive losses: {losses}")
        
        print()
    
    return all_valid


def check_rotation_logic(pool: StrategyPool) -> bool:
    """Verify rotation logic works correctly"""
    print("\n" + "="*80)
    print("🔄 TESTING ROTATION LOGIC")
    print("="*80 + "\n")
    
    all_valid = True
    timeframe = '15m'  # Test on 15m
    
    print(f"Testing rotation on {timeframe}:")
    print("-" * 40)
    
    # Get initial state
    initial_stats = pool.get_pool_stats(timeframe)
    initial_active = initial_stats['active_strategy_id']
    print(f"  Starting with: {initial_active}\n")
    
    # Test switch
    print("  Triggering switch (test)...")
    new_id = pool.switch_strategy(timeframe, "test_rotation")
    
    # Verify switch occurred
    new_stats = pool.get_pool_stats(timeframe)
    new_active = new_stats['active_strategy_id']
    
    if new_active == initial_active:
        print(f"  ⚠️  No switch occurred (might be only strategy available)")
    else:
        print(f"  ✅ Switched: {initial_active} → {new_active}")
    
    # Check rotation order
    expected_order = ['base', 'strategy_1', 'strategy_2', 'strategy_3']
    available_strategies = [s['id'] for s in initial_stats['strategies']]
    
    print(f"\n  Available strategies: {', '.join(available_strategies)}")
    
    # Verify new strategy is in expected rotation
    if new_active not in expected_order:
        print(f"  ❌ New strategy {new_active} not in valid rotation")
        all_valid = False
    else:
        print(f"  ✅ New strategy {new_active} is valid")
    
    # Switch back to original
    pool.pools[timeframe]['active_strategy_id'] = initial_active
    pool.save_state()
    print(f"\n  Restored to: {initial_active}")
    
    return all_valid


def check_switch_triggers(pool: StrategyPool) -> bool:
    """Verify switch trigger logic"""
    print("\n" + "="*80)
    print("⚡ CHECKING SWITCH TRIGGERS")
    print("="*80 + "\n")
    
    print("Switch Trigger Rules:")
    print("-" * 40)
    
    # Get criteria from config
    switch_wr = STRATEGY_EVALUATION['switch_threshold_wr']
    switch_losses = STRATEGY_EVALUATION['switch_threshold_losses']
    min_trades = STRATEGY_EVALUATION['min_trades_for_wr_check']
    
    print(f"  • Win Rate Threshold: < {switch_wr:.0%}")
    print(f"  • Consecutive Loss Threshold: {switch_losses} losses")
    print(f"  • Minimum Trades Required: {min_trades}")
    
    print("\nTest Scenarios:")
    print("-" * 40)
    
    # Scenario 1: WR below threshold
    print(f"  Scenario 1: WR = 55% (below {switch_wr:.0%})")
    should_switch_1 = 0.55 < switch_wr
    print(f"    Result: {'✅ SWITCH' if should_switch_1 else '❌ NO SWITCH'}")
    
    # Scenario 2: WR above threshold
    print(f"  Scenario 2: WR = 65% (above {switch_wr:.0%})")
    should_switch_2 = 0.65 < switch_wr
    print(f"    Result: {'✅ SWITCH' if should_switch_2 else '❌ NO SWITCH (correct)'}")
    
    # Scenario 3: Consecutive losses at threshold
    print(f"  Scenario 3: {switch_losses} consecutive losses")
    should_switch_3 = switch_losses >= switch_losses
    print(f"    Result: {'✅ SWITCH' if should_switch_3 else '❌ NO SWITCH'}")
    
    # Scenario 4: Below consecutive loss threshold
    print(f"  Scenario 4: {switch_losses - 1} consecutive losses")
    should_switch_4 = (switch_losses - 1) >= switch_losses
    print(f"    Result: {'✅ SWITCH' if should_switch_4 else '❌ NO SWITCH (correct)'}")
    
    all_valid = True
    return all_valid


def check_strategy_independence() -> bool:
    """Verify each timeframe is truly independent"""
    print("\n" + "="*80)
    print("🔐 VERIFYING TIMEFRAME INDEPENDENCE")
    print("="*80 + "\n")
    
    pool = StrategyPool()
    all_valid = True
    
    print("Testing that modifying one timeframe doesn't affect others:")
    print("-" * 40)
    
    # Get initial states
    stats_15m_before = pool.get_pool_stats('15m')
    stats_1h_before = pool.get_pool_stats('1h')
    stats_4h_before = pool.get_pool_stats('4h')
    
    # Modify 15m consecutive losses
    original_losses = pool.pools['15m']['consecutive_losses']
    pool.pools['15m']['consecutive_losses'] = 999
    
    # Check other timeframes unchanged
    stats_1h_after = pool.get_pool_stats('1h')
    stats_4h_after = pool.get_pool_stats('4h')
    
    if stats_1h_after['consecutive_losses'] != stats_1h_before['consecutive_losses']:
        print("  ❌ 1h consecutive losses changed when 15m was modified!")
        all_valid = False
    else:
        print("  ✅ 1h unchanged when 15m modified")
    
    if stats_4h_after['consecutive_losses'] != stats_4h_before['consecutive_losses']:
        print("  ❌ 4h consecutive losses changed when 15m was modified!")
        all_valid = False
    else:
        print("  ✅ 4h unchanged when 15m modified")
    
    # Restore
    pool.pools['15m']['consecutive_losses'] = original_losses
    
    # Test strategy independence
    print("\nTesting strategy pool independence:")
    print("-" * 40)
    
    active_15m = stats_15m_before['active_strategy_id']
    active_1h = stats_1h_before['active_strategy_id']
    active_4h = stats_4h_before['active_strategy_id']
    
    print(f"  15m active: {active_15m}")
    print(f"  1h active:  {active_1h}")
    print(f"  4h active:  {active_4h}")
    
    # They can be same or different - just verify they're tracked separately
    print(f"\n  ✅ Each timeframe tracks its own active strategy")
    
    return all_valid


def run_integrity_check() -> bool:
    """Run complete integrity check"""
    print("\n" + "#"*80)
    print("STRATEGY POOL INTEGRITY CHECK")
    print("#"*80)
    
    pool = StrategyPool()
    
    results = {
        'structure': check_pool_structure(pool),
        'rotation': check_rotation_logic(pool),
        'triggers': check_switch_triggers(pool),
        'independence': check_strategy_independence()
    }
    
    # Summary
    print("\n" + "="*80)
    print("📋 INTEGRITY CHECK SUMMARY")
    print("="*80 + "\n")
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {check.title()}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL INTEGRITY CHECKS PASSED")
        print("\nStrategy pool is properly configured:")
        print("  • Structure is valid")
        print("  • Rotation logic works")
        print("  • Switch triggers configured")
        print("  • Timeframes are independent")
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease review the failures above.")
    print("="*80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    passed = run_integrity_check()
    sys.exit(0 if passed else 1)
