#!/usr/bin/env python3
"""
Exhaustive Grid Search - Test ALL Possible Strategies

Systematically tests every combination of parameters to map the complete
strategy space and find optimal configurations.

This will generate a comprehensive CSV report with ALL results.
"""

import csv
import json
import itertools
from datetime import datetime
from backtest_90_complete import MultiTimeframeBacktest
import ml.base_strategy as bs


# Define parameter grid
PARAMETER_GRID = {
    'min_confidence': [0.60, 0.63, 0.66, 0.70, 0.73, 0.76, 0.80, 0.83, 0.86, 0.90],
    'min_volume': [1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40, 1.50],
    'min_trend': [0.40, 0.46, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80],
    'min_adx': [20, 23, 25, 28, 30, 33, 35, 38, 40],
    'atr_min': [0.3, 0.4, 0.5],
    'atr_max': [3.0, 3.5, 4.0, 4.5, 5.0]
}


def test_strategy(timeframe, strategy, data_file, asset):
    """Test a single strategy configuration"""
    original = bs.BASE_STRATEGY.copy()
    
    try:
        bs.BASE_STRATEGY[timeframe] = strategy.copy()
        bt = MultiTimeframeBacktest(data_file, 10.0, seed=42)
        bt.run()
        
        tf_trades = [t for t in bt.all_trades if t.get('timeframe') == timeframe]
        
        if not tf_trades:
            return {
                'asset': asset,
                'timeframe': timeframe,
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'final_balance': 10.0,
                'return_pct': 0.0,
                **strategy
            }
        
        wins = [t for t in tf_trades if t['pnl'] > 0]
        losses = [t for t in tf_trades if t['pnl'] <= 0]
        
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = win_count / len(tf_trades)
        total_pnl = sum(t['pnl'] for t in tf_trades)
        avg_win = sum(t['pnl'] for t in wins) / win_count if wins else 0
        avg_loss = sum(t['pnl'] for t in losses) / loss_count if losses else 0
        final_balance = 10.0 + total_pnl
        return_pct = (final_balance - 10.0) / 10.0 * 100
        
        return {
            'asset': asset,
            'timeframe': timeframe,
            'trades': len(tf_trades),
            'wins': win_count,
            'losses': loss_count,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'final_balance': final_balance,
            'return_pct': return_pct,
            'risk_reward': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            **strategy
        }
        
    finally:
        bs.BASE_STRATEGY = original


def generate_all_combinations():
    """Generate all possible parameter combinations"""
    keys = list(PARAMETER_GRID.keys())
    values = [PARAMETER_GRID[k] for k in keys]
    
    total = 1
    for v in values:
        total *= len(v)
    
    print(f"📊 Total combinations to test: {total:,}")
    print(f"   Parameters: {', '.join(keys)}")
    print(f"   Grid sizes: {[len(PARAMETER_GRID[k]) for k in keys]}")
    
    combinations = []
    for combo in itertools.product(*values):
        strategy = dict(zip(keys, combo))
        strategy['min_roc'] = -1.0  # Keep constant
        combinations.append(strategy)
    
    return combinations


def run_exhaustive_search(timeframe, data_file, asset, output_file):
    """Run exhaustive search for one timeframe/asset"""
    
    print(f"\n{'='*80}")
    print(f"EXHAUSTIVE SEARCH: {asset} - {timeframe}")
    print(f"{'='*80}\n")
    
    combinations = generate_all_combinations()
    total = len(combinations)
    
    print(f"Testing {total:,} strategies on {asset} {timeframe}...")
    print(f"Output: {output_file}\n")
    
    results = []
    
    for i, strategy in enumerate(combinations, 1):
        if i % 100 == 0 or i == 1:
            progress = (i / total) * 100
            print(f"Progress: {i:,}/{total:,} ({progress:.1f}%) - Testing strategy #{i}")
        
        result = test_strategy(timeframe, strategy, data_file, asset)
        results.append(result)
    
    # Write to CSV
    if results:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    print(f"\n✅ Complete! Results saved to {output_file}")
    
    return results


def analyze_results(results):
    """Analyze and summarize results"""
    
    if not results:
        print("No results to analyze")
        return
    
    print(f"\n{'='*80}")
    print("📊 RESULTS ANALYSIS")
    print(f"{'='*80}\n")
    
    # Filter valid results (with trades)
    valid = [r for r in results if r['trades'] >= 3]
    
    print(f"Total strategies tested: {len(results):,}")
    print(f"Strategies with 3+ trades: {len(valid):,}")
    
    if not valid:
        print("\n⚠️  No strategies produced 3+ trades")
        return
    
    # Sort by different metrics
    by_wr = sorted(valid, key=lambda x: x['win_rate'], reverse=True)
    by_pnl = sorted(valid, key=lambda x: x['total_pnl'], reverse=True)
    by_trades = sorted(valid, key=lambda x: x['trades'], reverse=True)
    
    # Top by win rate
    print(f"\n🏆 TOP 10 BY WIN RATE:")
    print(f"{'='*80}")
    for i, r in enumerate(by_wr[:10], 1):
        print(f"{i:2d}. WR: {r['win_rate']:5.1%} | "
              f"Trades: {r['trades']:3d} | "
              f"PnL: ${r['total_pnl']:+7.2f} | "
              f"Conf: {r['min_confidence']:.2f} | "
              f"Vol: {r['min_volume']:.2f} | "
              f"Trend: {r['min_trend']:.2f} | "
              f"ADX: {r['min_adx']}")
    
    # Top by PnL
    print(f"\n💰 TOP 10 BY PROFIT:")
    print(f"{'='*80}")
    for i, r in enumerate(by_pnl[:10], 1):
        print(f"{i:2d}. PnL: ${r['total_pnl']:+7.2f} | "
              f"WR: {r['win_rate']:5.1%} | "
              f"Trades: {r['trades']:3d} | "
              f"Conf: {r['min_confidence']:.2f} | "
              f"Vol: {r['min_volume']:.2f} | "
              f"Trend: {r['min_trend']:.2f} | "
              f"ADX: {r['min_adx']}")
    
    # Best balanced (high WR + profit)
    balanced = sorted(valid, key=lambda x: (x['win_rate'] * x['total_pnl']), reverse=True)
    
    print(f"\n⚖️  TOP 10 BALANCED (WR × PnL):")
    print(f"{'='*80}")
    for i, r in enumerate(balanced[:10], 1):
        score = r['win_rate'] * r['total_pnl']
        print(f"{i:2d}. Score: {score:6.2f} | "
              f"WR: {r['win_rate']:5.1%} | "
              f"PnL: ${r['total_pnl']:+7.2f} | "
              f"Trades: {r['trades']:3d} | "
              f"Conf: {r['min_confidence']:.2f} | "
              f"Vol: {r['min_volume']:.2f} | "
              f"Trend: {r['min_trend']:.2f} | "
              f"ADX: {r['min_adx']}")
    
    # Statistics
    print(f"\n📈 STATISTICS:")
    print(f"{'='*80}")
    
    wr_values = [r['win_rate'] for r in valid]
    pnl_values = [r['total_pnl'] for r in valid]
    trade_counts = [r['trades'] for r in valid]
    
    print(f"Win Rate:")
    print(f"  Best: {max(wr_values):.1%}")
    print(f"  Average: {sum(wr_values)/len(wr_values):.1%}")
    print(f"  Worst: {min(wr_values):.1%}")
    
    print(f"\nPnL:")
    print(f"  Best: ${max(pnl_values):+.2f}")
    print(f"  Average: ${sum(pnl_values)/len(pnl_values):+.2f}")
    print(f"  Worst: ${min(pnl_values):+.2f}")
    
    print(f"\nTrades:")
    print(f"  Most: {max(trade_counts)}")
    print(f"  Average: {sum(trade_counts)/len(trade_counts):.1f}")
    print(f"  Least: {min(trade_counts)}")
    
    # Return best configs
    return {
        'best_wr': by_wr[0],
        'best_pnl': by_pnl[0],
        'best_balanced': balanced[0]
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Exhaustive grid search for optimal strategies")
    parser.add_argument('--timeframe', '-t', choices=['15m', '1h', '4h'], required=True,
                       help='Timeframe to optimize')
    parser.add_argument('--asset', '-a', choices=['ETH', 'BTC'], required=True,
                       help='Asset to optimize')
    parser.add_argument('--output', '-o', default=None,
                       help='Output CSV file (default: grid_search_{asset}_{tf}_{timestamp}.csv)')
    
    args = parser.parse_args()
    
    # Determine data file (use 90-day data for better optimization)
    data_file = f"data/{args.asset.lower()}_90days.json"
    
    # Generate output filename
    if args.output is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f"grid_search_{args.asset}_{args.timeframe}_{timestamp}.csv"
    
    print("\n" + "="*80)
    print("🔬 EXHAUSTIVE GRID SEARCH - ALL POSSIBLE STRATEGIES")
    print("="*80)
    print(f"\nAsset: {args.asset}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Data: {data_file}")
    print(f"Output: {args.output}")
    
    # Run search
    results = run_exhaustive_search(args.timeframe, data_file, args.asset, args.output)
    
    # Analyze
    best_configs = analyze_results(results)
    
    # Save best configs
    if best_configs:
        summary_file = args.output.replace('.csv', '_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(best_configs, f, indent=2)
        print(f"\n💾 Best configurations saved to: {summary_file}")
    
    print(f"\n{'='*80}")
    print("✅ GRID SEARCH COMPLETE")
    print(f"{'='*80}")
    print(f"\nResults saved to: {args.output}")
    print(f"Open in Excel/Numbers to explore all {len(results):,} strategies!")
    print(f"\nRecommended commands:")
    print(f"  # View top strategies")
    print(f"  head -20 {args.output}")
    print(f"  # Sort by win rate")
    print(f"  sort -t',' -k7 -rn {args.output} | head -20")


if __name__ == "__main__":
    main()
