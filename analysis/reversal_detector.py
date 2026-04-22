"""
Reversal Detection System

Filters out trades near potential trend reversals using:
1. RSI divergence detection
2. Support/resistance proximity checks
3. Volume anomaly detection
"""

from typing import Dict, List, Optional, Tuple


class ReversalDetector:
    """Detects potential trend reversals to avoid bad entries"""
    
    def __init__(self):
        self.stats = {
            'total_checked': 0,
            'reversals_detected': 0,
            'trades_filtered': 0
        }
    
    def check_reversal_risk(
        self,
        candles: List[Dict],
        idx: int,
        current_price: float,
        trend_direction: str,  # 'SHORT' or 'LONG'
        timeframe: str = '1h'  # For adaptive thresholds
    ) -> Tuple[bool, str]:
        """
        Check if current setup shows reversal risk
        
        Args:
            candles: Historical candles
            idx: Current candle index
            current_price: Current price
            trend_direction: Direction we want to trade
            
        Returns:
            (has_risk, reason) tuple
        """
        self.stats['total_checked'] += 1
        
        if idx < 30:  # Need history
            return False, ""
        
        # Check RSI divergence
        has_divergence, div_reason = self._check_rsi_divergence(
            candles, idx, trend_direction
        )
        if has_divergence:
            self.stats['reversals_detected'] += 1
            self.stats['trades_filtered'] += 1
            return True, f"RSI Divergence: {div_reason}"
        
        # Check support/resistance proximity (adaptive threshold)
        near_sr, sr_reason = self._check_support_resistance(
            candles, idx, current_price, trend_direction, timeframe
        )
        if near_sr:
            self.stats['reversals_detected'] += 1
            self.stats['trades_filtered'] += 1
            return True, f"Near S/R: {sr_reason}"
        
        # Check volume exhaustion
        exhaustion, exh_reason = self._check_volume_exhaustion(
            candles, idx, trend_direction
        )
        if exhaustion:
            self.stats['reversals_detected'] += 1
            self.stats['trades_filtered'] += 1
            return True, f"Volume Exhaustion: {exh_reason}"
        
        return False, ""
    
    def _check_rsi_divergence(
        self,
        candles: List[Dict],
        idx: int,
        direction: str
    ) -> Tuple[bool, str]:
        """
        Detect RSI divergence
        
        Bearish divergence (avoid SHORT): Price makes higher high but RSI makes lower high
        Bullish divergence (avoid LONG): Price makes lower low but RSI makes higher low
        """
        if idx < 14:
            return False, ""
        
        # Calculate RSI
        rsi_values = self._calculate_rsi([c['close'] for c in candles[:idx + 1]], 14)
        
        if len(rsi_values) < 10:
            return False, ""
        
        recent_rsi = rsi_values[-10:]
        recent_prices = [c['close'] for c in candles[idx - 9:idx + 1]]
        
        if direction == 'SHORT':
            # Check for bearish divergence (avoid this)
            price_higher_high = recent_prices[-1] > max(recent_prices[:-1])
            rsi_lower_high = recent_rsi[-1] < max(recent_rsi[:-1])
            
            if price_higher_high and rsi_lower_high:
                return True, "Bearish divergence (momentum weakening)"
        
        elif direction == 'LONG':
            # Check for bullish divergence (avoid this)
            price_lower_low = recent_prices[-1] < min(recent_prices[:-1])
            rsi_higher_low = recent_rsi[-1] > min(recent_rsi[:-1])
            
            if price_lower_low and rsi_higher_low:
                return True, "Bullish divergence (momentum weakening)"
        
        return False, ""
    
    def _check_support_resistance(
        self,
        candles: List[Dict],
        idx: int,
        current_price: float,
        direction: str,
        timeframe: str = '1h'
    ) -> Tuple[bool, str]:
        """
        Check if price is near key support/resistance levels
        """
        lookback = min(100, idx)
        recent_candles = candles[idx - lookback:idx + 1]
        
        # Find pivot highs and lows
        highs = [c['high'] for c in recent_candles]
        lows = [c['low'] for c in recent_candles]
        
        # Key resistance levels (for SHORT)
        resistances = self._find_pivots(highs, is_high=True)
        # Key support levels (for LONG)
        supports = self._find_pivots(lows, is_high=False)
        
        # Adaptive threshold based on timeframe
        # 15m: 1.0% (less sensitive), 1h: 0.5%, 4h: 0.3% (more sensitive)
        threshold_pct = {'15m': 0.010, '1h': 0.005, '4h': 0.003}.get(timeframe, 0.005)
        threshold = current_price * threshold_pct
        
        if direction == 'SHORT':
            # Avoid shorting near support (might bounce)
            for support in supports:
                if abs(current_price - support) < threshold:
                    return True, f"Near support at ${support:.2f}"
        
        elif direction == 'LONG':
            # Avoid long near resistance (might reject)
            for resistance in resistances:
                if abs(current_price - resistance) < threshold:
                    return True, f"Near resistance at ${resistance:.2f}"
        
        return False, ""
    
    def _check_volume_exhaustion(
        self,
        candles: List[Dict],
        idx: int,
        direction: str
    ) -> Tuple[bool, str]:
        """
        Check for volume exhaustion (trend losing steam)
        """
        if idx < 10:
            return False, ""
        
        recent_volumes = [c['volume'] for c in candles[idx - 9:idx + 1]]
        avg_volume = sum(recent_volumes[:-1]) / len(recent_volumes[:-1])
        current_volume = recent_volumes[-1]
        
        # If current volume is significantly lower, trend may be exhausting
        if current_volume < avg_volume * 0.6:  # 40% drop in volume
            return True, f"Volume declining ({current_volume/avg_volume:.1%} of average)"
        
        return False, ""
    
    def _find_pivots(
        self,
        values: List[float],
        is_high: bool,
        window: int = 5
    ) -> List[float]:
        """Find pivot points (local maxima or minima)"""
        pivots = []
        
        for i in range(window, len(values) - window):
            if is_high:
                # Check if local maximum
                if all(values[i] >= values[i - j] for j in range(1, window + 1)) and \
                   all(values[i] >= values[i + j] for j in range(1, window + 1)):
                    pivots.append(values[i])
            else:
                # Check if local minimum
                if all(values[i] <= values[i - j] for j in range(1, window + 1)) and \
                   all(values[i] <= values[i + j] for j in range(1, window + 1)):
                    pivots.append(values[i])
        
        return pivots[-5:]  # Return last 5 pivots
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return []
        
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        rsi_values = []
        
        for i in range(period, len(gains)):
            if avg_loss == 0:
                rsi_values.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)
            
            # Update averages
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        return rsi_values
    
    def get_stats(self) -> Dict:
        """Get detection statistics"""
        return {
            **self.stats,
            'filter_rate': (self.stats['trades_filtered'] / self.stats['total_checked'] * 100) 
                          if self.stats['total_checked'] > 0 else 0
        }
