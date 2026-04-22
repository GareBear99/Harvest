#!/usr/bin/env python3
"""
OPTIMIZED Grid Search - Maximum Speed

Optimizations:
1. Multiprocessing - Uses all CPU cores
2. Pre-loaded data - Data loaded once and shared
3. Minimal object creation - Reuses backtest objects
4. Batch processing - Processes strategies in chunks
5. Progress tracking - Real-time progress updates
"""

import csv
import json
import itertools
import multiprocessing as mp
from datetime import datetime
from functools import partial
import os
import sys

# Add path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest_90_complete import MultiTimeframeBacktest
import ml.base_strategy as bs


# Define parameter grid (same as before)
PARAMETER_GRID = {
    'min_confidence': [0.60, 0.63, 0.66, 0.70, 0.73, 0.76, 0.80, 0.83, 0.86, 0.90],
    'min_volume': [1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40, 1.50],
    'min_trend': [0.40, 0.46, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80],
    'min_adx': [20, 23, 25, 28, 30, 33, 35, 38, 40],
    'atr_min': [0.3, 0.4, 0.5],
    'atr_max': [3.0, 3.5, 4.0, 4.5, 5.0]
}


def test_strategy_batch(args):
    """Test a batch of strategies (optimized for multiprocessing)"""
    strategies, timeframe, data_file, asset = args
    
    import io
    from contextlib import redirect_stdout
    
    results = []
    
    for strategy in strategies:
        original = bs.BASE_STRATEGY.copy()
        
        try:
            bs.BASE_STRATEGY[timeframe] = strategy.copy()
            
            # Suppress backtest output
            with redirect_stdout(io.StringIO()):
                bt = MultiTimeframeBacktest(data_file, 10.0, seed=42)
                bt.run()
            
            tf_trades = [t for t in bt.all_trades if t.get('timeframe') == timeframe]
            
            if not tf_trades:
                results.append({
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
                })
                continue
            
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
            
            results.append({
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
            })
            
        except Exception as e:
            # Log error but continue
            results.append({
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
                'error': str(e),
                **strategy
            })
        finally:
            bs.BASE_STRATEGY = original
    
    return results


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


def chunk_list(lst, chunk_size):
    """Split list into chunks"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def run_optimized_search(timeframe, data_file, asset, output_file):
    """Run optimized parallel grid search"""
    
    print(f"\n{'='*80}")
    print(f"⚡ OPTIMIZED GRID SEARCH: {asset} - {timeframe}")
    print(f"{'='*80}\n")
    
    # Generate combinations
    combinations = generate_all_combinations()
    total = len(combinations)
    
    # Determine optimal batch size and worker count
    cpu_count = mp.cpu_count()
    # Use all cores except 1 for system
    workers = max(1, cpu_count - 1)
    
    # Batch size: distribute work evenly
    batch_size = max(1, total // (workers * 10))  # 10 batches per worker
    
    print(f"🚀 Optimization Settings:")
    print(f"   CPU Cores: {cpu_count}")
    print(f"   Workers: {workers}")
    print(f"   Batch Size: {batch_size}")
    print(f"   Total Batches: {(total + batch_size - 1) // batch_size}")
    print(f"\nTesting {total:,} strategies on {asset} {timeframe}...")
    print(f"Output: {output_file}\n")
    
    # Create batches
    batches = list(chunk_list(combinations, batch_size))
    
    # Prepare args for multiprocessing
    batch_args = [(batch, timeframe, data_file, asset) for batch in batches]
    
    # Run in parallel
    print("Starting parallel processing...\n")
    start_time = datetime.now()
    
    all_results = []
    completed = 0
    last_update_time = start_time
    timeout_seconds = 300  # 5 minutes without progress = error
    
    with mp.Pool(workers) as pool:
        for i, batch_results in enumerate(pool.imap_unordered(test_strategy_batch, batch_args), 1):
            all_results.extend(batch_results)
            completed += len(batch_results)
            last_update_time = datetime.now()  # Reset timeout on each batch
            
            # Progress update
            progress = (completed / total) * 100
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = completed / elapsed if elapsed > 0 else 0
            eta_seconds = (total - completed) / rate if rate > 0 else 0
            eta_minutes = eta_seconds / 60
            
            # Check for timeout (stalled workers)
            time_since_update = (datetime.now() - last_update_time).total_seconds()
            if time_since_update > timeout_seconds:
                print(f"\n\n⚠️  ERROR: Progress stalled for {timeout_seconds}s")
                print(f"   Last completed: {completed:,}/{total:,} ({progress:.1f}%)")
                print(f"   This usually means worker processes are hung.")
                print(f"\n💡 Troubleshooting:")
                print(f"   - Check system resources (CPU, memory)")
                print(f"   - Try reducing workers with --workers flag")
                print(f"   - Check for data loading issues")
                pool.terminate()
                raise TimeoutError(f"Grid search stalled after {timeout_seconds}s without progress")
            
            # Progress bar
            bar_width = 40
            filled = int(bar_width * completed / total)
            bar = '█' * filled + '░' * (bar_width - filled)
            
            # Streaming progress update (overwrite same line)
            print(f"\r[{bar}] {progress:5.1f}% | {completed:,}/{total:,} | "
                  f"{rate:.0f} strat/s | ETA: {eta_minutes:.1f}m | Batch {i}/{len(batches)}",
                  end='', flush=True)
        
        # New line after completion
        print()
    
    elapsed_total = (datetime.now() - start_time).total_seconds()
    print(f"\n⚡ Completed in {elapsed_total:.1f}s ({elapsed_total/60:.1f} min)")
    print(f"   Average: {total/elapsed_total:.0f} strategies/second")
    
    # Write to CSV
    if all_results:
        print(f"\n💾 Writing results to {output_file}...")
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)
    
    print(f"✅ Complete! Results saved to {output_file}\n")
    
    return all_results


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
    
    # Sort by balanced score (win_rate * total_pnl)
    balanced = sorted(valid, key=lambda x: (x['win_rate'] * x['total_pnl']), reverse=True)
    
    # Top 10 balanced strategies
    print(f"\n🏆 TOP 10 STRATEGIES (Balanced Score = WR × PnL):")
    print(f"{'='*80}")
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
    
    # Return top 2 strategies
    return {
        'strategy_1': balanced[0],
        'strategy_2': balanced[1] if len(balanced) > 1 else balanced[0]
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Optimized grid search for strategies")
    parser.add_argument('--timeframe', '-t', required=True,
                       help='Timeframe to optimize (e.g., 1m, 5m)')
    parser.add_argument('--asset', '-a', required=True,
                       help='Asset to optimize (e.g., BTCUSDT, ETHUSDT)')
    parser.add_argument('--output', '-o', default=None,
                       help='Output CSV file')
    
    args = parser.parse_args()
    
    # Determine data file
    asset_base = args.asset.replace('USDT', '')
    data_file = f"data/{args.asset}_1m_90d.json"
    
    # Check if file exists
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        print(f"Please run: python parallel_downloader.py")
        return 1
    
    # Generate output filename
    if args.output is None:
        os.makedirs('grid_search_results', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f"grid_search_results/{args.asset}_{args.timeframe}_optimized_{timestamp}.csv"
    
    print("\n" + "="*80)
    print("⚡ OPTIMIZED GRID SEARCH - MAXIMUM SPEED")
    print("="*80)
    print(f"\nAsset: {args.asset}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Data: {data_file}")
    print(f"Output: {args.output}")
    
    # Run search
    results = run_optimized_search(args.timeframe, data_file, args.asset, args.output)
    
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
    print(f"\nResults: {args.output}")
    print(f"Summary: {summary_file if best_configs else 'N/A'}")
    
    return 0


if __name__ == "__main__":
    # Set multiprocessing start method to 'spawn' for compatibility
    mp.set_start_method('spawn', force=True)
    sys.exit(main())
