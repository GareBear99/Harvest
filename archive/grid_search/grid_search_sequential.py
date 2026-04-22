#!/usr/bin/env python3
"""
Sequential Grid Search - Reliable on macOS

Tests 121,500 combinations sequentially (no multiprocessing issues)
Uses 1h aggregated candles for speed
"""

import csv
import json
import itertools
from datetime import datetime
import os
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PARAMETER_GRID = {
    'min_confidence': [0.60, 0.63, 0.66, 0.70, 0.73, 0.76, 0.80, 0.83, 0.86, 0.90],
    'min_volume': [1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40, 1.50],
    'min_trend': [0.40, 0.46, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80],
    'min_adx': [20, 23, 25, 28, 30, 33, 35, 38, 40],
    'atr_min': [0.3, 0.4, 0.5],
    'atr_max': [3.0, 3.5, 4.0, 4.5, 5.0]
}


def test_strategy(strategy, timeframe, data_file, asset):
    """Test one strategy"""
    from backtest_90_complete import MultiTimeframeBacktest
    import ml.base_strategy as bs
    
    original = bs.BASE_STRATEGY.copy()
    
    try:
        bs.BASE_STRATEGY[timeframe] = strategy.copy()
        
        # Suppress output
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            bt = MultiTimeframeBacktest(data_file, 10.0, seed=42)
            bt.run()
        
        tf_trades = [t for t in bt.all_trades if t.get('timeframe') == timeframe]
        
        if not tf_trades:
            return None
        
        wins = [t for t in tf_trades if t['pnl'] > 0]
        losses = [t for t in tf_trades if t['pnl'] <= 0]
        
        win_count = len(wins)
        win_rate = win_count / len(tf_trades)
        total_pnl = sum(t['pnl'] for t in tf_trades)
        
        # Early exit for bad strategies
        if win_rate < 0.50 or total_pnl < -5:
            return None
        
        avg_win = sum(t['pnl'] for t in wins) / win_count if wins else 0
        avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
        
        return {
            'asset': asset,
            'timeframe': timeframe,
            'trades': len(tf_trades),
            'wins': win_count,
            'losses': len(losses),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'final_balance': 10.0 + total_pnl,
            'return_pct': total_pnl * 10,
            'risk_reward': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            **strategy
        }
        
    except Exception:
        return None
    finally:
        bs.BASE_STRATEGY = original


def run_search(timeframe, data_file, asset, output_file):
    """Run sequential grid search"""
    
    print(f"\n{'='*80}")
    print(f"🔍 SEQUENTIAL GRID SEARCH: {asset} - {timeframe}")
    print(f"{'='*80}\n")
    
    # Generate combinations
    keys = list(PARAMETER_GRID.keys())
    values = [PARAMETER_GRID[k] for k in keys]
    
    total = 1
    for v in values:
        total *= len(v)
    
    print(f"📊 Total combinations: {total:,}")
    print(f"⚡ Sequential processing (no multiprocessing)")
    print(f"📁 Output: {output_file}\n")
    
    print("Starting search...\n")
    start_time = datetime.now()
    
    all_results = []
    completed = 0
    valid_count = 0
    
    for combo in itertools.product(*values):
        strategy = dict(zip(keys, combo))
        strategy['min_roc'] = -1.0
        
        result = test_strategy(strategy, timeframe, data_file, asset)
        
        if result and result['trades'] >= 3:
            all_results.append(result)
            valid_count += 1
        
        completed += 1
        
        # Progress every 100
        if completed % 100 == 0 or completed == total:
            progress = (completed / total) * 100
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = completed / elapsed if elapsed > 0 else 0
            eta_seconds = (total - completed) / rate if rate > 0 else 0
            eta_minutes = eta_seconds / 60
            
            bar_width = 40
            filled = int(bar_width * completed / total)
            bar = '█' * filled + '░' * (bar_width - filled)
            
            print(f"\r[{bar}] {progress:5.1f}% | {completed:,}/{total:,} | "
                  f"{rate:.1f} strat/s | ETA: {eta_minutes:.1f}m | Valid: {valid_count}",
                  end='', flush=True)
    
    print()
    
    elapsed_total = (datetime.now() - start_time).total_seconds()
    
    print(f"\n⚡ Completed in {elapsed_total:.1f}s ({elapsed_total/60:.1f} min)")
    print(f"   Average: {total/elapsed_total:.1f} strategies/second")
    print(f"   Valid strategies: {len(all_results):,}")
    
    # Write results
    if all_results:
        print(f"\n💾 Writing {len(all_results):,} results...")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)
        print(f"✅ Results saved")
    
    return all_results


def analyze_top10(results):
    """Show top 10"""
    
    if not results:
        print("No valid strategies found")
        return None
    
    print(f"\n{'='*80}")
    print("🏆 TOP 10 STRATEGIES")
    print(f"{'='*80}\n")
    
    # Sort by balanced score
    balanced = sorted(results, key=lambda x: (x['win_rate'] * x['total_pnl']), reverse=True)
    
    for i, r in enumerate(balanced[:10], 1):
        score = r['win_rate'] * r['total_pnl']
        print(f"{i:2d}. Score: {score:6.2f} | "
              f"WR: {r['win_rate']:5.1%} | "
              f"PnL: ${r['total_pnl']:+7.2f} | "
              f"Trades: {r['trades']:3d}")
        print(f"    Conf: {r['min_confidence']:.2f} | "
              f"Vol: {r['min_volume']:.2f} | "
              f"Trend: {r['min_trend']:.2f} | "
              f"ADX: {r['min_adx']} | "
              f"ATR: {r['atr_min']:.1f}-{r['atr_max']:.1f}")
    
    return balanced[:10]


def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeframe', '-t', required=True)
    parser.add_argument('--asset', '-a', required=True)
    parser.add_argument('--output', '-o', default=None)
    
    args = parser.parse_args()
    
    data_file = f"data/{args.asset}_1m_90d.json"
    
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        return 1
    
    if args.output is None:
        os.makedirs('grid_search_results', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f"grid_search_results/{args.asset}_{args.timeframe}_seq_{timestamp}.csv"
    
    # Run
    results = run_search(args.timeframe, data_file, args.asset, args.output)
    
    # Analyze
    top10 = analyze_top10(results)
    
    # Save top 10
    if top10:
        summary_file = args.output.replace('.csv', '_top10.json')
        with open(summary_file, 'w') as f:
            json.dump(top10, f, indent=2)
        print(f"\n💾 Top 10 saved: {summary_file}")
    
    print(f"\n{'='*80}")
    print("✅ COMPLETE")
    print(f"{'='*80}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
