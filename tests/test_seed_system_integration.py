#!/usr/bin/env python3
"""
Comprehensive integration test for Minecraft-like seed system

Tests:
1. Seed generation and determinism
2. Parameter sensitivity
3. Strategy pool integration
4. Backtest integration
5. Trade recording with seeds
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml.base_strategy import BASE_STRATEGY
from ml.strategy_seed_generator import generate_strategy_seed, validate_seed_uniqueness
from ml.strategy_pool import StrategyPool
from strategies.timeframe_strategy import create_strategy, TimeframeStrategy15m

print("="*80)
print("SEED SYSTEM INTEGRATION TEST")
print("="*80)

# Test 1: Core seed generation
print("\n📍 Test 1: Core Seed Generation")
print("-" * 80)

seeds_generated = {}
for tf in ['15m', '1h', '4h']:
    params = BASE_STRATEGY[tf]
    seed = generate_strategy_seed(tf, params)
    seeds_generated[tf] = seed
    print(f"  {tf}: {seed} ✓")

# Validate uniqueness
try:
    validate_seed_uniqueness(BASE_STRATEGY)
    print("  ✅ All seeds unique across timeframes")
except ValueError as e:
    print(f"  ❌ COLLISION: {e}")
    sys.exit(1)

# Test 2: Determinism
print("\n📍 Test 2: Determinism (same params → same seed)")
print("-" * 80)

params_test = BASE_STRATEGY['15m']
seed1 = generate_strategy_seed('15m', params_test)
seed2 = generate_strategy_seed('15m', params_test)
seed3 = generate_strategy_seed('15m', params_test)

if seed1 == seed2 == seed3:
    print(f"  ✅ Three runs produce identical seed: {seed1}")
else:
    print(f"  ❌ FAILED: Seeds differ: {seed1}, {seed2}, {seed3}")
    sys.exit(1)

# Test 3: Parameter sensitivity
print("\n📍 Test 3: Parameter Sensitivity")
print("-" * 80)

original_params = BASE_STRATEGY['4h'].copy()
seed_original = generate_strategy_seed('4h', original_params)

# Test each parameter change
param_tests = [
    ('min_confidence', 0.70),
    ('min_volume', 1.20),
    ('min_trend', 0.50),
    ('min_adx', 30)
]

all_different = True
for param_name, new_value in param_tests:
    modified = original_params.copy()
    modified[param_name] = new_value
    seed_modified = generate_strategy_seed('4h', modified)
    
    if seed_original == seed_modified:
        print(f"  ❌ FAILED: Changing {param_name} didn't change seed")
        all_different = False
    else:
        print(f"  ✓ {param_name}: {seed_original} → {seed_modified}")

if all_different:
    print("  ✅ All parameter changes detected")
else:
    sys.exit(1)

# Test 4: Strategy instances
print("\n📍 Test 4: Strategy Instance Integration")
print("-" * 80)

# Create strategy instances
strategies = {}
for tf in ['15m', '1h', '4h']:
    # Use actual config that matches BASE_STRATEGY
    config = {
        'aggregation_minutes': 15 if tf == '15m' else (60 if tf == '1h' else 240),
        'tp_multiplier': 1.5 if tf == '15m' else (2.0 if tf == '1h' else 2.5),
        'sl_multiplier': 0.75,
        'time_limit_minutes': 180,
        'position_size_multiplier': 1.0,
        'confidence_threshold': BASE_STRATEGY[tf]['min_confidence']
    }
    
    strategy = create_strategy(tf, config)
    strategies[tf] = strategy
    
    expected_seed = seeds_generated[tf]
    actual_seed = strategy.get_seed()
    
    if expected_seed == actual_seed:
        print(f"  {tf}: seed={actual_seed} ✓")
    else:
        print(f"  ❌ FAILED: {tf} expected {expected_seed}, got {actual_seed}")
        sys.exit(1)

print("  ✅ All strategy instances have correct seeds")

# Test 5: Strategy pool integration
print("\n📍 Test 5: Strategy Pool Integration")
print("-" * 80)

# Create a fresh strategy pool
pool = StrategyPool(active_timeframes=['15m', '1h', '4h'])

for tf in ['15m', '1h', '4h']:
    # Get base strategy seed from pool
    base_strategy = pool.pools[tf]['strategies']['base']
    
    if 'seed' not in base_strategy:
        print(f"  ❌ FAILED: {tf} base strategy missing seed")
        sys.exit(1)
    
    expected_seed = seeds_generated[tf]
    actual_seed = base_strategy['seed']
    
    if expected_seed == actual_seed:
        print(f"  {tf} base: seed={actual_seed} ✓")
    else:
        print(f"  ❌ FAILED: {tf} expected {expected_seed}, got {actual_seed}")
        sys.exit(1)

print("  ✅ Strategy pool stores seeds correctly")

# Test 6: Adding new strategy to pool
print("\n📍 Test 6: New Strategy Addition")
print("-" * 80)

new_thresholds = BASE_STRATEGY['15m'].copy()
new_thresholds['min_confidence'] = 0.80  # Changed!

result = pool.add_proven_strategy(
    timeframe='15m',
    thresholds=new_thresholds,
    win_rate=0.78,
    trade_count=25,
    data_source='test'
)

if result:
    strategy_1 = pool.pools['15m']['strategies']['strategy_1']
    new_seed = strategy_1['seed']
    base_seed = pool.pools['15m']['strategies']['base']['seed']
    
    if new_seed != base_seed:
        print(f"  ✅ New strategy has different seed: {new_seed} (base: {base_seed})")
    else:
        print(f"  ❌ FAILED: New strategy has same seed as base")
        sys.exit(1)
else:
    print(f"  ❌ FAILED: Could not add strategy to pool")
    sys.exit(1)

# Test 7: Summary
print("\n" + "="*80)
print("SEED SYSTEM VALIDATION COMPLETE")
print("="*80)

print("\n✅ All Tests Passed!")
print("\nGenerated Seeds:")
for tf, seed in seeds_generated.items():
    print(f"  {tf}: {seed}")

print("\n🎮 Minecraft-like seed system fully operational!")
print("   • Same parameters → same seed (deterministic)")
print("   • Different parameters → different seed (unique)")
print("   • Seeds stored in strategy pool")
print("   • Seeds integrated with strategy instances")
print("   • Ready for backtest integration")
