#!/usr/bin/env python3
"""
Pre-Trading Validation System

Ensures system is ready before ANY trading activity:
1. Checks data freshness (<30 days)
2. Auto-downloads if stale
3. Runs grid search to find 2 best strategies per timeframe
4. Saves fallback strategies
5. Validates all components are ready
6. For LIVE trading: Requires 48h paper trading with 1+ successful trade

USE THIS BEFORE:
- Running backtests
- Starting live trading (requires paper trading validation)
- Optimization runs
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
from auto_strategy_updater import (
    check_data_freshness,
    download_fresh_data_parallel,
    find_best_strategies,
    save_fallback_strategies,
    DATA_FRESHNESS_DAYS
)
from trading_pairs_config import ACTIVE_PAIRS
from core.paper_trading_tracker import get_paper_trading_tracker


def validate_system_health() -> Dict:
    """
    Complete system health check
    
    Returns:
        Dict with status of all components
    """
    
    print("\n" + "="*80)
    print("🏥 SYSTEM HEALTH CHECK")
    print("="*80 + "\n")
    
    health = {
        'all_ok': True,
        'data_fresh': {},
        'data_issues': [],
        'fallback_strategies': {},
        'warnings': []
    }
    
    # 1. Check data freshness for all pairs
    print("📊 Checking data freshness...")
    for symbol in ACTIVE_PAIRS:
        asset = symbol.replace('USDT', '')
        data_file = f"data/{asset.lower()}_90days.json"
        
        is_fresh, age_days, last_ts = check_data_freshness(data_file)
        
        health['data_fresh'][symbol] = {
            'fresh': is_fresh,
            'age_days': age_days,
            'last_timestamp': last_ts,
            'file': data_file
        }
        
        if is_fresh:
            print(f"  ✅ {symbol}: Fresh ({age_days} days)")
        else:
            print(f"  ❌ {symbol}: Stale or missing ({age_days} days if exists)")
            health['data_issues'].append(symbol)
            health['all_ok'] = False
    
    # 2. Check fallback strategies exist
    print("\n🎯 Checking fallback strategies...")
    fallback_file = 'ml/fallback_strategies.json'
    
    if os.path.exists(fallback_file):
        with open(fallback_file, 'r') as f:
            fallbacks = json.load(f)
        
        for key, config in fallbacks.items():
            num_strategies = len(config.get('strategies', []))
            updated = config.get('updated_at', 'unknown')
            health['fallback_strategies'][key] = {
                'count': num_strategies,
                'updated_at': updated,
                'exists': True
            }
            print(f"  ✅ {key}: {num_strategies} strategies (updated: {updated[:10]})")
    else:
        print(f"  ⚠️  No fallback strategies file found")
        health['warnings'].append("No fallback strategies - will generate on first update")
    
    # 3. Check base strategy available
    print("\n📋 Checking BASE_STRATEGY...")
    try:
        from ml.base_strategy import BASE_STRATEGY
        timeframes = list(BASE_STRATEGY.keys())
        print(f"  ✅ BASE_STRATEGY loaded: {', '.join(timeframes)}")
    except Exception as e:
        print(f"  ❌ BASE_STRATEGY error: {e}")
        health['all_ok'] = False
    
    print("\n" + "="*80)
    if health['all_ok']:
        print("✅ SYSTEM HEALTHY - Ready to trade")
    else:
        print("⚠️  SYSTEM NEEDS UPDATES")
        if health['data_issues']:
            print(f"   Data issues: {', '.join(health['data_issues'])}")
    print("="*80 + "\n")
    
    return health


def update_stale_data(health: Dict, interactive: bool = True) -> bool:
    """
    Update any stale data
    
    Args:
        health: Health check results
        interactive: If True, ask user before updating
    
    Returns:
        True if updates successful, False otherwise
    """
    
    if not health['data_issues']:
        print("✅ No data updates needed\n")
        return True
    
    print("\n" + "="*80)
    print(f"🔄 DATA UPDATE REQUIRED")
    print("="*80)
    print(f"\nStale pairs: {', '.join(health['data_issues'])}")
    print(f"Freshness threshold: {DATA_FRESHNESS_DAYS} days\n")
    
    if interactive:
        response = input("Update now? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Update cancelled - system not ready for trading")
            return False
    
    # Download fresh data in parallel
    success = download_fresh_data_parallel(health['data_issues'])
    
    if not success:
        print("\n❌ Downloads failed - system not ready")
        return False
    
    # Generate fallback strategies for updated pairs
    print("\n" + "="*80)
    print("🎯 GENERATING FALLBACK STRATEGIES")
    print("="*80 + "\n")
    
    for symbol in health['data_issues']:
        asset = symbol.replace('USDT', '')
        
        for timeframe in ['15m', '1h', '4h']:
            print(f"\n{'='*80}")
            print(f"🔍 {asset} {timeframe}")
            print(f"{'='*80}")
            
            strategies = find_best_strategies(asset, timeframe, num_strategies=2)
            
            if strategies:
                save_fallback_strategies(asset, timeframe, strategies)
                print(f"✅ Saved 2 fallback strategies for {asset} {timeframe}")
            else:
                print(f"⚠️  No valid strategies found for {asset} {timeframe}")
                # This is OK - BASE_STRATEGY will be used
    
    print("\n✅ Data updates complete\n")
    return True


def validate_paper_trading(for_live_trading: bool = False) -> Dict:
    """
    Validate paper trading requirements for live trading
    
    Args:
        for_live_trading: If True, enforce paper trading requirements
    
    Returns:
        Dict with paper trading status and approval
    """
    if not for_live_trading:
        return {
            'required': False,
            'approved': True,
            'message': 'Paper trading not required for backtesting'
        }
    
    print("\n" + "="*80)
    print("📄 PAPER TRADING VALIDATION (Live Trading Requirement)")
    print("="*80 + "\n")
    
    tracker = get_paper_trading_tracker()
    status = tracker.get_status()
    
    print(f"Status: {status['status']}")
    print(f"Balance: ${status['starting_balance']:.2f} (Full Base System)")
    print(f"Active Slots: {status.get('active_slots', 10)}")
    print(f"Duration: {status['duration_hours']:.1f} hours")
    print(f"Total Trades: {status['total_trades']}")
    print(f"Win Rate: {status['win_rate']:.1%}")
    print(f"Total P&L: ${status['total_pnl']:.2f}")
    if status.get('btc_fees_paid', 0) > 0:
        print(f"BTC Fees Paid: ${status['btc_fees_paid']:.2f} (stair climbing)")
    print()
    
    # Check approval
    approved, reason = tracker.is_approved_for_live()
    
    if approved:
        print("✅ PAPER TRADING REQUIREMENTS MET")
        print(f"   {reason}")
        print()
        return {
            'required': True,
            'approved': True,
            'message': reason,
            'stats': status
        }
    else:
        print("❌ PAPER TRADING REQUIREMENTS NOT MET")
        print(f"   {reason}")
        print()
        print("Requirements:")
        reqs = tracker.check_requirements()
        if 'duration' in reqs:
            dur = reqs['duration']
            print(f"  • Duration: {dur['current']:.1f}h / {dur['required']}h {'✅' if dur['met'] else '❌'}")
            if not dur['met']:
                print(f"    Remaining: {dur['remaining']:.1f}h")
        if 'trades' in reqs:
            trades = reqs['trades']
            print(f"  • Min Trades: {trades['current']} / {trades['required']} {'✅' if trades['met'] else '❌'}")
        if 'pnl' in reqs:
            pnl = reqs['pnl']
            print(f"  • Positive P&L: ${pnl['current']:.2f} {'✅' if pnl['met'] else '❌'}")
        print()
        print("Start paper trading with: python3 -m core.paper_trading_tracker")
        print()
        
        return {
            'required': True,
            'approved': False,
            'message': reason,
            'stats': status,
            'requirements': reqs
        }


def pre_trading_check(interactive: bool = True, force_update: bool = False, for_live_trading: bool = False) -> Dict:
    """
    Complete pre-trading validation and update sequence
    
    Args:
        interactive: If True, prompt user for updates
        force_update: If True, force update all data regardless of freshness
        for_live_trading: If True, enforce paper trading requirements
    
    Returns:
        Dict with complete system status
    """
    
    print("\n" + "#"*80)
    print("🔍 PRE-TRADING VALIDATION")
    print("#"*80 + "\n")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Timestamp: {timestamp}")
    print(f"Active pairs: {', '.join(ACTIVE_PAIRS)}")
    print(f"Data freshness threshold: {DATA_FRESHNESS_DAYS} days\n")
    
    # Force update if requested
    if force_update:
        print("⚠️  FORCE UPDATE MODE - All data will be refreshed\n")
        import auto_strategy_updater
        original_threshold = auto_strategy_updater.DATA_FRESHNESS_DAYS
        auto_strategy_updater.DATA_FRESHNESS_DAYS = 0  # Make everything stale
    
    # 1. Check system health
    health = validate_system_health()
    
    # 2. Update stale data if needed
    if health['data_issues'] or force_update:
        if not update_stale_data(health, interactive=interactive):
            print("\n❌ SYSTEM NOT READY - Updates required but failed/cancelled")
            return {'ready': False, 'health': health}
        
        # Re-check health after updates
        health = validate_system_health()
    
    # Restore original threshold if we forced update
    if force_update:
        import auto_strategy_updater
        auto_strategy_updater.DATA_FRESHNESS_DAYS = original_threshold
    
    # 3. Paper trading validation (for live trading only)
    paper_trading_result = validate_paper_trading(for_live_trading=for_live_trading)
    
    # 4. Final validation
    print("\n" + "#"*80)
    if health['all_ok'] and paper_trading_result['approved']:
        if for_live_trading:
            print("✅ SYSTEM READY FOR LIVE TRADING")
        else:
            print("✅ SYSTEM READY FOR TRADING")
        print("#"*80 + "\n")
        
        return {
            'ready': True,
            'health': health,
            'paper_trading': paper_trading_result,
            'timestamp': timestamp,
            'message': 'All systems operational'
        }
    else:
        print("❌ SYSTEM NOT READY")
        if for_live_trading and not paper_trading_result['approved']:
            print("   Paper trading requirements not met")
        print("#"*80 + "\n")
        
        return {
            'ready': False,
            'health': health,
            'paper_trading': paper_trading_result,
            'timestamp': timestamp,
            'message': 'System checks failed'
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pre-trading validation system")
    parser.add_argument('--non-interactive', action='store_true',
                       help='Run without prompts (auto-update stale data)')
    parser.add_argument('--force', action='store_true',
                       help='Force update all data regardless of freshness')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check health, do not update')
    parser.add_argument('--live', action='store_true',
                       help='Validate for live trading (requires 48h paper trading)')
    
    args = parser.parse_args()
    
    if args.check_only:
        # Just check, don't update
        health = validate_system_health()
        
        # Exit with appropriate code
        sys.exit(0 if health['all_ok'] else 1)
    
    else:
        # Full check and update
        result = pre_trading_check(
            interactive=not args.non_interactive,
            force_update=args.force,
            for_live_trading=args.live
        )
        
        # Exit with appropriate code
        sys.exit(0 if result['ready'] else 1)
