#!/usr/bin/env python3
"""
Automated Timeframe Optimization
Runs backtests, tests seeds, and deploys best strategies for all timeframes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dashboard.timeout_manager import (
    TimeoutManager, 
    execute_backtest_with_progress,
    execute_seed_test_with_progress,
    show_error_menu,
    wait_for_user_acknowledgment
)
import subprocess


def run_initial_backtests(num_seeds: int = 5):
    """
    Run initial backtests to populate seed registry
    
    Args:
        num_seeds: Number of different seeds to test
    """
    print("\n" + "="*80)
    print("STEP 1: GENERATE SEED DATA")
    print("="*80)
    print(f"\nRunning {num_seeds} backtests with different seeds to populate registry...")
    print("This helps build a library of proven strategies.\n")
    
    manager = TimeoutManager()
    successful = 0
    
    for i in range(1, num_seeds + 1):
        seed = i * 111  # Use spaced seeds
        print(f"\n[{i}/{num_seeds}] Backtest with seed {seed}")
        print("-" * 60)
        
        result = execute_backtest_with_progress(seed=seed, timeout=600)
        
        if result['status'] == 'success':
            successful += 1
            print(f"✅ Completed {i}/{num_seeds}")
        elif result['status'] == 'timeout':
            choice = show_error_menu('timeout', result['error'])
            if choice == 'retry':
                print("\n🔄 Retrying with extended timeout...")
                result = execute_backtest_with_progress(seed=seed, timeout=1200)
                if result['status'] == 'success':
                    successful += 1
            elif choice == 'main':
                break
        else:
            print(f"⚠️  Failed: {result['error']}")
            choice = input("\nContinue with remaining tests? (y/n): ").strip().lower()
            if choice != 'y':
                break
    
    print(f"\n✅ Completed {successful}/{num_seeds} backtests successfully")
    wait_for_user_acknowledgment()
    return successful


def test_timeframe_seeds(timeframe: str):
    """
    Test top 10 seeds for a timeframe
    
    Args:
        timeframe: Timeframe to test
    """
    print(f"\n" + "="*80)
    print(f"TESTING TOP 10 SEEDS FOR {timeframe}")
    print("="*80)
    
    result = execute_seed_test_with_progress(
        timeframe=timeframe,
        test_type='top10',
        timeout=900  # 15 minutes
    )
    
    if result['status'] == 'success':
        print(f"\n✅ Seed testing completed for {timeframe}")
        return True
    elif result['status'] == 'timeout':
        choice = show_error_menu('timeout', result['error'])
        if choice == 'retry':
            print("\n🔄 Retrying with extended timeout (30 minutes)...")
            result = execute_seed_test_with_progress(
                timeframe=timeframe,
                test_type='top10',
                timeout=1800
            )
            return result['status'] == 'success'
        return False
    else:
        print(f"\n❌ Failed to test {timeframe} seeds")
        return False


def deploy_best_strategy(timeframe: str):
    """
    Deploy best seed to BASE_STRATEGY for timeframe
    
    Args:
        timeframe: Timeframe to optimize
    """
    print(f"\n🚀 Deploying best seed for {timeframe}...")
    
    manager = TimeoutManager()
    cmd = f"python ml/seed_tester.py overwrite {timeframe} --use-best"
    
    # This command needs user confirmation, so run it interactively
    try:
        subprocess.run(cmd, shell=True, check=False)
        return True
    except Exception as e:
        print(f"❌ Failed to deploy: {e}")
        return False


def show_final_status():
    """Show final configuration status"""
    print("\n" + "="*80)
    print("FINAL CONFIGURATION")
    print("="*80)
    
    manager = TimeoutManager()
    result = manager.execute_with_timeout("python ml/seed_tester.py status", timeout=30)
    
    if result['status'] == 'success':
        print(result['output'])
    else:
        print("❌ Failed to get status")


def main():
    """Main optimization workflow"""
    print("\n" + "="*80)
    print("🎯 AUTOMATED TIMEFRAME OPTIMIZATION")
    print("="*80)
    print("\nThis script will:")
    print("  1. Run initial backtests to generate seed data")
    print("  2. Test top 10 seeds for each timeframe")
    print("  3. Deploy best strategies to BASE_STRATEGY")
    print("  4. Show final configuration")
    print("\nEstimated time: 1-2 hours")
    print("="*80)
    
    response = input("\nContinue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("\n❌ Operation cancelled")
        return
    
    # Step 1: Generate seed data
    successful = run_initial_backtests(num_seeds=5)
    
    if successful < 3:
        print("\n⚠️  Not enough successful backtests to continue")
        print("   Please check system errors and try again")
        wait_for_user_acknowledgment()
        return
    
    # Step 2: Test seeds for each timeframe
    timeframes = ['1m', '5m', '15m', '1h', '4h']
    tested_timeframes = []
    
    for tf in timeframes:
        print(f"\n" + "="*80)
        print(f"STEP 2.{timeframes.index(tf) + 1}: TEST {tf.upper()} TIMEFRAME")
        print("="*80)
        
        response = input(f"\nTest {tf} timeframe? (y/n): ").strip().lower()
        if response != 'y':
            print(f"⏭️  Skipping {tf}")
            continue
        
        if test_timeframe_seeds(tf):
            tested_timeframes.append(tf)
            wait_for_user_acknowledgment()
        else:
            print(f"\n⚠️  Failed to test {tf}, continuing with next timeframe...")
            wait_for_user_acknowledgment()
    
    # Step 3: Deploy best strategies
    print("\n" + "="*80)
    print("STEP 3: DEPLOY BEST STRATEGIES")
    print("="*80)
    print(f"\nReady to deploy optimized strategies for:")
    for tf in tested_timeframes:
        print(f"  • {tf}")
    
    if not tested_timeframes:
        print("\n❌ No timeframes were successfully tested")
        wait_for_user_acknowledgment()
        return
    
    response = input("\nDeploy all? (yes/no): ").strip().lower()
    if response != 'yes':
        print("\n❌ Deployment cancelled")
        wait_for_user_acknowledgment()
        return
    
    deployed = []
    for tf in tested_timeframes:
        print(f"\n{'='*60}")
        if deploy_best_strategy(tf):
            deployed.append(tf)
            print(f"✅ Deployed {tf}")
        else:
            print(f"❌ Failed to deploy {tf}")
        print()
    
    # Step 4: Show final status
    print("\n" + "="*80)
    print("OPTIMIZATION COMPLETE")
    print("="*80)
    print(f"\n✅ Successfully optimized {len(deployed)} timeframes:")
    for tf in deployed:
        print(f"  • {tf}")
    
    print("\n📊 Final Configuration:")
    show_final_status()
    
    print("\n" + "="*80)
    print("🎉 ALL DONE!")
    print("="*80)
    print("\nNext steps:")
    print("  1. Review the configuration above")
    print("  2. Run a final backtest: python backtest_90_complete.py")
    print("  3. Launch dashboard: python dashboard/terminal_ui.py")
    print("="*80)
    
    wait_for_user_acknowledgment()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        wait_for_user_acknowledgment()
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        wait_for_user_acknowledgment()
        raise
