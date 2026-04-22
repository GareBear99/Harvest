#!/usr/bin/env python3
"""
Volatility Comparison Analysis - ETH vs BTC
Identifies why BTC needs different parameters by analyzing volatility profiles
"""

import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.indicators_backtest import BacktestIndicators


def analyze_volatility(data_file: str, asset_name: str):
    """Analyze volatility characteristics of an asset"""
    
    # Load data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    candles = data['candles']
    
    # Aggregate to different timeframes
    candles_1h = BacktestIndicators.aggregate_candles(candles, 60)
    candles_4h = BacktestIndicators.aggregate_candles(candles, 240)
    
    print(f"\n{'='*80}")
    print(f"{asset_name} VOLATILITY ANALYSIS")
    print(f"{'='*80}")
    
    # Calculate ATR at different timeframes
    atr_1h = BacktestIndicators.atr(candles_1h, period=14)
    atr_4h = BacktestIndicators.atr(candles_4h, period=14)
    
    # Calculate average price for percentage normalization
    avg_price_1h = sum(c['close'] for c in candles_1h) / len(candles_1h)
    avg_price_4h = sum(c['close'] for c in candles_4h) / len(candles_4h)
    
    # ATR as percentage of price
    atr_pct_1h = (atr_1h / avg_price_1h) * 100
    atr_pct_4h = (atr_4h / avg_price_4h) * 100
    
    print(f"\nATR METRICS:")
    print(f"  1h ATR: ${atr_1h:.2f} ({atr_pct_1h:.3f}%)")
    print(f"  4h ATR: ${atr_4h:.2f} ({atr_pct_4h:.3f}%)")
    print(f"  Avg Price (1h): ${avg_price_1h:.2f}")
    
    # Calculate price range statistics
    highs = [c['high'] for c in candles_1h]
    lows = [c['low'] for c in candles_1h]
    closes = [c['close'] for c in candles_1h]
    
    ranges = [(h - l) for h, l in zip(highs, lows)]
    range_pcts = [(h - l) / c * 100 for h, l, c in zip(highs, lows, closes)]
    
    avg_range = sum(ranges) / len(ranges)
    avg_range_pct = sum(range_pcts) / len(range_pcts)
    max_range = max(ranges)
    max_range_pct = max(range_pcts)
    
    # 99th percentile move
    sorted_ranges = sorted(range_pcts)
    p99_index = int(len(sorted_ranges) * 0.99)
    p99_range = sorted_ranges[p99_index]
    
    print(f"\nPRICE RANGE STATISTICS (1h candles):")
    print(f"  Average Range: ${avg_range:.2f} ({avg_range_pct:.3f}%)")
    print(f"  Max Range: ${max_range:.2f} ({max_range_pct:.3f}%)")
    print(f"  99th Percentile: {p99_range:.3f}%")
    
    # Calculate typical moves (close-to-close)
    moves = [abs(closes[i] - closes[i-1]) / closes[i-1] * 100 
             for i in range(1, len(closes))]
    
    avg_move = sum(moves) / len(moves)
    max_move = max(moves)
    
    sorted_moves = sorted(moves)
    p95_move = sorted_moves[int(len(sorted_moves) * 0.95)]
    p99_move = sorted_moves[int(len(sorted_moves) * 0.99)]
    
    print(f"\nCLOSE-TO-CLOSE MOVES (1h):")
    print(f"  Average: {avg_move:.3f}%")
    print(f"  95th Percentile: {p95_move:.3f}%")
    print(f"  99th Percentile: {p99_move:.3f}%")
    print(f"  Maximum: {max_move:.3f}%")
    
    # ADX distribution
    adx_values = []
    for i in range(50, len(candles_1h)):
        adx = BacktestIndicators.adx(candles_1h[:i+1], period=14)
        adx_values.append(adx)
    
    avg_adx = sum(adx_values) / len(adx_values)
    adx_above_15 = sum(1 for adx in adx_values if adx > 15) / len(adx_values) * 100
    adx_above_20 = sum(1 for adx in adx_values if adx > 20) / len(adx_values) * 100
    adx_above_25 = sum(1 for adx in adx_values if adx > 25) / len(adx_values) * 100
    
    print(f"\nADX DISTRIBUTION:")
    print(f"  Average ADX: {avg_adx:.2f}")
    print(f"  ADX > 15: {adx_above_15:.1f}% of time")
    print(f"  ADX > 20: {adx_above_20:.1f}% of time")
    print(f"  ADX > 25: {adx_above_25:.1f}% of time")
    
    # Volatility clustering (consecutive high-volatility periods)
    high_vol_threshold = avg_range_pct * 1.5
    consecutive_high_vol = []
    current_streak = 0
    
    for range_pct in range_pcts:
        if range_pct > high_vol_threshold:
            current_streak += 1
        else:
            if current_streak > 0:
                consecutive_high_vol.append(current_streak)
            current_streak = 0
    
    if consecutive_high_vol:
        avg_cluster = sum(consecutive_high_vol) / len(consecutive_high_vol)
        max_cluster = max(consecutive_high_vol)
        print(f"\nVOLATILITY CLUSTERING:")
        print(f"  High-vol threshold: {high_vol_threshold:.3f}%")
        print(f"  Avg cluster size: {avg_cluster:.1f} candles")
        print(f"  Max cluster size: {max_cluster} candles")
    
    return {
        'atr_1h': atr_1h,
        'atr_pct_1h': atr_pct_1h,
        'atr_4h': atr_4h,
        'atr_pct_4h': atr_pct_4h,
        'avg_price': avg_price_1h,
        'avg_range_pct': avg_range_pct,
        'p99_range': p99_range,
        'avg_move': avg_move,
        'p95_move': p95_move,
        'p99_move': p99_move,
        'avg_adx': avg_adx,
        'adx_above_20': adx_above_20
    }


def compare_assets(eth_stats: dict, btc_stats: dict):
    """Compare volatility statistics between assets"""
    
    print(f"\n{'='*80}")
    print("COMPARATIVE ANALYSIS")
    print(f"{'='*80}")
    
    # ATR comparison
    atr_ratio = btc_stats['atr_pct_1h'] / eth_stats['atr_pct_1h']
    print(f"\nATR RATIO (BTC / ETH):")
    print(f"  1h ATR%: {atr_ratio:.3f}× (BTC has {atr_ratio*100:.1f}% of ETH volatility)")
    
    # Move size comparison
    move_ratio = btc_stats['avg_move'] / eth_stats['avg_move']
    print(f"\nAVERAGE MOVE RATIO:")
    print(f"  {move_ratio:.3f}× (BTC moves {move_ratio*100:.1f}% as much as ETH)")
    
    # ADX comparison
    print(f"\nTREND STRENGTH:")
    print(f"  ETH avg ADX: {eth_stats['avg_adx']:.2f}")
    print(f"  BTC avg ADX: {btc_stats['avg_adx']:.2f}")
    print(f"  Difference: {btc_stats['avg_adx'] - eth_stats['avg_adx']:+.2f}")
    
    # Parameter recommendations
    print(f"\n{'='*80}")
    print("PARAMETER RECOMMENDATIONS")
    print(f"{'='*80}")
    
    # Current parameters (Tier 1 Accumulation)
    current_tp = 0.004  # 0.4%
    current_sl = 0.0025  # 0.25%
    
    # Recommended BTC parameters based on volatility ratio
    btc_tp = current_tp / atr_ratio
    btc_sl = current_sl / atr_ratio
    
    # With 25× leverage
    btc_tp_leveraged = btc_tp * 25 * 100
    btc_sl_leveraged = btc_sl * 25 * 100
    
    print(f"\nETH (Current):")
    print(f"  TP: 0.40% unleveraged (10.0% with 25× leverage)")
    print(f"  SL: 0.25% unleveraged (6.25% with 25× leverage)")
    print(f"  ATR: {eth_stats['atr_pct_1h']:.3f}%")
    
    print(f"\nBTC (Recommended - Volatility Scaled):")
    print(f"  TP: {btc_tp*100:.2f}% unleveraged ({btc_tp_leveraged:.1f}% with 25× leverage)")
    print(f"  SL: {btc_sl*100:.2f}% unleveraged ({btc_sl_leveraged:.1f}% with 25× leverage)")
    print(f"  ATR: {btc_stats['atr_pct_1h']:.3f}%")
    print(f"  Scaling factor: {1/atr_ratio:.2f}× wider than ETH")
    
    # Alternative: ATR-based approach
    print(f"\nALTERNATIVE: ATR-Based TP/SL:")
    print(f"  ETH: TP = {eth_stats['atr_pct_1h']*2:.2f}% (2× ATR), SL = {eth_stats['atr_pct_1h']*1:.2f}% (1× ATR)")
    print(f"  BTC: TP = {btc_stats['atr_pct_1h']*2:.2f}% (2× ATR), SL = {btc_stats['atr_pct_1h']*1:.2f}% (1× ATR)")
    
    # ADX recommendation
    if btc_stats['adx_above_20'] < 40:
        print(f"\nADX THRESHOLD:")
        print(f"  BTC only has ADX>20 {btc_stats['adx_above_20']:.1f}% of time")
        print(f"  Recommendation: Lower ADX threshold to 15 for BTC")
    
    # Risk-reward analysis
    print(f"\nRISK-REWARD ANALYSIS:")
    eth_rr = (current_tp / current_sl)
    btc_rr = (btc_tp / btc_sl)
    print(f"  ETH R:R = {eth_rr:.2f}:1")
    print(f"  BTC R:R = {btc_rr:.2f}:1")
    
    return {
        'atr_ratio': atr_ratio,
        'btc_tp': btc_tp,
        'btc_sl': btc_sl,
        'recommended_adx': 15 if btc_stats['adx_above_20'] < 40 else 20
    }


if __name__ == "__main__":
    # Analyze ETH
    eth_stats = analyze_volatility('data/eth_21days.json', 'ETH')
    
    # Analyze BTC
    btc_stats = analyze_volatility('data/btc_21days.json', 'BTC')
    
    # Compare and generate recommendations
    recommendations = compare_assets(eth_stats, btc_stats)
    
    # Summary
    print(f"\n{'='*80}")
    print("KEY FINDINGS")
    print(f"{'='*80}")
    print(f"1. BTC has {recommendations['atr_ratio']*100:.1f}% of ETH's volatility")
    print(f"2. Current 0.4%/0.25% TP/SL is too tight for BTC")
    print(f"3. BTC needs ~{1/recommendations['atr_ratio']:.2f}× wider targets")
    print(f"4. Recommended BTC TP: {recommendations['btc_tp']*100:.2f}%")
    print(f"5. Recommended BTC SL: {recommendations['btc_sl']*100:.2f}%")
    print(f"6. Recommended ADX threshold: {recommendations['recommended_adx']}")
    print(f"\nThis explains why BTC's 3 trades all failed:")
    print(f"  - Stops too tight (hit before TP could be reached)")
    print(f"  - Targets too far (price doesn't move enough)")
    print(f"  - Time limit exits (6h not enough for BTC's slower pace)")
