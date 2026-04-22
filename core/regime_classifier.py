"""Market regime classification."""
from typing import List
from .models import OHLCV, Regime, Config, AccountState
from .indicators import Indicators


class RegimeClassifier:
    """Classify market regime to determine which engine should be active."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def classify(self, candles_4h: List[OHLCV], account: AccountState) -> Regime:
        """
        Determine current market regime.
        
        Args:
            candles_4h: 4-hour candles for trend analysis
            account: Account state for drawdown check
        
        Returns:
            Market regime
        """
        # First check for drawdown - overrides everything
        if account.daily_pnl_pct <= -self.config.max_daily_drawdown_pct:
            return Regime.DRAWDOWN
        
        if account.consecutive_losses >= self.config.max_consecutive_losses:
            return Regime.DRAWDOWN
        
        # Insufficient data
        if len(candles_4h) < self.config.ema200_period:
            return Regime.RANGE
        
        # Calculate indicators
        closes = [c.close for c in candles_4h]
        ema50 = Indicators.ema(closes, self.config.ema50_period)
        ema200 = Indicators.ema(closes, self.config.ema200_period)
        adx = Indicators.adx(candles_4h, self.config.adx_period)
        
        # Determine trend strength
        ema_separation_pct = abs(ema50 - ema200) / ema200 * 100
        
        # Check for range break
        broke_up, broke_down = Indicators.range_break_detected(
            candles_4h, lookback_hours=24, candle_interval_minutes=240
        )
        range_break = broke_up or broke_down
        
        # Strong trend: EMA crossover + high ADX + range break
        if adx > self.config.sib_adx_threshold and ema_separation_pct > 2.0 and range_break:
            return Regime.STRONG_TREND
        
        # Weak trend: EMA crossover + moderate ADX
        if adx > self.config.sib_adx_threshold * 0.7 and ema_separation_pct > 1.0:
            return Regime.WEAK_TREND
        
        # Default to range
        return Regime.RANGE
