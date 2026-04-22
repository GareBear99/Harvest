"""Risk governance module - mandatory safety constraints."""
from typing import Optional
from .models import AccountState, ExecutionIntent, Engine, Config, Regime


class RiskGovernor:
    """
    Enforce mandatory risk rules. 
    System enters IDLE mode on any breach.
    """
    
    def __init__(self, config: Config):
        self.config = config
    
    def validate_account_state(self, account: AccountState) -> bool:
        """
        Check if account is within risk limits.
        
        Returns:
            True if safe to trade, False if must enter IDLE
        """
        # Check daily drawdown limit
        if account.daily_pnl_pct <= -self.config.max_daily_drawdown_pct:
            print(f"⚠️  RISK BREACH: Daily drawdown {account.daily_pnl_pct:.2f}% exceeds limit")
            return False
        
        # Check consecutive losses
        if account.consecutive_losses >= self.config.max_consecutive_losses:
            print(f"⚠️  RISK BREACH: {account.consecutive_losses} consecutive losses")
            return False
        
        return True
    
    def validate_execution_intent(self, intent: ExecutionIntent, 
                                 account: AccountState) -> bool:
        """
        Validate execution intent before allowing trade.
        
        Args:
            intent: Proposed execution intent
            account: Current account state
        
        Returns:
            True if intent is safe, False otherwise
        """
        # Stop loss must always be present
        if intent.stop is None or intent.stop == 0:
            print("⚠️  RISK BREACH: Stop loss missing")
            return False
        
        # Validate stop loss is in correct direction
        if intent.side.value == "long" and intent.stop >= intent.entry:
            print("⚠️  RISK BREACH: Stop loss invalid for LONG")
            return False
        
        if intent.side.value == "short" and intent.stop <= intent.entry:
            print("⚠️  RISK BREACH: Stop loss invalid for SHORT")
            return False
        
        # Validate risk percentage
        if intent.risk_pct > 1.0:  # Max 1% per trade
            print(f"⚠️  RISK BREACH: Risk {intent.risk_pct}% exceeds 1%")
            return False
        
        # Validate liquidation buffer
        stop_distance_pct = abs(intent.entry - intent.stop) / intent.entry * 100
        liq_distance_pct = 100 / intent.leverage_cap
        
        buffer_pct = abs(liq_distance_pct - stop_distance_pct)
        
        if buffer_pct < self.config.liquidation_buffer_pct:
            print(f"⚠️  RISK BREACH: Insufficient liquidation buffer ({buffer_pct:.1f}%)")
            return False
        
        # Validate position sizing
        max_notional = account.equity * intent.leverage_cap
        if intent.notional_usd > max_notional * 0.5:  # Max 50% of leveraged capital
            print(f"⚠️  RISK BREACH: Position size too large")
            return False
        
        return True
    
    def determine_active_engine(self, regime: Regime, account: AccountState) -> Engine:
        """
        Determine which engine should be active based on regime.
        Enforces mutual exclusivity - only one engine can be active.
        
        Args:
            regime: Current market regime
            account: Account state
        
        Returns:
            Active engine (ER90, SIB, or IDLE)
        """
        # First check account state
        if not self.validate_account_state(account):
            return Engine.IDLE
        
        # Regime-based engine selection
        if regime == Regime.DRAWDOWN:
            return Engine.IDLE
        
        elif regime == Regime.STRONG_TREND:
            # Enable SIB, disable ER-90
            return Engine.SIB
        
        elif regime == Regime.WEAK_TREND:
            # Could enable either, but prefer ER-90 for safety
            # In practice, both could have allocation, but only one trades at a time
            return Engine.ER90
        
        else:  # RANGE
            # Enable ER-90, disable SIB
            return Engine.ER90
    
    def record_trade_outcome(self, account: AccountState, engine: Engine, 
                           is_loss: bool) -> AccountState:
        """
        Update account state after trade outcome.
        
        Args:
            account: Current account state
            engine: Engine that took the trade
            is_loss: Whether trade was a loss
        
        Returns:
            Updated account state
        """
        # Update trade counts
        if engine not in account.trades_today:
            account.trades_today[engine] = 0
        account.trades_today[engine] += 1
        
        # Update loss tracking
        if is_loss:
            if engine not in account.losses_today:
                account.losses_today[engine] = 0
            account.losses_today[engine] += 1
            account.consecutive_losses += 1
        else:
            account.consecutive_losses = 0
        
        return account
