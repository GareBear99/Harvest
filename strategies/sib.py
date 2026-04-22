"""SIB (Single Impulse Breakout) strategy engine."""
from typing import List, Optional
from datetime import datetime
from core.models import OHLCV, Side, ExecutionIntent, Engine, Config, AccountState
from core.indicators import Indicators
from core.position_size_limiter import get_position_limiter


class SIBStrategy:
    """
    Single Impulse Breakout strategy for trending markets.
    Goal: Capture large trend expansions with low frequency.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.position_limiter = get_position_limiter()
    
    def check_entry(self, candles_1h: List[OHLCV], candles_4h: List[OHLCV],
                   account: AccountState, current_hour_utc: int) -> Optional[ExecutionIntent]:
        """
        Check for SIB entry conditions.
        
        Entry conditions (ALL required):
        - 4H EMA50 > EMA200 (long) or inverse (short)
        - ADX(14) > 20
        - 12-24h range break on candle close
        - Volume >= 1.5× average
        - Active liquidity window (UTC 07-16)
        
        Args:
            candles_1h: 1-hour candles
            candles_4h: 4-hour candles for trend
            account: Account state
            current_hour_utc: Current UTC hour (0-23)
        
        Returns:
            ExecutionIntent if conditions met, None otherwise
        """
        # OPTIMIZED: Time restriction removed to trade 24/7
        # (Previously limited to UTC 07-16)
        
        # Check if already hit max trades today
        if Engine.SIB in account.trades_today:
            if account.trades_today[Engine.SIB] >= self.config.sib_max_trades_per_day:
                return None
        
        # Need sufficient data
        if len(candles_4h) < self.config.ema200_period or len(candles_1h) < 30:
            return None
        
        current_price = candles_1h[-1].close
        
        # Calculate 4H trend indicators
        closes_4h = [c.close for c in candles_4h]
        ema50 = Indicators.ema(closes_4h, self.config.ema50_period)
        ema200 = Indicators.ema(closes_4h, self.config.ema200_period)
        adx = Indicators.adx(candles_4h, self.config.adx_period)
        
        # Check ADX threshold
        if adx < self.config.sib_adx_threshold:
            return None
        
        # Determine trend direction from EMAs
        trend_up = ema50 > ema200
        trend_down = ema50 < ema200
        
        if not trend_up and not trend_down:
            return None
        
        # Check for range break on 1h timeframe (12-24h lookback)
        broke_up, broke_down = Indicators.range_break_detected(
            candles_1h, lookback_hours=18, candle_interval_minutes=60
        )
        
        # Volume confirmation
        volume_avg = Indicators.volume_average(candles_1h, period=20)
        current_volume = candles_1h[-1].volume
        volume_sufficient = current_volume >= volume_avg * self.config.sib_volume_multiplier
        
        if not volume_sufficient:
            return None
        
        # Determine entry side
        side = None
        
        if trend_up and broke_up:
            side = Side.LONG
        elif trend_down and broke_down:
            side = Side.SHORT
        
        if side is None:
            return None
        
        # Calculate position sizing and risk parameters
        atr = Indicators.atr(candles_1h, self.config.atr_period)
        
        return self._calculate_execution_intent(
            timestamp=candles_1h[-1].timestamp,
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
        risk_pct = (self.config.sib_risk_pct_min + self.config.sib_risk_pct_max) / 2
        
        # Dynamic leverage based on volatility (lower volatility = higher leverage)
        # This is capped between sib_leverage_min and sib_leverage_max
        volatility_factor = atr / entry_price
        if volatility_factor > 0.03:  # High volatility
            leverage = self.config.sib_leverage_min
        elif volatility_factor < 0.015:  # Low volatility
            leverage = self.config.sib_leverage_max
        else:  # Medium volatility
            leverage = (self.config.sib_leverage_min + self.config.sib_leverage_max) / 2
        
        # Calculate stop loss based on ATR (typically 2-3 ATR)
        stop_distance_atr = 2.5
        
        if side == Side.LONG:
            stop = entry_price - (atr * stop_distance_atr)
            tp1 = entry_price + (abs(entry_price - stop) * self.config.sib_tp1_r)
            runner = entry_price + (abs(entry_price - stop) * self.config.sib_runner_r_min)
        else:  # SHORT
            stop = entry_price + (atr * stop_distance_atr)
            tp1 = entry_price - (abs(entry_price - stop) * self.config.sib_tp1_r)
            runner = entry_price - (abs(entry_price - stop) * self.config.sib_runner_r_min)
        
        # Calculate position size based on stop distance
        stop_distance = abs(entry_price - stop)
        risk_amount = account.equity * (risk_pct / 100)
        
        # Position size = risk amount / stop distance
        position_size_base = risk_amount / stop_distance
        
        # Apply leverage to get notional
        notional_usd = position_size_base * entry_price
        
        # Apply position size limits
        limited_notional, was_limited, limit_info = self.position_limiter.limit_position_size(
            notional_usd, account.equity, "SIB"
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
            leverage = leverage * 0.7
        
        return ExecutionIntent(
            timestamp=timestamp,
            engine=Engine.SIB,
            side=side,
            entry=entry_price,
            stop=stop,
            tp1=tp1,
            runner=runner,
            leverage_cap=leverage,
            notional_usd=notional_usd,
            risk_pct=risk_pct,
            symbol="BTCUSDT"
        )
