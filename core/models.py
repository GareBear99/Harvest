"""Core data models for HARVEST trading system."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Side(Enum):
    LONG = "long"
    SHORT = "short"


class Engine(Enum):
    ER90 = "ER-90"
    SIB = "SIB"
    SCALPER = "SCALPER"
    MOMENTUM = "MOMENTUM"
    IDLE = "IDLE"


class Regime(Enum):
    RANGE = "range"
    WEAK_TREND = "weak_trend"
    STRONG_TREND = "strong_trend"
    DRAWDOWN = "drawdown"


@dataclass
class OHLCV:
    """OHLCV candle data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class ExecutionIntent:
    """Execution intent object - never executes in test mode."""
    timestamp: datetime
    engine: Engine
    side: Side
    entry: float
    stop: float
    tp1: float
    runner: Optional[float]
    leverage_cap: float
    notional_usd: float
    risk_pct: float
    symbol: str
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "engine": self.engine.value,
            "side": self.side.value,
            "entry": self.entry,
            "stop": self.stop,
            "tp1": self.tp1,
            "runner": self.runner,
            "leverage_cap": self.leverage_cap,
            "notional_usd": self.notional_usd,
            "risk_pct": self.risk_pct,
            "symbol": self.symbol,
        }


@dataclass
class MarketState:
    """Current market state with indicators."""
    timestamp: datetime
    close: float
    rsi: float
    atr: float
    ema50: float
    ema200: float
    adx: float
    volume: float
    volume_avg: float
    regime: Regime


@dataclass
class AccountState:
    """Account state for risk management."""
    equity: float
    daily_pnl: float
    daily_pnl_pct: float
    consecutive_losses: int
    trades_today: dict  # {Engine: count}
    losses_today: dict  # {Engine: count}
    mode: Engine  # Current active engine or IDLE


@dataclass
class Config:
    """System configuration."""
    # Account
    initial_equity: float = 10000.0
    max_daily_drawdown_pct: float = 3.5  # OPTIMIZED: Increased from 2.0 to allow more trading
    max_consecutive_losses: int = 3  # OPTIMIZED: Increased from 2 to 3
    
    # ER-90 parameters
    er90_leverage_min: float = 10.0
    er90_leverage_max: float = 20.0
    er90_risk_pct_min: float = 0.25
    er90_risk_pct_max: float = 0.5
    er90_tp_pct_min: float = 0.8  # OPTIMIZED: Increased from 0.2 to improve R:R
    er90_tp_pct_max: float = 1.2  # OPTIMIZED: Increased from 0.4 to improve R:R
    er90_sl_pct_min: float = 0.6  # OPTIMIZED: Tightened from 1.2 for better R:R
    er90_sl_pct_max: float = 0.9  # OPTIMIZED: Tightened from 1.8 for better R:R
    er90_max_losses_per_day: int = 1
    er90_max_trades_per_day: int = 3  # OPTIMIZED: Allow multiple trades per day
    er90_impulse_atr_min: float = 1.0  # Relaxed from 1.5 for more opportunities
    er90_impulse_atr_max: float = 2.0
    er90_rsi_upper: float = 65.0  # OPTIMIZED: Relaxed from 70 to 65 for more signals
    er90_rsi_lower: float = 35.0  # OPTIMIZED: Relaxed from 30 to 35 for more signals
    
    # SIB parameters
    sib_leverage_min: float = 20.0
    sib_leverage_max: float = 40.0
    sib_risk_pct_min: float = 0.5
    sib_risk_pct_max: float = 1.0
    sib_tp1_r: float = 1.5
    sib_runner_r_min: float = 3.0
    sib_runner_r_max: float = 5.0
    sib_max_trades_per_day: int = 1
    sib_adx_threshold: float = 15.0  # OPTIMIZED: Lowered from 20 to 15 for current market conditions
    sib_volume_multiplier: float = 1.5
    
    # Indicator periods
    rsi_period: int = 5
    atr_period: int = 14
    ema50_period: int = 50
    ema200_period: int = 200
    adx_period: int = 14
    
    # Liquidation buffer
    liquidation_buffer_pct: float = 3.0  # OPTIMIZED: Reduced from 10.0 to allow trades (was blocking all signals)
    
    # Hyperliquid/Leverage Trading Settings
    use_hyperliquid: bool = False  # Enable Hyperliquid leveraged trading
    hyperliquid_testnet: bool = True  # Use testnet (True) or mainnet (False)
    min_position_size_usd: float = 10.0  # Minimum position size
    max_position_size_usd: float = 1000.0  # Maximum position size
    enable_paper_leverage: bool = True  # Simulate leverage trades without real execution
    
    # Small Capital Adjustments (for $10-100 range)
    small_capital_mode: bool = False  # Enable optimizations for <$100 capital
    small_capital_risk_pct: float = 5.0  # Higher risk % needed for viability with small capital
    small_capital_max_loss_pct: float = 20.0  # Daily loss limit for small capital
    
    # Gas Cost Protection
    min_profit_to_gas_ratio: float = 5.0  # Min expected profit should be 5x gas cost
    
    # Scalper parameters (high-frequency for hourly gains with small capital)
    scalper_leverage: float = 20.0
    scalper_risk_pct: float = 1.0  # Higher risk per trade for small frequent gains
    scalper_tp_pct: float = 0.4  # Quick 0.4% profit targets
    scalper_sl_pct: float = 0.3  # Tight 0.3% stop losses
    scalper_max_trades_per_day: int = 20  # High frequency trading
    
    # Momentum parameters (EMA crosses for 0.5-1% moves)
    momentum_leverage: float = 20.0
    momentum_risk_pct: float = 0.8
    momentum_tp_pct: float = 0.7  # 0.7% targets
    momentum_sl_pct: float = 0.4  # 0.4% stops
    momentum_max_trades_per_day: int = 15
