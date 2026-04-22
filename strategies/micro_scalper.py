"""
Micro-Scalper Strategy
High-frequency scalping on 1-minute timeframe with 30× leverage.
Target: 20-30 trades/day, 0.2-0.3% moves amplified to 6-9% gains.
"""

from typing import Optional, Dict, List
import numpy as np


class MicroScalper:
    """
    Ultra-sensitive 1-minute scalping strategy.
    
    Entry Conditions (LONG):
    - RSI(5) < 40
    - Price touches EMA(9) from above
    - MACD crosses up
    - Price -0.3% from 5m high with volume spike
    
    Entry Conditions (SHORT):
    - RSI(5) > 60
    - Price touches EMA(9) from below
    - MACD crosses down
    - Price +0.3% from 5m low with volume spike
    
    Risk Management:
    - TP: 0.2-0.3% (6-9% with 30× leverage)
    - SL: 0.15% (4.5% with 30× leverage)
    - Max 3 consecutive losses → reduce leverage to 10×
    """
    
    def __init__(self, leverage: int = 30):
        """
        Initialize micro-scalper.
        
        Args:
            leverage: Trading leverage (default 30×)
        """
        self.leverage = leverage
        self.base_leverage = leverage
        self.consecutive_losses = 0
        
        # Parameters
        self.rsi_period = 5
        self.ema_period = 9
        self.macd_fast = 8
        self.macd_slow = 17
        self.macd_signal = 9
        
        # TP/SL
        self.tp_pct = 0.0025  # 0.25%
        self.sl_pct = 0.0015  # 0.15%
        
        # Volume threshold
        self.volume_spike_multiplier = 2.0
    
    def calculate_rsi(self, closes: List[float], period: int) -> float:
        """Calculate RSI."""
        if len(closes) < period + 1:
            return 50.0
        
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_ema(self, closes: List[float], period: int) -> float:
        """Calculate EMA."""
        if len(closes) < period:
            return sum(closes) / len(closes) if closes else 0
        
        multiplier = 2 / (period + 1)
        ema = sum(closes[:period]) / period
        
        for price in closes[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def calculate_macd(self, closes: List[float]) -> Dict[str, float]:
        """Calculate MACD."""
        if len(closes) < self.macd_slow:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        ema_fast = self.calculate_ema(closes, self.macd_fast)
        ema_slow = self.calculate_ema(closes, self.macd_slow)
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line (EMA of MACD)
        macd_values = []
        for i in range(self.macd_slow, len(closes)):
            fast = self.calculate_ema(closes[:i+1], self.macd_fast)
            slow = self.calculate_ema(closes[:i+1], self.macd_slow)
            macd_values.append(fast - slow)
        
        if len(macd_values) >= self.macd_signal:
            signal = self.calculate_ema(macd_values, self.macd_signal)
        else:
            signal = sum(macd_values) / len(macd_values) if macd_values else 0
        
        histogram = macd_line - signal
        
        return {
            'macd': macd_line,
            'signal': signal,
            'histogram': histogram
        }
    
    def detect_macd_cross(self, closes: List[float]) -> str:
        """
        Detect MACD crossover.
        
        Returns:
            'bullish', 'bearish', or 'none'
        """
        if len(closes) < self.macd_slow + 1:
            return 'none'
        
        current = self.calculate_macd(closes)
        previous = self.calculate_macd(closes[:-1])
        
        # Bullish cross: histogram crosses from negative to positive
        if previous['histogram'] <= 0 and current['histogram'] > 0:
            return 'bullish'
        # Bearish cross: histogram crosses from positive to negative
        elif previous['histogram'] >= 0 and current['histogram'] < 0:
            return 'bearish'
        
        return 'none'
    
    def check_ema_touch(self, closes: List[float], current_price: float) -> Dict[str, bool]:
        """
        Check if price is touching EMA from above or below.
        
        Returns:
            {'from_above': bool, 'from_below': bool}
        """
        if len(closes) < self.ema_period + 1:
            return {'from_above': False, 'from_below': False}
        
        ema = self.calculate_ema(closes, self.ema_period)
        prev_price = closes[-1]
        
        # Tolerance: within 0.1% of EMA
        tolerance = ema * 0.001
        
        from_above = (prev_price > ema and 
                     abs(current_price - ema) <= tolerance and
                     current_price <= ema)
        
        from_below = (prev_price < ema and 
                     abs(current_price - ema) <= tolerance and
                     current_price >= ema)
        
        return {'from_above': from_above, 'from_below': from_below}
    
    def check_volume_spike(self, volumes: List[float]) -> bool:
        """Check if current volume is a spike."""
        if len(volumes) < 20:
            return False
        
        avg_volume = sum(volumes[-20:-1]) / 19
        current_volume = volumes[-1]
        
        return current_volume > avg_volume * self.volume_spike_multiplier
    
    def check_price_extremes(self, closes_1m: List[float], closes_5m: List[float],
                            current_price: float) -> Dict[str, bool]:
        """
        Check if price is at extreme from 5m high/low.
        
        Returns:
            {'near_low': bool, 'near_high': bool}
        """
        if len(closes_5m) < 12:  # Need at least 1 hour
            return {'near_low': False, 'near_high': False}
        
        # Get recent 5m high/low
        recent_5m = closes_5m[-12:]  # Last hour
        high_5m = max(recent_5m)
        low_5m = min(recent_5m)
        
        # Check if within 0.3% of extremes
        near_low = (high_5m - current_price) / high_5m >= 0.003
        near_high = (current_price - low_5m) / low_5m >= 0.003
        
        return {'near_low': near_low, 'near_high': near_high}
    
    def generate_signal(self, closes_1m: List[float], closes_5m: List[float],
                       volumes_1m: List[float], current_price: float) -> Optional[Dict]:
        """
        Generate trading signal based on 1-minute data.
        
        Args:
            closes_1m: 1-minute close prices
            closes_5m: 5-minute close prices
            volumes_1m: 1-minute volumes
            current_price: Current price
        
        Returns:
            Dict with signal or None
        """
        if len(closes_1m) < 30:  # Need warmup
            return None
        
        # Calculate indicators
        rsi = self.calculate_rsi(closes_1m, self.rsi_period)
        ema = self.calculate_ema(closes_1m, self.ema_period)
        macd_cross = self.detect_macd_cross(closes_1m)
        ema_touch = self.check_ema_touch(closes_1m, current_price)
        volume_spike = self.check_volume_spike(volumes_1m)
        extremes = self.check_price_extremes(closes_1m, closes_5m, current_price)
        
        # LONG conditions (loosened for more trades)
        long_signals = []
        
        # 1. RSI oversold (loosened from <40 to <45)
        if rsi < 45:
            long_signals.append('rsi_oversold')
        
        # 2. Price below EMA (not just touching)
        if current_price < ema * 0.999:  # 0.1% below EMA
            long_signals.append('below_ema')
        
        # 3. MACD bullish cross
        if macd_cross == 'bullish':
            long_signals.append('macd_bullish')
        
        # 4. Price near low (removed volume requirement)
        if extremes['near_low']:
            long_signals.append('near_low')
        
        # SHORT conditions (loosened for more trades)
        short_signals = []
        
        # 1. RSI overbought (loosened from >60 to >55)
        if rsi > 55:
            short_signals.append('rsi_overbought')
        
        # 2. Price above EMA (not just touching)
        if current_price > ema * 1.001:  # 0.1% above EMA
            short_signals.append('above_ema')
        
        # 3. MACD bearish cross
        if macd_cross == 'bearish':
            short_signals.append('macd_bearish')
        
        # 4. Price near high (removed volume requirement)
        if extremes['near_high']:
            short_signals.append('near_high')
        
        # Generate signal if any condition met
        if long_signals:
            return {
                'direction': 'LONG',
                'entry_price': current_price,
                'tp_price': current_price * (1 + self.tp_pct),
                'sl_price': current_price * (1 - self.sl_pct),
                'leverage': self.leverage,
                'tp_pct': self.tp_pct * 100,
                'sl_pct': self.sl_pct * 100,
                'signals': long_signals,
                'rsi': rsi,
                'ema': ema
            }
        elif short_signals:
            return {
                'direction': 'SHORT',
                'entry_price': current_price,
                'tp_price': current_price * (1 - self.tp_pct),
                'sl_price': current_price * (1 + self.sl_pct),
                'leverage': self.leverage,
                'tp_pct': self.tp_pct * 100,
                'sl_pct': self.sl_pct * 100,
                'signals': short_signals,
                'rsi': rsi,
                'ema': ema
            }
        
        return None
    
    def update_after_trade(self, won: bool):
        """
        Update strategy state after trade.
        
        Args:
            won: True if trade was profitable
        """
        if won:
            self.consecutive_losses = 0
            # Reset to base leverage on win
            self.leverage = self.base_leverage
        else:
            self.consecutive_losses += 1
            
            # Reduce leverage after 3 consecutive losses
            if self.consecutive_losses >= 3:
                self.leverage = 10  # Drop to 10× leverage
    
    def get_status(self) -> Dict:
        """Get strategy status."""
        return {
            'leverage': self.leverage,
            'base_leverage': self.base_leverage,
            'consecutive_losses': self.consecutive_losses,
            'tp_pct': self.tp_pct * 100,
            'sl_pct': self.sl_pct * 100,
            'risk_reduction_active': self.leverage < self.base_leverage
        }


# Example usage
if __name__ == '__main__':
    import json
    
    # Load 1-minute data
    with open('../data/eth_minute_data_7days.json', 'r') as f:
        data = json.load(f)
    
    candles = data['candles']
    closes_1m = [c['close'] for c in candles[:100]]
    closes_5m = [c['close'] for c in candles[::5][:20]]
    volumes_1m = [c['volume'] for c in candles[:100]]
    current_price = candles[99]['close']
    
    # Test strategy
    scalper = MicroScalper(leverage=30)
    signal = scalper.generate_signal(closes_1m, closes_5m, volumes_1m, current_price)
    
    if signal:
        print(f"Signal: {signal['direction']}")
        print(f"Entry: ${signal['entry_price']:.2f}")
        print(f"TP: ${signal['tp_price']:.2f} ({signal['tp_pct']:.2f}%)")
        print(f"SL: ${signal['sl_price']:.2f} ({signal['sl_pct']:.2f}%)")
        print(f"Leverage: {signal['leverage']}×")
        print(f"Triggers: {', '.join(signal['signals'])}")
        print(f"RSI: {signal['rsi']:.1f}")
    else:
        print("No signal")
    
    print(f"\nStrategy status: {scalper.get_status()}")
