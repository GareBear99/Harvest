#!/usr/bin/env python3
"""
Complete Optimization Pipeline

1. Verify data with blockchain verifier
2. Run comprehensive audit
3. Execute exhaustive grid search (121,500 combinations)
4. Analyze and report optimal strategies

This is the end-to-end pipeline for finding 90% WR strategies.
"""

import subprocess
import sys
import os
from datetime import datetime
import json


def run_command(cmd, description):
    """Run a command and handle output"""
    print(f"\n{'='*80}")
    print(f"🚀 {description}")
    print(f"{'='*80}\n")
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"\n❌ {description} FAILED with code {result.returncode}")
        return False
    
    print(f"\n✅ {description} COMPLETE")
    return True


def verify_data_files(asset):
    """Verify data files exist and are valid"""
    
    data_file = f"data/{asset.lower()}_90days.json"
    
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        print(f"\nRun: python download_90day_data.py")
        return False
    
    # Check file size
    size_mb = os.path.getsize(data_file) / (1024 * 1024)
    
    if size_mb < 1.0:
        print(f"❌ Data file too small: {size_mb:.1f} MB")
        print(f"   Expected: ~19-20 MB for 90 days of 1-minute data")
        return False
    
    print(f"✅ Data file found: {data_file} ({size_mb:.1f} MB)")
    return True


def run_blockchain_verification(asset):
    """Run blockchain verification and auto-correction"""
    
    symbol = f"{asset}USDT"
    data_file = f"data/{asset.lower()}_90days.json"
    
    cmd = ['python', 'blockchain_verifier.py', data_file, symbol]
    
    return run_command(cmd, f"Blockchain Verification ({symbol})")


def run_comprehensive_audit():
    """Run comprehensive audit on all data"""
    
    cmd = ['python', 'audit_blockchain_data.py']
    
    return run_command(cmd, "Comprehensive Data Audit")


def run_grid_search(asset, timeframe, output_dir='grid_search_results'):
    """Run exhaustive grid search"""
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"{output_dir}/{asset.lower()}_{timeframe}_{timestamp}.csv"
    
    cmd = [
        'python', 'grid_search_all_strategies.py',
        '--asset', asset,
        '--timeframe', timeframe,
        '--output', output_file
    ]
    
    success = run_command(cmd, f"Grid Search ({asset} {timeframe})")
    
    if success:
        print(f"\n📊 Results saved to: {output_file}")
        
        # Check results
        if os.path.exists(output_file):
            line_count = sum(1 for _ in open(output_file)) - 1  # Subtract header
            print(f"   Tested: {line_count:,} strategies")
            
            # Check for summary
            summary_file = output_file.replace('.csv', '_summary.json')
            if os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
                
                print(f"\n🏆 BEST STRATEGIES:")
                
                if 'best_wr' in summary:
                    best = summary['best_wr']
                    print(f"\n   Highest Win Rate:")
                    print(f"      WR: {best.get('win_rate', 0)*100:.1f}%")
                    print(f"      Trades: {best.get('trades', 0)}")
                    print(f"      PnL: ${best.get('total_pnl', 0):+.2f}")
                    print(f"      Confidence: {best.get('min_confidence', 0):.2f}")
                    print(f"      Volume: {best.get('min_volume', 0):.2f}")
                    print(f"      Trend: {best.get('min_trend', 0):.2f}")
                    print(f"      ADX: {best.get('min_adx', 0)}")
                
                if 'best_pnl' in summary:
                    best = summary['best_pnl']
                    print(f"\n   Highest Profit:")
                    print(f"      PnL: ${best.get('total_pnl', 0):+.2f}")
                    print(f"      WR: {best.get('win_rate', 0)*100:.1f}%")
                    print(f"      Trades: {best.get('trades', 0)}")
    
    return success


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Complete optimization pipeline")
    parser.add_argument('--asset', '-a', choices=['ETH', 'BTC'], required=True,
                       help='Asset to optimize')
    parser.add_argument('--timeframe', '-t', choices=['15m', '1h', '4h'], required=True,
                       help='Timeframe to optimize')
    parser.add_argument('--skip-verification', action='store_true',
                       help='Skip blockchain verification (use if already verified)')
    parser.add_argument('--skip-audit', action='store_true',
                       help='Skip comprehensive audit (use if already audited)')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🎯 COMPLETE OPTIMIZATION PIPELINE")
    print("="*80)
    print(f"\nAsset: {args.asset}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Target: 90%+ Win Rate Strategy")
    print(f"\nPipeline Steps:")
    if not args.skip_verification:
        print("  1. ✓ Blockchain Verification & Auto-Correction")
    else:
        print("  1. ⊘ Blockchain Verification (SKIPPED)")
    
    if not args.skip_audit:
        print("  2. ✓ Comprehensive Data Audit")
    else:
        print("  2. ⊘ Comprehensive Data Audit (SKIPPED)")
    
    print("  3. ✓ Exhaustive Grid Search (121,500 combinations)")
    print("  4. ✓ Results Analysis & Optimization")
    
    # Step 0: Verify data files exist
    print(f"\n{'='*80}")
    print(f"📁 VERIFYING DATA FILES")
    print(f"{'='*80}\n")
    
    if not verify_data_files(args.asset):
        print("\n❌ Data files not ready. Please run data download first.")
        sys.exit(1)
    
    # Step 1: Blockchain Verification (unless skipped)
    if not args.skip_verification:
        if not run_blockchain_verification(args.asset):
            print("\n❌ Blockchain verification failed")
            response = input("\nContinue anyway? (y/n): ")
            if response.lower() != 'y':
                sys.exit(1)
    else:
        print(f"\n⊘ Skipping blockchain verification (--skip-verification)")
    
    # Step 2: Comprehensive Audit (unless skipped)
    if not args.skip_audit:
        if not run_comprehensive_audit():
            print("\n❌ Audit failed")
            response = input("\nContinue anyway? (y/n): ")
            if response.lower() != 'y':
                sys.exit(1)
    else:
        print(f"\n⊘ Skipping comprehensive audit (--skip-audit)")
    
    # Step 3: Grid Search
    if not run_grid_search(args.asset, args.timeframe):
        print("\n❌ Grid search failed")
        sys.exit(1)
    
    # Step 4: Summary
    print(f"\n{'='*80}")
    print(f"✅ OPTIMIZATION COMPLETE")
    print(f"{'='*80}\n")
    
    print(f"Results Location: grid_search_results/")
    print(f"\nNext Steps:")
    print(f"1. Review CSV results in Excel/Numbers")
    print(f"2. Identify strategies with 90%+ win rate and 10+ trades")
    print(f"3. Update BASE_STRATEGY in ml/base_strategy.py")
    print(f"4. Run validation backtest")
    print(f"5. Deploy to live trading")
    
    print(f"\n{'='*80}")
    print(f"🎯 Ready for 90% WR Trading!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
