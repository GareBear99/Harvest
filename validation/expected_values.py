#!/usr/bin/env python3
"""
Expected Values and Validation Bounds

Pre-calculated expectations for validation across all system components.
All values based on historical data analysis and realistic market conditions.
"""

from datetime import timedelta

# Data validation bounds (simplified for direct access)
DATA_EXPECTATIONS = {
    'candle_count_min': 129000,
    'candle_count_max': 130000,
    'date_span_days_min': 88,
    'date_span_days_max': 92,
    'volume_min_btc_eth': 0.001,
}

# Strategy parameter bounds
STRATEGY_BOUNDS = {
    'min_confidence': (0.60, 0.95),  # Valid confidence range
    'min_volume': (1.5, 6.0),  # Volume multiplier range
    'min_trend': (0.40, 0.70),  # Trend strength range
    'min_adx': (20, 40),  # ADX indicator range
    'atr_min': (0.005, 0.050),  # ATR minimum
    'atr_max': (0.010, 0.060),  # ATR maximum
    'min_roc': (-5.0, 5.0),  # Rate of change
}

# Performance expectations
PERFORMANCE_EXPECTATIONS = {
    'win_rate': (0.70, 0.98),  # Realistic win rate range
    'trades_min': 3,  # Minimum trades for validity
    'trades_max': 1000,  # Maximum reasonable trades in 90 days
    'pnl_per_trade': (-10, 100),  # $ range per trade
    'total_pnl': (-100, 1000),  # Total P&L range for 90 days
    'max_drawdown': (0.0, 0.35),  # Max 35% drawdown
    'profit_factor': (1.2, 15.0),  # Realistic profit factor
    'sharpe_ratio': (0.3, 6.0),  # Realistic Sharpe ratio
    'trades_per_day': (0.1, 12.0),  # Reasonable frequency
}

# Backtest validation
BACKTEST_EXPECTATIONS = {
    'starting_balance': (5.0, 100.0),  # Typical starting amounts
    'final_balance': (0.0, 10000.0),  # Reasonable final amounts
    'max_position_size': (0.0, 1000.0),  # Max position in $
    'leverage_max': 25,  # Maximum leverage allowed
    'min_leverage': 1,  # Minimum leverage
    'risk_per_trade_max': 0.05,  # Max 5% risk per trade
}

# Data quality metrics
DATA_QUALITY_THRESHOLDS = {
    'integrity_score_min': 0.95,  # 95% data quality minimum
    'completeness_min': 0.98,  # 98% completeness minimum
    'ohlc_valid_min': 0.999,  # 99.9% OHLC relationships valid
    'volume_valid_min': 0.99,  # 99% volume data valid
    'timestamp_alignment': 0.999,  # 99.9% timestamps aligned
}

# Grid search expectations
GRID_SEARCH_EXPECTATIONS = {
    'total_combinations': 121500,  # Expected total combinations
    'min_valid_strategies': 2,  # Minimum strategies to find
    'max_runtime_hours': 24,  # Maximum runtime
    'csv_columns_expected': [
        'min_confidence', 'min_volume', 'min_trend', 'min_adx',
        'atr_min', 'atr_max', 'trades', 'win_rate', 'total_pnl'
    ],
}

# Fallback strategy requirements
FALLBACK_STRATEGY_REQUIREMENTS = {
    'min_strategies_per_timeframe': 2,  # Must have 2 per TF
    'max_age_days': 90,  # Fallbacks expire after 90 days
    'required_fields': [
        'min_confidence', 'min_volume', 'min_trend', 'min_adx',
        'min_roc', 'atr_min', 'atr_max', 'win_rate', 'trades',
        'total_pnl', 'updated'
    ],
}

# System health thresholds
SYSTEM_HEALTH_THRESHOLDS = {
    'data_freshness_days': 30,  # Max data age
    'fallback_freshness_days': 90,  # Max fallback age
    'base_strategy_required': True,  # BASE_STRATEGY must exist
    'ml_config_required': True,  # ML config must exist
    'min_disk_space_mb': 100,  # Minimum disk space
}

# Cross-validation tolerances
CROSS_VALIDATION_TOLERANCES = {
    'win_rate_deviation': 0.05,  # ±5% allowed deviation
    'pnl_deviation': 0.10,  # ±10% allowed deviation
    'trade_count_deviation': 0.15,  # ±15% allowed deviation
    'correlation_min': 0.60,  # Min correlation between metrics
}

# Alert thresholds
ALERT_THRESHOLDS = {
    'win_rate_below': 0.70,  # Alert if WR < 70%
    'pnl_negative_consecutive': 5,  # Alert after 5 losses
    'drawdown_warning': 0.20,  # Warning at 20% drawdown
    'drawdown_critical': 0.30,  # Critical at 30% drawdown
    'data_gap_warning_minutes': 60,  # Warn if gap > 1 hour
    'strategy_age_warning_days': 60,  # Warn if strategy > 60 days old
}


def get_expected_range(component, metric):
    """
    Get expected range for a specific metric
    
    Args:
        component: Component name (e.g., 'eth_90days', 'strategy', 'backtest')
        metric: Metric name (e.g., 'win_rate', 'candle_count')
    
    Returns:
        Tuple of (min, max) or None if not found
    """
    
    # Check data expectations
    if component in DATA_EXPECTATIONS:
        if metric in DATA_EXPECTATIONS[component]:
            value = DATA_EXPECTATIONS[component][metric]
            return value if isinstance(value, tuple) else (value, value)
    
    # Check strategy bounds
    if component == 'strategy' and metric in STRATEGY_BOUNDS:
        return STRATEGY_BOUNDS[metric]
    
    # Check performance expectations
    if component == 'performance' and metric in PERFORMANCE_EXPECTATIONS:
        value = PERFORMANCE_EXPECTATIONS[metric]
        # For single values like trades_min/trades_max, create appropriate range
        if metric == 'trades_min':
            return (value, PERFORMANCE_EXPECTATIONS.get('trades_max', 1000))
        elif metric == 'trades_max':
            return (PERFORMANCE_EXPECTATIONS.get('trades_min', 0), value)
        return value if isinstance(value, tuple) else (value, value)
    
    # Check backtest expectations
    if component == 'backtest' and metric in BACKTEST_EXPECTATIONS:
        value = BACKTEST_EXPECTATIONS[metric]
        return value if isinstance(value, tuple) else (value, value)
    
    return None


def is_within_expected_range(value, min_val, max_val=None):
    """
    Check if value is within expected range (simple version)
    
    Args:
        value: Value to check
        min_val: Minimum expected value (or component name for complex check)
        max_val: Maximum expected value (or metric name if min_val is component)
    
    Returns:
        bool if simple (min, max) call, or (is_valid, expected_range, deviation) if complex
    """
    
    # Simple usage: is_within_expected_range(value, min, max)
    if max_val is not None and isinstance(min_val, (int, float)):
        return min_val <= value <= max_val
    
    # Complex usage: is_within_expected_range(value, component, metric)
    component = min_val
    metric = max_val
    
    expected = get_expected_range(component, metric)
    
    if expected is None:
        return True, None, 0  # No expectation = pass
    
    min_val, max_val = expected
    
    if min_val <= value <= max_val:
        return True, expected, 0
    
    # Calculate deviation
    if value < min_val:
        deviation = (min_val - value) / min_val
    else:
        deviation = (value - max_val) / max_val
    
    return False, expected, deviation


def validate_strategy_params(strategy_dict):
    """
    Validate all parameters in a strategy dictionary
    
    Args:
        strategy_dict: Strategy parameters
    
    Returns:
        (is_valid, violations)
    """
    
    violations = []
    
    for param, value in strategy_dict.items():
        if param in STRATEGY_BOUNDS:
            is_valid, expected, deviation = is_within_expected_range(
                value, 'strategy', param
            )
            
            if not is_valid:
                violations.append({
                    'parameter': param,
                    'value': value,
                    'expected': expected,
                    'deviation': deviation
                })
    
    return len(violations) == 0, violations


def validate_performance_metrics(metrics_dict):
    """
    Validate performance metrics
    
    Args:
        metrics_dict: Performance metrics
    
    Returns:
        (is_valid, violations)
    """
    
    violations = []
    
    for metric, value in metrics_dict.items():
        if metric in PERFORMANCE_EXPECTATIONS:
            is_valid, expected, deviation = is_within_expected_range(
                value, 'performance', metric
            )
            
            if not is_valid:
                violations.append({
                    'metric': metric,
                    'value': value,
                    'expected': expected,
                    'deviation': deviation
                })
    
    return len(violations) == 0, violations


if __name__ == "__main__":
    # Test validation
    print("Expected Values Validation Tests\n")
    
    # Test strategy parameters
    test_strategy = {
        'min_confidence': 0.75,
        'min_trend': 0.50,
        'min_adx': 25,
    }
    
    valid, violations = validate_strategy_params(test_strategy)
    print(f"Strategy validation: {'✅ PASS' if valid else '❌ FAIL'}")
    if violations:
        for v in violations:
            print(f"  - {v['parameter']}: {v['value']} (expected {v['expected']})")
    
    # Test performance metrics
    test_performance = {
        'win_rate': 0.92,
        'trades_min': 5,
        'total_pnl': 45.0,
    }
    
    valid, violations = validate_performance_metrics(test_performance)
    print(f"\nPerformance validation: {'✅ PASS' if valid else '❌ FAIL'}")
    if violations:
        for v in violations:
            print(f"  - {v['metric']}: {v['value']} (expected {v['expected']})")
    
    # Test out of range
    test_invalid = {
        'win_rate': 1.5,  # Impossible win rate
        'total_pnl': -200,  # Excessive loss
    }
    
    valid, violations = validate_performance_metrics(test_invalid)
    print(f"\nInvalid test: {'✅ PASS' if valid else '❌ FAIL (expected)'}")
    if violations:
        for v in violations:
            print(f"  - {v['metric']}: {v['value']} (expected {v['expected']}, deviation: {v['deviation']:.1%})")
