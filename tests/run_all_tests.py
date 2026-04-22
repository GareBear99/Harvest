#!/usr/bin/env python3
"""
Master Validation Suite
Runs all validation tests for the trading system
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_determinism import test_determinism
from tests.test_base_strategy import test_base_strategy


def run_all_tests():
    """Run all validation tests"""
    
    print(f"\n{'#'*80}")
    print("TRADING SYSTEM VALIDATION SUITE")
    print(f"{'#'*80}")
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nRunning comprehensive validation tests...")
    
    results = {}
    
    # Test 1: Determinism
    try:
        print(f"\n{'='*80}")
        print("TEST 1: DETERMINISM")
        print(f"{'='*80}")
        results['determinism'] = test_determinism()
    except Exception as e:
        print(f"\n❌ Determinism test crashed: {e}")
        results['determinism'] = False
    
    # Test 2: Base Strategy
    try:
        print(f"\n{'='*80}")
        print("TEST 2: BASE STRATEGY")
        print(f"{'='*80}")
        results['base_strategy'] = test_base_strategy()
    except Exception as e:
        print(f"\n❌ Base strategy test crashed: {e}")
        results['base_strategy'] = False
    
    # Summary
    print(f"\n{'#'*80}")
    print("VALIDATION SUITE RESULTS")
    print(f"{'#'*80}\n")
    
    all_passed = True
    
    print("Test Results:")
    print(f"  1. Determinism:    {'✅ PASS' if results.get('determinism') else '❌ FAIL'}")
    print(f"  2. Base Strategy:  {'✅ PASS' if results.get('base_strategy') else '❌ FAIL'}")
    
    all_passed = all(results.values())
    
    print(f"\n{'='*80}")
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nThe trading system is validated and ready for production.")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease fix the failing tests before using in production.")
    print(f"{'='*80}\n")
    
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return all_passed


if __name__ == "__main__":
    passed = run_all_tests()
    sys.exit(0 if passed else 1)
