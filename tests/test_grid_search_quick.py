#!/usr/bin/env python3
"""
Quick Test of Optimized Grid Search
Tests with a small subset to verify functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Temporarily reduce parameter grid for testing
import grid_search_ultra as gs

# Override with smaller grid for quick test
gs.PARAMETER_GRID = {
    'min_confidence': [0.70, 0.80, 0.90],  # 3 values
    'min_volume': [1.00, 1.20, 1.40],      # 3 values  
    'min_trend': [0.50, 0.60, 0.70],       # 3 values
    'min_adx': [25, 30, 35],               # 3 values
    'atr_min': [0.3, 0.4],                 # 2 values
    'atr_max': [3.5, 4.5]                  # 2 values
}

# Total: 3 * 3 * 3 * 3 * 2 * 2 = 324 combinations

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 QUICK TEST - Optimized Grid Search")
    print("="*80)
    print("\nTesting with reduced parameter grid: 324 combinations")
    print("This should complete in under 2 minutes\n")
    
    # Run with test parameters
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset', '-a', default='BTCUSDT', help='Asset (default: BTCUSDT)')
    parser.add_argument('--timeframe', '-t', default='1m', help='Timeframe (default: 1m)')
    
    args = parser.parse_args()
    
    # Check if data exists
    data_file = f"data/{args.asset}_1m_90d.json"
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        print(f"\nTo test, you need data first. Run:")
        print(f"  python parallel_downloader.py")
        sys.exit(1)
    
    # Create output directory
    os.makedirs('grid_search_results', exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"grid_search_results/{args.asset}_{args.timeframe}_quicktest_{timestamp}.csv"
    
    print(f"Asset: {args.asset}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Data: {data_file}")
    print(f"Output: {output_file}\n")
    
    # Run search (ultra version has progress bar)
    print("\n⚡ Running ultra-optimized search with progress bar...\n")
    results = gs.run_ultra_search(args.timeframe, data_file, args.asset, output_file)
    
    # Analyze
    best_configs = gs.analyze_results(results)
    
    if best_configs:
        summary_file = output_file.replace('.csv', '_summary.json')
        import json
        with open(summary_file, 'w') as f:
            json.dump(best_configs, f, indent=2)
        print(f"\n💾 Best configurations saved to: {summary_file}")
    
    print(f"\n{'='*80}")
    print("✅ QUICK TEST COMPLETE")
    print(f"{'='*80}")
    print(f"\nResults: {output_file}")
    print("\nIf this worked, the full 121,500 combination search should work similarly!")
