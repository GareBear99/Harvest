#!/usr/bin/env python3
"""
Comprehensive Bidirectional Seed System Test

Tests both directions:
1. Seed → Parameters (seed_to_strategy)
2. Parameters → Seed (generate_strategy_seed)

Validates:
- Determinism (same input → same output)
- Uniqueness (different input → different output)
- Reproducibility (round-trip consistency)
- Multiple timeframes
"""

import sys
from ml.seed_to_strategy import seed_to_strategy, generate_strategy_from_seed
from ml.strategy_seed_generator import generate_strategy_seed

def test_seed_to_params_determinism():
    """Test: Same seed → same parameters every time"""
    print("\n" + "="*80)
    print("TEST 1: SEED → PARAMETERS (Determinism)")
    print("="*80)
    
    test_cases = [
        ('15m', 42),
        ('1h', 777),
        ('4h', 12345)
    ]
    
    all_passed = True
    
    for tf, seed in test_cases:
        # Generate 5 times
        results = [seed_to_strategy(tf, seed) for _ in range(5)]
        
        # Check all identical
        first = results[0]
        if all(r == first for r in results):
            print(f"  ✅ {tf} seed={seed}: 5 runs produced identical parameters")
        else:
            print(f"  ❌ {tf} seed={seed}: Parameters differed across runs!")
            all_passed = False
    
    return all_passed


def test_seed_to_params_uniqueness():
    """Test: Different seeds → different parameters"""
    print("\n" + "="*80)
    print("TEST 2: SEED → PARAMETERS (Uniqueness)")
    print("="*80)
    
    timeframe = '15m'
    seeds = [1, 2, 3, 100, 999, 12345]
    
    params_list = [seed_to_strategy(timeframe, s) for s in seeds]
    
    # Check all different
    all_unique = True
    for i in range(len(params_list)):
        for j in range(i+1, len(params_list)):
            if params_list[i] == params_list[j]:
                print(f"  ❌ COLLISION: seed={seeds[i]} and seed={seeds[j]} produced same params!")
                all_unique = False
    
    if all_unique:
        print(f"  ✅ All {len(seeds)} seeds produced unique parameters")
        print(f"     Seeds tested: {seeds}")
    
    return all_unique


def test_params_to_seed_determinism():
    """Test: Same parameters → same strategy seed"""
    print("\n" + "="*80)
    print("TEST 3: PARAMETERS → SEED (Determinism)")
    print("="*80)
    
    # Generate some test parameters
    params = {
        'min_confidence': 0.75,
        'min_volume': 1.25,
        'min_trend': 0.55,
        'min_adx': 28,
        'min_roc': 0.18,
        'atr_min': 0.85,
        'atr_max': 2.10
    }
    
    timeframes = ['15m', '1h', '4h']
    all_passed = True
    
    for tf in timeframes:
        # Generate seed 5 times
        seeds = [generate_strategy_seed(tf, params) for _ in range(5)]
        
        if len(set(seeds)) == 1:
            print(f"  ✅ {tf}: 5 runs produced identical seed={seeds[0]}")
        else:
            print(f"  ❌ {tf}: Seeds differed: {seeds}")
            all_passed = False
    
    return all_passed


def test_params_to_seed_sensitivity():
    """Test: Different parameters → different seeds"""
    print("\n" + "="*80)
    print("TEST 4: PARAMETERS → SEED (Sensitivity)")
    print("="*80)
    
    base_params = {
        'min_confidence': 0.75,
        'min_volume': 1.25,
        'min_trend': 0.55,
        'min_adx': 28,
        'min_roc': 0.18,
        'atr_min': 0.85,
        'atr_max': 2.10
    }
    
    timeframe = '15m'
    base_seed = generate_strategy_seed(timeframe, base_params)
    
    # Test changing each parameter
    params_to_test = [
        ('min_confidence', 0.76),
        ('min_volume', 1.26),
        ('min_trend', 0.56),
        ('min_adx', 29),
        ('min_roc', 0.19)
    ]
    
    all_different = True
    for param_name, new_value in params_to_test:
        modified = base_params.copy()
        modified[param_name] = new_value
        modified_seed = generate_strategy_seed(timeframe, modified)
        
        if modified_seed != base_seed:
            print(f"  ✅ {param_name} change detected: {base_seed} → {modified_seed}")
        else:
            print(f"  ❌ {param_name} change NOT detected!")
            all_different = False
    
    return all_different


def test_round_trip_consistency():
    """Test: Seed → Params → Seed produces consistent strategy seed"""
    print("\n" + "="*80)
    print("TEST 5: ROUND-TRIP CONSISTENCY")
    print("="*80)
    print("Input Seed → Generate Params → Calculate Strategy Seed")
    
    test_cases = [
        ('15m', 42),
        ('15m', 777),
        ('1h', 100),
        ('1h', 999),
        ('4h', 12345),
        ('4h', 54321)
    ]
    
    all_passed = True
    
    for tf, input_seed in test_cases:
        # Step 1: Input seed → parameters
        params = seed_to_strategy(tf, input_seed)
        
        # Step 2: Parameters → strategy seed
        strategy_seed = generate_strategy_seed(tf, params)
        
        # Step 3: Do it again to verify consistency
        params2 = seed_to_strategy(tf, input_seed)
        strategy_seed2 = generate_strategy_seed(tf, params2)
        
        if params == params2 and strategy_seed == strategy_seed2:
            print(f"  ✅ {tf} input_seed={input_seed} → strategy_seed={strategy_seed} (consistent)")
        else:
            print(f"  ❌ {tf} input_seed={input_seed}: Inconsistent round-trip!")
            all_passed = False
    
    return all_passed


def test_cross_timeframe_isolation():
    """Test: Same input seed produces different params per timeframe"""
    print("\n" + "="*80)
    print("TEST 6: CROSS-TIMEFRAME ISOLATION")
    print("="*80)
    
    input_seed = 42
    timeframes = ['15m', '1h', '4h']
    
    params_by_tf = {}
    for tf in timeframes:
        params_by_tf[tf] = seed_to_strategy(tf, input_seed)
    
    # Check all different
    all_different = True
    tfs = list(params_by_tf.keys())
    for i in range(len(tfs)):
        for j in range(i+1, len(tfs)):
            tf1, tf2 = tfs[i], tfs[j]
            if params_by_tf[tf1] == params_by_tf[tf2]:
                print(f"  ❌ {tf1} and {tf2} produced identical params!")
                all_different = False
    
    if all_different:
        print(f"  ✅ Input seed={input_seed} produces different params per timeframe")
        for tf, params in params_by_tf.items():
            strategy_seed = generate_strategy_seed(tf, params)
            print(f"     {tf}: conf={params['min_confidence']}, "
                  f"strategy_seed={strategy_seed}")
    
    return all_different


def test_strategy_seed_uniqueness():
    """Test: Strategy seeds don't collide across different input seeds"""
    print("\n" + "="*80)
    print("TEST 7: STRATEGY SEED UNIQUENESS")
    print("="*80)
    
    timeframe = '15m'
    input_seeds = range(1, 101)  # Test 100 different input seeds
    
    strategy_seeds = []
    for input_seed in input_seeds:
        params = seed_to_strategy(timeframe, input_seed)
        strat_seed = generate_strategy_seed(timeframe, params)
        strategy_seeds.append(strat_seed)
    
    unique_count = len(set(strategy_seeds))
    total_count = len(strategy_seeds)
    
    if unique_count == total_count:
        print(f"  ✅ All {total_count} strategy seeds are unique")
        print(f"     Input seeds: 1-100")
        print(f"     Sample strategy seeds: {strategy_seeds[:5]}")
    else:
        collisions = total_count - unique_count
        print(f"  ❌ {collisions} collisions detected out of {total_count} seeds!")
    
    return unique_count == total_count


def test_reproducibility_real_world():
    """Test: Real-world scenario - reproduce a strategy configuration"""
    print("\n" + "="*80)
    print("TEST 8: REAL-WORLD REPRODUCIBILITY")
    print("="*80)
    print("Scenario: Found a good strategy with input_seed=777, reproduce it later")
    
    timeframe = '15m'
    input_seed = 777
    
    # Day 1: Test seed 777
    print(f"\n  Day 1: Testing seed {input_seed}")
    params_day1 = seed_to_strategy(timeframe, input_seed)
    strategy_seed_day1 = generate_strategy_seed(timeframe, params_day1)
    print(f"    Generated params: conf={params_day1['min_confidence']}, "
          f"vol={params_day1['min_volume']}")
    print(f"    Strategy seed: {strategy_seed_day1}")
    print(f"    Result: 80% win rate! 🎉")
    
    # Day 30: Reproduce seed 777
    print(f"\n  Day 30: Reproducing seed {input_seed}")
    params_day30 = seed_to_strategy(timeframe, input_seed)
    strategy_seed_day30 = generate_strategy_seed(timeframe, params_day30)
    print(f"    Generated params: conf={params_day30['min_confidence']}, "
          f"vol={params_day30['min_volume']}")
    print(f"    Strategy seed: {strategy_seed_day30}")
    
    # Verify identical
    if params_day1 == params_day30 and strategy_seed_day1 == strategy_seed_day30:
        print(f"\n  ✅ REPRODUCED PERFECTLY!")
        print(f"     Same parameters, same strategy seed after 30 days")
        return True
    else:
        print(f"\n  ❌ FAILED TO REPRODUCE!")
        return False


def run_all_tests():
    """Run all tests and report results"""
    
    print("="*80)
    print("COMPREHENSIVE BIDIRECTIONAL SEED SYSTEM TEST")
    print("="*80)
    print("\nTesting both directions:")
    print("  1. Input Seed → Parameters (seed_to_strategy)")
    print("  2. Parameters → Strategy Seed (generate_strategy_seed)")
    
    tests = [
        ("Seed→Params Determinism", test_seed_to_params_determinism),
        ("Seed→Params Uniqueness", test_seed_to_params_uniqueness),
        ("Params→Seed Determinism", test_params_to_seed_determinism),
        ("Params→Seed Sensitivity", test_params_to_seed_sensitivity),
        ("Round-Trip Consistency", test_round_trip_consistency),
        ("Cross-Timeframe Isolation", test_cross_timeframe_isolation),
        ("Strategy Seed Uniqueness", test_strategy_seed_uniqueness),
        ("Real-World Reproducibility", test_reproducibility_real_world)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n  ❌ EXCEPTION: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n{'='*80}")
    print(f"TOTAL: {passed_count}/{total_count} tests passed")
    print(f"{'='*80}")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! Bidirectional seed system fully operational!")
        print("\nYou can now:")
        print("  1. Pick any input seed (e.g., 777)")
        print("  2. Generate parameters from it")
        print("  3. Test in backtest")
        print("  4. Reproduce anytime with that seed")
        return 0
    else:
        print(f"\n❌ {total_count - passed_count} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
