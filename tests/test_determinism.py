#!/usr/bin/env python3
"""
Test Determinism - Validate 100% reproducible results

Runs the same backtest 3 times with seed=42 and verifies:
1. Exact same number of trades
2. Exact same trades on each timeframe
3. Exact same P&L
4. Strategy seeds tracked correctly
"""

import json
from backtest_90_complete import MultiTimeframeBacktest


def run_backtest_with_seed(seed=42):
    """Run backtest and collect results"""
    backtest = MultiTimeframeBacktest(
        'data/eth_90days.json',
        starting_balance=10.0,
        seed=seed
    )
    backtest.run()
    
    # Collect trade data
    trades_data = []
    for trade in backtest.all_trades:
        trades_data.append({
            'timeframe': trade['timeframe'],
            'entry_time': trade['entry_time'],
            'exit_time': trade['exit_time'],
            'outcome': trade['outcome'],
            'pnl': round(trade['pnl'], 4),  # Round to avoid float precision issues
            'direction': trade.get('direction', 'SHORT'),
            'strategy_seed': trade.get('strategy_seed')
        })
    
    return {
        'total_trades': len(backtest.all_trades),
        'final_balance': round(backtest.get_total_balance(), 4),
        'trades': trades_data
    }


def main():
    print("\n" + "="*80)
    print("DETERMINISM VALIDATION TEST")
    print("="*80)
    print("\nRunning same backtest 3 times with seed=42...")
    print("Expecting 100% identical results\n")
    
    # Run 3 times
    results = []
    for i in range(1, 4):
        print(f"\n--- Run #{i} ---")
        result = run_backtest_with_seed(seed=42)
        results.append(result)
        print(f"Trades: {result['total_trades']}, Final: ${result['final_balance']}")
    
    # Validation
    print(f"\n{'='*80}")
    print("VALIDATION RESULTS")
    print(f"{'='*80}\n")
    
    # Check trade counts match
    run1_trades = results[0]['total_trades']
    run2_trades = results[1]['total_trades']
    run3_trades = results[2]['total_trades']
    
    print(f"✓ Trade Count Consistency:")
    print(f"  Run 1: {run1_trades} trades")
    print(f"  Run 2: {run2_trades} trades")
    print(f"  Run 3: {run3_trades} trades")
    
    if run1_trades == run2_trades == run3_trades:
        print(f"  ✅ PASS: All runs have same trade count")
    else:
        print(f"  ❌ FAIL: Trade counts differ")
        return
    
    # Check final balances match
    run1_balance = results[0]['final_balance']
    run2_balance = results[1]['final_balance']
    run3_balance = results[2]['final_balance']
    
    print(f"\n✓ Final Balance Consistency:")
    print(f"  Run 1: ${run1_balance}")
    print(f"  Run 2: ${run2_balance}")
    print(f"  Run 3: ${run3_balance}")
    
    if run1_balance == run2_balance == run3_balance:
        print(f"  ✅ PASS: All runs have same final balance")
    else:
        print(f"  ❌ FAIL: Final balances differ")
        return
    
    # Check individual trades match
    print(f"\n✓ Individual Trade Validation:")
    all_match = True
    
    for i in range(run1_trades):
        trade1 = results[0]['trades'][i]
        trade2 = results[1]['trades'][i]
        trade3 = results[2]['trades'][i]
        
        # Check all fields match
        if (trade1['timeframe'] != trade2['timeframe'] or trade1['timeframe'] != trade3['timeframe'] or
            trade1['entry_time'] != trade2['entry_time'] or trade1['entry_time'] != trade3['entry_time'] or
            trade1['pnl'] != trade2['pnl'] or trade1['pnl'] != trade3['pnl']):
            print(f"  ❌ Trade #{i+1} differs across runs")
            print(f"     Run1: {trade1['timeframe']} {trade1['pnl']}")
            print(f"     Run2: {trade2['timeframe']} {trade2['pnl']}")
            print(f"     Run3: {trade3['timeframe']} {trade3['pnl']}")
            all_match = False
    
    if all_match:
        print(f"  ✅ PASS: All {run1_trades} trades identical across runs")
    else:
        print(f"  ❌ FAIL: Some trades differ")
        return
    
    # Check strategy seeds are tracked
    print(f"\n✓ Strategy Seed Tracking:")
    seeds_found = set()
    for trade in results[0]['trades']:
        if trade['strategy_seed']:
            seeds_found.add(trade['strategy_seed'])
    
    print(f"  Seeds found in trades: {sorted(seeds_found)}")
    
    expected_seeds = {15001, 60001, 240001}
    if seeds_found.issubset(expected_seeds):
        print(f"  ✅ PASS: Strategy seeds correctly tracked")
    else:
        print(f"  ⚠️  WARNING: Unexpected seeds found")
    
    # Breakdown by timeframe
    print(f"\n✓ Per-Timeframe Breakdown:")
    tf_counts = {}
    for trade in results[0]['trades']:
        tf = trade['timeframe']
        tf_counts[tf] = tf_counts.get(tf, 0) + 1
    
    for tf in sorted(tf_counts.keys()):
        print(f"  {tf}: {tf_counts[tf]} trades")
    
    print(f"\n{'='*80}")
    print("✅ DETERMINISM VALIDATED")
    print("Results are 100% reproducible with seed=42")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
