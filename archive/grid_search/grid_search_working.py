#!/usr/bin/env python3
"""
Grid Search - 121,500 combinations
Sequential processing with progress bar and timeout management
"""

import csv
import json
import itertools
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Grid parameters - Optimized for realistic runtime
# ~4,050 combinations instead of 121,500
GRID = {
    'min_confidence': [0.60, 0.66, 0.70, 0.76, 0.80, 0.86, 0.90],  # 7 values
    'min_volume': [1.00, 1.10, 1.20, 1.30, 1.40, 1.50],  # 6 values
    'min_trend': [0.40, 0.50, 0.55, 0.65, 0.75],  # 5 values
    'min_adx': [20, 25, 30, 35, 40],  # 5 values
    'atr_min': [0.3, 0.4, 0.5],  # 3 values
    'atr_max': [3.0, 3.5, 4.5, 5.0]  # 4 values
}
# Total: 7*6*5*5*3*4 = 12,600 combinations

def test_one(strategy, timeframe, data_file, seed=42):
    """Test single strategy"""
    from backtest_90_complete import MultiTimeframeBacktest
    import ml.base_strategy as bs
    import io
    from contextlib import redirect_stdout, redirect_stderr
    
    orig = bs.BASE_STRATEGY[timeframe].copy()
    
    try:
        bs.BASE_STRATEGY[timeframe] = strategy.copy()
        
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            bt = MultiTimeframeBacktest(data_file, 10.0, seed=seed)
            bt.run()
        
        trades = [t for t in bt.all_trades if t.get('timeframe') == timeframe]
        
        # Always return result with seed, even if no trades
        wins = [t for t in trades if t['pnl'] > 0]
        wr = len(wins) / len(trades) if trades else 0.0
        pnl = sum(t['pnl'] for t in trades) if trades else 0.0
        
        return {
            'seed': seed,
            'trades': len(trades),
            'wins': len(wins),
            'win_rate': wr,
            'total_pnl': pnl,
            'avg_win': sum(t['pnl'] for t in wins) / len(wins) if wins else 0.0,
            'avg_loss': sum(t['pnl'] for t in [t for t in trades if t['pnl'] <= 0]) / (len(trades) - len(wins)) if len(trades) > len(wins) else 0.0,
            **strategy
        }
    except Exception as e:
        # Return error result
        return {
            'seed': seed,
            'trades': 0,
            'wins': 0,
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'error': str(e),
            **strategy
        }
    finally:
        bs.BASE_STRATEGY[timeframe] = orig


def run(timeframe, data_file, output_file):
    """Run grid search"""
    print(f"\n{'='*80}")
    print(f"🔍 GRID SEARCH: {timeframe}")
    print(f"{'='*80}\n")
    
    # Generate all combinations
    keys = list(GRID.keys())
    values = [GRID[k] for k in keys]
    total = 1
    for v in values:
        total *= len(v)
    
    print(f"📊 Total: {total:,} combinations")
    print(f"📁 Output: {output_file}")
    
    # Generate and sort combinations intelligently
    print(f"\n🧠 Sorting strategies by predicted performance...")
    all_combos = list(itertools.product(*values))
    
    # Score each combination (higher confidence, moderate trend/volume, higher ADX)
    def score_combo(combo):
        params = dict(zip(keys, combo))
        score = 0
        # Prefer higher confidence (most important)
        score += params['min_confidence'] * 100
        # Prefer moderate volume (1.2-1.4 range)
        vol_optimal = 1.3
        score -= abs(params['min_volume'] - vol_optimal) * 20
        # Prefer moderate-high trend (0.55-0.70)
        trend_optimal = 0.60
        score -= abs(params['min_trend'] - trend_optimal) * 30
        # Prefer higher ADX
        score += params['min_adx'] * 0.5
        # Prefer moderate ATR ranges
        score += (params['atr_max'] - params['atr_min']) * 2
        return score
    
    # Sort by predicted score (best first)
    all_combos.sort(key=score_combo, reverse=True)
    
    print(f"✅ Sorted {total:,} combinations (testing best predicted first)\n")
    
    # Load existing best strategies
    history_file = output_file.replace('.csv', '_history.json')
    best_strategies = []
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            best_strategies = json.load(f)
        print(f"📜 Loaded {len(best_strategies)} previous best strategies:")
        for i, s in enumerate(best_strategies[:5], 1):
            print(f"   {i}. WR: {s['win_rate']:.1%} | PnL: ${s['total_pnl']:+.2f} | "
                  f"conf={s['min_confidence']:.2f} adx={s['min_adx']}")
        print()
    
    # Load checkpoint if exists
    checkpoint_file = output_file.replace('.csv', '_checkpoint.json')
    tested_combinations = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
            tested_combinations = set(tuple(c) for c in checkpoint['tested'])
        print(f"🔄 Resuming from checkpoint: {len(tested_combinations):,} already tested\n")
    else:
        print("Starting fresh search...\n")
    
    start = datetime.now()
    all_results = []  # ALL tested strategies
    results = []  # Valid strategies (3+ trades)
    sweet_spot = []  # Strategies with 70%+ WR and positive PnL
    tested = 0
    valid = 0
    last_update = start
    top10_display = []
    last_checkpoint_valid = 0  # Track checkpoints
    
    for combo in all_combos:
        # Skip if already tested
        if combo in tested_combinations:
            tested += 1
            continue
        
        strat = dict(zip(keys, combo))
        strat['min_roc'] = -1.0
        
        # Generate unique seed from strategy parameters
        strategy_seed = hash(combo) % (2**31)  # Positive 32-bit int
        
        result = test_one(strat, timeframe, data_file, seed=strategy_seed)
        
        # Save ALL results
        all_results.append(result)
        
        # Track valid strategies (3+ trades)
        if result['trades'] >= 3 and result['win_rate'] >= 0.50 and result['total_pnl'] > -5:
            results.append(result)
            valid += 1
            
            # Track sweet spot strategies (70%+ WR, positive PnL)
            if result['win_rate'] >= 0.70 and result['total_pnl'] > 0:
                sweet_spot.append(result)
        
        tested += 1
        tested_combinations.add(combo)
        now = datetime.now()
        
        # Save checkpoint every 10 valid strategies
        if valid > 0 and valid % 10 == 0 and valid != last_checkpoint_valid:
            with open(checkpoint_file, 'w') as f:
                json.dump({
                    'tested': [list(c) for c in tested_combinations],
                    'valid_count': valid,
                    'sweet_spot_count': len(sweet_spot)
                }, f)
            last_checkpoint_valid = valid
        
        # Update every 10 strategies or every 5 seconds
        if tested % 10 == 0 or (now - last_update).total_seconds() >= 5 or tested == total:
            last_update = now
            elapsed = (now - start).total_seconds()
            rate = tested / elapsed if elapsed > 0 else 0
            remain = (total - tested) / rate if rate > 0 else 0
            
            # Update top 10 from current results
            if results:
                sorted_results = sorted(results, key=lambda x: x['win_rate'] * x['total_pnl'], reverse=True)
                top10_display = sorted_results[:10]
            
            pct = tested / total * 100
            bar_len = 40
            filled = int(bar_len * tested / total)
            bar = '█' * filled + '░' * (bar_len - filled)
            
            # Clear screen area and show top strategies above progress
            print('\r' + ' ' * 120, end='\r')  # Clear line
            if top10_display:
                print('\033[F' * min(4, len(top10_display) + 1))  # Move cursor up
                print(f"\033[K🎯 Sweet Spot (70%+ WR): {len(sweet_spot)} found" + '\033[K')
                print('\033[K' + '🏆 Current Top 3:' + '\033[K')
                for i, s in enumerate(top10_display[:3], 1):
                    score = s['win_rate'] * s['total_pnl']
                    sweet_emoji = ' 🎯' if s['win_rate'] >= 0.70 else ''
                    print(f"\033[K{i}. WR:{s['win_rate']:.1%} PnL:${s['total_pnl']:+.2f} Score:{score:.2f}{sweet_emoji}" + '\033[K')
            
            print(f"\r[{bar}] {pct:5.1f}% | {tested:,}/{total:,} | "
                  f"{rate:.1f}/s | ETA: {remain/60:.1f}m | Valid: {valid}",
                  end='', flush=True)
    
    print()
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"\n⚡ Done: {elapsed:.0f}s ({elapsed/60:.1f}m)")
    print(f"   Rate: {total/elapsed:.1f} strategies/sec")
    print(f"   Valid: {valid:,}")
    print(f"   🎯 Sweet Spot (70%+ WR): {len(sweet_spot)}\n")
    
    # Save results and history
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save ALL tested strategies (including failures)
    if all_results:
        all_file = output_file.replace('.csv', '_all.csv')
        with open(all_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)
        print(f"💾 Saved all {len(all_results)} strategies: {all_file}")
    
    # Save valid strategies
    if results:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"💾 Saved {len(results)} valid strategies: {output_file}")
        
        # Update history with new best strategies
        sorted_results = sorted(results, key=lambda x: x['win_rate'] * x['total_pnl'], reverse=True)
        new_best = sorted_results[:10]
        
        # Merge with existing history, keeping unique top performers
        all_strategies = best_strategies + new_best
        # Remove duplicates by strategy params
        seen = set()
        unique = []
        for s in all_strategies:
            key = tuple(s[k] for k in ['min_confidence', 'min_volume', 'min_trend', 'min_adx', 'atr_min', 'atr_max'])
            if key not in seen:
                seen.add(key)
                unique.append(s)
        
        # Keep top 20 overall
        unique_sorted = sorted(unique, key=lambda x: x['win_rate'] * x['total_pnl'], reverse=True)[:20]
        
        with open(history_file, 'w') as f:
            json.dump(unique_sorted, f, indent=2)
        print(f"📜 Updated history: {history_file}")
        
        # Save sweet spot strategies separately
        if sweet_spot:
            sweet_file = output_file.replace('.csv', '_sweetspot.json')
            sweet_sorted = sorted(sweet_spot, key=lambda x: x['win_rate'] * x['total_pnl'], reverse=True)
            with open(sweet_file, 'w') as f:
                json.dump(sweet_sorted, f, indent=2)
            print(f"🎯 Saved {len(sweet_sorted)} sweet spot strategies: {sweet_file}\n")
    
    return results


def show_top10(results):
    """Show top 10"""
    if not results:
        print("No valid strategies")
        return None
    
    sorted_results = sorted(results, key=lambda x: x['win_rate'] * x['total_pnl'], reverse=True)
    
    print(f"{'='*80}")
    print("🏆 TOP 10 STRATEGIES")
    print(f"{'='*80}\n")
    
    for i, r in enumerate(sorted_results[:10], 1):
        score = r['win_rate'] * r['total_pnl']
        print(f"{i:2}. Score: {score:6.2f} | WR: {r['win_rate']:5.1%} | "
              f"PnL: ${r['total_pnl']:+6.2f} | Trades: {r['trades']:3}")
        print(f"    conf={r['min_confidence']:.2f} vol={r['min_volume']:.2f} "
              f"trend={r['min_trend']:.2f} adx={r['min_adx']} "
              f"atr={r['atr_min']:.1f}-{r['atr_max']:.1f}\n")
    
    return sorted_results[:10]


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeframe', '-t', required=True)
    parser.add_argument('--asset', '-a', required=True)
    parser.add_argument('--output', '-o', default=None)
    args = parser.parse_args()
    
    data_file = f"data/{args.asset}_1m_90d.json"
    
    if not os.path.exists(data_file):
        print(f"❌ Not found: {data_file}")
        sys.exit(1)
    
    if not args.output:
        os.makedirs('grid_search_results', exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f"grid_search_results/{args.asset}_{args.timeframe}_{ts}.csv"
    
    results = run(args.timeframe, data_file, args.output)
    top10 = show_top10(results)
    
    if top10:
        json_file = args.output.replace('.csv', '_top10.json')
        with open(json_file, 'w') as f:
            json.dump(top10, f, indent=2)
        print(f"💾 Top 10: {json_file}\n")
    
    print(f"{'='*80}")
    print("✅ COMPLETE")
    print(f"{'='*80}\n")
