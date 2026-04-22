#!/usr/bin/env python3
"""
Realistic BASE_STRATEGY Optimization

Finds the best achievable win rate given the current dataset
"""

import sys
from backtest_90_complete import MultiTimeframeBacktest
import ml.base_strategy as bs


def test_config(timeframe, conf, vol, trend, adx, data_file):
    """Quick test of a config"""
    original = bs.BASE_STRATEGY.copy()
    
    try:
        test_strat = bs.BASE_STRATEGY[timeframe].copy()
        test_strat['min_confidence'] = conf
        test_strat['min_volume'] = vol
        test_strat['min_trend'] = trend
        test_strat['min_adx'] = adx
        
        bs.BASE_STRATEGY[timeframe] = test_strat
        
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


def find_best_config_for_asset(asset, data_file):
    """Find best config for an asset"""
    
    print(f"\n{'='*80}")
    print(f"OPTIMIZING {asset} - BEST ACHIEVABLE WR")
    print(f"{'='*80}\n")
    
    # Test combinations
    configs = []
    
    for tf in ['15m', '1h', '4h']:
        print(f"\n{tf} Timeframe:")
        print(f"{'-'*40}")
        
        best_for_tf = None
        best_wr = 0
        
        # Test key combinations
        for conf in [0.70, 0.76, 0.80, 0.86]:
            for vol in [1.15, 1.25, 1.35]:
                for trend in [0.55, 0.65, 0.75]:
                    for adx in [25, 30, 35]:
                        trades, wr, pnl = test_config(tf, conf, vol, trend, adx, data_file)
                        
                        if trades >= 3 and wr > best_wr:
                            best_wr = wr
                            best_for_tf = {
                                'timeframe': tf,
                                'trades': trades,
                                'wr': wr,
                                'pnl': pnl,
                                'min_confidence': conf,
                                'min_volume': vol,
                                'min_trend': trend,
                                'min_adx': adx
                            }
                            
                            print(f"  conf={conf:.2f} vol={vol:.2f} trend={trend:.2f} adx={adx} → "
                                  f"{trades} trades, {wr:.1%} WR, ${pnl:+.2f} PnL")
        
        if best_for_tf:
            configs.append(best_for_tf)
            print(f"\n  🏆 Best {tf}: {best_for_tf['wr']:.1%} WR ({best_for_tf['trades']} trades)")
    
    return configs


def main():
    print("\n" + "="*80)
    print("🎯 REALISTIC BASE_STRATEGY OPTIMIZATION")
    print("="*80)
    print("\nFinding best achievable win rates with current data...")
    
    eth_configs = find_best_config_for_asset('ETH', 'data/eth_21days.json')
    btc_configs = find_best_config_for_asset('BTC', 'data/btc_21days.json')
    
    # Summary
    print("\n" + "="*80)
    print("📊 OPTIMIZATION RESULTS")
    print("="*80)
    
    print("\n🔹 ETH:")
    for cfg in eth_configs:
        print(f"  {cfg['timeframe']}: {cfg['wr']:.1%} WR ({cfg['trades']} trades, ${cfg['pnl']:+.2f} PnL)")
        print(f"    conf={cfg['min_confidence']:.2f}, vol={cfg['min_volume']:.2f}, "
              f"trend={cfg['min_trend']:.2f}, adx={cfg['min_adx']}")
    
    print("\n🔹 BTC:")
    for cfg in btc_configs:
        print(f"  {cfg['timeframe']}: {cfg['wr']:.1%} WR ({cfg['trades']} trades, ${cfg['pnl']:+.2f} PnL)")
        print(f"    conf={cfg['min_confidence']:.2f}, vol={cfg['min_volume']:.2f}, "
              f"trend={cfg['min_trend']:.2f}, adx={cfg['min_adx']}")
    
    # Generate BASE_STRATEGY
    print("\n" + "="*80)
    print("💡 OPTIMIZED BASE_STRATEGY")
    print("="*80)
    
    print("\nBASE_STRATEGY = {")
    for tf in ['15m', '1h', '4h']:
        eth_cfg = next((c for c in eth_configs if c['timeframe'] == tf), None)
        btc_cfg = next((c for c in btc_configs if c['timeframe'] == tf), None)
        
        if eth_cfg and btc_cfg:
            # Use stricter of the two
            print(f"    '{tf}': {{")
            print(f"        'min_confidence': {max(eth_cfg['min_confidence'], btc_cfg['min_confidence'])},")
            print(f"        'min_volume': {max(eth_cfg['min_volume'], btc_cfg['min_volume'])},")
            print(f"        'min_trend': {max(eth_cfg['min_trend'], btc_cfg['min_trend'])},")
            print(f"        'min_adx': {max(eth_cfg['min_adx'], btc_cfg['min_adx'])},")
            print(f"        'min_roc': -1.0,")
            print(f"        'atr_min': 0.4,")
            print(f"        'atr_max': 3.5")
            print(f"    }},")
    
    print("}")
    
    # Overall stats
    eth_avg_wr = sum(c['wr'] for c in eth_configs) / len(eth_configs) if eth_configs else 0
    btc_avg_wr = sum(c['wr'] for c in btc_configs) / len(btc_configs) if btc_configs else 0
    
    print(f"\n📈 Average Win Rates:")
    print(f"  ETH: {eth_avg_wr:.1%}")
    print(f"  BTC: {btc_avg_wr:.1%}")
    print(f"  Combined: {(eth_avg_wr + btc_avg_wr) / 2:.1%}")


if __name__ == "__main__":
    main()
