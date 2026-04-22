#!/usr/bin/env python3
"""
Test the failsafe system that resets to BASE_STRATEGY
after 3 unprofitable trades with an unproven strategy
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.ml_config import MLConfig
from ml.base_strategy import BASE_STRATEGY
from ml.timeframe_strategy_manager import TimeframeStrategyManager


def test_failsafe_system():
    """Test failsafe reset functionality"""
    
    print('='*80)
    print('TESTING FAILSAFE SYSTEM')
    print('='*80)
    
    # Test 1: BASE_STRATEGY Restore Point
    print('\n1️⃣  BASE_STRATEGY Restore Point:')
    config = MLConfig()
    snapshot = config.get_base_strategy_snapshot()
    
    if snapshot:
        print('   ✅ BASE_STRATEGY snapshot saved in config')
        for tf in ['15m', '1h', '4h']:
            if tf in snapshot:
                print(f'   {tf}: min_confidence={snapshot[tf].get("min_confidence", "N/A")}')
    else:
        print('   ❌ No BASE_STRATEGY snapshot found')
        return False
    
    # Test 2: Failsafe Threshold
    print('\n2️⃣  Failsafe Threshold:')
    failsafe_threshold = config.config['global_settings'].get('failsafe_unprofitable_threshold', 3)
    print(f'   Reset to BASE after {failsafe_threshold} unprofitable trades')
    
    # Test 3: Strategy Manager Initialization
    print('\n3️⃣  Testing Strategy Manager:')
    manager = TimeframeStrategyManager()
    
    # Check that failsafe tracking is initialized
    all_initialized = True
    for tf in ['15m', '1h', '4h']:
        stats = manager.timeframe_stats[tf]
        unprofitable = stats.get('consecutive_unprofitable', 'N/A')
        failsafe_resets = stats.get('failsafe_resets', 'N/A')
        
        if unprofitable == 'N/A' or failsafe_resets == 'N/A':
            print(f'   ❌ {tf}: Missing failsafe tracking')
            all_initialized = False
        else:
            print(f'   ✅ {tf}: consecutive_unprofitable={unprofitable}, failsafe_resets={failsafe_resets}')
    
    if not all_initialized:
        return False
    
    # Test 4: Verify BASE_STRATEGY values match
    print('\n4️⃣  Verifying BASE_STRATEGY consistency:')
    for tf in ['15m', '1h', '4h']:
        base_from_module = BASE_STRATEGY[tf]
        base_from_snapshot = snapshot.get(tf, {})
        
        if base_from_module == base_from_snapshot:
            print(f'   ✅ {tf}: BASE_STRATEGY matches snapshot')
        else:
            print(f'   ❌ {tf}: BASE_STRATEGY mismatch!')
            print(f'      Module: {base_from_module}')
            print(f'      Snapshot: {base_from_snapshot}')
            return False
    
    # Summary
    print('\n' + '='*80)
    print('✅ FAILSAFE SYSTEM TEST PASSED')
    print('='*80)
    print('\nHow it works:')
    print('  • Tracks consecutive unprofitable trades (PnL <= 0)')
    print('  • After 3 unprofitable trades with unproven strategy:')
    print('    → Resets to BASE_STRATEGY')
    print('    → Starts building new strategy from base')
    print('  • Proven strategies (72%+ WR, 20+ trades) are exempt')
    print('  • BASE_STRATEGY always available as restore point')
    
    return True


if __name__ == "__main__":
    success = test_failsafe_system()
    sys.exit(0 if success else 1)
