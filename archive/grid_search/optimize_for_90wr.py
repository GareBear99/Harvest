#!/usr/bin/env python3
"""
Aggressive BASE_STRATEGY Optimizer - Target 90% WR

Systematically tightens filters to achieve 90% win rate
"""

import sys
from backtest_90_complete import MultiTimeframeBacktest
import ml.base_strategy as bs


# More aggressive parameter ranges for 90% WR target
AGGRESSIVE_RANGES = {
    'min_confidence': [0.70, 0.73, 0.76, 0.80, 0.83, 0.86, 0.90],
    'min_volume': [1.15, 1.20, 1.25, 1.30, 1.35, 1.40, 1.50],
    'min_trend': [0.55, 0.60, 0.65, 0.70, 0.75, 0.80],
    'min_adx': [25, 28, 30, 33, 35, 38, 40],
}


def test_strategy_combination(timeframe, strategy, data_file):
    """Test a strategy configuration"""
    original = bs.BASE_STRATEGY.copy()
    
    try:
        bs.BASE_STRATEGY[timeframe] = strategy.copy()
        bt = MultiTimeframeBacktest(data_file, 10.0, seed=42)
        bt.run()
        
        tf_trades = [t for t in bt.all_trades if t.get('timeframe') == timeframe]
        
        if not tf_trades:
            return 0, 0.0, 0.0
        
        wins = len([t for t in tf_trades if t['pnl'] > 0])
        wr = wins / len(tf_trades)
        pnl = sum(t['pnl'] for t in tf_trades)
        
        return len(tf_trades), wr, pnl
    finally:
        bs.BASE_STRATEGY = original


def find_90wr_strategy(timeframe, data_file, asset):
    """Find strategy that achieves ~90% WR"""
    
    print(f"\n{'='*80}")
    print(f"OPTIMIZING {asset} - {timeframe} FOR 90% WIN RATE")
    print(f"{'='*80}\n")
    
    base = bs.BASE_STRATEGY[timeframe].copy()
    best_configs = []
    
    # Test confidence levels
    for conf in AGGRESSIVE_RANGES['min_confidence']:
        test_strat = base.copy()
        test_strat['min_confidence'] = conf
        
        trades, wr, pnl = test_strategy_combination(timeframe, test_strat, data_file)
        
        print(f"min_confidence={conf:.2f} → Trades: {trades:2d} | WR: {wr:5.1%} | PnL: ${pnl:+6.2f}")
        
        if trades > 0:
            best_configs.append({
                'config': test_strat.copy(),
                'trades': trades,
                'wr': wr,
                'pnl': pnl,
                'param': 'min_confidence',
                'value': conf
            })
    
    # Test volume levels with best confidence
    best_conf = sorted([c for c in best_configs if c['wr'] >= 0.70], 
                      key=lambda x: x['wr'], reverse=True)
    
    if best_conf:
        print(f"\n🔍 Testing volume with confidence={best_conf[0]['value']:.2f}")
        base_with_conf = best_conf[0]['config'].copy()
        
        for vol in AGGRESSIVE_RANGES['min_volume']:
            test_strat = base_with_conf.copy()
            test_strat['min_volume'] = vol
            
            trades, wr, pnl = test_strategy_combination(timeframe, test_strat, data_file)
            
            print(f"min_volume={vol:.2f} → Trades: {trades:2d} | WR: {wr:5.1%} | PnL: ${pnl:+6.2f}")
            
            if trades > 0:
                best_configs.append({
                    'config': test_strat.copy(),
                    'trades': trades,
                    'wr': wr,
                    'pnl': pnl,
                    'param': 'min_volume',
                    'value': vol
                })
    
    # Test trend with best combo
    best_combo = sorted([c for c in best_configs if c['wr'] >= 0.75], 
                       key=lambda x: x['wr'], reverse=True)
    
    if best_combo:
        print(f"\n🔍 Testing trend strength")
        base_with_combo = best_combo[0]['config'].copy()
        
        for trend in AGGRESSIVE_RANGES['min_trend']:
            test_strat = base_with_combo.copy()
            test_strat['min_trend'] = trend
            
            trades, wr, pnl = test_strategy_combination(timeframe, test_strat, data_file)
            
            print(f"min_trend={trend:.2f} → Trades: {trades:2d} | WR: {wr:5.1%} | PnL: ${pnl:+6.2f}")
            
            if trades > 0:
                best_configs.append({
                    'config': test_strat.copy(),
                    'trades': trades,
                    'wr': wr,
                    'pnl': pnl,
                    'param': 'min_trend',
                    'value': trend
                })
    
    # Test ADX with best combo
    best_so_far = sorted([c for c in best_configs if c['wr'] >= 0.80], 
                         key=lambda x: x['wr'], reverse=True)
    
    if best_so_far:
        print(f"\n🔍 Testing ADX strength")
        base_final = best_so_far[0]['config'].copy()
        
        for adx in AGGRESSIVE_RANGES['min_adx']:
            test_strat = base_final.copy()
            test_strat['min_adx'] = adx
            
            trades, wr, pnl = test_strategy_combination(timeframe, test_strat, data_file)
            
            print(f"min_adx={adx:.0f} → Trades: {trades:2d} | WR: {wr:5.1%} | PnL: ${pnl:+6.2f}")
            
            if trades > 0:
                best_configs.append({
                    'config': test_strat.copy(),
                    'trades': trades,
                    'wr': wr,
                    'pnl': pnl,
                    'param': 'min_adx',
                    'value': adx
                })
    
    # Find best configuration
    valid_configs = [c for c in best_configs if c['trades'] >= 3]  # Need at least 3 trades
    
    if not valid_configs:
        print(f"\n❌ Could not find configuration with 3+ trades")
        return None
    
    # Sort by WR, then PnL
    valid_configs.sort(key=lambda x: (x['wr'], x['pnl']), reverse=True)
    
    best = valid_configs[0]
    
    print(f"\n{'='*80}")
    print(f"🏆 BEST CONFIGURATION FOR {asset} {timeframe}")
    print(f"{'='*80}")
    print(f"Win Rate: {best['wr']:.1%}")
    print(f"Trades: {best['trades']}")
    print(f"PnL: ${best['pnl']:+.2f}")
    print(f"\nStrategy:")
    for key, val in best['config'].items():
        print(f"  {key:20s}: {val}")
    
    return best


def main():
    print("\n" + "="*80)
    print("🎯 AGGRESSIVE OPTIMIZATION FOR 90% WIN RATE")
    print("="*80)
    
    results = {}
    
    # Optimize ETH
    for timeframe in ['15m', '1h', '4h']:
        result = find_90wr_strategy(timeframe, 'data/eth_21days.json', 'ETH')
        if result:
            results[f'ETH_{timeframe}'] = result
    
    # Optimize BTC
    for timeframe in ['15m', '1h', '4h']:
        result = find_90wr_strategy(timeframe, 'data/btc_21days.json', 'BTC')
        if result:
            results[f'BTC_{timeframe}'] = result
    
    # Summary
    print("\n" + "="*80)
    print("📊 OPTIMIZATION SUMMARY")
    print("="*80)
    
    for key, result in results.items():
        asset, tf = key.split('_')
        wr_icon = "✅" if result['wr'] >= 0.90 else "⚠️" if result['wr'] >= 0.75 else "❌"
        print(f"\n{wr_icon} {asset} {tf}: {result['wr']:.1%} WR ({result['trades']} trades, ${result['pnl']:+.2f} PnL)")
    
    # Check if we hit 90% on any
    winners = [k for k, v in results.items() if v['wr'] >= 0.90]
    
    if winners:
        print(f"\n🎉 ACHIEVED 90%+ WR ON: {', '.join(winners)}")
    else:
        best_wr = max(results.values(), key=lambda x: x['wr'])
        print(f"\n📈 Best WR achieved: {best_wr['wr']:.1%}")
        print(f"   Target 90% requires even tighter filters or more selective signals")
    
    # Generate proposed BASE_STRATEGY
    print("\n" + "="*80)
    print("💡 PROPOSED BASE_STRATEGY (Copy to ml/base_strategy.py)")
    print("="*80)
    
    print("\nBASE_STRATEGY = {")
    for timeframe in ['15m', '1h', '4h']:
        # Find best config for this timeframe (average ETH/BTC)
        eth_key = f'ETH_{timeframe}'
        btc_key = f'BTC_{timeframe}'
        
        if eth_key in results and btc_key in results:
            eth_conf = results[eth_key]['config']
            btc_conf = results[btc_key]['config']
            
            # Use stricter of the two for safety
            merged = {}
            for key in eth_conf.keys():
                if key in ['atr_min', 'atr_max', 'min_roc']:
                    merged[key] = eth_conf[key]  # Keep original
                else:
                    # Use higher (stricter) value
                    merged[key] = max(eth_conf[key], btc_conf[key])
            
            print(f"    '{timeframe}': {{")
            for k, v in merged.items():
                print(f"        '{k}': {v},")
            print(f"    }},")
    
    print("}")


if __name__ == "__main__":
    main()
