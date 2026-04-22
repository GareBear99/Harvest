"""
Tier Manager - Multi-tier risk management system
Manages tier selection, transitions, and tier-specific parameters
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class TierConfig:
    """Configuration for a trading tier"""
    tier_id: int
    name: str
    leverage: int
    position_size_pct: float
    tp_pct: float
    sl_pct: float
    check_interval_minutes: int
    max_risk_per_trade_pct: float
    min_adx: float = 20.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tier_id': self.tier_id,
            'name': self.name,
            'leverage': self.leverage,
            'position_size_pct': self.position_size_pct,
            'tp_pct': self.tp_pct,
            'sl_pct': self.sl_pct,
            'check_interval_minutes': self.check_interval_minutes,
            'max_risk_per_trade_pct': self.max_risk_per_trade_pct,
            'min_adx': self.min_adx
        }


class TierManager:
    """
    Manages tier transitions and configurations
    
    Four tiers:
    - Tier 0: Recovery (< $10) - Rebuild with ultra-conservative approach
    - Tier 1: Accumulation ($10-30) - Aggressive growth phase
    - Tier 2: Growth ($30-70) - Balanced growth with first profit lock
    - Tier 3: Preservation ($70+) - Capital preservation with full locks
    """
    
    def __init__(self):
        # Define tier configurations
        self.tiers = {
            0: TierConfig(
                tier_id=0,
                name="Recovery",
                leverage=15,
                position_size_pct=0.40,
                tp_pct=0.003,  # 0.3%
                sl_pct=0.002,  # 0.2%
                check_interval_minutes=15,
                max_risk_per_trade_pct=1.2,
                min_adx=25.0  # Only best setups
            ),
            1: TierConfig(
                tier_id=1,
                name="Accumulation",
                leverage=25,
                position_size_pct=0.60,
                tp_pct=0.004,  # 0.4%
                sl_pct=0.0025,  # 0.25%
                check_interval_minutes=5,
                max_risk_per_trade_pct=3.75
            ),
            2: TierConfig(
                tier_id=2,
                name="Growth",
                leverage=15,
                position_size_pct=0.40,
                tp_pct=0.005,  # 0.5%
                sl_pct=0.003,  # 0.3%
                check_interval_minutes=10,
                max_risk_per_trade_pct=1.8
            ),
            3: TierConfig(
                tier_id=3,
                name="Preservation",
                leverage=8,
                position_size_pct=0.30,
                tp_pct=0.006,  # 0.6%
                sl_pct=0.004,  # 0.4%
                check_interval_minutes=15,
                max_risk_per_trade_pct=0.96
            )
        }
        
        # Tier thresholds
        self.tier_thresholds = {
            0: (0, 10),      # Recovery: $0 to $10
            1: (10, 30),     # Accumulation: $10 to $30
            2: (30, 70),     # Growth: $30 to $70
            3: (70, float('inf'))  # Preservation: $70+
        }
        
        # Lock thresholds for each tier
        self.lock_thresholds = {
            0: 0,   # No lock in recovery
            1: 0,   # No lock in accumulation (need growth first)
            2: 15,  # Lock $15 when entering tier 2
            3: 35   # Lock $35 when entering tier 3
        }
        
        # Track current state
        self.current_tier = None
        self.locked_balance = 0
        self.tier_entry_balance = None
        self.tier_transitions = []  # History of tier changes
        
    def get_tier(self, balance: float) -> int:
        """Determine current tier based on balance"""
        if balance < 10:
            return 0
        elif balance < 30:
            return 1
        elif balance < 70:
            return 2
        else:
            return 3
    
    def update_tier(self, balance: float) -> Dict[str, Any]:
        """
        Update tier and locked balance based on current balance
        Returns dict with transition info
        """
        new_tier = self.get_tier(balance)
        
        transition_info = {
            'tier_changed': False,
            'old_tier': self.current_tier,
            'new_tier': new_tier,
            'locked_balance': self.locked_balance,
            'balance': balance,
            'tradeable_balance': balance - self.locked_balance
        }
        
        # Check if tier changed
        if self.current_tier != new_tier:
            transition_info['tier_changed'] = True
            
            # Update locked balance based on new tier
            new_lock = self.lock_thresholds.get(new_tier, 0)
            if new_lock > self.locked_balance:
                self.locked_balance = new_lock
                transition_info['locked_balance'] = self.locked_balance
                transition_info['lock_increased'] = True
            
            # Record transition
            self.tier_transitions.append({
                'from_tier': self.current_tier,
                'to_tier': new_tier,
                'balance': balance,
                'locked_balance': self.locked_balance
            })
            
            # Update current tier
            self.current_tier = new_tier
            self.tier_entry_balance = balance
        
        return transition_info
    
    def get_config(self, tier: int = None) -> TierConfig:
        """Get configuration for specified tier (or current tier)"""
        if tier is None:
            tier = self.current_tier
        
        if tier is None:
            tier = 0  # Default to recovery if not set
        
        return self.tiers[tier]
    
    def get_tradeable_balance(self, total_balance: float) -> float:
        """Calculate tradeable balance after locked funds"""
        return max(0, total_balance - self.locked_balance)
    
    def should_check_entry(self, minutes_since_last: int, regime: str) -> bool:
        """
        Determine if we should check for entry based on tier and regime
        Returns True if enough time has passed
        """
        config = self.get_config()
        base_interval = config.check_interval_minutes
        
        # Adjust by regime
        if regime == 'BEAR':
            interval = base_interval  # Full frequency in BEAR
        elif regime == 'BULL':
            interval = base_interval * 2  # Half frequency in BULL
        else:  # RANGE
            interval = base_interval * 3  # 1/3 frequency in RANGE
        
        return minutes_since_last >= interval
    
    def get_daily_loss_limit(self) -> float:
        """Get daily loss limit as percentage for current tier"""
        limits = {
            0: 0.08,  # 8% for recovery
            1: 0.10,  # 10% for accumulation
            2: 0.05,  # 5% for growth
            3: 0.03   # 3% for preservation
        }
        return limits.get(self.current_tier, 0.10)
    
    def get_leverage_for_balance(self, balance: float) -> int:
        """
        Get progressive leverage based on balance
        More granular than tier-based for smoother transitions
        """
        if balance < 10:
            return 15  # Recovery
        elif balance < 30:
            return 25  # Accumulation
        elif balance < 50:
            return 20
        elif balance < 70:
            return 15
        elif balance < 100:
            return 10
        elif balance < 150:
            return 8
        else:
            return 5  # Maximum safety
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tier manager statistics"""
        return {
            'current_tier': self.current_tier,
            'tier_name': self.tiers[self.current_tier].name if self.current_tier is not None else 'None',
            'locked_balance': self.locked_balance,
            'tier_entry_balance': self.tier_entry_balance,
            'num_transitions': len(self.tier_transitions),
            'transitions': self.tier_transitions
        }
    
    def reset(self):
        """Reset tier manager state"""
        self.current_tier = None
        self.locked_balance = 0
        self.tier_entry_balance = None
        self.tier_transitions = []


# Testing
if __name__ == "__main__":
    tm = TierManager()
    
    print("=== TIER MANAGER TEST ===\n")
    
    # Simulate balance growth
    balances = [8, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 100, 150, 200]
    
    for balance in balances:
        info = tm.update_tier(balance)
        
        if info['tier_changed']:
            config = tm.get_config()
            print(f"\n💫 TIER TRANSITION at ${balance:.2f}")
            print(f"   {info['old_tier']} → {info['new_tier']} ({config.name})")
            print(f"   Leverage: {config.leverage}×")
            print(f"   Position Size: {config.position_size_pct*100:.0f}%")
            print(f"   TP/SL: {config.tp_pct*100:.2f}% / {config.sl_pct*100:.2f}%")
            print(f"   Check Interval: {config.check_interval_minutes} min")
            print(f"   Locked: ${info['locked_balance']:.2f}")
            print(f"   Tradeable: ${info['tradeable_balance']:.2f}")
    
    print("\n=== FINAL STATS ===")
    stats = tm.get_stats()
    print(f"Current Tier: {stats['tier_name']}")
    print(f"Locked Balance: ${stats['locked_balance']:.2f}")
    print(f"Total Transitions: {stats['num_transitions']}")
