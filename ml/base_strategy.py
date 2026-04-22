"""
Base Strategy - Default Strategies
These are the proven strategies used when ML is disabled.
They serve as the baseline for all strategy variations and validation tests.

15m & 1h: Proven strategy with 76% WR on test data (conf=0.75, vol=1.25, trend=0.60, adx=28)
4h: Conservative base strategy (conf=0.63, vol=1.05, trend=0.46, adx=25)

IMPORTANT: The 'seed' values shown here (1001, 5001, etc.) are TIMEFRAME PREFIXES only!
The REAL strategy seed is calculated via SHA-256 hash from parameters:
  - Real seed = generate_strategy_seed(timeframe, params)
  - Example: 15m params → SHA-256 → strategy seed 15782130065
  - This real seed is bidirectionally traceable through 4-layer tracking system
  - See ml/strategy_seed_generator.py for implementation
  - See docs/SEED_SYSTEM.md for complete documentation
"""

# Base strategy thresholds used when ML is disabled
# These are the default strategies users will get
BASE_STRATEGY = {
    '1m': {
        'seed': 1001,  # TIMEFRAME PREFIX - Real seed calculated via SHA-256 (see strategy_seed_generator.py)
        'min_confidence': 0.82,  # Very high confidence for ultra-fast trades
        'min_volume': 1.35,  # Strong volume essential
        'min_trend': 0.68,  # Very strong trend alignment
        'min_adx': 32,  # Very strong trend required
        'min_roc': -1.05,  # Tight momentum filter
        'atr_min': 0.50,  # Higher volatility floor
        'atr_max': 3.0  # Tighter volatility ceiling
    },
    '5m': {
        'seed': 5001,  # TIMEFRAME PREFIX - Real seed calculated via SHA-256 (see strategy_seed_generator.py)
        'min_confidence': 0.80,  # High confidence for fast trades
        'min_volume': 1.30,  # Strong volume confirmation
        'min_trend': 0.65,  # Strong trend alignment
        'min_adx': 30,  # Strong trend
        'min_roc': -1.1,  # Strict momentum filter
        'atr_min': 0.45,  # Higher volatility minimum
        'atr_max': 3.2  # Reasonable volatility ceiling
    },
    '15m': {
        'seed': 15001,  # TIMEFRAME PREFIX - Real seed calculated via SHA-256 (see strategy_seed_generator.py)
        'min_confidence': 0.78,  # Higher confidence for fast 15m trades
        'min_volume': 1.30,  # Strong volume required
        'min_trend': 0.65,  # Stronger trend alignment
        'min_adx': 30,  # Stronger trend strength
        'min_roc': -1.1,  # Tighter momentum
        'atr_min': 0.45,
        'atr_max': 3.2
    },
    '1h': {
        'seed': 60001,  # TIMEFRAME PREFIX - Real seed calculated via SHA-256 (see strategy_seed_generator.py)
        'min_confidence': 0.72,  # Balanced confidence for 1h
        'min_volume': 1.20,  # Moderate volume
        'min_trend': 0.55,  # Moderate trend alignment
        'min_adx': 27,  # Good trend strength
        'min_roc': -1.15,  # Balanced momentum
        'atr_min': 0.42,
        'atr_max': 3.3
    },
    '4h': {
        'seed': 240001,  # TIMEFRAME PREFIX - Real seed calculated via SHA-256 (see strategy_seed_generator.py)
        'min_confidence': 0.63,  # Original base strategy (conservative)
        'min_volume': 1.05,
        'min_trend': 0.46,
        'min_adx': 25,
        'min_roc': -1.0,
        'atr_min': 0.4,
        'atr_max': 3.5
    }
}

# Expected baseline results for validation
# These are the exact results we expect when running with BASE_STRATEGY on known data
# Used to validate determinism and correctness
BASELINE_RESULTS = {
    'eth_21days': {
        'data_file': 'data/eth_21days.json',
        'starting_balance': 10.0,
        'seed': 42,
        'expected': {
            'total_trades': 6,
            'win_rate': 0.50,  # 3 wins, 3 losses
            'final_balance': 9.78,
            'total_return': -0.0223,  # -2.23%
            'timeframe_breakdown': {
                '15m': {'trades': 3, 'win_rate': 0.667},
                '1h': {'trades': 3, 'win_rate': 0.333},
                '4h': {'trades': 0, 'win_rate': 0.0}
            }
        }
    },
    'btc_21days': {
        'data_file': 'data/btc_21days.json',
        'starting_balance': 10.0,
        'seed': 42,
        'expected': {
            'total_trades': 7,
            'win_rate': 0.286,  # 2 wins, 5 losses
            'final_balance': 9.63,
            'total_return': -0.0373,  # -3.73%
            'timeframe_breakdown': {
                '15m': {'trades': 3, 'win_rate': 0.667},
                '1h': {'trades': 3, 'win_rate': 0.0},
                '4h': {'trades': 1, 'win_rate': 0.0}
            }
        }
    },
    'combined': {
        'starting_capital': 20.0,
        'seed': 42,
        'expected': {
            'total_trades': 13,
            'combined_win_rate': 0.385,  # 5 wins, 8 losses
            'final_balance': 19.40,
            'total_return': -0.0298  # -2.98%
        }
    }
}

# Strategy evaluation criteria
STRATEGY_EVALUATION = {
    'min_trades_for_pool': 20,  # Need 20+ trades before strategy is "proven"
    'min_win_rate_for_pool': 0.72,  # Need 72%+ WR to be added to pool
    'max_strategies_per_timeframe': 3,  # Maximum 3 strategies per timeframe
    'switch_threshold_wr': 0.58,  # Switch if WR drops below 58%
    'switch_threshold_losses': 5,  # Switch after 5 consecutive losses
    'min_trades_for_wr_check': 10  # Need 10+ trades before checking WR threshold
}


def get_base_strategy(timeframe: str) -> dict:
    """
    Get immutable copy of base strategy for timeframe
    
    Args:
        timeframe: '1m', '5m', '15m', '1h', or '4h'
    
    Returns:
        Copy of base strategy thresholds (never modify original)
    """
    if timeframe not in BASE_STRATEGY:
        raise ValueError(f"Invalid timeframe: {timeframe}. Must be '1m', '5m', '15m', '1h', or '4h'")
    
    return BASE_STRATEGY[timeframe].copy()


def get_baseline_results(dataset: str) -> dict:
    """
    Get expected baseline results for validation
    
    Args:
        dataset: 'eth_21days', 'btc_21days', or 'combined'
    
    Returns:
        Expected results dictionary
    """
    if dataset not in BASELINE_RESULTS:
        raise ValueError(f"Invalid dataset: {dataset}")
    
    return BASELINE_RESULTS[dataset].copy()


def validate_strategy_format(strategy: dict) -> bool:
    """
    Validate that strategy dict has all required keys
    
    Args:
        strategy: Strategy dictionary to validate
    
    Returns:
        True if valid, raises ValueError if not
    """
    required_keys = {
        'min_confidence', 'min_volume', 'min_trend',
        'min_adx', 'min_roc', 'atr_min', 'atr_max'
    }
    
    if not all(key in strategy for key in required_keys):
        missing = required_keys - set(strategy.keys())
        raise ValueError(f"Strategy missing required keys: {missing}")
    
    return True


if __name__ == "__main__":
    # Demonstrate usage
    print("📋 BASE STRATEGY CONSTANTS\n")
    
    for tf in ['1m', '5m', '15m', '1h', '4h']:
        strategy = get_base_strategy(tf)
        print(f"{tf}:")
        for key, val in strategy.items():
            print(f"  {key}: {val}")
        print()
    
    print("\n📊 BASELINE VALIDATION RESULTS\n")
    
    for dataset in ['eth_21days', 'btc_21days', 'combined']:
        results = get_baseline_results(dataset)
        print(f"{dataset}:")
        if 'expected' in results:
            expected = results['expected']
            print(f"  Trades: {expected.get('total_trades', 'N/A')}")
            print(f"  Win Rate: {expected.get('win_rate', expected.get('combined_win_rate', 'N/A')):.1%}")
            print(f"  Final Balance: ${expected.get('final_balance', 'N/A')}")
        print()
    
    print("\n⚙️  STRATEGY EVALUATION CRITERIA\n")
    for key, val in STRATEGY_EVALUATION.items():
        print(f"  {key}: {val}")
