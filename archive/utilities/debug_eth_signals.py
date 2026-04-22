"""Debug script to understand signal generation."""
import sys
sys.path.insert(0, '.')

from backtester import Backtester
from core.indicators import Indicators

print("="*80)
print("DEBUGGING ETH SIGNAL GENERATION")
print("="*80)

bt = Backtester(symbol='ETHUSDT', initial_equity=10000.0)
data = bt.fetch_data(days=30)

if not data:
    print("Failed to fetch data")
    sys.exit(1)

candles_5m = data['5m']
candles_1h = data['1h']

print(f"\nData available:")
print(f"  5m: {len(candles_5m)} candles")
print(f"  1h: {len(candles_1h)} candles")

# Check a few sample points for ER-90 conditions
print(f"\n" + "="*80)
print("Checking ER-90 conditions at random points:")
print("="*80)

import random
sample_indices = random.sample(range(100, len(candles_1h)-10), 5)

for idx in sample_indices:
    current_1h = candles_1h[:idx+1]
    current_5m = [c for c in candles_5m if c.timestamp <= current_1h[-1].timestamp]
    
    if len(current_5m) < 50:
        continue
    
    closes_5m = [c.close for c in current_5m]
    closes_1h = [c.close for c in current_1h]
    
    rsi_5m = Indicators.rsi(closes_5m, 5)
    rsi_1h = Indicators.rsi(closes_1h, 5)
    atr = Indicators.atr(current_1h, 14)
    impulse = Indicators.price_impulse(current_5m, lookback_hours=2, candle_interval_minutes=5)
    
    volume_avg = Indicators.volume_average(current_5m, period=20)
    current_volume = current_5m[-1].volume
    prev_volume = current_5m[-2].volume if len(current_5m) > 1 else current_volume
    
    volume_spiked = prev_volume > volume_avg * 1.2
    volume_declining = current_volume < prev_volume * 0.85
    
    print(f"\nTimestamp: {current_1h[-1].timestamp}")
    print(f"  RSI(5m): {rsi_5m:.1f} | RSI(1h): {rsi_1h:.1f}")
    print(f"  Impulse: {impulse:.2f} | ATR: {atr:.2f} | Ratio: {impulse/atr:.2f}")
    print(f"  Volume spike: {volume_spiked} | Volume decline: {volume_declining}")
    print(f"  Price: ${current_1h[-1].close:.2f}")
    
    # Check if close to triggering
    if rsi_5m > 70 or rsi_5m < 30:
        print(f"  ⚠️  RSI is getting extreme!")
    if impulse/atr > 0.8:
        print(f"  ⚠️  Impulse is significant!")

print(f"\n" + "="*80)
print("Running full backtest with signal detection...")
print("="*80)

# Temporarily add debug to ER90
bt.er90.config.er90_rsi_upper = 70  # Even more relaxed for testing
bt.er90.config.er90_rsi_lower = 30

results = bt.run_backtest(data)
print(f"\nFinal result: {results.get('total_execution_intents', 0)} signals generated")
