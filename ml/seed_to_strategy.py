"""
Seed-to-Strategy Generator - REVERSE of strategy_seed_generator

Like Minecraft: Give it a seed, get reproducible random parameters.

Usage:
    seed_to_strategy(15m, 12345) → deterministic parameters
    seed_to_strategy(15m, 12345) → same parameters every time
    seed_to_strategy(15m, 67890) → different parameters
"""

import random
from typing import Dict


def seed_to_strategy(timeframe: str, seed: int) -> Dict:
    """
    Generate deterministic strategy parameters from a seed
    
    Like Minecraft: same seed always produces same parameters
    
    Args:
        timeframe: '15m', '1h', '4h'
        seed: Integer seed (e.g., 12345)
        
    Returns:
        Dict of strategy parameters
        
    Example:
        >>> params = seed_to_strategy('15m', 42)
        >>> params
        {'min_confidence': 0.73, 'min_volume': 1.22, ...}
        
        >>> params2 = seed_to_strategy('15m', 42)
        >>> params == params2  # True - same seed, same params
    """
    # Create RNG with this seed
    rng = random.Random(seed)
    
    # Define parameter ranges per timeframe
    ranges = get_parameter_ranges(timeframe)
    
    # Generate parameters deterministically
    params = {}
    for param_name, (min_val, max_val, is_int) in ranges.items():
        if is_int:
            params[param_name] = rng.randint(int(min_val), int(max_val))
        else:
            value = rng.uniform(min_val, max_val)
            params[param_name] = round(value, 2)
    
    return params


def get_parameter_ranges(timeframe: str) -> Dict:
    """
    Get valid parameter ranges for a timeframe
    
    Returns:
        Dict of {param_name: (min, max, is_integer)}
    """
    # Base ranges (apply to all timeframes)
    base_ranges = {
        'min_confidence': (0.60, 0.85, False),
        'min_volume': (1.0, 1.5, False),
        'min_trend': (0.40, 0.70, False),
        'min_adx': (20, 35, True),
        'min_roc': (0.10, 0.25, False),
        'atr_min': (0.6, 1.0, False),
        'atr_max': (1.8, 2.5, False)
    }
    
    # Timeframe-specific adjustments
    if timeframe == '15m':
        # 15m: More aggressive (higher thresholds)
        base_ranges['min_confidence'] = (0.70, 0.85, False)
        base_ranges['min_adx'] = (25, 35, True)
    elif timeframe == '1h':
        # 1h: Balanced
        base_ranges['min_confidence'] = (0.65, 0.80, False)
        base_ranges['min_adx'] = (22, 32, True)
    elif timeframe == '4h':
        # 4h: More conservative (lower thresholds)
        base_ranges['min_confidence'] = (0.60, 0.75, False)
        base_ranges['min_adx'] = (20, 30, True)
    
    return base_ranges


def generate_strategy_from_seed(timeframe: str, seed: int) -> Dict:
    """
    Full strategy generation from seed (with metadata)
    
    Returns complete strategy dict with parameters and seed info
    """
    params = seed_to_strategy(timeframe, seed)
    
    # Calculate actual seed (for reverse lookup)
    from ml.strategy_seed_generator import generate_strategy_seed
    actual_seed = generate_strategy_seed(timeframe, params)
    
    return {
        'input_seed': seed,
        'strategy_seed': actual_seed,
        'timeframe': timeframe,
        'parameters': params,
        'reproducible': True
    }


if __name__ == "__main__":
    import sys
    
    print("="*80)
    print("SEED-TO-STRATEGY GENERATOR (Minecraft-style)")
    print("="*80)
    print("\nGive it a seed → Get reproducible random parameters\n")
    
    # Allow command line args
    if len(sys.argv) >= 3:
        timeframe = sys.argv[1]
        seed = int(sys.argv[2])
    else:
        timeframe = '15m'
        seed = 42
        print(f"Usage: python ml/seed_to_strategy.py <timeframe> <seed>")
        print(f"Example: python ml/seed_to_strategy.py 15m 12345\n")
        print(f"Running default: {timeframe} with seed {seed}\n")
    
    # Generate strategy
    strategy = generate_strategy_from_seed(timeframe, seed)
    
    print(f"Timeframe: {timeframe}")
    print(f"Input Seed: {seed}")
    print(f"\nGenerated Parameters:")
    for key, value in strategy['parameters'].items():
        print(f"  {key}: {value}")
    
    print(f"\nStrategy Seed: {strategy['strategy_seed']}")
    
    # Test determinism
    print("\n" + "="*80)
    print("DETERMINISM TEST")
    print("="*80 + "\n")
    
    params1 = seed_to_strategy(timeframe, seed)
    params2 = seed_to_strategy(timeframe, seed)
    params3 = seed_to_strategy(timeframe, seed)
    
    if params1 == params2 == params3:
        print(f"✅ Same seed ({seed}) produces identical parameters every time")
    else:
        print(f"❌ FAILED: Parameters differ!")
    
    # Test different seed
    different_seed = seed + 1
    params_different = seed_to_strategy(timeframe, different_seed)
    
    if params1 != params_different:
        print(f"✅ Different seed ({different_seed}) produces different parameters")
    else:
        print(f"❌ FAILED: Different seeds produced same parameters!")
    
    # Show usage
    print("\n" + "="*80)
    print("HOW TO USE FOR TESTING")
    print("="*80)
    print(f"""
1. Pick a random seed number: {seed}

2. Generate parameters:
   python ml/seed_to_strategy.py {timeframe} {seed}

3. Copy parameters to BASE_STRATEGY in ml/base_strategy.py:
   BASE_STRATEGY['{timeframe}'] = {{
     'min_confidence': {params1['min_confidence']},
     'min_volume': {params1['min_volume']},
     'min_trend': {params1['min_trend']},
     'min_adx': {params1['min_adx']},
     'min_roc': {params1['min_roc']},
     'atr_min': {params1['atr_min']},
     'atr_max': {params1['atr_max']}
   }}

4. Run backtest

5. If it performs well, save the seed ({seed}) for reproduction!

To test many random seeds:
  for i in {{1..100}}; do
    python ml/seed_to_strategy.py {timeframe} $i >> test_results.txt
  done
""")
