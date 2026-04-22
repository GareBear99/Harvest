"""
Position Sizer - Kelly Criterion based position sizing
Implements Half Kelly with tier-based caps and volatility adjustments
"""

from typing import Dict, Any


class PositionSizer:
    """
    Manages position sizing using Kelly Criterion
    
    Formula: f = (p*b - q) / b
    where:
    - p = win rate
    - q = loss rate (1 - p)
    - b = win/loss ratio
    - f = fraction of capital to risk
    
    Uses Half Kelly for conservative approach
    """
    
    def __init__(self, min_position: float = 5.0):
        """
        Args:
            min_position: Minimum position size in dollars
        """
        self.min_position = min_position
        
        # Track historical performance for Kelly calculation
        self.wins = []
        self.losses = []
        self.total_trades = 0
        
        # Default stats (optimistic initial values)
        self.win_rate = 0.60
        self.avg_win = 0.10  # 10% avg win
        self.avg_loss = 0.06  # 6% avg loss (1.67:1 risk/reward)
    
    def update_performance(self, pnl_pct: float):
        """Update performance tracking with trade result"""
        self.total_trades += 1
        
        if pnl_pct > 0:
            self.wins.append(pnl_pct)
        else:
            self.losses.append(abs(pnl_pct))
        
        # Recalculate statistics (use last 20 trades for relevance)
        recent_wins = self.wins[-20:] if len(self.wins) > 0 else []
        recent_losses = self.losses[-20:] if len(self.losses) > 0 else []
        
        total_recent = len(recent_wins) + len(recent_losses)
        
        if total_recent >= 5:  # Need at least 5 trades for stats
            self.win_rate = len(recent_wins) / total_recent
            self.avg_win = sum(recent_wins) / len(recent_wins) if recent_wins else 0.10
            self.avg_loss = sum(recent_losses) / len(recent_losses) if recent_losses else 0.06
    
    def calculate_kelly(self) -> float:
        """
        Calculate Kelly Criterion percentage
        Returns fraction of capital to risk (0 to 1)
        """
        if self.avg_win <= 0:
            return 0.0
        
        # Kelly formula: (p*b - q) / b
        # where b = avg_win / avg_loss
        p = self.win_rate
        q = 1 - self.win_rate
        b = self.avg_win / self.avg_loss if self.avg_loss > 0 else 1.67
        
        kelly = (p * b - q) / b
        
        # Never negative
        kelly = max(0, kelly)
        
        # Half Kelly for conservative approach
        half_kelly = kelly / 2
        
        # Cap at 80% (even Half Kelly can be aggressive)
        return min(half_kelly, 0.80)
    
    def calculate_position_size(
        self, 
        balance: float, 
        tier_config: Any,
        current_atr: float = None,
        avg_atr: float = None
    ) -> Dict[str, Any]:
        """
        Calculate position size based on Kelly + tier constraints
        
        Args:
            balance: Current account balance
            tier_config: TierConfig object with tier parameters
            current_atr: Current ATR value (for volatility adjustment)
            avg_atr: Average ATR value (for volatility adjustment)
        
        Returns:
            Dict with position size and metadata
        """
        # Get Kelly fraction
        kelly_fraction = self.calculate_kelly()
        
        # Get tier-based maximum
        tier_max_pct = tier_config.position_size_pct
        
        # Use minimum of Kelly and Tier cap
        position_pct = min(kelly_fraction, tier_max_pct)
        
        # Calculate base position size
        position_size = balance * position_pct
        
        # Apply volatility adjustment if ATR data provided
        if current_atr is not None and avg_atr is not None:
            volatility_multiplier = self._get_volatility_multiplier(current_atr, avg_atr)
            position_size *= volatility_multiplier
        else:
            volatility_multiplier = 1.0
        
        # Enforce minimum
        position_size = max(position_size, self.min_position)
        
        # Never exceed balance
        position_size = min(position_size, balance)
        
        return {
            'position_size': position_size,
            'position_pct': position_size / balance,
            'kelly_fraction': kelly_fraction,
            'tier_max_pct': tier_max_pct,
            'volatility_multiplier': volatility_multiplier,
            'limited_by': self._get_limiting_factor(kelly_fraction, tier_max_pct, position_size)
        }
    
    def _get_volatility_multiplier(self, current_atr: float, avg_atr: float) -> float:
        """
        Adjust position size based on volatility
        High volatility = reduce position
        Low volatility = increase position
        """
        if avg_atr <= 0:
            return 1.0
        
        volatility_ratio = current_atr / avg_atr
        
        if volatility_ratio > 1.5:
            # High volatility: reduce by 30%
            return 0.7
        elif volatility_ratio > 1.2:
            # Elevated volatility: reduce by 15%
            return 0.85
        elif volatility_ratio < 0.7:
            # Low volatility: increase by 20%
            return 1.2
        elif volatility_ratio < 0.85:
            # Below average volatility: increase by 10%
            return 1.1
        else:
            # Normal volatility: no adjustment
            return 1.0
    
    def _get_limiting_factor(self, kelly: float, tier_max: float, position: float) -> str:
        """Determine what limited the position size"""
        if position <= self.min_position:
            return 'minimum'
        elif kelly <= tier_max:
            return 'kelly'
        else:
            return 'tier_cap'
    
    def get_stats(self) -> Dict[str, Any]:
        """Get position sizer statistics"""
        return {
            'total_trades': self.total_trades,
            'total_wins': len(self.wins),
            'total_losses': len(self.losses),
            'win_rate': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'risk_reward_ratio': self.avg_win / self.avg_loss if self.avg_loss > 0 else 0,
            'kelly_fraction': self.calculate_kelly(),
            'half_kelly': self.calculate_kelly()  # Already halved
        }
    
    def reset(self):
        """Reset position sizer state"""
        self.wins = []
        self.losses = []
        self.total_trades = 0
        self.win_rate = 0.60
        self.avg_win = 0.10
        self.avg_loss = 0.06


# Testing
if __name__ == "__main__":
    from tier_manager import TierManager, TierConfig
    
    print("=== POSITION SIZER TEST ===\n")
    
    # Create instances
    ps = PositionSizer()
    tm = TierManager()
    
    # Simulate trades at different balances
    test_scenarios = [
        {'balance': 10, 'trades': [(0.08, True), (0.05, True), (-0.04, False)]},
        {'balance': 20, 'trades': [(0.09, True), (-0.05, False), (0.10, True)]},
        {'balance': 40, 'trades': [(0.07, True), (0.08, True), (0.06, True)]},
        {'balance': 80, 'trades': [(0.05, True), (-0.03, False), (0.06, True)]}
    ]
    
    for scenario in test_scenarios:
        balance = scenario['balance']
        trades = scenario['trades']
        
        # Update tier
        tm.update_tier(balance)
        config = tm.get_config()
        
        print(f"\n{'='*60}")
        print(f"Balance: ${balance:.2f} | Tier: {config.name} ({config.tier_id})")
        print(f"{'='*60}")
        
        # Process trades
        for pnl_pct, is_win in trades:
            # Update performance
            ps.update_performance(pnl_pct if is_win else -pnl_pct)
            
            # Calculate position size
            result = ps.calculate_position_size(balance, config)
            
            print(f"\n{'✅ WIN' if is_win else '❌ LOSS'}: {pnl_pct*100:+.1f}%")
            print(f"  Position Size: ${result['position_size']:.2f} ({result['position_pct']*100:.1f}%)")
            print(f"  Kelly Fraction: {result['kelly_fraction']*100:.1f}%")
            print(f"  Tier Max: {result['tier_max_pct']*100:.1f}%")
            print(f"  Limited By: {result['limited_by']}")
    
    # Final stats
    print(f"\n{'='*60}")
    print("FINAL POSITION SIZER STATS")
    print(f"{'='*60}")
    stats = ps.get_stats()
    print(f"Total Trades: {stats['total_trades']}")
    print(f"Win Rate: {stats['win_rate']*100:.1f}%")
    print(f"Avg Win: {stats['avg_win']*100:.1f}%")
    print(f"Avg Loss: {stats['avg_loss']*100:.1f}%")
    print(f"Risk/Reward: {stats['risk_reward_ratio']:.2f}")
    print(f"Kelly Fraction: {stats['kelly_fraction']*100:.1f}%")
