"""
Portfolio Manager - Multi-asset risk management
Manages exposure limits, correlation, and daily loss limits
"""

from typing import Dict, List, Optional
import numpy as np


class PortfolioManager:
    """
    Manages portfolio-level risk across multiple assets and timeframes
    """
    
    def __init__(self, max_portfolio_exposure: float = 0.80, max_concurrent_positions: int = 5):
        """
        Args:
            max_portfolio_exposure: Max % of capital that can be in positions (0.80 = 80%)
            max_concurrent_positions: Max number of positions across all assets/timeframes
        """
        self.max_portfolio_exposure = max_portfolio_exposure
        self.max_concurrent_positions = max_concurrent_positions
        
        # Daily tracking
        self.daily_start_balance = None
        self.daily_loss_limit_pct = 0.15  # -15% max loss per day
        self.daily_trades = []
        self.trading_paused = False
        
        # Position tracking
        self.active_positions = {}  # {(asset, timeframe): position_dict}
        
    def start_new_day(self, current_balance: float):
        """Mark start of new trading day"""
        self.daily_start_balance = current_balance
        self.daily_trades = []
        self.trading_paused = False
    
    def can_open_position(
        self, 
        asset: str, 
        timeframe: str,
        margin_required: float,
        current_balance: float,
        total_balance: float
    ) -> tuple[bool, str]:
        """
        Check if we can open a new position
        
        Returns:
            (can_open, reason)
        """
        # Check if trading paused due to daily loss limit
        if self.trading_paused:
            return False, "Trading paused - daily loss limit hit"
        
        # Check daily loss limit
        if self.daily_start_balance:
            daily_pnl = total_balance - self.daily_start_balance
            daily_loss_pct = (daily_pnl / self.daily_start_balance)
            if daily_loss_pct < -self.daily_loss_limit_pct:
                self.trading_paused = True
                return False, f"Daily loss limit hit: {daily_loss_pct*100:.1f}%"
        
        # Check max concurrent positions
        if len(self.active_positions) >= self.max_concurrent_positions:
            return False, f"Max concurrent positions ({self.max_concurrent_positions})"
        
        # Check if already have position on this asset+timeframe
        position_key = (asset, timeframe)
        if position_key in self.active_positions:
            return False, f"Already have {asset} {timeframe} position"
        
        # Check portfolio exposure
        current_exposure = sum(p['margin'] for p in self.active_positions.values())
        new_exposure = (current_exposure + margin_required) / total_balance
        
        if new_exposure > self.max_portfolio_exposure:
            return False, f"Portfolio exposure limit ({new_exposure*100:.1f}% > {self.max_portfolio_exposure*100:.0f}%)"
        
        return True, "OK"
    
    def register_position(
        self,
        asset: str,
        timeframe: str,
        margin: float,
        position_size: float,
        entry_price: float,
        tp_price: float,
        sl_price: float,
        leverage: float,
        confidence: float
    ):
        """Register a new position"""
        position_key = (asset, timeframe)
        self.active_positions[position_key] = {
            'asset': asset,
            'timeframe': timeframe,
            'margin': margin,
            'position_size': position_size,
            'entry_price': entry_price,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'leverage': leverage,
            'confidence': confidence
        }
    
    def close_position(self, asset: str, timeframe: str, pnl: float):
        """Remove position and record trade"""
        position_key = (asset, timeframe)
        if position_key in self.active_positions:
            del self.active_positions[position_key]
        
        self.daily_trades.append({'pnl': pnl})
    
    def get_portfolio_exposure(self, total_balance: float) -> float:
        """Get current portfolio exposure as percentage"""
        if total_balance <= 0:
            return 0.0
        
        total_margin = sum(p['margin'] for p in self.active_positions.values())
        return total_margin / total_balance
    
    def get_daily_stats(self) -> Dict:
        """Get daily trading statistics"""
        if not self.daily_start_balance:
            return {}
        
        total_pnl = sum(t['pnl'] for t in self.daily_trades)
        daily_return = (total_pnl / self.daily_start_balance) * 100
        
        return {
            'trades_today': len(self.daily_trades),
            'daily_pnl': total_pnl,
            'daily_return_pct': daily_return,
            'trading_paused': self.trading_paused,
            'active_positions': len(self.active_positions)
        }
    
    def calculate_position_sizing_multiplier(self, confidence: float, timeframe: str) -> float:
        """
        Calculate position size multiplier based on confidence and timeframe
        
        Higher confidence = bigger positions
        """
        # Base multiplier by timeframe (already in TIMEFRAME_CONFIGS)
        timeframe_base = {
            '15m': 0.5,
            '1h': 1.0,
            '4h': 1.5
        }.get(timeframe, 1.0)
        
        # Confidence multiplier
        if confidence >= 0.95:
            confidence_mult = 1.5  # Bet big on ultra-high confidence
        elif confidence >= 0.90:
            confidence_mult = 1.2
        elif confidence >= 0.85:
            confidence_mult = 1.0
        elif confidence >= 0.80:
            confidence_mult = 0.9
        else:
            confidence_mult = 0.8
        
        return timeframe_base * confidence_mult
    
    def get_stats(self) -> Dict:
        """Get comprehensive portfolio statistics"""
        return {
            'active_positions': len(self.active_positions),
            'max_positions': self.max_concurrent_positions,
            'max_exposure': self.max_portfolio_exposure,
            'daily_loss_limit': self.daily_loss_limit_pct,
            'trading_paused': self.trading_paused,
            'positions': list(self.active_positions.keys())
        }
