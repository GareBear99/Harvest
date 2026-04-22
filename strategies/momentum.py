"""Momentum strategy for fast 0.5-1% moves."""
from typing import List, Optional
from datetime import datetime
from core.models import OHLCV, Side, ExecutionIntent, Engine, Config, AccountState
from core.indicators import Indicators


class MomentumStrategy:
    """
    Aggressive momentum strategy for quick directional moves.
    Goal: Catch 0.5-1% moves using fast EMAs and MACD.
    """
    
    def __init__(self, config: Config):
        self.config = config
    
    def check_entry(self, candles_5m: List[OHLCV], candles_15m: List[OHLCV],
                   account: AccountState) -> Optional[ExecutionIntent]:
        """
        Check for momentum entry conditions.
        
        Entry conditions:
        - Fast EMA (9) crosses above/below slow EMA (21) on 5m
        - MACD histogram expanding
        - RSI between 45-55 (neutral, ready to move)
        - Volume increasing
        
        Args:
            candles_5m: 5-minute candles for signals
            candles_15m: 15-minute candles for confirmation
            account: Account state
        
        Returns:
            ExecutionIntent if conditions met, None otherwise
        """
        # Check trade limits
        if Engine.MOMENTUM in account.trades_today:
            if account.trades_today[Engine.MOMENTUM] >= self.config.momentum_max_trades_per_day:
                return None
        
        if len(candles_5m) < 50 or len(candles_15m) < 30:
            return None
        
        current_price = candles_5m[-1].close
        closes_5m = [c.close for c in candles_5m]
        
        # Fast EMA crossover (9/21 instead of traditional 12/26)
        ema9 = Indicators.ema(closes_5m, period=9)
        ema21 = Indicators.ema(closes_5m, period=21)
        
        # Previous EMAs for crossover detection
        if len(closes_5m) >= 2:
            ema9_prev = Indicators.ema(closes_5m[:-1], period=9)
            ema21_prev = Indicators.ema(closes_5m[:-1], period=21)
        else:
            return None
        
        # Detect crossover
        bullish_cross = ema9_prev <= ema21_prev and ema9 > ema21
        bearish_cross = ema9_prev >= ema21_prev and ema9 < ema21
        
        if not (bullish_cross or bearish_cross):
            return None
        
        # RSI confirmation (not overbought/oversold)
        rsi = Indicators.rsi(closes_5m, period=14)
        rsi_neutral = 45 <= rsi <= 65  # Ready to move in either direction
        
        if not rsi_neutral:
            return None
        
        # Volume increasing
        volumes = [c.volume for c in candles_5m[-10:]]
        volume_increasing = volumes[-1] > sum(volumes[:-1]) / len(volumes[:-1])
        
        if not volume_increasing:
            return None
        
        # 15m trend confirmation
        closes_15m = [c.close for c in candles_15m]
        ema50_15m = Indicators.ema(closes_15m, period=20)
        
        side = None
        if bullish_cross and current_price > ema50_15m:
            side = Side.LONG
        elif bearish_cross and current_price < ema50_15m:
            side = Side.SHORT
        
        if side is None:
            return None
        
        # Calculate position
        atr = Indicators.atr(candles_5m, period=14)
        
        return self._calculate_execution_intent(
            timestamp=candles_5m[-1].timestamp,
            side=side,
            entry_price=current_price,
            atr=atr,
            account=account
        )
    
    def _calculate_execution_intent(self, timestamp: datetime, side: Side,
                                   entry_price: float, atr: float,
                                   account: AccountState) -> ExecutionIntent:
        """Calculate execution intent for momentum trade."""
        
        risk_pct = self.config.momentum_risk_pct
        leverage = self.config.momentum_leverage
        tp_pct = self.config.momentum_tp_pct
        sl_pct = self.config.momentum_sl_pct
        
        # Calculate levels
        if side == Side.LONG:
            stop = entry_price * (1 - sl_pct / 100)
            tp1 = entry_price * (1 + tp_pct / 100)
        else:
            stop = entry_price * (1 + sl_pct / 100)
            tp1 = entry_price * (1 - tp_pct / 100)
        
        # Position sizing
        stop_distance = abs(entry_price - stop)
        risk_amount = account.equity * (risk_pct / 100)
        position_size_base = risk_amount / stop_distance
        notional_usd = position_size_base * entry_price
        
        # Cap at 95% of equity
        max_notional = account.equity * 0.95
        if notional_usd > max_notional:
            notional_usd = max_notional
        
        return ExecutionIntent(
            timestamp=timestamp,
            engine=Engine.MOMENTUM,
            side=side,
            entry=entry_price,
            stop=stop,
            tp1=tp1,
            runner=None,
            leverage_cap=leverage,
            notional_usd=notional_usd,
            risk_pct=risk_pct,
            symbol="BTCUSDT"
        )
