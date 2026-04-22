#!/usr/bin/env python3
"""
Comprehensive Seed Reproducibility Test

Tests that:
1. Same input seed → same parameters (always)
2. Same parameters → same strategy seed (always)
3. Configuration snapshots work correctly
4. Adding new parameters doesn't break old seeds
5. Stats match when using same data
"""

import sys
from ml.seed_to_strategy import seed_to_strategy
from ml.strategy_seed_generator import generate_strategy_seed
from ml.seed_snapshot import SeedSnapshot
from ml.seed_versioning import generate_versioned_seed, PARAMETER_VERSIONS

print("="*80)
print("COMPREHENSIVE SEED REPRODUCIBILITY TEST")
print("="*80)

# Test 1: Input seed reproducibility
print("\n📍 TEST 1: Input Seed → Parameters Reproducibility")
print("-"*80)

input_seed = 777
timeframe = '15m'

# Generate 10 times
params_list = [seed_to_strategy(timeframe, input_seed) for _ in range(10)]

# Check all identical
all_same = all(p == params_list[0] for p in params_list)

if all_same:
    print(f"✅ Input seed {input_seed} produces identical parameters 10/10 times")
    print(f"   Sample: conf={params_list[0]['min_confidence']}, vol={params_list[0]['min_volume']}")
else:
    print(f"❌ FAILED: Input seed {input_seed} produced different parameters!")
    sys.exit(1)

# Test 2: Strategy seed reproducibility
print("\n📍 TEST 2: Parameters → Strategy Seed Reproducibility")
print("-"*80)

params = params_list[0]
strategy_seeds = [generate_strategy_seed(timeframe, params) for _ in range(10)]

all_same = all(s == strategy_seeds[0] for s in strategy_seeds)

if all_same:
    print(f"✅ Parameters produce identical strategy seed 10/10 times")
    print(f"   Strategy seed: {strategy_seeds[0]}")
else:
    print(f"❌ FAILED: Parameters produced different strategy seeds!")
    sys.exit(1)

# Test 3: Complete round-trip
print("\n📍 TEST 3: Complete Round-Trip Consistency")
print("-"*80)

print(f"Input seed {input_seed} →")
print(f"  Parameters: {params}")
print(f"  Strategy seed: {strategy_seeds[0]}")

# Do round trip again
params_rt = seed_to_strategy(timeframe, input_seed)
strategy_seed_rt = generate_strategy_seed(timeframe, params_rt)

if params == params_rt and strategy_seeds[0] == strategy_seed_rt:
    print(f"✅ Complete round-trip produces identical results")
else:
    print(f"❌ FAILED: Round-trip produced different results!")
    sys.exit(1)

# Test 4: Snapshot creation and verification
print("\n📍 TEST 4: Snapshot Creation & Verification")
print("-"*80)

snapshot_mgr = SeedSnapshot("ml/seed_snapshots_test.json")

# Create snapshot
snapshot = snapshot_mgr.create_snapshot(
    seed=strategy_seeds[0],
    timeframe=timeframe,
    parameters=params,
    version='v1',
    input_seed=input_seed,
    backtest_stats={'win_rate': 0.82, 'trades': 18, 'wins': 15, 'losses': 3}
)

print(f"✅ Created snapshot for seed {strategy_seeds[0]}")
print(f"   Config hash: {snapshot['config_hash']}")

# Verify immediately
result = snapshot_mgr.verify_seed(
    seed=strategy_seeds[0],
    parameters=params,
    backtest_stats={'win_rate': 0.82, 'trades': 18, 'wins': 15, 'losses': 3}
)

if result['verified']:
    print(f"✅ Immediate verification passed")
    if result.get('stats_match'):
        print(f"✅ Stats match exactly")
else:
    print(f"❌ FAILED: Immediate verification failed!")
    sys.exit(1)

# Test 5: Detect parameter changes
print("\n📍 TEST 5: Detecting Parameter Changes")
print("-"*80)

params_modified = params.copy()
params_modified['min_confidence'] = 0.99  # Changed!

result_modified = snapshot_mgr.verify_seed(strategy_seeds[0], params_modified)

if not result_modified['verified']:
    print(f"✅ Correctly detected parameter change")
    print(f"   Changed: {list(result_modified['differences']['changed'].keys())}")
else:
    print(f"❌ FAILED: Did not detect parameter change!")
    sys.exit(1)

# Test 6: Multiple input seeds
print("\n📍 TEST 6: Multiple Input Seeds Generate Unique Configs")
print("-"*80)

test_seeds = [1, 42, 100, 777, 12345]
configs = {}

for input_s in test_seeds:
    p = seed_to_strategy(timeframe, input_s)
    strat_seed = generate_strategy_seed(timeframe, p)
    configs[input_s] = (p, strat_seed)

# Check all unique
strategy_seeds_set = set(c[1] for c in configs.values())
if len(strategy_seeds_set) == len(test_seeds):
    print(f"✅ All {len(test_seeds)} input seeds produced unique strategy seeds")
    for input_s, (p, strat_seed) in configs.items():
        print(f"   Input {input_s:5d} → Strategy seed {strat_seed}")
else:
    print(f"❌ FAILED: Collision detected among {len(test_seeds)} seeds!")
    sys.exit(1)

# Test 7: Versioned seeds with v1
print("\n📍 TEST 7: Versioned Seeds (v1)")
print("-"*80)

versioned_seed = generate_versioned_seed(timeframe, params, version='v1')
print(f"Version: {versioned_seed['version']}")
print(f"Seed: {versioned_seed['seed']}")

# Generate again
versioned_seed_2 = generate_versioned_seed(timeframe, params, version='v1')

if versioned_seed['seed'] == versioned_seed_2['seed']:
    print(f"✅ v1 versioned seed is reproducible")
else:
    print(f"❌ FAILED: v1 seed not reproducible!")
    sys.exit(1)

# Test 8: Future-proofing with v2 (simulated)
print("\n📍 TEST 8: Adding New Parameters (v2) Doesn't Break v1")
print("-"*80)

# Add v2 temporarily
PARAMETER_VERSIONS['v2'] = PARAMETER_VERSIONS['v1'] + ['rsi_threshold', 'macd_threshold']

params_v2 = params.copy()
params_v2['rsi_threshold'] = 70.0
params_v2['macd_threshold'] = 0.05

# Generate v2 seed
versioned_seed_v2 = generate_versioned_seed(timeframe, params_v2, version='v2')

# Verify v1 seed unchanged
versioned_seed_v1_check = generate_versioned_seed(timeframe, params, version='v1')

if versioned_seed['seed'] == versioned_seed_v1_check['seed']:
    print(f"✅ v1 seed unchanged after v2 addition")
    print(f"   v1 seed: {versioned_seed['seed']}")
    print(f"   v2 seed: {versioned_seed_v2['seed']}")
else:
    print(f"❌ FAILED: v1 seed changed after v2 addition!")
    print(f"   Original: {versioned_seed['seed']}")
    print(f"   After v2: {versioned_seed_v1_check['seed']}")
    sys.exit(1)

# Test 9: Simulate system restart (reload and verify)
print("\n📍 TEST 9: System Restart - Verify Snapshots Persist")
print("-"*80)

# Create new snapshot manager (simulates restart)
snapshot_mgr_2 = SeedSnapshot("ml/seed_snapshots_test.json")

# Verify seed again after "restart"
result_after_restart = snapshot_mgr_2.verify_seed(
    seed=strategy_seeds[0],
    parameters=params
)

if result_after_restart['verified']:
    print(f"✅ Snapshot verified after system restart")
    print(f"   Verifications logged: {len(snapshot_mgr_2.snapshots[str(strategy_seeds[0])]['verification_history'])}")
else:
    print(f"❌ FAILED: Verification failed after restart!")
    sys.exit(1)

# Test 10: Complete workflow simulation
print("\n📍 TEST 10: Complete Workflow Simulation")
print("-"*80)

print("Simulating: Test 5 different seeds, verify all reproducible")

test_input_seeds = [10, 20, 30, 40, 50]
workflow_snapshots = SeedSnapshot("ml/seed_snapshots_workflow.json")

for input_s in test_input_seeds:
    # Generate config
    p = seed_to_strategy(timeframe, input_s)
    strat_seed = generate_strategy_seed(timeframe, p)
    
    # Create snapshot
    workflow_snapshots.create_snapshot(
        seed=strat_seed,
        timeframe=timeframe,
        parameters=p,
        version='v1',
        input_seed=input_s,
        backtest_stats={'win_rate': 0.70, 'trades': 20}
    )
    
    # Immediately verify
    verify_result = workflow_snapshots.verify_seed(strat_seed, p)
    
    if not verify_result['verified']:
        print(f"❌ FAILED: Seed {strat_seed} verification failed!")
        sys.exit(1)

print(f"✅ All {len(test_input_seeds)} seeds verified successfully")

# Final report
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)

tests = [
    "Input Seed → Parameters Reproducibility",
    "Parameters → Strategy Seed Reproducibility",
    "Complete Round-Trip Consistency",
    "Snapshot Creation & Verification",
    "Detecting Parameter Changes",
    "Multiple Seeds Generate Unique Configs",
    "Versioned Seeds (v1)",
    "Adding v2 Parameters Doesn't Break v1",
    "System Restart - Snapshots Persist",
    "Complete Workflow Simulation"
]

print("\n✅ ALL TESTS PASSED!\n")
for i, test in enumerate(tests, 1):
    print(f"  {i}. {test}")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("""
✅ Seed system is FULLY REPRODUCIBLE

Verified:
• Same input seed always produces same parameters
• Same parameters always produce same strategy seed
• Configuration snapshots correctly detect changes
• Adding new parameters (v2) doesn't break old seeds (v1)
• System restart preserves all snapshots
• Complete workflow maintains reproducibility

You can now:
1. Test any seed with confidence it will reproduce
2. Add new parameters without breaking old seeds
3. Detect if ANY configuration change occurs
4. Track complete history of every seed tested

Ready for production! 🎉
""")
