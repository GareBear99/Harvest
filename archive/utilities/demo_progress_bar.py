#!/usr/bin/env python3
"""
Quick Progress Bar Demo
Shows the streaming progress bar with a minimal grid search
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import grid_search_ultra as gs

# Super minimal grid for quick demo (27 combinations, ~10 seconds)
gs.PARAMETER_GRID = {
    'min_confidence': [0.70, 0.80, 0.90],  # 3
    'min_volume': [1.20, 1.40],            # 2
    'min_trend': [0.55, 0.65],             # 2
    'min_adx': [30],                       # 1
    'atr_min': [0.4],                      # 1
    'atr_max': [4.0, 4.5]                  # 2
}
# Total: 3 × 2 × 2 × 1 × 1 × 2 = 24 combinations

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🎬 PROGRESS BAR DEMO")
    print("="*80)
    print("\nTesting with minimal parameter grid: 24 combinations")
    print("This should complete in ~10 seconds and show the progress bar\n")
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset', '-a', default='BTCUSDT')
    parser.add_argument('--timeframe', '-t', default='1m')
    args = parser.parse_args()
    
    data_file = f"data/{args.asset}_1m_90d.json"
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        sys.exit(1)
    
    os.makedirs('grid_search_results', exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"grid_search_results/{args.asset}_{args.timeframe}_demo_{timestamp}.csv"
    
    print(f"Asset: {args.asset}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Data: {data_file}\n")
    
    print("Watch for the progress bar:")
    print("[████████░░░░] XX.X% | completed/total | XX strat/s | ETA: X.Xm\n")
    
    # Run search
    results = gs.run_ultra_search(args.timeframe, data_file, args.asset, output_file)
    
    # Quick summary
    valid = [r for r in results if r['trades'] >= 3]
    print(f"\n📊 Quick Results:")
    print(f"   Total tested: {len(results)}")
    print(f"   Valid (3+ trades): {len(valid)}")
    
    if valid:
        best = max(valid, key=lambda x: x['win_rate'] * x['total_pnl'])
        print(f"\n🏆 Best Strategy:")
        print(f"   Win Rate: {best['win_rate']:.1%}")
        print(f"   Total P&L: ${best['total_pnl']:+.2f}")
        print(f"   Trades: {best['trades']}")
    
    print(f"\n✅ Results saved to: {output_file}")
    print("\n" + "="*80)
    print("✅ DEMO COMPLETE - Progress bar worked!")
    print("="*80 + "\n")
