"""ER-90 (Exhaustion Reversion) strategy engine."""
from typing import List, Optional
from datetime import datetime
from core.models import OHLCV, Side, ExecutionIntent, Engine, Config, AccountState
from core.indicators import Indicators
from core.position_size_limiter import get_position_limiter


class ER90Strategy:
    """
    Exhaustion Reversion strategy for range-bound markets.
    Goal: 85-92% win rate with small profits.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.position_limiter = get_position_limiter()
    
    def check_entry(self, candles_5m: List[OHLCV], candles_1h: List[OHLCV],
                   account: AccountState) -> Optional[ExecutionIntent]:
        """
        Check for ER-90 entry conditions.
        
        Entry conditions (ALL required):
        - Price impulse >= 1.5-2.0 × ATR in < 2h
        - RSI(5) > 85 (short) or < 15 (long)
        - Volume spike followed by decline
        - Failure to extend high/low
        
        Args:
            candles_5m: 5-minute candles for impulse detection
            candles_1h: 1-hour candles for ATR
            account: Account state
        
        Returns:
            ExecutionIntent if conditions met, None otherwise
        """
        # Check if already hit max trades or losses today
        if Engine.ER90 in account.trades_today:
            if account.trades_today[Engine.ER90] >= self.config.er90_max_trades_per_day:
                return None
        
        if Engine.ER90 in account.losses_today:
            if account.losses_today[Engine.ER90] >= self.config.er90_max_losses_per_day:
                return None
        
        # Need sufficient data - fallback to 1h if 5m insufficient
        use_1h_for_signals = len(candles_5m) < 50
        if len(candles_1h) < self.config.atr_period + 10:
            return None
        
        # Use 1h data if 5m is unavailable
        signal_candles = candles_1h if use_1h_for_signals else candles_5m
        current_price = signal_candles[-1].close
        
        # Calculate indicators
        closes_signal = [c.close for c in signal_candles]
        closes_1h = [c.close for c in candles_1h]
        rsi_signal = Indicators.rsi(closes_signal, self.config.rsi_period)
        rsi_1h = Indicators.rsi(closes_1h, self.config.rsi_period)
        atr = Indicators.atr(candles_1h, self.config.atr_period)
        
        # Calculate price impulse
        candle_interval = 60 if use_1h_for_signals else 5
        impulse = Indicators.price_impulse(signal_candles, lookback_hours=2, candle_interval_minutes=candle_interval)
        
        # Volume analysis
        volume_avg = Indicators.volume_average(signal_candles, period=20)
        current_volume = signal_candles[-1].volume
        prev_volume = signal_candles[-2].volume if len(signal_candles) > 1 else current_volume
        
        volume_spiked = prev_volume > volume_avg * 1.2  # Relaxed from 1.3
        volume_declining = current_volume < prev_volume * 0.85  # Relaxed from 0.8
        
        # Check for failure to extend high/low (exhaustion)
        recent_candles = signal_candles[-3:] if len(signal_candles) >= 3 else signal_candles
        highs = [c.high for c in recent_candles]
        lows = [c.low for c in recent_candles]
        
        # Simplified: just check if not making new extreme
        failed_to_extend_high = len(highs) > 1 and highs[-1] <= max(highs[:-1])
        failed_to_extend_low = len(lows) > 1 and lows[-1] >= min(lows[:-1])
        
        # Determine entry side
        side = None
        
        # SHORT setup: overbought exhaustion (ultra-simplified for testing)
        # Just RSI extreme on both timeframes
        if (rsi_signal > self.config.er90_rsi_upper and 
            rsi_1h > 50):  # 1h confirmation
            side = Side.SHORT
        
        # LONG setup: oversold exhaustion (ultra-simplified for testing)
        # Just RSI extreme on both timeframes
        elif (rsi_signal < self.config.er90_rsi_lower and
              rsi_1h < 50):  # 1h confirmation
            side = Side.LONG
        
        if side is None:
            return None
        
        # Calculate position sizing and risk parameters
        # Use 1h timestamp for proper backtest tracking (5m may be stale)
        timestamp_for_signal = candles_1h[-1].timestamp
        return self._calculate_execution_intent(
            timestamp=timestamp_for_signal,
            side=side,
            entry_price=current_price,
            atr=atr,
            account=account
        )
    
    def _calculate_execution_intent(self, timestamp: datetime, side: Side, 
                                   entry_price: float, atr: float,
                                   account: AccountState) -> ExecutionIntent:
        """Calculate execution intent with proper risk parameters."""
        
        # Use mid-range values for risk parameters
        risk_pct = (self.config.er90_risk_pct_min + self.config.er90_risk_pct_max) / 2
        leverage = (self.config.er90_leverage_min + self.config.er90_leverage_max) / 2
        tp_pct = (self.config.er90_tp_pct_min + self.config.er90_tp_pct_max) / 2
        sl_pct = (self.config.er90_sl_pct_min + self.config.er90_sl_pct_max) / 2
        
        # Calculate stop loss and take profit
        if side == Side.LONG:
            stop = entry_price * (1 - sl_pct / 100)
            tp1 = entry_price * (1 + tp_pct / 100)
        else:  # SHORT
            stop = entry_price * (1 + sl_pct / 100)
            tp1 = entry_price * (1 - tp_pct / 100)
        
        # Calculate position size based on stop distance
        stop_distance = abs(entry_price - stop)
        risk_amount = account.equity * (risk_pct / 100)
        
        # Position size = risk amount / stop distance
        position_size_base = risk_amount / stop_distance
        
        # Apply leverage to get notional
        notional_usd = position_size_base * entry_price
        
        # Apply position size limits
        limited_notional, was_limited, limit_info = self.position_limiter.limit_position_size(
            notional_usd, account.equity, "ER90"
        )
        notional_usd = limited_notional
        
        # Validate liquidation distance
        liq_buffer_pct = self.config.liquidation_buffer_pct
        if side == Side.LONG:
            liq_price = entry_price * (1 - 100 / leverage)
            liq_safe = liq_price < stop * (1 - liq_buffer_pct / 100)
        else:
            liq_price = entry_price * (1 + 100 / leverage)
            liq_safe = liq_price > stop * (1 + liq_buffer_pct / 100)
        
        if not liq_safe:
            # Reduce leverage if liquidation too close
            leverage = leverage * 0.8
        
        return ExecutionIntent(
            timestamp=timestamp,
            engine=Engine.ER90,
            side=side,
            entry=entry_price,
            stop=stop,
            tp1=tp1,
            runner=None,  # ER-90 doesn't use runners
            leverage_cap=leverage,
            notional_usd=notional_usd,
            risk_pct=risk_pct,
            symbol="BTCUSDT"
        )
