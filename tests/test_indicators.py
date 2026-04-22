"""Indicator validation tests."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.indicators import Indicators
from test_data_generators import *


class TestIndicators:
    """Test suite for technical indicators."""
    
    def test_rsi_trending_up(self):
        """RSI should approach 100 on steady uptrend."""
        candles = generate_trending_up(length=50)
        closes = [c.close for c in candles]
        
        rsi = Indicators.rsi(closes, period=14)
        
        print(f"RSI on uptrend: {rsi:.2f}")
        assert rsi > 80, f"Expected RSI > 80 on strong uptrend, got {rsi:.2f}"
        assert rsi <= 100, "RSI should not exceed 100"
        return True
    
    def test_rsi_trending_down(self):
        """RSI should approach 0 on steady downtrend."""
        candles = generate_trending_down(length=50)
        closes = [c.close for c in candles]
        
        rsi = Indicators.rsi(closes, period=14)
        
        print(f"RSI on downtrend: {rsi:.2f}")
        assert rsi < 20, f"Expected RSI < 20 on strong downtrend, got {rsi:.2f}"
        assert rsi >= 0, "RSI should not go below 0"
        return True
    
    def test_rsi_flat(self):
        """RSI should be near 50 on flat prices."""
        candles = generate_flat(length=50)
        closes = [c.close for c in candles]
        
        rsi = Indicators.rsi(closes, period=14)
        
        print(f"RSI on flat: {rsi:.2f}")
        # Flat prices should give RSI of 50 (neutral)
        assert 45 < rsi < 55, f"Expected RSI ~50 on flat, got {rsi:.2f}"
        return True
    
    def test_rsi_oscillating(self):
        """RSI should oscillate between 30-70 on sine wave."""
        candles = generate_sine_wave(length=100)
        closes = [c.close for c in candles]
        
        # Our implementation
        rsi = Indicators.rsi(closes, period=14)
        
        print(f"RSI on sine wave: {rsi:.2f}")
        
        # On oscillating data, RSI should be in middle range
        assert 20 < rsi < 80, f"RSI should oscillate, got {rsi:.2f}"
        return True
    
    def test_atr_simple(self):
        """ATR on constant range should equal that range."""
        # Create candles with consistent 10-point range
        candles = []
        base_time = datetime(2024, 1, 1)
        for i in range(20):
            candles.append(OHLCV(
                timestamp=base_time + timedelta(hours=i),
                open=100,
                high=105,
                low=95,
                close=100,
                volume=1000
            ))
        
        atr = Indicators.atr(candles, period=14)
        
        print(f"ATR with 10-point range: {atr:.2f}")
        assert 9 < atr < 11, f"Expected ATR ~10, got {atr:.2f}"
        return True
    
    def test_atr_increasing_volatility(self):
        """ATR should increase with volatility."""
        # Low volatility
        candles_low = generate_flat(length=30)
        atr_low = Indicators.atr(candles_low, period=14)
        
        # High volatility
        candles_high = generate_sine_wave(length=30, amplitude=20)
        atr_high = Indicators.atr(candles_high, period=14)
        
        print(f"ATR low volatility: {atr_low:.2f}, high volatility: {atr_high:.2f}")
        
        assert atr_high > atr_low, "ATR should be higher with more volatility"
        return True
    
    def test_ema_trending(self):
        """EMA should track trend."""
        candles = generate_trending_up(length=100)
        closes = [c.close for c in candles]
        
        ema20 = Indicators.ema(closes, period=20)
        ema50 = Indicators.ema(closes, period=50)
        
        print(f"EMA20: {ema20:.2f}, EMA50: {ema50:.2f}, Latest price: {closes[-1]:.2f}")
        
        # In uptrend: shorter EMA > longer EMA
        assert ema20 > ema50, "EMA20 should be above EMA50 in uptrend"
        
        # Both should be below current price in uptrend
        assert ema20 < closes[-1], "EMA20 should lag price in uptrend"
        return True
    
    def test_volume_average(self):
        """Volume average should match simple average."""
        candles = generate_flat(length=30)
        
        # All have volume=1000
        vol_avg = Indicators.volume_average(candles, period=20)
        
        print(f"Volume average: {vol_avg:.2f}")
        assert abs(vol_avg - 1000) < 1, f"Expected volume avg=1000, got {vol_avg:.2f}"
        return True
    
    def test_range_break_detection(self):
        """Range break detection should identify breakouts."""
        candles = generate_breakout_scenario(base_price=100, range_days=5)
        
        # Test before breakout
        broke_up_before, broke_down_before = Indicators.range_break_detected(
            candles[:120],  # Before breakout
            lookback_hours=24,
            candle_interval_minutes=60
        )
        
        # Test after breakout
        broke_up_after, broke_down_after = Indicators.range_break_detected(
            candles,  # Full data including breakout
            lookback_hours=24,
            candle_interval_minutes=60
        )
        
        print(f"Before breakout: up={broke_up_before}, down={broke_down_before}")
        print(f"After breakout: up={broke_up_after}, down={broke_down_after}")
        
        assert broke_up_after == True, "Should detect upward breakout"
        return True


def run_all_tests():
    """Run all indicator validation tests."""
    print("="*70)
    print("INDICATOR VALIDATION TESTS")
    print("="*70)
    
    tester = TestIndicators()
    tests = [
        ("RSI Trending Up", tester.test_rsi_trending_up),
        ("RSI Trending Down", tester.test_rsi_trending_down),
        ("RSI Flat", tester.test_rsi_flat),
        ("RSI Oscillating", tester.test_rsi_oscillating),
        ("ATR Simple", tester.test_atr_simple),
        ("ATR Increasing Volatility", tester.test_atr_increasing_volatility),
        ("EMA Trending", tester.test_ema_trending),
        ("Volume Average", tester.test_volume_average),
        ("Range Break Detection", tester.test_range_break_detection),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n📝 Testing: {name}")
        try:
            result = test_func()
            if result:
                print(f"✅ PASS: {name}")
                passed += 1
            else:
                print(f"❌ FAIL: {name}")
                failed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {name} - {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {name} - {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
