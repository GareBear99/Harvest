"""
Leverage Scaler - Progressive leverage management
Reduces leverage as balance grows to protect accumulated gains
"""

from typing import Dict, Any, List, Tuple


class LeverageScaler:
    """
    Manages progressive leverage scaling
    
    Leverage reduces as balance grows:
    - $5-10: 15× (recovery mode)
    - $10-30: 25× (accumulation phase)
    - $30-50: 20× 
    - $50-70: 15×
    - $70-100: 10×
    - $100-150: 8×
    - $150+: 5× (maximum safety)
    """
    
    def __init__(self):
        """Initialize leverage scaler with predefined brackets"""
        # Define leverage brackets: (min_balance, max_balance, leverage)
        self.leverage_brackets = [
            (0, 10, 15),      # Recovery
            (10, 30, 25),     # Accumulation
            (30, 50, 20),     # Early growth
            (50, 70, 15),     # Mid growth
            (70, 100, 10),    # Late growth
            (100, 150, 8),    # Early preservation
            (150, float('inf'), 5)  # Full preservation
        ]
        
        # Track leverage changes
        self.leverage_history = []
        self.current_leverage = None
    
    def get_leverage(self, balance: float) -> int:
        """
        Get appropriate leverage for current balance
        
        Args:
            balance: Current account balance
        
        Returns:
            Leverage multiplier
        """
        for min_bal, max_bal, leverage in self.leverage_brackets:
            if min_bal <= balance < max_bal:
                return leverage
        
        # Fallback to minimum leverage
        return 5
    
    def update_leverage(self, balance: float) -> Dict[str, Any]:
        """
        Update leverage and track changes
        
        Args:
            balance: Current balance
        
        Returns:
            Dict with leverage info and change status
        """
        new_leverage = self.get_leverage(balance)
        
        result = {
            'leverage': new_leverage,
            'changed': False,
            'old_leverage': self.current_leverage,
            'balance': balance,
            'bracket': self._get_bracket_name(balance)
        }
        
        # Check if leverage changed
        if self.current_leverage != new_leverage:
            result['changed'] = True
            
            # Record change
            self.leverage_history.append({
                'from_leverage': self.current_leverage,
                'to_leverage': new_leverage,
                'balance': balance,
                'bracket': result['bracket']
            })
            
            self.current_leverage = new_leverage
        
        return result
    
    def _get_bracket_name(self, balance: float) -> str:
        """Get human-readable bracket name"""
        if balance < 10:
            return "Recovery"
        elif balance < 30:
            return "Accumulation"
        elif balance < 50:
            return "Early Growth"
        elif balance < 70:
            return "Mid Growth"
        elif balance < 100:
            return "Late Growth"
        elif balance < 150:
            return "Early Preservation"
        else:
            return "Full Preservation"
    
    def calculate_effective_pnl(
        self, 
        price_move_pct: float, 
        leverage: int = None
    ) -> float:
        """
        Calculate P&L percentage with leverage applied
        
        Args:
            price_move_pct: Price movement percentage (e.g., 0.01 = 1%)
            leverage: Leverage to use (default: current)
        
        Returns:
            Effective P&L percentage with leverage
        """
        if leverage is None:
            leverage = self.current_leverage or 1
        
        return price_move_pct * leverage
    
    def calculate_liquidation_distance(self, leverage: int = None) -> float:
        """
        Calculate how far price can move before liquidation
        
        Args:
            leverage: Leverage to use (default: current)
        
        Returns:
            Price movement percentage that causes liquidation
        """
        if leverage is None:
            leverage = self.current_leverage or 1
        
        # Simplified: liquidation at ~90% loss with leverage
        # Real formula more complex, but this is close enough
        return 0.90 / leverage
    
    def get_risk_metrics(self, balance: float) -> Dict[str, Any]:
        """
        Get comprehensive risk metrics for current balance
        
        Args:
            balance: Current balance
        
        Returns:
            Dict with risk metrics
        """
        leverage = self.get_leverage(balance)
        
        # Calculate various risk scenarios
        scenarios = {
            '1%_move': self.calculate_effective_pnl(0.01, leverage),
            '2%_move': self.calculate_effective_pnl(0.02, leverage),
            '5%_move': self.calculate_effective_pnl(0.05, leverage),
            '10%_move': self.calculate_effective_pnl(0.10, leverage)
        }
        
        return {
            'balance': balance,
            'leverage': leverage,
            'bracket': self._get_bracket_name(balance),
            'liquidation_distance': self.calculate_liquidation_distance(leverage),
            'scenarios': scenarios
        }
    
    def get_next_leverage_change(self, current_balance: float) -> Tuple[float, int]:
        """
        Get info about next leverage bracket
        
        Args:
            current_balance: Current balance
        
        Returns:
            Tuple of (threshold_balance, new_leverage)
        """
        current_leverage = self.get_leverage(current_balance)
        
        # Find current bracket
        for i, (min_bal, max_bal, leverage) in enumerate(self.leverage_brackets):
            if min_bal <= current_balance < max_bal:
                # Check if there's a next bracket
                if i + 1 < len(self.leverage_brackets):
                    next_bracket = self.leverage_brackets[i + 1]
                    return (next_bracket[0], next_bracket[2])
                else:
                    return (None, current_leverage)  # Already at max
        
        return (None, current_leverage)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get leverage scaler statistics"""
        return {
            'current_leverage': self.current_leverage,
            'total_changes': len(self.leverage_history),
            'leverage_history': self.leverage_history,
            'brackets': [
                {
                    'min': min_bal,
                    'max': max_bal if max_bal != float('inf') else '∞',
                    'leverage': leverage
                }
                for min_bal, max_bal, leverage in self.leverage_brackets
            ]
        }
    
    def reset(self):
        """Reset leverage scaler state"""
        self.leverage_history = []
        self.current_leverage = None


# Testing
if __name__ == "__main__":
    print("=== LEVERAGE SCALER TEST ===\n")
    
    ls = LeverageScaler()
    
    # Test balances
    test_balances = [
        5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100,
        120, 140, 150, 180, 200, 250
    ]
    
    print("LEVERAGE BRACKETS:")
    print("-" * 60)
    for min_bal, max_bal, leverage in ls.leverage_brackets:
        max_str = f"${max_bal:.0f}" if max_bal != float('inf') else "∞"
        print(f"${min_bal:.0f} - {max_str:>10s}: {leverage:>2d}×")
    
    print("\n" + "="*60)
    print("BALANCE PROGRESSION")
    print("="*60)
    
    for balance in test_balances:
        result = ls.update_leverage(balance)
        
        if result['changed']:
            print(f"\n⚡ LEVERAGE CHANGE at ${balance:.2f}")
            print(f"   {result['old_leverage']}× → {result['leverage']}×")
            print(f"   Bracket: {result['bracket']}")
            
            # Show risk metrics
            metrics = ls.get_risk_metrics(balance)
            print(f"   Liquidation Distance: {metrics['liquidation_distance']*100:.2f}%")
            print(f"   1% move = {metrics['scenarios']['1%_move']*100:.1f}% P&L")
            print(f"   5% move = {metrics['scenarios']['5%_move']*100:.1f}% P&L")
            
            # Show next change
            next_threshold, next_leverage = ls.get_next_leverage_change(balance)
            if next_threshold:
                print(f"   Next: {next_leverage}× at ${next_threshold:.2f}")
    
    # Risk comparison table
    print("\n" + "="*60)
    print("RISK COMPARISON ACROSS BALANCES")
    print("="*60)
    print(f"{'Balance':<12} {'Leverage':<10} {'1% Move':<12} {'5% Move':<12} {'Liq Dist':<12}")
    print("-" * 60)
    
    comparison_balances = [10, 25, 40, 60, 80, 100, 150, 200]
    for bal in comparison_balances:
        metrics = ls.get_risk_metrics(bal)
        print(f"${bal:<11.2f} {metrics['leverage']:<10d}× "
              f"{metrics['scenarios']['1%_move']*100:<12.1f}% "
              f"{metrics['scenarios']['5%_move']*100:<12.1f}% "
              f"{metrics['liquidation_distance']*100:<12.2f}%")
    
    # Final stats
    print("\n" + "="*60)
    print("LEVERAGE SCALER STATS")
    print("="*60)
    stats = ls.get_stats()
    print(f"Current Leverage: {stats['current_leverage']}×")
    print(f"Total Changes: {stats['total_changes']}")
    print(f"\nChange History:")
    for i, change in enumerate(stats['leverage_history'], 1):
        print(f"  {i}. {change['from_leverage']}× → {change['to_leverage']}× "
              f"at ${change['balance']:.2f} ({change['bracket']})")
