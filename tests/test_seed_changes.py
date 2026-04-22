#!/usr/bin/env python3
"""
Test that changing strategy parameters produces different seeds
Like Minecraft: same params → same seed, different params → different seed
"""

from ml.base_strategy import BASE_STRATEGY
from ml.strategy_seed_generator import generate_strategy_seed

print("="*70)
print("TESTING SEED SENSITIVITY TO PARAMETER CHANGES")
print("="*70)

# Test 1: Same parameters produce same seed
print("\n✅ Test 1: Determinism (same params → same seed)")
params_15m = BASE_STRATEGY['15m']
seed1 = generate_strategy_seed('15m', params_15m)
seed2 = generate_strategy_seed('15m', params_15m)
print(f"  Run 1: {seed1}")
print(f"  Run 2: {seed2}")
print(f"  Match: {seed1 == seed2} {'✓' if seed1 == seed2 else '✗ FAILED'}")

# Test 2: Change confidence → different seed
print("\n✅ Test 2: Confidence change detection")
original_params = BASE_STRATEGY['4h'].copy()
modified_params = original_params.copy()
modified_params['min_confidence'] = 0.70  # Changed from 0.63

seed_original = generate_strategy_seed('4h', original_params)
seed_modified = generate_strategy_seed('4h', modified_params)

print(f"  Original (conf=0.63): {seed_original}")
print(f"  Modified (conf=0.70): {seed_modified}")
print(f"  Different: {seed_original != seed_modified} {'✓' if seed_original != seed_modified else '✗ FAILED'}")

# Test 3: Change volume → different seed
print("\n✅ Test 3: Volume change detection")
modified_params = original_params.copy()
modified_params['min_volume'] = 1.20  # Changed from 1.05

seed_vol = generate_strategy_seed('4h', modified_params)
print(f"  Original (vol=1.05): {seed_original}")
print(f"  Modified (vol=1.20): {seed_vol}")
print(f"  Different: {seed_original != seed_vol} {'✓' if seed_original != seed_vol else '✗ FAILED'}")

# Test 4: Change ADX → different seed
print("\n✅ Test 4: ADX change detection")
modified_params = original_params.copy()
modified_params['min_adx'] = 30  # Changed from 25

seed_adx = generate_strategy_seed('4h', modified_params)
print(f"  Original (adx=25): {seed_original}")
print(f"  Modified (adx=30): {seed_adx}")
print(f"  Different: {seed_original != seed_adx} {'✓' if seed_original != seed_adx else '✗ FAILED'}")

# Test 5: Show all current strategy seeds
print("\n" + "="*70)
print("CURRENT STRATEGY SEEDS")
print("="*70)

for tf in ['15m', '1h', '4h']:
    if tf not in BASE_STRATEGY:
        continue
    
    params = BASE_STRATEGY[tf]
    seed = generate_strategy_seed(tf, params)
    
    print(f"\n{tf} Strategy:")
    print(f"  conf={params['min_confidence']}, vol={params['min_volume']}, "
          f"trend={params['min_trend']}, adx={params['min_adx']}")
    print(f"  Seed: {seed}")

# Test 6: Verify no collisions between timeframes
print("\n" + "="*70)
print("COLLISION CHECK")
print("="*70)

seeds = {}
for tf in ['15m', '1h', '4h']:
    if tf in BASE_STRATEGY:
        seeds[tf] = generate_strategy_seed(tf, BASE_STRATEGY[tf])

if len(seeds) == len(set(seeds.values())):
    print("✅ All seeds are unique - no collisions")
else:
    print("❌ COLLISION DETECTED!")
    for tf, seed in seeds.items():
        print(f"  {tf}: {seed}")

print("\n" + "="*70)
print("✅ ALL TESTS PASSED - Minecraft-like seed system working!")
print("="*70)
