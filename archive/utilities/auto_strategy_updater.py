#!/usr/bin/env python3
"""
Automatic Strategy Updater

Ensures data is fresh and automatically finds best fallback strategies:
1. Checks if data is < 30 days old
2. Re-downloads if stale
3. Runs grid search to find 2 best strategies
4. Saves as fallback strategies per timeframe
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from trading_pairs_config import get_active_pairs, ACTIVE_PAIRS

# Add validation path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validation.audit_logger import log_grid_search


DATA_FRESHNESS_DAYS = 30  # Max age before re-download


def check_data_freshness(data_file):
    """
    Check if data file is fresh (< 30 days old)
    
    Returns:
        (is_fresh, age_days, last_timestamp)
    """
    
    if not os.path.exists(data_file):
        return False, None, None
    
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        candles = data.get('candles', data) if isinstance(data, dict) else data
        
        if not candles:
            return False, None, None
        
        # Get last timestamp
        last_candle = candles[-1]
        last_ts_str = last_candle.get('timestamp', last_candle.get('time', ''))
        
        if not last_ts_str:
            return False, None, None
        
        last_ts = datetime.fromisoformat(last_ts_str.replace('Z', ''))
        now = datetime.now()
        age = now - last_ts
        age_days = age.days
        
        is_fresh = age_days < DATA_FRESHNESS_DAYS
        
        return is_fresh, age_days, last_ts
    
    except Exception as e:
        print(f"⚠️  Error checking {data_file}: {e}")
        return False, None, None


def download_fresh_data_parallel(symbols):
    """Download fresh 90-day data for multiple trading pairs in parallel"""
    
    if not symbols:
        return True
    
    print(f"\n{'='*80}")
    print(f"📥 DOWNLOADING FRESH DATA (PARALLEL)")
    print(f"{'='*80}")
    print(f"Pairs: {', '.join(symbols)}\n")
    
    # Use parallel downloader with verification
    try:
        from parallel_downloader import download_and_save_all
        saved_files = download_and_save_all(symbols=symbols, days=90, verify=True)
        return len(saved_files) == len(symbols)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False


def find_best_strategies(asset, timeframe, num_strategies=2):
    """
    Run grid search and find N best strategies
    
    Returns:
        List of best strategy configs
    """
    
    print(f"\n{'='*80}")
    print(f"🔍 FINDING BEST STRATEGIES: {asset} {timeframe}")
    print(f"{'='*80}\n")
    
    # Import spinner
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from utils.spinner import Spinner
    
    # Run grid search
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"grid_search_results/{asset.lower()}_{timeframe}_auto_{timestamp}.csv"
    
    # Start spinner
    spinner = Spinner(f"Testing 121,500 combinations for {asset} {timeframe}", style='dots_pulse')
    spinner.start()
    
    start_time = time.time()
    
    result = subprocess.run(
        [
            'python', 'grid_search_optimized.py',
            '--asset', asset,
            '--timeframe', timeframe,
            '--output', output_file
        ],
        capture_output=True,
        text=True,
        timeout=3600 * 2  # 2 hour timeout (optimized version is much faster)
    )
    
    elapsed = time.time() - start_time
    
    # Stop spinner
    spinner.stop()
    
    if result.returncode != 0:
        print(f"❌ Grid search failed for {asset} {timeframe}")
        return []
    
    # Load results
    if not os.path.exists(output_file):
        print(f"❌ Results file not found: {output_file}")
        return []
    
    import csv
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        all_results = list(reader)
    
    # Filter for valid strategies (3+ trades)
    valid = [r for r in all_results if int(r['trades']) >= 3]
    
    if not valid:
        print(f"⚠️  No valid strategies found (all had < 3 trades)")
        return []
    
    # Sort by balanced score (WR × PnL)
    valid.sort(key=lambda x: float(x['win_rate']) * float(x['total_pnl']), reverse=True)
    
    # Get top N
    best = valid[:num_strategies]
    
    # Log grid search with audit trail
    if valid:
        best_win_rate = max(float(r['win_rate']) for r in valid)
        log_grid_search(
            asset=asset,
            timeframe=timeframe,
            combinations=len(all_results),
            duration_seconds=elapsed,
            best_win_rate=best_win_rate
        )
    
    # Import validation
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from validation.expected_values import validate_strategy_params, validate_performance_metrics
    
    print(f"\n{'='*80}")
    print(f"📊 FOUND {len(best)} BEST STRATEGIES - DETAILED ANALYSIS")
    print(f"{'='*80}\n")
    
    for i, strat in enumerate(best, 1):
        wr = float(strat['win_rate'])
        trades = int(strat['trades'])
        pnl = float(strat['total_pnl'])
        pnl_per_trade = pnl / trades if trades > 0 else 0
        
        print(f"{'─'*80}")
        print(f"Strategy #{i}")
        print(f"{'─'*80}")
        
        # Performance Metrics
        print(f"\n📈 Performance:")
        print(f"  Win Rate:        {wr*100:.2f}%  {'✅' if wr >= 0.90 else '⚠️' if wr >= 0.70 else '❌'}")
        print(f"  Total Trades:    {trades}")
        print(f"  Total P&L:       ${pnl:+.2f}")
        print(f"  Avg P&L/Trade:   ${pnl_per_trade:+.2f}")
        
        # Calculate additional metrics
        wins = int(trades * wr)
        losses = trades - wins
        print(f"  Wins/Losses:     {wins}W / {losses}L")
        
        if losses > 0:
            # Estimate profit factor (assuming 2:1 RR)
            est_profit_factor = (wins * 2) / losses if losses > 0 else 999
            print(f"  Est. Profit Factor: {est_profit_factor:.2f}")
        
        # Strategy Parameters
        print(f"\n⚙️  Parameters:")
        print(f"  Confidence:      {strat['min_confidence']}")
        print(f"  Volume:          {strat['min_volume']}")
        print(f"  Trend:           {strat['min_trend']}")
        print(f"  ADX:             {strat['min_adx']}")
        print(f"  ATR Range:       {strat['atr_min']} - {strat['atr_max']}")
        
        # Validate Parameters
        strategy_params = {
            'min_confidence': float(strat['min_confidence']),
            'min_volume': float(strat['min_volume']),
            'min_trend': float(strat['min_trend']),
            'min_adx': int(strat['min_adx']),
            'atr_min': float(strat['atr_min']),
            'atr_max': float(strat['atr_max']),
        }
        
        params_valid, param_violations = validate_strategy_params(strategy_params)
        
        # Validate Performance
        performance_metrics = {
            'win_rate': wr,
            'trades_min': trades,
            'total_pnl': pnl,
        }
        
        perf_valid, perf_violations = validate_performance_metrics(performance_metrics)
        
        # Validation Status
        print(f"\n🔍 Validation:")
        if params_valid and perf_valid:
            print(f"  Status:          ✅ PASSED - All checks valid")
        else:
            print(f"  Status:          ⚠️  WARNINGS DETECTED")
            
            if param_violations:
                print(f"\n  Parameter Issues:")
                for v in param_violations:
                    print(f"    - {v['parameter']}: {v['value']} (expected {v['expected']})")
            
            if perf_violations:
                print(f"\n  Performance Issues:")
                for v in perf_violations:
                    print(f"    - {v['metric']}: {v['value']} (expected {v['expected']})")
        
        print()
    
    print(f"{'='*80}\n")
    
    return best


def save_fallback_strategies(asset, timeframe, strategies):
    """Save fallback strategies to config file with validation"""
    
    # Import validation
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from validation.expected_values import validate_strategy_params, validate_performance_metrics
    from validation.audit_logger import log_strategy_validation, log_fallback_save
    
    fallback_file = 'ml/fallback_strategies.json'
    
    print(f"\n{'='*80}")
    print(f"🔍 VALIDATING STRATEGIES BEFORE SAVING")
    print(f"{'='*80}\n")
    
    # Validate each strategy before saving
    validated_strategies = []
    for i, strat in enumerate(strategies, 1):
        print(f"Validating Strategy #{i}...")
        
        # Validate parameters
        params = {
            'min_confidence': float(strat['min_confidence']),
            'min_volume': float(strat['min_volume']),
            'min_trend': float(strat['min_trend']),
            'min_adx': int(strat['min_adx']),
            'atr_min': float(strat['atr_min']),
            'atr_max': float(strat['atr_max']),
        }
        
        params_valid, param_violations = validate_strategy_params(params)
        
        # Validate performance
        performance = {
            'win_rate': float(strat['win_rate']),
            'trades_min': int(strat['trades']),
            'total_pnl': float(strat['total_pnl']),
        }
        
        perf_valid, perf_violations = validate_performance_metrics(performance)
        
        # Check validation results
        all_violations = param_violations + perf_violations
        
        if params_valid and perf_valid:
            print(f"  ✅ Strategy #{i} validation PASSED")
            validated_strategies.append(strat)
            
            # Log success
            log_strategy_validation(asset, timeframe, i, True, [])
        else:
            print(f"  ⚠️  Strategy #{i} validation FAILED")
            
            if param_violations:
                for v in param_violations:
                    print(f"    - Parameter issue: {v['parameter']} = {v['value']} (expected {v['expected']})")
            
            if perf_violations:
                for v in perf_violations:
                    print(f"    - Performance issue: {v['metric']} = {v['value']} (expected {v['expected']})")
            
            print(f"  ❌ Skipping invalid strategy")
            
            # Log failure
            log_strategy_validation(asset, timeframe, i, False, all_violations)
    
    if not validated_strategies:
        print(f"\n❌ No valid strategies to save!")
        return
    
    print(f"\n✅ {len(validated_strategies)}/{len(strategies)} strategies passed validation\n")
    
    # Load existing fallbacks
    if os.path.exists(fallback_file):
        with open(fallback_file, 'r') as f:
            fallbacks = json.load(f)
    else:
        fallbacks = {}
    
    # Create key
    key = f"{asset}_{timeframe}"
    
    # Convert strategies to config format
    strategy_configs = []
    for strat in validated_strategies:
        config = {
            'min_confidence': float(strat['min_confidence']),
            'min_volume': float(strat['min_volume']),
            'min_trend': float(strat['min_trend']),
            'min_adx': int(strat['min_adx']),
            'min_roc': -1.0,
            'atr_min': float(strat['atr_min']),
            'atr_max': float(strat['atr_max']),
            'win_rate': float(strat['win_rate']),
            'trades': int(strat['trades']),
            'total_pnl': float(strat['total_pnl']),
            'updated': datetime.now().isoformat()
        }
        strategy_configs.append(config)
    
    # Save
    fallbacks[key] = {
        'strategies': strategy_configs,
        'updated_at': datetime.now().isoformat(),
        'data_period': '90_days',
        'validation_passed': True
    }
    
    with open(fallback_file, 'w') as f:
        json.dump(fallbacks, f, indent=2)
    
    # Log save
    log_fallback_save(asset, timeframe, len(validated_strategies), True)
    
    print(f"💾 Saved {len(validated_strategies)} validated fallback strategies to {fallback_file}")
    print(f"{'='*80}\n")


def update_strategies_if_needed():
    """
    Main function: Check data freshness and update strategies if needed
    
    Returns:
        Dictionary of updates performed
    """
    
    print("\n" + "="*80)
    print("🔄 AUTOMATIC STRATEGY UPDATER")
    print("="*80)
    print(f"\nChecking data freshness threshold: {DATA_FRESHNESS_DAYS} days")
    print(f"Active trading pairs: {', '.join(ACTIVE_PAIRS)}\n")
    
    updates = {
        'data_downloads': [],
        'strategies_updated': [],
        'up_to_date': []
    }
    
    # Check each active pair
    for symbol in ACTIVE_PAIRS:
        asset = symbol.replace('USDT', '').replace('BTC', '')  # ETH or BTC
        data_file = f"data/{asset.lower()}_90days.json"
        
        print(f"\n{'='*80}")
        print(f"📊 CHECKING: {symbol}")
        print(f"{'='*80}")
        print(f"Data file: {data_file}")
        
        # Check freshness
        is_fresh, age_days, last_ts = check_data_freshness(data_file)
        
        if is_fresh:
            print(f"✅ Data is fresh ({age_days} days old)")
            print(f"   Last update: {last_ts}")
            updates['up_to_date'].append(symbol)
            continue
        
        # Data is stale or missing
        if age_days is None:
            print(f"❌ Data file missing or corrupted")
        else:
            print(f"⚠️  Data is stale ({age_days} days old)")
            print(f"   Last update: {last_ts}")
        
        print(f"\n🔄 Re-downloading data...")
        
        # Download fresh data
        if download_fresh_data_for_pair(symbol):
            updates['data_downloads'].append(symbol)
            
            # Find best strategies for each timeframe
            for timeframe in ['15m', '1h', '4h']:
                print(f"\n{'='*80}")
                print(f"🔍 UPDATING FALLBACK STRATEGIES: {asset} {timeframe}")
                print(f"{'='*80}")
                
                strategies = find_best_strategies(asset, timeframe, num_strategies=2)
                
                if strategies:
                    save_fallback_strategies(asset, timeframe, strategies)
                    updates['strategies_updated'].append(f"{asset}_{timeframe}")
                else:
                    print(f"⚠️  No valid strategies found for {asset} {timeframe}")
    
    # Summary
    print("\n" + "="*80)
    print("📊 UPDATE SUMMARY")
    print("="*80)
    print(f"\nData Downloads: {len(updates['data_downloads'])}")
    for symbol in updates['data_downloads']:
        print(f"  ✅ {symbol}")
    
    print(f"\nStrategies Updated: {len(updates['strategies_updated'])}")
    for key in updates['strategies_updated']:
        print(f"  ✅ {key}")
    
    print(f"\nAlready Up-to-Date: {len(updates['up_to_date'])}")
    for symbol in updates['up_to_date']:
        print(f"  ✅ {symbol}")
    
    return updates


def check_before_trading():
    """
    Call this before starting any trading session
    
    Ensures:
    1. Data is fresh (< 30 days)
    2. Fallback strategies are available
    """
    
    print("\n" + "="*80)
    print("🔍 PRE-TRADING VALIDATION")
    print("="*80)
    
    updates = update_strategies_if_needed()
    
    # Load fallback strategies
    fallback_file = 'ml/fallback_strategies.json'
    if os.path.exists(fallback_file):
        with open(fallback_file, 'r') as f:
            fallbacks = json.load(f)
        
        print(f"\n✅ Fallback strategies loaded: {len(fallbacks)} configs")
    else:
        print(f"\n⚠️  No fallback strategies file found")
        print(f"   Run full update to generate fallbacks")
    
    print("\n" + "="*80)
    print("✅ PRE-TRADING VALIDATION COMPLETE")
    print("="*80)
    
    return updates


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Automatic strategy updater")
    parser.add_argument('--check', action='store_true',
                       help='Check data freshness only (no updates)')
    parser.add_argument('--force', action='store_true',
                       help='Force re-download and update all strategies')
    
    args = parser.parse_args()
    
    if args.check:
        # Just check, don't update
        print("\n" + "="*80)
        print("🔍 DATA FRESHNESS CHECK")
        print("="*80)
        
        for symbol in ACTIVE_PAIRS:
            asset = symbol.replace('USDT', '').replace('BTC', '')
            data_file = f"data/{asset.lower()}_90days.json"
            
            is_fresh, age_days, last_ts = check_data_freshness(data_file)
            
            status = "✅ FRESH" if is_fresh else "⚠️  STALE"
            age_str = f"{age_days} days" if age_days is not None else "N/A"
            
            print(f"\n{symbol:10s} {status:10s} Age: {age_str:10s}")
            if last_ts:
                print(f"           Last update: {last_ts}")
    
    elif args.force:
        # Force update everything
        import auto_strategy_updater
        auto_strategy_updater.DATA_FRESHNESS_DAYS = 0  # Force all to be stale
        
        print("\n⚠️  FORCING COMPLETE UPDATE")
        print("   All data will be re-downloaded")
        print("   All strategies will be regenerated\n")
        
        response = input("Continue? (yes/no): ")
        if response.lower() == 'yes':
            update_strategies_if_needed()
        else:
            print("Cancelled")
    
    else:
        # Normal update check
        check_before_trading()
