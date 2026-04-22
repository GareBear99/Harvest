#!/usr/bin/env python3
"""
Slot Allocation Validation Test
Comprehensive testing of stair-climbing balance allocation system

Tests critical balance points from $0 to $250 to verify:
1. ETH→BTC slot alternation every $10
2. Progressive timeframe unlocks
3. Position tier system at $100+
4. Slot deactivation on balance drops
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.slot_allocation_strategy import get_slot_allocation_strategy, Asset
from core.founder_fee_manager import FounderFeeManager


def test_slot_allocation():
    """Test slot allocation at critical balance points"""
    
    strategy = get_slot_allocation_strategy()
    
    print("=" * 80)
    print("SLOT ALLOCATION VALIDATION TEST")
    print("=" * 80)
    
    # Test cases: (balance, expected_slots, expected_eth_slots, expected_btc_slots, expected_timeframes)
    test_cases = [
        (0, 0, [], [], []),
        (5, 0, [], [], []),
        (10, 1, [1], [], ['1m']),
        (15, 1, [1], [], ['1m']),
        (20, 2, [1], [2], ['1m']),
        (25, 2, [1], [2], ['1m']),
        (30, 3, [1, 3], [2], ['1m', '5m']),
        (35, 3, [1, 3], [2], ['1m', '5m']),
        (40, 4, [1, 3], [2, 4], ['1m', '5m']),
        (45, 4, [1, 3], [2, 4], ['1m', '5m']),
        (50, 5, [1, 3, 5], [2, 4], ['1m', '5m', '15m']),
        (55, 5, [1, 3, 5], [2, 4], ['1m', '5m', '15m']),
        (60, 6, [1, 3, 5], [2, 4, 6], ['1m', '5m', '15m']),
        (65, 6, [1, 3, 5], [2, 4, 6], ['1m', '5m', '15m']),
        (70, 7, [1, 3, 5, 7], [2, 4, 6], ['1m', '5m', '15m', '1h']),
        (75, 7, [1, 3, 5, 7], [2, 4, 6], ['1m', '5m', '15m', '1h']),
        (80, 8, [1, 3, 5, 7], [2, 4, 6, 8], ['1m', '5m', '15m', '1h']),
        (85, 8, [1, 3, 5, 7], [2, 4, 6, 8], ['1m', '5m', '15m', '1h']),
        (90, 9, [1, 3, 5, 7, 9], [2, 4, 6, 8], ['1m', '5m', '15m', '1h', '4h']),
        (95, 9, [1, 3, 5, 7, 9], [2, 4, 6, 8], ['1m', '5m', '15m', '1h', '4h']),
        (100, 10, [1, 3, 5, 7, 9], [2, 4, 6, 8, 10], ['1m', '5m', '15m', '1h', '4h']),
        (105, 10, [1, 3, 5, 7, 9], [2, 4, 6, 8, 10], ['1m', '5m', '15m', '1h', '4h']),
        (110, 10, [1, 3, 5, 7, 9], [2, 4, 6, 8, 10], ['1m', '5m', '15m', '1h', '4h']),
        (150, 10, [1, 3, 5, 7, 9], [2, 4, 6, 8, 10], ['1m', '5m', '15m', '1h', '4h']),
        (210, 10, [1, 3, 5, 7, 9], [2, 4, 6, 8, 10], ['1m', '5m', '15m', '1h', '4h']),
        (250, 10, [1, 3, 5, 7, 9], [2, 4, 6, 8, 10], ['1m', '5m', '15m', '1h', '4h']),
    ]
    
    passed = 0
    failed = 0
    
    for balance, exp_slots, exp_eth, exp_btc, exp_tfs in test_cases:
        summary = strategy.get_slot_summary(balance)
        
        # Get actual values
        actual_slots = summary['active_slots']
        actual_eth = strategy.get_active_slots_for_asset(balance, Asset.ETH)
        actual_btc = strategy.get_active_slots_for_asset(balance, Asset.BTC)
        actual_tfs = summary['active_timeframes']
        
        # Validate
        checks = []
        checks.append(actual_slots == exp_slots)
        checks.append(actual_eth == exp_eth)
        checks.append(actual_btc == exp_btc)
        checks.append(actual_tfs == exp_tfs)
        
        all_passed = all(checks)
        
        if all_passed:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "❌ FAIL"
        
        print(f"\n{status} | ${balance:>3.0f} | Slots: {actual_slots:2d}/10 | ETH: {actual_eth} | BTC: {actual_btc}")
        
        if not all_passed:
            print(f"  Expected: slots={exp_slots}, ETH={exp_eth}, BTC={exp_btc}, TFs={exp_tfs}")
            print(f"  Got:      slots={actual_slots}, ETH={actual_eth}, BTC={actual_btc}, TFs={actual_tfs}")
    
    print(f"\n{'=' * 80}")
    print(f"SLOT ALLOCATION TESTS: {passed}/{passed + failed} PASSED")
    print(f"{'=' * 80}")
    
    return failed == 0


def test_position_tiers():
    """Test position tier system at $100+"""
    
    print(f"\n{'=' * 80}")
    print("POSITION TIER TESTS (BACKTEST MODE)")
    print(f"{'=' * 80}")
    
    fee_manager = FounderFeeManager(mode='BACKTEST')
    
    # Test cases: (balance, expected_tier, expected_positions_per_tf_per_asset, expected_total_slots)
    test_cases = [
        (50, 0, 1, 10),    # Below $100: tier 0
        (100, 0, 1, 10),   # At $100: tier 0 (baseline)
        (105, 0, 1, 10),   # $100-109: tier 0
        (110, 1, 2, 20),   # $110: tier 1 (after first fee milestone)
        (150, 1, 2, 20),   # $110-209: tier 1
        (210, 2, 3, 30),   # $210: tier 2 (MAXED)
        (250, 2, 3, 30),   # $210+: tier 2 (maxed)
        (500, 2, 3, 30),   # Still maxed at tier 2
    ]
    
    passed = 0
    failed = 0
    
    for balance, exp_tier, exp_per_tf, exp_total in test_cases:
        # Simulate tier update (backtest mode doesn't collect fees)
        fee_manager.check_and_collect(
            current_balance=balance,
            active_timeframes=['1m', '5m', '15m', '1h', '4h'],
            active_assets=['ETH', 'BTC'],
            mode='BACKTEST'
        )
        
        actual_tier = fee_manager.config.get('position_tier', 0)
        actual_per_tf = fee_manager.get_position_limit()
        actual_total = fee_manager.get_total_position_limit()
        
        if actual_tier == exp_tier and actual_per_tf == exp_per_tf and actual_total == exp_total:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "❌ FAIL"
        
        print(f"{status} | ${balance:>3.0f} | Tier: {actual_tier} | Per TF/Asset: {actual_per_tf} | Total: {actual_total}")
        
        if actual_tier != exp_tier or actual_per_tf != exp_per_tf or actual_total != exp_total:
            print(f"  Expected: tier={exp_tier}, per_tf={exp_per_tf}, total={exp_total}")
            print(f"  Got:      tier={actual_tier}, per_tf={actual_per_tf}, total={actual_total}")
    
    print(f"\n{'=' * 80}")
    print(f"POSITION TIER TESTS: {passed}/{passed + failed} PASSED")
    print(f"{'=' * 80}")
    
    return failed == 0


def test_alternation_pattern():
    """Test that ETH→BTC alternation is correct"""
    
    print(f"\n{'=' * 80}")
    print("ETH→BTC ALTERNATION PATTERN TEST")
    print(f"{'=' * 80}")
    
    strategy = get_slot_allocation_strategy()
    
    # Expected pattern: odd slots = ETH, even slots = BTC
    expected_pattern = {
        1: 'ETH', 2: 'BTC', 3: 'ETH', 4: 'BTC', 5: 'ETH',
        6: 'BTC', 7: 'ETH', 8: 'BTC', 9: 'ETH', 10: 'BTC'
    }
    
    passed = 0
    failed = 0
    
    for slot_num, expected_asset in expected_pattern.items():
        actual_asset = strategy.get_slot_asset(slot_num)
        
        if actual_asset.name == expected_asset:
            passed += 1
            status = "✅"
        else:
            failed += 1
            status = "❌"
        
        print(f"{status} Slot {slot_num:2d}: {actual_asset.name:3s} (expected: {expected_asset})")
    
    print(f"\n{'=' * 80}")
    print(f"ALTERNATION TESTS: {passed}/{passed + failed} PASSED")
    print(f"{'=' * 80}")
    
    return failed == 0


def test_timeframe_progression():
    """Test that timeframes unlock correctly by slot count"""
    
    print(f"\n{'=' * 80}")
    print("TIMEFRAME PROGRESSION TEST")
    print(f"{'=' * 80}")
    
    strategy = get_slot_allocation_strategy()
    
    # Expected timeframe unlocks
    expected = {
        1: ['1m'],
        2: ['1m'],
        3: ['1m', '5m'],
        4: ['1m', '5m'],
        5: ['1m', '5m', '15m'],
        6: ['1m', '5m', '15m'],
        7: ['1m', '5m', '15m', '1h'],
        8: ['1m', '5m', '15m', '1h'],
        9: ['1m', '5m', '15m', '1h', '4h'],
        10: ['1m', '5m', '15m', '1h', '4h']
    }
    
    passed = 0
    failed = 0
    
    for slots, exp_tfs in expected.items():
        balance = slots * 10  # Each slot = $10
        actual_tfs = strategy.get_active_timeframes(balance)
        
        if actual_tfs == exp_tfs:
            passed += 1
            status = "✅"
        else:
            failed += 1
            status = "❌"
        
        print(f"{status} {slots:2d} slots (${balance:>3.0f}): {', '.join(actual_tfs):30s} | Expected: {', '.join(exp_tfs)}")
    
    print(f"\n{'=' * 80}")
    print(f"TIMEFRAME PROGRESSION TESTS: {passed}/{passed + failed} PASSED")
    print(f"{'=' * 80}")
    
    return failed == 0


def test_balance_drops():
    """Test that slots deactivate when balance drops"""
    
    print(f"\n{'=' * 80}")
    print("BALANCE DROP / SLOT DEACTIVATION TEST")
    print(f"{'=' * 80}")
    
    strategy = get_slot_allocation_strategy()
    
    # Test balance drops
    test_scenarios = [
        # (from_balance, to_balance, expected_slots_lost)
        (100, 95, 1),   # Lose slot 10
        (100, 85, 2),   # Lose slots 9-10
        (70, 55, 2),    # Lose slots 7-8
        (50, 35, 2),    # Lose slots 5-6
        (30, 15, 2),    # Lose slots 3-4
        (20, 5, 2),     # Lose all slots
    ]
    
    passed = 0
    failed = 0
    
    for from_bal, to_bal, exp_lost in test_scenarios:
        from_slots = strategy.get_active_slots(from_bal)
        to_slots = strategy.get_active_slots(to_bal)
        actual_lost = from_slots - to_slots
        
        if actual_lost == exp_lost:
            passed += 1
            status = "✅"
        else:
            failed += 1
            status = "❌"
        
        print(f"{status} ${from_bal:>3.0f} → ${to_bal:>3.0f}: Lost {actual_lost} slots ({from_slots}→{to_slots}) | Expected: {exp_lost}")
    
    print(f"\n{'=' * 80}")
    print(f"BALANCE DROP TESTS: {passed}/{passed + failed} PASSED")
    print(f"{'=' * 80}")
    
    return failed == 0


def main():
    """Run all validation tests"""
    
    print("\n" + "=" * 80)
    print("COMPREHENSIVE SLOT ALLOCATION VALIDATION")
    print("=" * 80)
    
    results = []
    
    # Run all test suites
    results.append(("Slot Allocation", test_slot_allocation()))
    results.append(("ETH→BTC Alternation", test_alternation_pattern()))
    results.append(("Timeframe Progression", test_timeframe_progression()))
    results.append(("Position Tiers", test_position_tiers()))
    results.append(("Balance Drops", test_balance_drops()))
    
    # Summary
    print(f"\n{'=' * 80}")
    print("FINAL RESULTS")
    print(f"{'=' * 80}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")
    
    print(f"\n{'=' * 80}")
    print(f"OVERALL: {total_passed}/{total_tests} TEST SUITES PASSED")
    
    if total_passed == total_tests:
        print("🎉 ALL VALIDATION TESTS PASSED - SYSTEM READY")
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW IMPLEMENTATION")
    
    print(f"{'=' * 80}\n")
    
    return total_passed == total_tests


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
