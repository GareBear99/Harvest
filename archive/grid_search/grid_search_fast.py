#!/usr/bin/env python3
"""
FAST Grid Search - Simple and Reliable

Tests 121,500 combinations quickly using:
- Multiprocessing with all cores
- Process-level timeouts (works on macOS)
- Progress tracking
- Early termination for bad strategies
"""

import csv
import json
import itertools
import multiprocessing as mp
from datetime import datetime
import os
import sys
import io
import threading
import time
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


def test_single_strategy(args):
    """Test one strategy with timeout protection"""
    strategy, timeframe, data_file, asset = args
    
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
            return make_empty_result(asset, timeframe, strategy)
        
        wins = [t for t in tf_trades if t['pnl'] > 0]
        losses = [t for t in tf_trades if t['pnl'] <= 0]
        
        win_count = len(wins)
        win_rate = win_count / len(tf_trades)
        total_pnl = sum(t['pnl'] for t in tf_trades)
        
        # Early exit for bad strategies
        if win_rate < 0.50 or total_pnl < -5:
            return make_empty_result(asset, timeframe, strategy)
        
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
        
    except Exception as e:
        return make_empty_result(asset, timeframe, strategy, str(e))
    finally:
        bs.BASE_STRATEGY = original


def make_empty_result(asset, timeframe, strategy, error=None):
    """Create empty result"""
    result = {
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
    if error:
        result['error'] = error
    return result


def generate_combinations():
    """Generate all combinations"""
    keys = list(PARAMETER_GRID.keys())
    values = [PARAMETER_GRID[k] for k in keys]
    
    combinations = []
    for combo in itertools.product(*values):
        strategy = dict(zip(keys, combo))
        strategy['min_roc'] = -1.0
        combinations.append(strategy)
    
    return combinations


def run_search(timeframe, data_file, asset, output_file):
    """Run grid search"""
    
    print(f"\n{'='*80}")
    print(f"⚡ FAST GRID SEARCH: {asset} - {timeframe}")
    print(f"{'='*80}\n")
    
    # Generate combinations
    combinations = generate_combinations()
    total = len(combinations)
    
    print(f"📊 Total combinations: {total:,}")
    
    # Setup workers
    cpu_count = mp.cpu_count()
    workers = max(1, cpu_count - 1)
    
    print(f"🚀 Using {workers} workers (of {cpu_count} cores)")
    print(f"\nTesting strategies on {asset} {timeframe}...")
    print(f"Output: {output_file}\n")
    
    # Prepare args
    args_list = [(strategy, timeframe, data_file, asset) for strategy in combinations]
    
    # Run with timeout
    print("Starting parallel processing...")
    print("⏳ Initializing workers and loading data...\n")
    start_time = datetime.now()
    
    all_results = []
    completed = 0
    first_result = True
    last_progress_time = [start_time]  # Mutable for thread access
    timeout_triggered = [False]
    
    # Watchdog thread to detect stalls
    def watchdog():
        spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        idx = 0
        while not timeout_triggered[0]:
            elapsed = (datetime.now() - last_progress_time[0]).total_seconds()
            if elapsed > 120:  # 2 minute timeout
                timeout_triggered[0] = True
                print(f"\n\n❌ TIMEOUT: No progress for {elapsed:.0f}s")
                print("Workers appear to be stuck. Terminating...")
                break
            
            if completed == 0:
                # Show spinner while waiting for first result
                print(f"\r{spinner[idx % len(spinner)]} Waiting for workers... {elapsed:.0f}s", 
                      end='', flush=True)
                idx += 1
            
            time.sleep(0.2)
    
    watchdog_thread = threading.Thread(target=watchdog, daemon=True)
    watchdog_thread.start()
    
    # Use imap_unordered for progress tracking
    with mp.Pool(workers) as pool:
        try:
            # Use async with timeout for each batch
            for result in pool.imap_unordered(test_single_strategy, args_list, chunksize=10):
                if timeout_triggered[0]:
                    print("\n\n⚠️  Terminating due to timeout")
                    pool.terminate()
                    pool.join()
                    raise TimeoutError("Grid search timed out")
                
                if first_result:
                    print("\r" + " " * 80 + "\r", end='')  # Clear spinner
                    print("✅ First results received, processing in parallel...\n")
                    first_result = False
                
                all_results.append(result)
                completed += 1
                last_progress_time[0] = datetime.now()  # Reset watchdog
                
                # Progress update on EVERY result for streaming
                progress = (completed / total) * 100
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = completed / elapsed if elapsed > 0 else 0
                eta_seconds = (total - completed) / rate if rate > 0 else 0
                eta_minutes = eta_seconds / 60
                
                bar_width = 40
                filled = int(bar_width * completed / total)
                bar = '█' * filled + '░' * (bar_width - filled)
                
                # Stream every result
                print(f"\r[{bar}] {progress:5.1f}% | {completed:,}/{total:,} | "
                      f"{rate:.0f} strat/s | ETA: {eta_minutes:.1f}m",
                      end='', flush=True)
            
            timeout_triggered[0] = True  # Stop watchdog
            print()  # New line
            
        except KeyboardInterrupt:
            timeout_triggered[0] = True
            print("\n\n⚠️  Interrupted by user")
            pool.terminate()
            pool.join()
            raise
        except Exception as e:
            timeout_triggered[0] = True
            print(f"\n\n❌ Error: {e}")
            pool.terminate()
            pool.join()
            raise
    
    elapsed_total = (datetime.now() - start_time).total_seconds()
    
    print(f"\n⚡ Completed in {elapsed_total:.1f}s ({elapsed_total/60:.1f} min)")
    print(f"   Average: {total/elapsed_total:.0f} strategies/second")
    
    # Write results
    if all_results:
        print(f"\n💾 Writing {len(all_results):,} results...")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)
        print(f"✅ Results saved to {output_file}")
    
    return all_results


def analyze_results(results):
    """Analyze and show top 10"""
    
    if not results:
        print("No results")
        return
    
    print(f"\n{'='*80}")
    print("📊 RESULTS ANALYSIS")
    print(f"{'='*80}\n")
    
    # Filter valid
    valid = [r for r in results if r['trades'] >= 3]
    
    print(f"Total tested: {len(results):,}")
    print(f"Valid (3+ trades): {len(valid):,}")
    
    if not valid:
        print("\n⚠️  No valid strategies")
        return None
    
    # Sort by balanced score
    balanced = sorted(valid, key=lambda x: (x['win_rate'] * x['total_pnl']), reverse=True)
    
    # Top 10
    print(f"\n🏆 TOP 10 STRATEGIES:")
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
    
    # Return top 10 for saving
    return balanced[:10]


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fast grid search")
    parser.add_argument('--timeframe', '-t', required=True, help='Timeframe (e.g., 1h)')
    parser.add_argument('--asset', '-a', required=True, help='Asset (e.g., BTCUSDT)')
    parser.add_argument('--output', '-o', default=None, help='Output CSV file')
    
    args = parser.parse_args()
    
    # Determine data file
    data_file = f"data/{args.asset}_1m_90d.json"
    
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        return 1
    
    # Generate output filename
    if args.output is None:
        os.makedirs('grid_search_results', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f"grid_search_results/{args.asset}_{args.timeframe}_fast_{timestamp}.csv"
    
    # Run search
    results = run_search(args.timeframe, data_file, args.asset, args.output)
    
    # Analyze
    top10 = analyze_results(results)
    
    # Save top 10
    if top10:
        summary_file = args.output.replace('.csv', '_top10.json')
        with open(summary_file, 'w') as f:
            json.dump(top10, f, indent=2)
        print(f"\n💾 Top 10 saved to: {summary_file}")
    
    print(f"\n{'='*80}")
    print("✅ GRID SEARCH COMPLETE")
    print(f"{'='*80}\n")
    
    return 0


if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    sys.exit(main())
