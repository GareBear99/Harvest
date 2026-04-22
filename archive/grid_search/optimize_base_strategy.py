#!/usr/bin/env python3
"""
BASE_STRATEGY Optimization Tool

Systematically tests different BASE_STRATEGY parameter combinations
to find the optimal baseline configuration.

Usage:
    python optimize_base_strategy.py --timeframe 15m --parameter min_confidence
    python optimize_base_strategy.py --full-scan
"""

import argparse
import json
import sys
from typing import Dict, List, Tuple
from backtest_90_complete import MultiTimeframeBacktest


# Current BASE_STRATEGY values
CURRENT_BASE = {
    '15m': {
        'min_confidence': 0.70,
        'min_volume': 1.15,
        'min_trend': 0.55,
        'min_adx': 25,
        'atr_min': 0.4,
        'atr_max': 3.5
    },
    '1h': {
        'min_confidence': 0.66,
        'min_volume': 1.10,
        'min_trend': 0.50,
        'min_adx': 25,
        'atr_min': 0.4,
        'atr_max': 3.5
    },
    '4h': {
        'min_confidence': 0.63,
        'min_volume': 1.05,
        'min_trend': 0.46,
        'min_adx': 25,
        'atr_min': 0.4,
        'atr_max': 3.5
    }
}


# Parameter test ranges
PARAM_RANGES = {
    'min_confidence': [0.60, 0.63, 0.66, 0.70, 0.73, 0.76, 0.80],
    'min_volume': [1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30],
    'min_trend': [0.40, 0.46, 0.50, 0.55, 0.60, 0.65],
    'min_adx': [20, 23, 25, 28, 30, 33],
    'atr_min': [0.3, 0.4, 0.5],
    'atr_max': [3.0, 3.5, 4.0, 4.5]
}


def run_backtest_with_strategy(
    data_file: str,
    timeframe: str,
    strategy: Dict,
    seed: int = 42
) -> Dict:
    """
    Run backtest with specific strategy parameters
    
    Returns metrics: trades, WR, PnL, final_balance
    """
    # Create modified base strategy
    test_base = CURRENT_BASE.copy()
    test_base[timeframe] = strategy
    
    # Temporarily update BASE_STRATEGY
    import ml.base_strategy as bs
    original = bs.BASE_STRATEGY.copy()
    bs.BASE_STRATEGY[timeframe] = strategy.copy()
    
    try:
        # Run backtest
        bt = MultiTimeframeBacktest(data_file, 10.0, seed=seed)
        bt.run()
        
        # Get results
        all_trades = bt.all_trades
        tf_trades = [t for t in all_trades if t.get('timeframe') == timeframe]
        
        if not tf_trades:
            return {
                'trades': 0,
                'win_rate': 0.0,
                'pnl': 0.0,
                'final_balance': 10.0
            }
        
        wins = len([t for t in tf_trades if t['pnl'] > 0])
        total_pnl = sum(t['pnl'] for t in tf_trades)
        
        return {
            'trades': len(tf_trades),
            'win_rate': wins / len(tf_trades),
            'pnl': total_pnl,
            'final_balance': 10.0 + total_pnl
        }
    
    finally:
        # Restore original
        bs.BASE_STRATEGY = original


def optimize_parameter(
    timeframe: str,
    parameter: str,
    data_files: List[str]
) -> List[Tuple[float, Dict]]:
    """
    Test different values for a single parameter
    
    Returns list of (value, metrics) sorted by performance
    """
    print(f"\n{'='*80}")
    print(f"OPTIMIZING {timeframe} - {parameter}")
    print(f"{'='*80}\n")
    
    if parameter not in PARAM_RANGES:
        print(f"❌ Unknown parameter: {parameter}")
        return []
    
    results = []
    
    for value in PARAM_RANGES[parameter]:
        # Create test strategy
        test_strategy = CURRENT_BASE[timeframe].copy()
        test_strategy[parameter] = value
        
        # Test on both datasets
        total_trades = 0
        total_wins = 0
        total_pnl = 0.0
        
        for data_file in data_files:
            asset = 'ETH' if 'eth' in data_file else 'BTC'
            metrics = run_backtest_with_strategy(data_file, timeframe, test_strategy)
            
            total_trades += metrics['trades']
            total_wins += int(metrics['trades'] * metrics['win_rate'])
            total_pnl += metrics['pnl']
        
        # Calculate combined metrics
        combined_wr = total_wins / total_trades if total_trades > 0 else 0.0
        
        results.append({
            'value': value,
            'trades': total_trades,
            'win_rate': combined_wr,
            'pnl': total_pnl,
            'final_balance': 20.0 + total_pnl
        })
        
        # Print result
        print(f"{parameter}={value:6.2f} → "
              f"Trades: {total_trades:3d} | "
              f"WR: {combined_wr:5.1%} | "
              f"PnL: ${total_pnl:+7.2f} | "
              f"Balance: ${20.0 + total_pnl:7.2f}")
    
    # Sort by PnL (best first)
    results.sort(key=lambda x: x['pnl'], reverse=True)
    
    print(f"\n🏆 Best {parameter} for {timeframe}: {results[0]['value']:.2f}")
    print(f"   Trades: {results[0]['trades']}, "
          f"WR: {results[0]['win_rate']:.1%}, "
          f"PnL: ${results[0]['pnl']:+.2f}")
    
    return results


def full_optimization_scan(data_files: List[str], timeframe: str = None):
    """
    Run full parameter optimization for timeframe(s)
    """
    timeframes = [timeframe] if timeframe else ['15m', '1h', '4h']
    
    print(f"\n{'='*80}")
    print(f"FULL BASE_STRATEGY OPTIMIZATION")
    print(f"{'='*80}")
    print(f"\nTimeframes: {', '.join(timeframes)}")
    print(f"Datasets: {', '.join(data_files)}")
    print(f"\nThis will test multiple parameter combinations...")
    print(f"Estimated time: ~{len(timeframes) * len(PARAM_RANGES) * 5} seconds\n")
    
    all_results = {}
    
    for tf in timeframes:
        print(f"\n{'#'*80}")
        print(f"# OPTIMIZING {tf}")
        print(f"{'#'*80}")
        
        tf_results = {}
        
        for param in PARAM_RANGES.keys():
            results = optimize_parameter(tf, param, data_files)
            tf_results[param] = results
        
        all_results[tf] = tf_results
        
        # Print timeframe summary
        print(f"\n{'='*80}")
        print(f"BEST VALUES FOR {tf}")
        print(f"{'='*80}")
        
        best_strategy = CURRENT_BASE[tf].copy()
        
        for param, results in tf_results.items():
            if results:
                best_value = results[0]['value']
                best_strategy[param] = best_value
                current_value = CURRENT_BASE[tf][param]
                
                if best_value != current_value:
                    print(f"  {param:20s}: {current_value:6.2f} → {best_value:6.2f} ✨")
                else:
                    print(f"  {param:20s}: {current_value:6.2f} (no change)")
        
        # Test complete optimized strategy
        print(f"\n📊 Testing optimized {tf} strategy...")
        
        total_trades = 0
        total_wins = 0
        total_pnl = 0.0
        
        for data_file in data_files:
            metrics = run_backtest_with_strategy(data_file, tf, best_strategy)
            total_trades += metrics['trades']
            total_wins += int(metrics['trades'] * metrics['win_rate'])
            total_pnl += metrics['pnl']
        
        combined_wr = total_wins / total_trades if total_trades > 0 else 0.0
        
        print(f"\nOptimized {tf} Results:")
        print(f"  Trades: {total_trades}")
        print(f"  Win Rate: {combined_wr:.1%}")
        print(f"  Total PnL: ${total_pnl:+.2f}")
        print(f"  Final Balance: ${20.0 + total_pnl:.2f}")
    
    return all_results


def quick_test(data_files: List[str]):
    """Quick test of current BASE_STRATEGY"""
    print(f"\n{'='*80}")
    print("QUICK TEST - CURRENT BASE_STRATEGY")
    print(f"{'='*80}\n")
    
    results = {}
    
    for data_file in data_files:
        asset = 'ETH' if 'eth' in data_file else 'BTC'
        print(f"Testing {asset}...")
        
        bt = MultiTimeframeBacktest(data_file, 10.0, seed=42)
        bt.run()
        
        wins = len([t for t in bt.all_trades if t['pnl'] > 0])
        wr = wins / len(bt.all_trades) if bt.all_trades else 0
        total_pnl = sum(t['pnl'] for t in bt.all_trades)
        
        results[asset] = {
            'trades': len(bt.all_trades),
            'win_rate': wr,
            'pnl': total_pnl,
            'final_balance': bt.get_total_balance()
        }
        
        print(f"  {asset}: {len(bt.all_trades)} trades, "
              f"{wr:.1%} WR, ${total_pnl:+.2f} PnL, "
              f"${bt.get_total_balance():.2f} balance")
    
    # Combined
    total_trades = sum(r['trades'] for r in results.values())
    total_wins = sum(int(r['trades'] * r['win_rate']) for r in results.values())
    total_pnl = sum(r['pnl'] for r in results.values())
    combined_wr = total_wins / total_trades if total_trades > 0 else 0
    
    print(f"\nCombined: {total_trades} trades, "
          f"{combined_wr:.1%} WR, ${total_pnl:+.2f} PnL, "
          f"${20.0 + total_pnl:.2f} balance")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Optimize BASE_STRATEGY parameters through backtesting"
    )
    
    parser.add_argument(
        '--timeframe', '-t',
        choices=['15m', '1h', '4h'],
        help='Timeframe to optimize'
    )
    
    parser.add_argument(
        '--parameter', '-p',
        choices=list(PARAM_RANGES.keys()),
        help='Single parameter to optimize'
    )
    
    parser.add_argument(
        '--full-scan', '-f',
        action='store_true',
        help='Run full optimization scan'
    )
    
    parser.add_argument(
        '--quick-test', '-q',
        action='store_true',
        help='Quick test of current BASE_STRATEGY'
    )
    
    args = parser.parse_args()
    
    # Data files
    data_files = ['data/eth_21days.json', 'data/btc_21days.json']
    
    if args.quick_test:
        quick_test(data_files)
    
    elif args.full_scan:
        full_optimization_scan(data_files, args.timeframe)
    
    elif args.parameter and args.timeframe:
        optimize_parameter(args.timeframe, args.parameter, data_files)
    
    else:
        parser.print_help()
        print("\n💡 Examples:")
        print("  python optimize_base_strategy.py --quick-test")
        print("  python optimize_base_strategy.py -t 15m -p min_confidence")
        print("  python optimize_base_strategy.py --full-scan")
        print("  python optimize_base_strategy.py --full-scan -t 15m")


if __name__ == "__main__":
    main()
