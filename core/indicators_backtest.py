"""Indicator calculations optimized for backtesting with minute data."""
from typing import List, Dict
from datetime import datetime, timedelta


class BacktestIndicators:
    """Calculate technical indicators from minute candle data."""
    
    @staticmethod
    def aggregate_candles(minute_candles: List[Dict], timeframe_minutes: int) -> List[Dict]:
        """
        Aggregate minute candles to higher timeframes.
        
        Args:
            minute_candles: List of 1-minute candles
            timeframe_minutes: Target timeframe (5, 15, 60, 240, etc.)
            
        Returns:
            List of aggregated candles
        """
        if not minute_candles:
            return []
        
        aggregated = []
        current_group = []
        
        for i, candle in enumerate(minute_candles):
            current_group.append(candle)
            
            # Check if we've hit the timeframe boundary
            if (i + 1) % timeframe_minutes == 0 or i == len(minute_candles) - 1:
                if current_group:
                    agg_candle = {
                        'timestamp': current_group[0]['timestamp'],
                        'open': current_group[0]['open'],
                        'high': max(c['high'] for c in current_group),
                        'low': min(c['low'] for c in current_group),
                        'close': current_group[-1]['close'],
                        'volume': sum(c['volume'] for c in current_group)
                    }
                    aggregated.append(agg_candle)
                    current_group = []
        
        return aggregated
    
    @staticmethod
    def rsi(closes: List[float], period: int = 14) -> float:
        """Calculate RSI indicator."""
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
    
    @staticmethod
    def ema(closes: List[float], period: int) -> float:
        """Calculate EMA (Exponential Moving Average)."""
        if len(closes) < period:
            return sum(closes) / len(closes) if closes else 0
        
        multiplier = 2 / (period + 1)
        ema_val = sum(closes[:period]) / period
        
        for price in closes[period:]:
            ema_val = (price * multiplier) + (ema_val * (1 - multiplier))
        
        return ema_val
    
    @staticmethod
    def atr(candles: List[Dict], period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(candles) < period + 1:
            return 0
        
        true_ranges = []
        for i in range(1, len(candles)):
            high = candles[i]['high']
            low = candles[i]['low']
            prev_close = candles[i-1]['close']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        return sum(true_ranges[-period:]) / period
    
    @staticmethod
    def adx(candles: List[Dict], period: int = 14) -> float:
        """Calculate ADX (Average Directional Index)."""
        if len(candles) < period + 1:
            return 0
        
        plus_dm = []
        minus_dm = []
        
        for i in range(1, len(candles)):
            high_diff = candles[i]['high'] - candles[i-1]['high']
            low_diff = candles[i-1]['low'] - candles[i]['low']
            
            plus_dm.append(high_diff if high_diff > low_diff and high_diff > 0 else 0)
            minus_dm.append(low_diff if low_diff > high_diff and low_diff > 0 else 0)
        
        atr_val = BacktestIndicators.atr(candles, period)
        if atr_val == 0:
            return 0
        
        plus_di = (sum(plus_dm[-period:]) / period) / atr_val * 100
        minus_di = (sum(minus_dm[-period:]) / period) / atr_val * 100
        
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) != 0 else 0
        return dx
    
    @staticmethod
    def volume_average(candles: List[Dict], period: int = 10) -> float:
        """Calculate average volume."""
        if len(candles) < period:
            return sum(c['volume'] for c in candles) / len(candles) if candles else 0
        
        return sum(c['volume'] for c in candles[-period:]) / period
    
    @staticmethod
    def detect_ema_crossover(closes: List[float], fast_period: int, slow_period: int) -> str:
        """
        Detect EMA crossover.
        
        Returns:
            'bullish' if fast crosses above slow
            'bearish' if fast crosses below slow
            'none' if no crossover
        """
        if len(closes) < max(fast_period, slow_period) + 1:
            return 'none'
        
        # Current EMAs
        fast_ema = BacktestIndicators.ema(closes, fast_period)
        slow_ema = BacktestIndicators.ema(closes, slow_period)
        
        # Previous EMAs
        fast_ema_prev = BacktestIndicators.ema(closes[:-1], fast_period)
        slow_ema_prev = BacktestIndicators.ema(closes[:-1], slow_period)
        
        # Detect crossover
        if fast_ema_prev <= slow_ema_prev and fast_ema > slow_ema:
            return 'bullish'
        elif fast_ema_prev >= slow_ema_prev and fast_ema < slow_ema:
            return 'bearish'
        
        return 'none'
    
    @staticmethod
    def classify_regime(candles_4h: List[Dict]) -> str:
        """
        Classify market regime.
        
        Returns:
            'RANGE', 'TREND_UP', 'TREND_DOWN', or 'DRAWDOWN'
        """
        if len(candles_4h) < 200:
            return 'RANGE'
        
        closes = [c['close'] for c in candles_4h]
        ema50 = BacktestIndicators.ema(closes, 50)
        ema200 = BacktestIndicators.ema(closes, 200)
        adx = BacktestIndicators.adx(candles_4h, 14)
        
        # DRAWDOWN: EMA50 < EMA200 and declining
        if ema50 < ema200:
            ema50_prev = BacktestIndicators.ema(closes[:-10], 50)
            if ema50 < ema50_prev:
                return 'DRAWDOWN'
            return 'TREND_DOWN'
        
        # STRONG TREND
        if adx > 25:
            return 'TREND_UP' if closes[-1] > ema50 else 'TREND_DOWN'
        
        # RANGE
        if adx < 20:
            return 'RANGE'
        
        return 'TREND_UP' if ema50 > ema200 else 'TREND_DOWN'
    
    @staticmethod
    def get_market_regime(candles_1h: List[Dict], candles_4h: List[Dict]) -> str:
        """
        Get simplified market regime for strategy adaptation.
        
        Returns:
            'BULL' - uptrend, favor LONG
            'BEAR' - downtrend, favor SHORT
            'RANGE' - choppy, trade extremes only
        """
        # Use shorter EMAs that work with limited data (7 days = ~40 4h candles)
        if len(candles_4h) < 30 or len(candles_1h) < 50:
            return 'RANGE'
        
        closes_4h = [c['close'] for c in candles_4h]
        closes_1h = [c['close'] for c in candles_1h]
        
        # Use EMA(20) and EMA(50) instead of 50/200 for 7-day data
        ema20_4h = BacktestIndicators.ema(closes_4h, 20)
        ema50_4h = BacktestIndicators.ema(closes_4h, min(50, len(closes_4h) - 10))
        adx_4h = BacktestIndicators.adx(candles_4h, 14)
        
        # Check if EMAs are rising or falling
        ema20_4h_prev = BacktestIndicators.ema(closes_4h[:-3], 20)
        ema20_rising = ema20_4h > ema20_4h_prev
        
        # BULL: EMA20 > EMA50 and rising, strong trend
        if ema20_4h > ema50_4h and ema20_rising and adx_4h > 20:
            return 'BULL'
        
        # BEAR: EMA20 < EMA50 or falling, strong trend
        if (ema20_4h < ema50_4h or not ema20_rising) and adx_4h > 20:
            return 'BEAR'
        
        # RANGE: weak trend
        return 'RANGE'
    
    @staticmethod
    def get_adaptive_params(regime: str, strategy: str) -> Dict:
        """
        Get regime-specific parameters for each strategy.
        
        Args:
            regime: 'BULL', 'BEAR', or 'RANGE'
            strategy: 'ER90', 'SCALPER', or 'MOMENTUM'
            
        Returns:
            Dict with strategy-specific parameters
        """
        params = {
            'BULL': {
                'ER90': {
                    'rsi_long': 40,
                    'rsi_short': 60,
                    'bias': 'LONG',  # Prefer LONG entries
                    'enabled': True
                },
                'SCALPER': {
                    'rsi_threshold': 48,
                    'direction': 'LONG',  # Buy dips
                    'enabled': True
                },
                'MOMENTUM': {
                    'direction': 'LONG',  # EMA crossover LONG
                    'enabled': True
                }
            },
            'BEAR': {
                'ER90': {
                    'rsi_long': 30,  # Tighter for LONG (rarely)
                    'rsi_short': 60,  # Easier for SHORT (often)
                    'bias': 'SHORT',  # Prefer SHORT entries
                    'enabled': True
                },
                'SCALPER': {
                    'rsi_threshold': 55,  # Only SHORT strong rallies
                    'direction': 'SHORT',  # Sell rallies
                    'enabled': False  # Disable - too choppy
                },
                'MOMENTUM': {
                    'direction': 'SHORT',  # EMA crossover SHORT
                    'enabled': True
                }
            },
            'RANGE': {
                'ER90': {
                    'rsi_long': 30,
                    'rsi_short': 70,
                    'bias': 'BOTH',  # Trade both directions
                    'enabled': True
                },
                'SCALPER': {
                    'enabled': False  # Too many false breakouts
                },
                'MOMENTUM': {
                    'enabled': False  # No clear trend
                }
            }
        }
        
        return params.get(regime, {}).get(strategy, {'enabled': False})
    
    @staticmethod
    def calculate_atr_targets(candles_1h: List[Dict], multiplier_tp: float = 2.0, multiplier_sl: float = 1.5) -> Dict:
        """
        Calculate ATR-based TP/SL targets.
        
        Args:
            candles_1h: 1-hour candles for ATR calculation
            multiplier_tp: TP multiplier (default 2.0x ATR)
            multiplier_sl: SL multiplier (default 1.5x ATR)
            
        Returns:
            Dict with 'tp_pct' and 'sl_pct' as percentages
        """
        if len(candles_1h) < 15:
            return {'tp_pct': 1.0, 'sl_pct': 0.5}
        
        atr = BacktestIndicators.atr(candles_1h, 14)
        current_price = candles_1h[-1]['close']
        
        if current_price == 0:
            return {'tp_pct': 1.0, 'sl_pct': 0.5}
        
        tp_pct = (atr * multiplier_tp / current_price) * 100
        sl_pct = (atr * multiplier_sl / current_price) * 100
        
        # Clamp to reasonable ranges
        tp_pct = max(0.3, min(tp_pct, 3.0))
        sl_pct = max(0.2, min(sl_pct, 2.0))
        
        return {'tp_pct': tp_pct, 'sl_pct': sl_pct}
