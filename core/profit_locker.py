"""
Profit Locker - Milestone-based profit locking system
Locks profits at predetermined milestones to prevent boom-bust cycles
"""

from typing import Dict, Any, List, Tuple


class ProfitLocker:
    """
    Manages milestone-based profit locking
    
    Locks portions of balance at growth milestones:
    - $20 (2x): Lock $10 (50% of gains)
    - $40 (4x): Lock $20 (50% of gains)
    - $80 (8x): Lock $40 (50% of gains)
    - $160 (16x): Lock $80 (50% of gains)
    """
    
    def __init__(self, initial_balance: float = 10.0):
        """
        Args:
            initial_balance: Starting balance for calculating multiples
        """
        self.initial_balance = initial_balance
        self.locked_balance = 0.0
        
        # Define milestones: (balance_threshold, lock_amount)
        self.milestones = [
            (20, 10),   # At $20 (2x), lock $10
            (40, 20),   # At $40 (4x), lock $20
            (80, 40),   # At $80 (8x), lock $40
            (160, 80),  # At $160 (16x), lock $80
            (320, 160), # At $320 (32x), lock $160
            (640, 320), # At $640 (64x), lock $320
        ]
        
        # Track which milestones have been reached
        self.reached_milestones = []
        
        # Track lock events
        self.lock_events = []
    
    def check_and_lock(self, current_balance: float) -> Dict[str, Any]:
        """
        Check if any milestones reached and update locked balance
        
        Args:
            current_balance: Current total balance
        
        Returns:
            Dict with lock status and events
        """
        result = {
            'locked': False,
            'locked_balance': self.locked_balance,
            'tradeable_balance': self.get_tradeable_balance(current_balance),
            'milestone_reached': None,
            'lock_amount': 0
        }
        
        # Check each milestone
        for milestone_balance, lock_amount in self.milestones:
            # Skip if already reached
            if milestone_balance in self.reached_milestones:
                continue
            
            # Check if milestone reached
            if current_balance >= milestone_balance:
                # Only increase lock (never decrease)
                if lock_amount > self.locked_balance:
                    old_locked = self.locked_balance
                    self.locked_balance = lock_amount
                    
                    # Record milestone
                    self.reached_milestones.append(milestone_balance)
                    
                    # Record event
                    event = {
                        'milestone': milestone_balance,
                        'balance': current_balance,
                        'locked_amount': lock_amount,
                        'locked_increase': lock_amount - old_locked,
                        'multiple': current_balance / self.initial_balance
                    }
                    self.lock_events.append(event)
                    
                    # Update result
                    result['locked'] = True
                    result['locked_balance'] = self.locked_balance
                    result['tradeable_balance'] = self.get_tradeable_balance(current_balance)
                    result['milestone_reached'] = milestone_balance
                    result['lock_amount'] = lock_amount
                    
                    break  # Only process one milestone per check
        
        return result
    
    def get_tradeable_balance(self, total_balance: float) -> float:
        """
        Calculate balance available for trading
        
        Args:
            total_balance: Total account balance
        
        Returns:
            Balance available for trading (total - locked)
        """
        tradeable = total_balance - self.locked_balance
        
        # Never negative
        return max(0, tradeable)
    
    def get_locked_percentage(self, total_balance: float) -> float:
        """
        Calculate percentage of balance that is locked
        
        Args:
            total_balance: Total account balance
        
        Returns:
            Percentage locked (0 to 1)
        """
        if total_balance <= 0:
            return 0.0
        
        return self.locked_balance / total_balance
    
    def get_next_milestone(self, current_balance: float) -> Tuple[float, float, float]:
        """
        Get information about next milestone
        
        Args:
            current_balance: Current balance
        
        Returns:
            Tuple of (milestone_balance, lock_amount, progress_pct)
        """
        for milestone_balance, lock_amount in self.milestones:
            if milestone_balance not in self.reached_milestones:
                progress = (current_balance / milestone_balance) * 100
                return (milestone_balance, lock_amount, min(progress, 100))
        
        # All milestones reached
        return (None, None, 100)
    
    def should_allow_trade(self, total_balance: float, position_size: float) -> bool:
        """
        Check if trade should be allowed based on locked funds
        
        Args:
            total_balance: Current total balance
            position_size: Proposed position size
        
        Returns:
            True if trade is allowed, False otherwise
        """
        tradeable = self.get_tradeable_balance(total_balance)
        
        # Can't trade if no tradeable balance
        if tradeable <= 0:
            return False
        
        # Can't trade if position size exceeds tradeable balance
        if position_size > tradeable:
            return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get profit locker statistics"""
        return {
            'initial_balance': self.initial_balance,
            'locked_balance': self.locked_balance,
            'milestones_reached': len(self.reached_milestones),
            'total_milestones': len(self.milestones),
            'reached_list': self.reached_milestones,
            'lock_events': self.lock_events
        }
    
    def reset(self, initial_balance: float = 10.0):
        """Reset profit locker state"""
        self.initial_balance = initial_balance
        self.locked_balance = 0.0
        self.reached_milestones = []
        self.lock_events = []


# Testing
if __name__ == "__main__":
    print("=== PROFIT LOCKER TEST ===\n")
    
    pl = ProfitLocker(initial_balance=10.0)
    
    # Simulate balance growth
    test_balances = [
        10, 12, 15, 18, 20, 25, 28, 35, 40, 45, 50, 60, 70, 80, 
        90, 100, 120, 140, 160, 180, 200, 250, 300, 320
    ]
    
    for balance in test_balances:
        result = pl.check_and_lock(balance)
        
        if result['locked']:
            multiple = balance / pl.initial_balance
            print(f"\n🔒 MILESTONE REACHED!")
            print(f"   Balance: ${balance:.2f} ({multiple:.1f}x)")
            print(f"   Milestone: ${result['milestone_reached']:.2f}")
            print(f"   Locked: ${result['locked_balance']:.2f}")
            print(f"   Tradeable: ${result['tradeable_balance']:.2f}")
            print(f"   Locked %: {pl.get_locked_percentage(balance)*100:.1f}%")
        
        # Show next milestone info
        if balance in [10, 30, 50, 100, 200]:
            next_milestone, next_lock, progress = pl.get_next_milestone(balance)
            if next_milestone:
                print(f"\n📊 Status at ${balance:.2f}")
                print(f"   Next Milestone: ${next_milestone:.2f} (lock ${next_lock:.2f})")
                print(f"   Progress: {progress:.1f}%")
                print(f"   Currently Locked: ${pl.locked_balance:.2f}")
                print(f"   Tradeable: ${pl.get_tradeable_balance(balance):.2f}")
    
    # Final stats
    print("\n" + "="*60)
    print("FINAL PROFIT LOCKER STATS")
    print("="*60)
    stats = pl.get_stats()
    print(f"Initial Balance: ${stats['initial_balance']:.2f}")
    print(f"Locked Balance: ${stats['locked_balance']:.2f}")
    print(f"Milestones Reached: {stats['milestones_reached']}/{stats['total_milestones']}")
    print(f"\nMilestones Reached: {stats['reached_list']}")
    
    print("\n" + "="*60)
    print("LOCK EVENTS")
    print("="*60)
    for i, event in enumerate(stats['lock_events'], 1):
        print(f"\n{i}. At ${event['balance']:.2f} ({event['multiple']:.1f}x)")
        print(f"   Milestone: ${event['milestone']:.2f}")
        print(f"   Locked: ${event['locked_amount']:.2f}")
        print(f"   Increase: +${event['locked_increase']:.2f}")
