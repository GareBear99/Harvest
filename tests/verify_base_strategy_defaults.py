#!/usr/bin/env python3
"""
Verify BASE_STRATEGY Defaults
Confirms that all BASE_STRATEGY values match the expected defaults
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.base_strategy import BASE_STRATEGY, get_base_strategy
import json


def verify_base_strategy_defaults():
    """Verify that BASE_STRATEGY matches expected defaults"""
    
    # Expected default values
    expected = {
        '1m': {
            'seed': 1001,
            'min_confidence': 0.82,
            'min_volume': 1.35,
            'min_trend': 0.68,
            'min_adx': 32,
            'min_roc': -1.05,
            'atr_min': 0.50,
            'atr_max': 3.0
        },
        '5m': {
            'seed': 5001,
            'min_confidence': 0.80,
            'min_volume': 1.30,
            'min_trend': 0.65,
            'min_adx': 30,
            'min_roc': -1.1,
            'atr_min': 0.45,
            'atr_max': 3.2
        },
        '15m': {
            'seed': 15001,
            'min_confidence': 0.78,
            'min_volume': 1.30,
            'min_trend': 0.65,
            'min_adx': 30,
            'min_roc': -1.1,
            'atr_min': 0.45,
            'atr_max': 3.2
        },
        '1h': {
            'seed': 60001,
            'min_confidence': 0.72,
            'min_volume': 1.20,
            'min_trend': 0.55,
            'min_adx': 27,
            'min_roc': -1.15,
            'atr_min': 0.42,
            'atr_max': 3.3
        },
        '4h': {
            'seed': 240001,
            'min_confidence': 0.63,
            'min_volume': 1.05,
            'min_trend': 0.46,
            'min_adx': 25,
            'min_roc': -1.0,
            'atr_min': 0.4,
            'atr_max': 3.5
        }
    }
    
    print("=" * 70)
    print("BASE_STRATEGY DEFAULT VERIFICATION")
    print("=" * 70)
    print()
    
    all_match = True
    
    for timeframe in ['1m', '5m', '15m', '1h', '4h']:
        print(f"Checking {timeframe}...")
        
        current = get_base_strategy(timeframe)
        exp = expected[timeframe]
        
        mismatches = []
        for key in exp.keys():
            if current.get(key) != exp[key]:
                mismatches.append(f"  ❌ {key}: current={current.get(key)} expected={exp[key]}")
                all_match = False
        
        if mismatches:
            print(f"  ❌ {timeframe} has mismatches:")
            for m in mismatches:
                print(m)
        else:
            print(f"  ✅ {timeframe} matches defaults")
        print()
    
    # Verify backup file
    print("Checking backup file...")
    backup_file = 'ml/base_strategy_backup.json'
    if os.path.exists(backup_file):
        with open(backup_file, 'r') as f:
            backup = json.load(f)
        
        if 'original' in backup:
            backup_strategies = backup['original']
            
            # Check all 5 timeframes exist
            if set(backup_strategies.keys()) == {'1m', '5m', '15m', '1h', '4h'}:
                print("  ✅ Backup contains all 5 timeframes")
            else:
                print(f"  ❌ Backup missing timeframes: {set(['1m', '5m', '15m', '1h', '4h']) - set(backup_strategies.keys())}")
                all_match = False
            
            # Check values match
            for tf in ['1m', '5m', '15m', '1h', '4h']:
                if tf in backup_strategies:
                    if backup_strategies[tf] == expected[tf]:
                        print(f"  ✅ Backup {tf} matches defaults")
                    else:
                        print(f"  ❌ Backup {tf} doesn't match defaults")
                        all_match = False
        else:
            print("  ❌ Backup file missing 'original' key")
            all_match = False
    else:
        print("  ❌ Backup file not found")
        all_match = False
    
    print()
    print("=" * 70)
    if all_match:
        print("✅ ALL BASE_STRATEGY VALUES ARE SET TO DEFAULTS")
    else:
        print("❌ SOME BASE_STRATEGY VALUES DO NOT MATCH DEFAULTS")
    print("=" * 70)
    
    return all_match


if __name__ == "__main__":
    success = verify_base_strategy_defaults()
    sys.exit(0 if success else 1)
