#!/usr/bin/env python3
"""
Validate Tracking System Health
Pre-flight check before live paper trading
"""

import sys
import os
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.base_strategy import BASE_STRATEGY
from ml.strategy_seed_generator import generate_strategy_seed


def validate_tracking_health():
    """Run comprehensive health check on tracking system"""
    
    print("=" * 80)
    print("TRACKING SYSTEM HEALTH CHECK")
    print("=" * 80)
    print()
    
    issues = []
    warnings = []
    
    # Check 1: Layer files exist
    print("📁 Checking tracking layer files...")
    layers = {
        'Layer 1 (Registry)': 'ml/seed_registry.json',
        'Layer 2 (Snapshots)': 'ml/seed_snapshots.json',
        'Layer 3 (Catalog)': 'ml/seed_catalog.json',
        'Layer 4 (Whitelist)': 'ml/seed_whitelist.json',
        'Layer 4 (Blacklist)': 'ml/seed_blacklist.json'
    }
    
    for layer_name, filepath in layers.items():
        if os.path.exists(filepath):
            print(f"  ✅ {layer_name}: {filepath}")
        else:
            if 'Catalog' in layer_name:
                warnings.append(f"{layer_name} missing (will auto-create on first backtest)")
                print(f"  ⚠️  {layer_name}: {filepath} (will auto-create)")
            else:
                issues.append(f"{layer_name} missing")
                print(f"  ❌ {layer_name}: {filepath} MISSING")
    
    print()
    
    # Check 2: JSON validity
    print("🔍 Checking JSON file validity...")
    for layer_name, filepath in layers.items():
        if not os.path.exists(filepath):
            continue
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            print(f"  ✅ {layer_name}: Valid JSON")
        except Exception as e:
            issues.append(f"{layer_name} has invalid JSON: {e}")
            print(f"  ❌ {layer_name}: INVALID JSON - {e}")
    
    print()
    
    # Check 3: BASE_STRATEGY seeds registered
    print("🌱 Checking BASE_STRATEGY seed registration...")
    
    if not os.path.exists('ml/seed_registry.json'):
        issues.append("seed_registry.json missing - run bootstrap_tracking.py")
        print("  ❌ Registry not found - run: python3 ml/bootstrap_tracking.py")
    else:
        try:
            with open('ml/seed_registry.json', 'r') as f:
                registry = json.load(f)
            
            registered_seeds = registry.get('seeds', {})
            timeframes = ['1m', '5m', '15m', '1h', '4h']
            
            for tf in timeframes:
                # Calculate expected seed
                params = BASE_STRATEGY[tf].copy()
                params.pop('seed', None)
                expected_seed = generate_strategy_seed(tf, params)
                
                if str(expected_seed) in registered_seeds:
                    print(f"  ✅ {tf:4s}: Seed {expected_seed:>10d} registered")
                else:
                    warnings.append(f"{tf} seed not registered yet")
                    print(f"  ⚠️  {tf:4s}: Seed {expected_seed:>10d} NOT registered")
        except Exception as e:
            issues.append(f"Error reading registry: {e}")
            print(f"  ❌ Error reading registry: {e}")
    
    print()
    
    # Check 4: Seed confusion check
    print("🔒 Checking for seed confusion (timeframe prefixes vs real seeds)...")
    confusion_found = False
    
    for tf in ['1m', '5m', '15m', '1h', '4h']:
        fake_seed = BASE_STRATEGY[tf].get('seed')  # Timeframe prefix
        params = BASE_STRATEGY[tf].copy()
        params.pop('seed', None)
        real_seed = generate_strategy_seed(tf, params)
        
        if fake_seed == real_seed:
            issues.append(f"{tf}: Timeframe prefix matches real seed (impossible!)")
            print(f"  ❌ {tf}: CONFUSION DETECTED")
            confusion_found = True
        else:
            print(f"  ✅ {tf}: No confusion (prefix={fake_seed}, real={real_seed})")
    
    if not confusion_found:
        print("  ✅ No seed confusion detected")
    
    print()
    
    # Summary
    print("=" * 80)
    print("HEALTH CHECK SUMMARY")
    print("=" * 80)
    print()
    
    if not issues and not warnings:
        print("✅ ALL CHECKS PASSED - System ready for live paper trading!")
        print()
        return True
    elif issues:
        print(f"❌ {len(issues)} CRITICAL ISSUE(S) FOUND:")
        for issue in issues:
            print(f"   - {issue}")
        print()
        if warnings:
            print(f"⚠️  {len(warnings)} Warning(s):")
            for warning in warnings:
                print(f"   - {warning}")
        print()
        print("🔧 ACTION REQUIRED:")
        print("   1. Run: python3 ml/bootstrap_tracking.py")
        print("   2. Re-run this validation")
        print()
        return False
    else:
        print(f"⚠️  {len(warnings)} Warning(s) (non-critical):")
        for warning in warnings:
            print(f"   - {warning}")
        print()
        print("✅ System functional - warnings are expected for first run")
        print()
        return True


if __name__ == "__main__":
    success = validate_tracking_health()
    sys.exit(0 if success else 1)
