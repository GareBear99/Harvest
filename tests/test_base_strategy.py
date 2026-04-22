#!/usr/bin/env python3
"""
Base Strategy Validation Test
Ensures base strategy produces expected baseline results
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest_90_complete import MultiTimeframeBacktest
from ml.base_strategy import BASELINE_RESULTS, BASE_STRATEGY


def run_baseline_test(data_file: str, expected: dict, seed: int = 42):
    """Run backtest with base strategy and compare to expected results"""
    
    symbol = data_file.split('/')[-1].split('_')[0].upper()
    print(f"\n🧪 Testing Base Strategy: {symbol}")
    print(f"   Expected: {expected['total_trades']} trades, {expected['win_rate']:.1%} WR, ${expected['final_balance']:.2f}")
    
    # Run backtest with seed for determinism
    backtest = MultiTimeframeBacktest(data_file, starting_balance=10.0, seed=seed)
    
    # Disable print output during run
    import io
    from contextlib import redirect_stdout
    
    with redirect_stdout(io.StringIO()):
        backtest.run()
    
    # Extract results
    trade_count = len(backtest.all_trades)
    wins = len([t for t in backtest.all_trades if t['pnl'] > 0])
    win_rate = wins / trade_count if trade_count > 0 else 0
    final_balance = backtest.get_total_balance()
    
    print(f"   Actual:   {trade_count} trades, {win_rate:.1%} WR, ${final_balance:.2f}\n")
    
    # Check results
    passed = True
    
    # Trade count (exact match)
    if trade_count != expected['total_trades']:
        print(f"   ❌ Trade count mismatch: {trade_count} != {expected['total_trades']}")
        passed = False
    else:
        print(f"   ✅ Trade count matches: {trade_count}")
    
    # Win rate (allow 5% tolerance)
    wr_diff = abs(win_rate - expected['win_rate'])
    if wr_diff > 0.05:
        print(f"   ❌ Win rate mismatch: {win_rate:.1%} vs {expected['win_rate']:.1%} (diff: {wr_diff:.1%})")
        passed = False
    else:
        print(f"   ✅ Win rate matches: {win_rate:.1%}")
    
    # Final balance (allow 5% tolerance)
    balance_diff_pct = abs(final_balance - expected['final_balance']) / expected['final_balance']
    if balance_diff_pct > 0.05:
        print(f"   ❌ Balance mismatch: ${final_balance:.2f} vs ${expected['final_balance']:.2f} (diff: {balance_diff_pct:.1%})")
        passed = False
    else:
        print(f"   ✅ Balance matches: ${final_balance:.2f}")
    
    return passed


def test_base_strategy():
    """Test base strategy produces expected results"""
    
    print(f"\n{'='*80}")
    print("BASE STRATEGY VALIDATION TEST")
    print(f"{'='*80}")
    print("\nVerifies that base strategy with seed=42 produces expected results.")
    print("This ensures strategy changes don't break the baseline.\n")
    
    print("📋 Base Strategy Configuration:")
    for tf, thresholds in BASE_STRATEGY.items():
        print(f"\n   {tf}:")
        print(f"      Confidence: {thresholds['min_confidence']:.2f}")
        print(f"      Volume: {thresholds['min_volume']:.2f}x")
        print(f"      Trend: {thresholds['min_trend']:.2f}")
        print(f"      ADX: {thresholds['min_adx']}")
        print(f"      ATR: {thresholds['atr_min']:.2f}-{thresholds['atr_max']:.2f}%")
    
    # Test both assets
    eth_results = BASELINE_RESULTS['eth_21days']
    eth_passed = run_baseline_test(
        eth_results['data_file'],
        eth_results['expected'],
        seed=eth_results['seed']
    )
    
    btc_results = BASELINE_RESULTS['btc_21days']
    btc_passed = run_baseline_test(
        btc_results['data_file'],
        btc_results['expected'],
        seed=btc_results['seed']
    )
    
    # Final result
    print(f"\n{'='*80}")
    print("BASE STRATEGY TEST RESULTS")
    print(f"{'='*80}\n")
    
    print(f"ETH: {'✅ PASS' if eth_passed else '❌ FAIL'}")
    print(f"BTC: {'✅ PASS' if btc_passed else '❌ FAIL'}")
    
    if eth_passed and btc_passed:
        print(f"\n✅ BASE STRATEGY TEST PASSED")
        print("Base strategy produces expected results.\n")
        return True
    else:
        print(f"\n❌ BASE STRATEGY TEST FAILED")
        print("Base strategy results differ from baseline.")
        print("This may indicate strategy changes or non-deterministic behavior.\n")
        return False


if __name__ == "__main__":
    import sys
    passed = test_base_strategy()
    sys.exit(0 if passed else 1)
