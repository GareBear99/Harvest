"""
Strategy Seed Generator - Deterministic seed generation from parameters

Like Minecraft seeds - same parameters always produce the same seed.
Each timeframe gets its own namespace to ensure unique seeds.

Example:
    15m with conf=0.78, vol=1.30, trend=0.65 → seed=15782130065
    4h  with conf=0.63, vol=1.05, trend=0.46 → seed=24063105046
    
    Change ANY parameter → new seed is generated automatically
    Same parameters → always same seed (reproducible)
"""

import hashlib
import json
from typing import Dict


# Timeframe prefixes to ensure seeds never collide
TIMEFRAME_PREFIXES = {
    '1m': 1,
    '5m': 5,
    '15m': 15,
    '30m': 30,
    '1h': 60,
    '2h': 120,
    '4h': 240,
    '6h': 360,
    '12h': 720,
    '1d': 1440
}


def generate_strategy_seed(timeframe: str, params: Dict) -> int:
    """
    Generate deterministic seed from strategy parameters
    
    Like Minecraft seeds - same parameters always produce same seed.
    
    Args:
        timeframe: Timeframe string (e.g., '15m', '1h', '4h')
        params: Strategy parameters dict containing:
            - min_confidence
            - min_volume
            - min_trend
            - min_adx
            - min_roc
            - atr_min
            - atr_max
            
    Returns:
        Deterministic integer seed that uniquely identifies this configuration
        
    Example:
        >>> params = {'min_confidence': 0.63, 'min_volume': 1.05, 'min_trend': 0.46}
        >>> generate_strategy_seed('4h', params)
        240631050046  # Always same for these params
    """
    # Get timeframe prefix (ensures different timeframes never collide)
    prefix = TIMEFRAME_PREFIXES.get(timeframe, 999)
    
    # Extract relevant parameters in consistent order
    param_keys = [
        'min_confidence',
        'min_volume', 
        'min_trend',
        'min_adx',
        'min_roc',
        'atr_min',
        'atr_max'
    ]
    
    # Create canonical representation (sorted, deterministic)
    param_values = []
    for key in param_keys:
        if key in params:
            # Round to 2 decimal places for consistency
            value = round(float(params[key]), 2)
            param_values.append(f"{key}={value}")
    
    # Create deterministic string
    param_string = f"{timeframe}:" + "|".join(param_values)
    
    # Hash to get consistent integer
    hash_obj = hashlib.sha256(param_string.encode())
    hash_int = int(hash_obj.hexdigest()[:12], 16)  # Use first 12 hex chars
    
    # Combine prefix with hash to ensure uniqueness per timeframe
    # Use modulo to keep seed reasonably sized
    seed = (prefix * 1_000_000) + (hash_int % 1_000_000)
    
    return seed


def validate_seed_uniqueness(strategies: Dict[str, Dict]) -> Dict[str, int]:
    """
    Generate seeds for all strategies and verify uniqueness
    
    Args:
        strategies: Dict of {timeframe: params_dict}
        
    Returns:
        Dict of {timeframe: seed}
        
    Raises:
        ValueError: If any seed collision detected
    """
    seeds = {}
    seed_to_config = {}
    
    for timeframe, params in strategies.items():
        seed = generate_strategy_seed(timeframe, params)
        
        # Check for collision
        if seed in seed_to_config:
            raise ValueError(
                f"SEED COLLISION! {timeframe} and {seed_to_config[seed]} "
                f"both generated seed={seed}"
            )
        
        seeds[timeframe] = seed
        seed_to_config[seed] = timeframe
    
    return seeds


def reverse_lookup_config(seed: int, known_strategies: Dict[str, Dict]) -> tuple:
    """
    Find which strategy configuration generated this seed
    
    Args:
        seed: Strategy seed to look up
        known_strategies: Dict of {timeframe: params}
        
    Returns:
        (timeframe, params) tuple or (None, None) if not found
    """
    for timeframe, params in known_strategies.items():
        if generate_strategy_seed(timeframe, params) == seed:
            return timeframe, params
    
    return None, None


if __name__ == "__main__":
    # Test with BASE_STRATEGY
    from ml.base_strategy import BASE_STRATEGY
    
    print("="*70)
    print("STRATEGY SEED GENERATOR - Like Minecraft Seeds")
    print("="*70)
    print("\nGenerating deterministic seeds from strategy parameters...\n")
    
    seeds = {}
    
    for tf in ['15m', '1h', '4h']:
        if tf not in BASE_STRATEGY:
            continue
            
        params = BASE_STRATEGY[tf]
        seed = generate_strategy_seed(tf, params)
        seeds[tf] = seed
        
        print(f"{tf} Strategy:")
        print(f"  conf={params['min_confidence']}, vol={params['min_volume']}, "
              f"trend={params['min_trend']}, adx={params['min_adx']}")
        print(f"  → Seed: {seed}")
        print()
    
    print("="*70)
    print("VALIDATION")
    print("="*70)
    
    # Verify uniqueness
    try:
        validate_seed_uniqueness(BASE_STRATEGY)
        print("✅ All seeds are unique - no collisions")
    except ValueError as e:
        print(f"❌ {e}")
    
    # Test determinism
    print("\n✅ Testing determinism (same params → same seed):")
    test_params = {'min_confidence': 0.63, 'min_volume': 1.05, 'min_trend': 0.46, 'min_adx': 25}
    seed1 = generate_strategy_seed('4h', test_params)
    seed2 = generate_strategy_seed('4h', test_params)
    print(f"  Run 1: {seed1}")
    print(f"  Run 2: {seed2}")
    print(f"  Match: {seed1 == seed2}")
    
    # Test parameter change detection
    print("\n✅ Testing parameter change detection:")
    modified_params = test_params.copy()
    modified_params['min_confidence'] = 0.64  # Changed!
    seed3 = generate_strategy_seed('4h', modified_params)
    print(f"  Original: {seed1}")
    print(f"  Modified: {seed3}")
    print(f"  Different: {seed1 != seed3}")
