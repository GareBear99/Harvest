"""Synthetic test data generators for validation."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import math
from core.models import OHLCV


def generate_trending_up(start_price=100, length=100, increment=1):
    """Generate steadily increasing prices."""
    candles = []
    base_time = datetime(2024, 1, 1)
    
    for i in range(length):
        price = start_price + (i * increment)
        candle = OHLCV(
            timestamp=base_time + timedelta(hours=i),
            open=price - 0.5,
            high=price + 1,
            low=price - 1,
            close=price,
            volume=1000
        )
        candles.append(candle)
    
    return candles


def generate_trending_down(start_price=100, length=100, decrement=1):
    """Generate steadily decreasing prices."""
    candles = []
    base_time = datetime(2024, 1, 1)
    
    for i in range(length):
        price = start_price - (i * decrement)
        candle = OHLCV(
            timestamp=base_time + timedelta(hours=i),
            open=price + 0.5,
            high=price + 1,
            low=price - 1,
            close=price,
            volume=1000
        )
        candles.append(candle)
    
    return candles


def generate_flat(price=100, length=100):
    """Generate flat prices (no movement)."""
    candles = []
    base_time = datetime(2024, 1, 1)
    
    for i in range(length):
        candle = OHLCV(
            timestamp=base_time + timedelta(hours=i),
            open=price,
            high=price,
            low=price,
            close=price,
            volume=1000
        )
        candles.append(candle)
    
    return candles


def generate_sine_wave(center=100, amplitude=10, length=100, period=20):
    """Generate oscillating prices (sine wave)."""
    candles = []
    base_time = datetime(2024, 1, 1)
    
    for i in range(length):
        price = center + amplitude * math.sin(2 * math.pi * i / period)
        candle = OHLCV(
            timestamp=base_time + timedelta(hours=i),
            open=price - 0.5,
            high=price + 1,
            low=price - 1,
            close=price,
            volume=1000
        )
        candles.append(candle)
    
    return candles


def generate_overbought_scenario(base_price=3000, length=50):
    """
    Generate price data that creates overbought RSI condition.
    - Initial uptrend to build RSI
    - Sharp spike to push RSI > 70
    - 1h timeframe also elevated
    """
    candles = []
    base_time = datetime(2024, 1, 1)
    
    # Phase 1: Steady climb (0-30)
    for i in range(30):
        price = base_price + (i * 5)
        candle = OHLCV(
            timestamp=base_time + timedelta(hours=i),
            open=price - 2,
            high=price + 2,
            low=price - 3,
            close=price,
            volume=1000
        )
        candles.append(candle)
    
    # Phase 2: Sharp spike (30-40)
    for i in range(30, 40):
        price = base_price + 150 + ((i-30) * 10)  # Rapid increase
        candle = OHLCV(
            timestamp=base_time + timedelta(hours=i),
            open=price - 3,
            high=price + 5,
            low=price - 2,
            close=price,
            volume=2000  # High volume
        )
        candles.append(candle)
    
    # Phase 3: Consolidation (40-50)
    peak_price = base_price + 150 + 100
    for i in range(40, length):
        price = peak_price + (i % 3) - 1  # Small fluctuations
        candle = OHLCV(
            timestamp=base_time + timedelta(hours=i),
            open=price,
            high=price + 1,
            low=price - 1,
            close=price,
            volume=800  # Declining volume
        )
        candles.append(candle)
    
    return candles


def generate_oversold_scenario(base_price=3000, length=50):
    """
    Generate price data that creates oversold RSI condition.
    """
    candles = []
    base_time = datetime(2024, 1, 1)
    
    # Phase 1: Steady decline (0-30)
    for i in range(30):
        price = base_price - (i * 5)
        candle = OHLCV(
            timestamp=base_time + timedelta(hours=i),
            open=price + 2,
            high=price + 3,
            low=price - 2,
            close=price,
            volume=1000
        )
        candles.append(candle)
    
    # Phase 2: Sharp drop (30-40)
    for i in range(30, 40):
        price = base_price - 150 - ((i-30) * 10)  # Rapid decrease
        candle = OHLCV(
            timestamp=base_time + timedelta(hours=i),
            open=price + 3,
            high=price + 2,
            low=price - 5,
            close=price,
            volume=2000
        )
        candles.append(candle)
    
    # Phase 3: Consolidation (40-50)
    bottom_price = base_price - 150 - 100
    for i in range(40, length):
        price = bottom_price + (i % 3) - 1
        candle = OHLCV(
            timestamp=base_time + timedelta(hours=i),
            open=price,
            high=price + 1,
            low=price - 1,
            close=price,
            volume=800
        )
        candles.append(candle)
    
    return candles


def generate_breakout_scenario(base_price=3000, range_days=20, breakout_strength=1.5):
    """
    Generate price data showing range-bound then breakout.
    For SIB testing.
    """
    candles = []
    base_time = datetime(2024, 1, 1)
    
    # Phase 1: Range-bound (oscillating between support/resistance)
    range_size = base_price * 0.03  # 3% range
    for i in range(range_days * 24):  # Hourly candles
        # Oscillate within range
        position = (i % 48) / 48.0  # 48-hour cycle
        price = base_price + (math.sin(position * 2 * math.pi) * range_size)
        
        candle = OHLCV(
            timestamp=base_time + timedelta(hours=i),
            open=price - 5,
            high=price + 5,
            low=price - 5,
            close=price,
            volume=1000
        )
        candles.append(candle)
    
    # Phase 2: Breakout with volume
    breakout_start = range_days * 24
    breakout_price = base_price + range_size
    
    for i in range(breakout_start, breakout_start + 24):
        move = ((i - breakout_start) / 24) * (base_price * 0.05 * breakout_strength)
        price = breakout_price + move
        
        candle = OHLCV(
            timestamp=base_time + timedelta(hours=i),
            open=price - 10,
            high=price + 15,
            low=price - 5,
            close=price,
            volume=2500  # High volume breakout
        )
        candles.append(candle)
    
    return candles


if __name__ == "__main__":
    # Test generators
    print("Testing synthetic data generators...")
    
    up = generate_trending_up()
    print(f"✓ Trending up: {len(up)} candles, price {up[0].close:.2f} → {up[-1].close:.2f}")
    
    down = generate_trending_down()
    print(f"✓ Trending down: {len(down)} candles, price {down[0].close:.2f} → {down[-1].close:.2f}")
    
    flat = generate_flat()
    print(f"✓ Flat: {len(flat)} candles, all at price {flat[0].close:.2f}")
    
    sine = generate_sine_wave()
    print(f"✓ Sine wave: {len(sine)} candles, oscillating around {sine[0].close:.2f}")
    
    overbought = generate_overbought_scenario()
    print(f"✓ Overbought: {len(overbought)} candles, {overbought[0].close:.2f} → {overbought[-1].close:.2f}")
    
    oversold = generate_oversold_scenario()
    print(f"✓ Oversold: {len(oversold)} candles, {oversold[0].close:.2f} → {oversold[-1].close:.2f}")
    
    breakout = generate_breakout_scenario()
    print(f"✓ Breakout: {len(breakout)} candles")
    
    print("\n✅ All generators working")
