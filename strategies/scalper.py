"""Scalper strategy for high-frequency trading with small gains."""
from typing import List, Optional
from datetime import datetime
from core.models import OHLCV, Side, ExecutionIntent, Engine, Config, AccountState
from core.indicators import Indicators


class ScalperStrategy:
    """
    High-frequency scalping strategy for hourly gains.
    Goal: 0.3-0.5% gains per trade, high frequency (10-20 trades/day).
    """
    
    def __init__(self, config: Config):
        self.config = config
    
    def check_entry(self, candles_5m: List[OHLCV], candles_1h: List[OHLCV],
                   account: AccountState) -> Optional[ExecutionIntent]:
        """
        Check for scalping entry conditions.
        
        Entry conditions (simplified for speed):
        - Quick momentum shift (RSI cross 50)
        - Price near EMA20 (5m)
        - Volume confirmation
        
        Args:
            candles_5m: 5-minute candles
            candles_1h: 1-hour candles for context
            account: Account state
        
        Returns:
            ExecutionIntent if conditions met, None otherwise
        """
        # Check if already hit max trades today
        if Engine.SCALPER in account.trades_today:
            if account.trades_today[Engine.SCALPER] >= self.config.scalper_max_trades_per_day:
                return None
        
        # Need sufficient data
        if len(candles_5m) < 50 or len(candles_1h) < 20:
            return None
        
        current_price = candles_5m[-1].close
        
        # Calculate 5m indicators for quick signals
        closes_5m = [c.close for c in candles_5m]
        rsi_5m = Indicators.rsi(closes_5m, period=7)  # Faster RSI
        ema20_5m = Indicators.ema(closes_5m, period=20)
        
        # Volume confirmation
        volume_avg = Indicators.volume_average(candles_5m, period=10)
        current_volume = candles_5m[-1].volume
        volume_ok = current_volume >= volume_avg * 0.8  # Lower threshold
        
        if not volume_ok:
            return None
        
        # Price near EMA20 (within 0.2%)
        price_distance = abs(current_price - ema20_5m) / current_price
        near_ema = price_distance < 0.002
        
        # Determine entry side based on RSI momentum
        side = None
        
        # LONG: RSI crossing above 50 (bullish momentum)
        if len(closes_5m) >= 2:
            rsi_prev = Indicators.rsi(closes_5m[:-1], period=7)
            
            if rsi_prev < 50 and rsi_5m >= 50 and near_ema:
                side = Side.LONG
            elif rsi_prev > 50 and rsi_5m <= 50 and near_ema:
                side = Side.SHORT
        
        if side is None:
            return None
        
        # Calculate position sizing
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
        """Calculate execution intent for scalping."""
        
        # Aggressive parameters for scalping
        risk_pct = self.config.scalper_risk_pct
        leverage = self.config.scalper_leverage
        tp_pct = self.config.scalper_tp_pct
        sl_pct = self.config.scalper_sl_pct
        
        # Calculate stop loss and take profit
        if side == Side.LONG:
            stop = entry_price * (1 - sl_pct / 100)
            tp1 = entry_price * (1 + tp_pct / 100)
        else:  # SHORT
            stop = entry_price * (1 + sl_pct / 100)
            tp1 = entry_price * (1 - tp_pct / 100)
        
        # Calculate position size
        stop_distance = abs(entry_price - stop)
        risk_amount = account.equity * (risk_pct / 100)
        position_size_base = risk_amount / stop_distance
        notional_usd = position_size_base * entry_price
        
        # Cap notional at 95% of equity for small capital
        max_notional = account.equity * 0.95
        if notional_usd > max_notional:
            notional_usd = max_notional
        
        return ExecutionIntent(
            timestamp=timestamp,
            engine=Engine.SCALPER,
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
