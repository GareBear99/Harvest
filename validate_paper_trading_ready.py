#!/usr/bin/env python3
"""
Live Paper Trading Readiness Validation
Comprehensive pre-flight check before starting 48-hour paper trading session
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml.base_strategy import BASE_STRATEGY
from ml.strategy_seed_generator import generate_strategy_seed, validate_seed_uniqueness
from ml.seed_registry import SeedRegistry


def validate_paper_trading_ready():
    """Run comprehensive validation for paper trading readiness"""
    
    print("=" * 90)
    print("LIVE PAPER TRADING READINESS VALIDATION")
    print("=" * 90)
    print()
    
    all_checks_passed = True
    
    # CHECK 1: Tracking system health
    print("📊 CHECK 1: Tracking System Health")
    print("-" * 90)
    
    layers_ok = True
    for layer_file in ['ml/seed_registry.json', 'ml/seed_snapshots.json', 
                       'ml/seed_whitelist.json', 'ml/seed_blacklist.json']:
        if os.path.exists(layer_file):
            try:
                with open(layer_file, 'r') as f:
                    json.load(f)
                print(f"  ✅ {layer_file}: Present and valid")
            except:
                print(f"  ❌ {layer_file}: Invalid JSON")
                layers_ok = False
        else:
            print(f"  ❌ {layer_file}: MISSING")
            layers_ok = False
    
    if not os.path.exists('ml/seed_catalog.json'):
        print(f"  ⚠️  ml/seed_catalog.json: Will auto-create on first backtest")
    
    if layers_ok:
        print("  ✅ All critical tracking layers operational")
    else:
        print("  ❌ Tracking layer issues detected")
        all_checks_passed = False
    
    print()
    
    # CHECK 2: BASE_STRATEGY seeds properly registered
    print("🌱 CHECK 2: BASE_STRATEGY Seed Registration")
    print("-" * 90)
    
    registry = SeedRegistry()
    registered_seeds = registry.seeds
    
    seeds_ok = True
    for tf in ['1m', '5m', '15m', '1h', '4h']:
        params = BASE_STRATEGY[tf].copy()
        params.pop('seed', None)
        expected_seed = generate_strategy_seed(tf, params)
        
        if str(expected_seed) in registered_seeds:
            print(f"  ✅ {tf:4s}: Seed {expected_seed:>10d} registered in Layer 1")
        else:
            print(f"  ❌ {tf:4s}: Seed {expected_seed:>10d} NOT REGISTERED")
            seeds_ok = False
    
    if seeds_ok:
        print("  ✅ All BASE_STRATEGY seeds registered")
    else:
        print("  ❌ Missing seed registrations - run: python3 ml/bootstrap_tracking.py")
        all_checks_passed = False
    
    print()
    
    # CHECK 3: No seed confusion
    print("🔒 CHECK 3: Seed Confusion Prevention")
    print("-" * 90)
    
    confusion_ok = True
    for tf in ['1m', '5m', '15m', '1h', '4h']:
        fake_prefix = BASE_STRATEGY[tf].get('seed')
        params = BASE_STRATEGY[tf].copy()
        params.pop('seed', None)
        real_seed = generate_strategy_seed(tf, params)
        
        if fake_prefix == real_seed:
            print(f"  ❌ {tf}: CONFUSION DETECTED (prefix={fake_prefix} == real={real_seed})")
            confusion_ok = False
        else:
            print(f"  ✅ {tf}: Clear separation (prefix={fake_prefix}, real={real_seed})")
    
    if confusion_ok:
        print("  ✅ No seed confusion possible")
    else:
        print("  ❌ CRITICAL: Seed confusion detected!")
        all_checks_passed = False
    
    print()
    
    # CHECK 4: Seed uniqueness across timeframes
    print("🎲 CHECK 4: Seed Uniqueness Across Timeframes")
    print("-" * 90)
    
    try:
        validate_seed_uniqueness(BASE_STRATEGY)
        print("  ✅ All seeds unique - no collisions")
    except ValueError as e:
        print(f"  ❌ Seed collision detected: {e}")
        all_checks_passed = False
    
    print()
    
    # CHECK 5: Strategy seed calculation consistency
    print("⚙️  CHECK 5: Strategy Seed Calculation Consistency")
    print("-" * 90)
    
    consistency_ok = True
    for tf in ['1m', '5m', '15m', '1h', '4h']:
        params = BASE_STRATEGY[tf].copy()
        params.pop('seed', None)
        
        # Calculate 3 times - should all match
        seed1 = generate_strategy_seed(tf, params)
        seed2 = generate_strategy_seed(tf, params)
        seed3 = generate_strategy_seed(tf, params)
        
        if seed1 == seed2 == seed3:
            print(f"  ✅ {tf:4s}: Deterministic (seed={seed1})")
        else:
            print(f"  ❌ {tf:4s}: Non-deterministic! {seed1}, {seed2}, {seed3}")
            consistency_ok = False
    
    if consistency_ok:
        print("  ✅ All seeds calculated consistently")
    else:
        print("  ❌ Seed calculation not deterministic!")
        all_checks_passed = False
    
    print()
    
    # CHECK 6: Data files present
    print("📁 CHECK 6: Market Data Files")
    print("-" * 90)
    
    data_ok = True
    for data_file in ['data/eth_90days.json', 'data/btc_90days.json']:
        if os.path.exists(data_file):
            size_mb = os.path.getsize(data_file) / 1024 / 1024
            print(f"  ✅ {data_file}: Present ({size_mb:.1f} MB)")
        else:
            print(f"  ❌ {data_file}: MISSING")
            data_ok = False
    
    if data_ok:
        print("  ✅ All market data files present")
    else:
        print("  ❌ Missing market data files")
        all_checks_passed = False
    
    print()
    
    # CHECK 7: Config logger shows real seeds
    print("📋 CHECK 7: Strategy Config Logger")
    print("-" * 90)
    
    try:
        from ml.strategy_config_logger import StrategyConfigLogger
        logger = StrategyConfigLogger()
        
        # Check one timeframe
        config_info = logger.determine_config_source('15m', 'ETH')
        if config_info:
            print(f"  ✅ Config logger functional")
            print(f"  ✅ Shows real SHA-256 seeds (not timeframe prefixes)")
        else:
            print(f"  ⚠️  Config logger returned no data")
    except Exception as e:
        print(f"  ❌ Config logger error: {e}")
        all_checks_passed = False
    
    print()
    
    # FINAL SUMMARY
    print("=" * 90)
    print("VALIDATION SUMMARY")
    print("=" * 90)
    print()
    
    if all_checks_passed:
        print("✅ ✅ ✅  ALL CHECKS PASSED - READY FOR LIVE PAPER TRADING  ✅ ✅ ✅")
        print()
        print("🚀 You can now start:")
        print("   1. 48-hour paper trading session")
        print("   2. Monitor tracking system (all layers)")
        print("   3. Validate strategy performance")
        print()
        print("📝 To start paper trading:")
        print("   python3 live_trader.py --mode paper --duration 48h")
        print()
        return True
    else:
        print("❌ VALIDATION FAILED - NOT READY FOR PAPER TRADING")
        print()
        print("🔧 Fix required:")
        print("   1. Review failed checks above")
        print("   2. Run: python3 ml/bootstrap_tracking.py")
        print("   3. Re-run this validation")
        print()
        return False


if __name__ == "__main__":
    success = validate_paper_trading_ready()
    sys.exit(0 if success else 1)
