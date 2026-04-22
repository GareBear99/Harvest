"""Technical indicator calculations."""
import numpy as np
from typing import List
from .models import OHLCV


class Indicators:
    """Calculate technical indicators for trading strategies."""
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> float:
        """
        Calculate RSI (Relative Strength Index).
        
        Args:
            prices: List of closing prices
            period: RSI period
        
        Returns:
            RSI value (0-100)
        """
        if len(prices) < period + 1:
            return 50.0  # Neutral value if insufficient data
        
        prices_array = np.array(prices)
        deltas = np.diff(prices_array)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        # Handle edge cases
        if avg_loss == 0 and avg_gain == 0:
            return 50.0  # Flat prices = neutral RSI
        elif avg_loss == 0:
            return 100.0  # Only gains
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def atr(candles: List[OHLCV], period: int = 14) -> float:
        """
        Calculate ATR (Average True Range).
        
        Args:
            candles: List of OHLCV candles
            period: ATR period
        
        Returns:
            ATR value
        """
        if len(candles) < period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(candles)):
            high = candles[i].high
            low = candles[i].low
            prev_close = candles[i-1].close
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        return np.mean(true_ranges[-period:])
    
    @staticmethod
    def ema(prices: List[float], period: int) -> float:
        """
        Calculate EMA (Exponential Moving Average).
        
        Args:
            prices: List of closing prices
            period: EMA period
        
        Returns:
            EMA value
        """
        if len(prices) < period:
            return np.mean(prices) if prices else 0.0
        
        prices_array = np.array(prices)
        multiplier = 2 / (period + 1)
        
        ema_val = np.mean(prices_array[:period])
        
        for price in prices_array[period:]:
            ema_val = (price - ema_val) * multiplier + ema_val
        
        return ema_val
    
    @staticmethod
    def adx(candles: List[OHLCV], period: int = 14) -> float:
        """
        Calculate ADX (Average Directional Index).
        
        Args:
            candles: List of OHLCV candles
            period: ADX period
        
        Returns:
            ADX value
        """
        if len(candles) < period + 1:
            return 0.0
        
        plus_dm = []
        minus_dm = []
        tr_list = []
        
        for i in range(1, len(candles)):
            high_diff = candles[i].high - candles[i-1].high
            low_diff = candles[i-1].low - candles[i].low
            
            plus_dm.append(high_diff if high_diff > low_diff and high_diff > 0 else 0)
            minus_dm.append(low_diff if low_diff > high_diff and low_diff > 0 else 0)
            
            high = candles[i].high
            low = candles[i].low
            prev_close = candles[i-1].close
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_list.append(tr)
        
        plus_dm_array = np.array(plus_dm[-period:])
        minus_dm_array = np.array(minus_dm[-period:])
        tr_array = np.array(tr_list[-period:])
        
        plus_di = 100 * (np.mean(plus_dm_array) / np.mean(tr_array)) if np.mean(tr_array) > 0 else 0
        minus_di = 100 * (np.mean(minus_dm_array) / np.mean(tr_array)) if np.mean(tr_array) > 0 else 0
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) > 0 else 0
        
        return dx
    
    @staticmethod
    def volume_average(candles: List[OHLCV], period: int = 20) -> float:
        """
        Calculate average volume.
        
        Args:
            candles: List of OHLCV candles
            period: Period for average
        
        Returns:
            Average volume
        """
        if len(candles) < period:
            return np.mean([c.volume for c in candles]) if candles else 0.0
        
        volumes = [c.volume for c in candles[-period:]]
        return np.mean(volumes)
    
    @staticmethod
    def price_impulse(candles: List[OHLCV], lookback_hours: int = 2, 
                      candle_interval_minutes: int = 5) -> float:
        """
        Calculate price impulse (max price move in time window).
        
        Args:
            candles: List of OHLCV candles
            lookback_hours: Hours to look back
            candle_interval_minutes: Candle interval in minutes
        
        Returns:
            Maximum absolute price change
        """
        lookback_candles = (lookback_hours * 60) // candle_interval_minutes
        
        if len(candles) < lookback_candles:
            return 0.0
        
        recent_candles = candles[-lookback_candles:]
        prices = [c.close for c in recent_candles]
        
        max_impulse = max(prices) - min(prices)
        
        return max_impulse
    
    @staticmethod
    def range_break_detected(candles: List[OHLCV], lookback_hours: int = 24,
                            candle_interval_minutes: int = 60) -> tuple:
        """
        Detect if price broke out of recent range.
        
        Args:
            candles: List of OHLCV candles
            lookback_hours: Hours to look back for range
            candle_interval_minutes: Candle interval in minutes
        
        Returns:
            (broke_up, broke_down) boolean tuple
        """
        lookback_candles = (lookback_hours * 60) // candle_interval_minutes
        
        if len(candles) < lookback_candles + 1:
            return (False, False)
        
        range_candles = candles[-(lookback_candles+1):-1]
        current_candle = candles[-1]
        
        range_high = max(c.high for c in range_candles)
        range_low = min(c.low for c in range_candles)
        
        broke_up = current_candle.close > range_high
        broke_down = current_candle.close < range_low
        
        return (broke_up, broke_down)
