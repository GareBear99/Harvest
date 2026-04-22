#!/usr/bin/env python3
"""
Random Strategy Generator - Test different strategy configurations

Generates random parameter combinations and shows their automatic seeds.
Like Minecraft: change the world (parameters), get a new seed automatically.
"""

import random
import json
from ml.strategy_seed_generator import generate_strategy_seed

def generate_random_strategy(timeframe: str, base_params: dict = None) -> dict:
    """
    Generate a random strategy configuration
    
    Args:
        timeframe: '15m', '1h', or '4h'
        base_params: Optional base to vary from
        
    Returns:
        Dict of strategy parameters
    """
    # Define reasonable ranges for each parameter
    ranges = {
        'min_confidence': (0.60, 0.85),
        'min_volume': (1.0, 1.5),
        'min_trend': (0.40, 0.70),
        'min_adx': (20, 35),
        'min_roc': (0.10, 0.25),
        'atr_min': (0.6, 1.0),
        'atr_max': (1.8, 2.5)
    }
    
    params = {}
    for key, (min_val, max_val) in ranges.items():
        if key == 'min_adx':
            # Integer for ADX
            params[key] = random.randint(int(min_val), int(max_val))
        else:
            # Float for others, rounded to 2 decimals
            params[key] = round(random.uniform(min_val, max_val), 2)
    
    return params


def generate_strategy_variants(timeframe: str, count: int = 5):
    """Generate multiple random strategy variants for a timeframe"""
    
    print(f"\n{'='*80}")
    print(f"RANDOM STRATEGY GENERATOR - {timeframe.upper()}")
    print(f"{'='*80}\n")
    
    variants = []
    
    for i in range(count):
        params = generate_random_strategy(timeframe)
        seed = generate_strategy_seed(timeframe, params)
        
        variants.append({
            'variant_id': i + 1,
            'seed': seed,
            'params': params
        })
        
        print(f"Variant {i+1}:")
        print(f"  Seed: {seed}")
        print(f"  conf={params['min_confidence']}, vol={params['min_volume']}, "
              f"trend={params['min_trend']}, adx={params['min_adx']}")
        print()
    
    return variants


def save_variants_to_file(timeframe: str, variants: list, filename: str = None):
    """Save generated variants to a JSON file for testing"""
    
    if filename is None:
        filename = f"test_strategies_{timeframe}.json"
    
    output = {
        'timeframe': timeframe,
        'generated_at': '2025-12-17',
        'count': len(variants),
        'variants': variants
    }
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Saved {len(variants)} variants to {filename}")


def compare_seeds(variants: list):
    """Verify all seeds are unique"""
    seeds = [v['seed'] for v in variants]
    unique_seeds = set(seeds)
    
    if len(seeds) == len(unique_seeds):
        print(f"✅ All {len(seeds)} seeds are unique - no collisions")
    else:
        print(f"❌ WARNING: {len(seeds) - len(unique_seeds)} seed collisions detected!")


if __name__ == "__main__":
    import sys
    
    print("="*80)
    print("RANDOM STRATEGY CONFIGURATION GENERATOR")
    print("="*80)
    print("\nGenerates random parameter combinations and shows their automatic seeds")
    print("Like Minecraft: change parameters → get new seed automatically\n")
    
    # Allow command line args
    timeframe = sys.argv[1] if len(sys.argv) > 1 else '15m'
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    # Generate variants
    variants = generate_strategy_variants(timeframe, count)
    
    # Verify uniqueness
    print("="*80)
    print("VERIFICATION")
    print("="*80 + "\n")
    compare_seeds(variants)
    
    # Save to file
    print("\n" + "="*80)
    print("SAVING")
    print("="*80 + "\n")
    save_variants_to_file(timeframe, variants)
    
    # Show how to use
    print("\n" + "="*80)
    print("HOW TO USE")
    print("="*80)
    print("\nTo test a variant in BASE_STRATEGY:")
    print("1. Copy the parameters from a variant above")
    print("2. Update ml/base_strategy.py BASE_STRATEGY['{timeframe}']")
    print("3. Run backtest - seed will update automatically!")
    print("\nExample:")
    print(f"  BASE_STRATEGY['{timeframe}'] = {{")
    if variants:
        v = variants[0]
        for key, val in v['params'].items():
            print(f"    '{key}': {val},")
    print("  }")
    print(f"  # This will automatically generate seed: {variants[0]['seed']}")
    
    print("\n" + "="*80)
    print("GENERATE MORE")
    print("="*80)
    print(f"\npython generate_random_strategies.py 15m 10  # Generate 10 variants for 15m")
    print(f"python generate_random_strategies.py 1h 20   # Generate 20 variants for 1h")
    print(f"python generate_random_strategies.py 4h 15   # Generate 15 variants for 4h")
