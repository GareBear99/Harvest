#!/usr/bin/env python3
"""
Position Size Limiter for HARVEST
Enforces maximum position sizes based on account capital
Ensures consistent sizing between backtest and live trading
"""

from typing import Dict, Tuple
import logging

logger = logging.getLogger("harvest.position_limiter")


class PositionSizeLimiter:
    """
    Enforces position size limits based on account capital.
    
    Rules:
    - Capital < $5,000: Max $100 per position
    - Capital >= $5,000: Max 2% of capital per position
    - Prevents over-leveraging on small accounts
    - Ensures backtest and live trading use same limits
    """
    
    # Capital thresholds
    SMALL_ACCOUNT_THRESHOLD = 5000.0  # USD
    MAX_POSITION_SMALL_ACCOUNT = 100.0  # USD
    MAX_POSITION_PCT_LARGE_ACCOUNT = 0.02  # 2% of capital
    
    def __init__(self):
        """Initialize position size limiter."""
        self.limits_applied = 0
        self.total_checks = 0
        
    def get_max_position_size(self, total_capital: float) -> float:
        """
        Get maximum allowed position size for given capital.
        
        Args:
            total_capital: Total account capital in USD
            
        Returns:
            Maximum position size in USD
        """
        if total_capital < self.SMALL_ACCOUNT_THRESHOLD:
            # Small account: hard cap at $100
            return self.MAX_POSITION_SMALL_ACCOUNT
        else:
            # Large account: 2% of capital
            return total_capital * self.MAX_POSITION_PCT_LARGE_ACCOUNT
    
    def limit_position_size(
        self, 
        requested_size: float, 
        total_capital: float,
        timeframe: str = None
    ) -> Tuple[float, bool, Dict]:
        """
        Limit position size to maximum allowed.
        
        Args:
            requested_size: Requested position size in USD
            total_capital: Total account capital in USD
            timeframe: Optional timeframe identifier
            
        Returns:
            Tuple of (limited_size, was_limited, info_dict)
        """
        self.total_checks += 1
        
        max_size = self.get_max_position_size(total_capital)
        
        if requested_size > max_size:
            self.limits_applied += 1
            limited = True
            
            logger.debug(
                f"Position size limited: ${requested_size:.2f} → ${max_size:.2f} "
                f"(Capital: ${total_capital:.2f}, TF: {timeframe})"
            )
            
            reason = 'small_account' if total_capital < self.SMALL_ACCOUNT_THRESHOLD else 'pct_limit'
            message = f"${self.MAX_POSITION_SMALL_ACCOUNT} cap" if total_capital < self.SMALL_ACCOUNT_THRESHOLD else f"{self.MAX_POSITION_PCT_LARGE_ACCOUNT*100}% of capital cap"
            
            info = {
                'requested': requested_size,
                'limited_to': max_size,
                'capital': total_capital,
                'timeframe': timeframe,
                'reduction_pct': ((requested_size - max_size) / requested_size) * 100,
                'reason': reason,
                'message': message
            }
            
            return max_size, True, info
        else:
            info = {
                'requested': requested_size,
                'limited_to': requested_size,
                'capital': total_capital,
                'timeframe': timeframe,
                'reduction_pct': 0.0,
                'reason': 'within_limits',
                'message': 'No limit applied'
            }
            
            return requested_size, False, info
    
    def get_stats(self) -> Dict:
        """
        Get statistics on position size limiting.
        
        Returns:
            Dict with stats
        """
        limit_rate = (self.limits_applied / self.total_checks * 100) if self.total_checks > 0 else 0.0
        
        return {
            'total_checks': self.total_checks,
            'limits_applied': self.limits_applied,
            'limit_rate_pct': limit_rate,
            'small_account_threshold': self.SMALL_ACCOUNT_THRESHOLD,
            'max_position_small': self.MAX_POSITION_SMALL_ACCOUNT,
            'max_position_pct_large': self.MAX_POSITION_PCT_LARGE_ACCOUNT * 100
        }
    
    def calculate_adjusted_margin(
        self,
        position_value: float,
        leverage: float,
        total_capital: float
    ) -> Tuple[float, float]:
        """
        Calculate margin with position size limits applied.
        
        Args:
            position_value: Desired position value in USD
            leverage: Leverage multiplier
            total_capital: Total account capital
            
        Returns:
            Tuple of (limited_position_value, required_margin)
        """
        # Apply position size limit
        limited_value, was_limited, info = self.limit_position_size(
            position_value, 
            total_capital
        )
        
        # Calculate margin required
        margin = limited_value / leverage
        
        return limited_value, margin
    
    def validate_position_for_backtest(
        self,
        position_size: float,
        position_value: float,
        margin: float,
        balance: float,
        total_balance: float,
        timeframe: str
    ) -> Tuple[bool, str, Dict]:
        """
        Validate position meets all requirements for backtest.
        
        Args:
            position_size: Position size in coins
            position_value: Position value in USD
            margin: Required margin
            balance: Available balance
            total_balance: Total balance (including locked)
            timeframe: Timeframe identifier
            
        Returns:
            Tuple of (is_valid, reason, adjusted_values)
        """
        # Check margin availability
        if margin > balance:
            return False, "Insufficient margin", {}
        
        # Check position size limit
        max_size = self.get_max_position_size(total_balance)
        
        if position_value > max_size:
            # Calculate adjusted values
            size_ratio = max_size / position_value
            
            adjusted = {
                'position_value': max_size,
                'position_size': position_size * size_ratio,
                'margin': margin * size_ratio,
                'original_value': position_value,
                'limited': True,
                'timeframe': timeframe
            }
            
            # Check if adjusted margin is still available
            if adjusted['margin'] > balance:
                return False, "Insufficient margin even after limiting", {}
            
            logger.debug(
                f"{timeframe}: Position limited from ${position_value:.2f} to ${max_size:.2f}"
            )
            
            return True, "Limited to maximum size", adjusted
        
        return True, "Within limits", {
            'position_value': position_value,
            'position_size': position_size,
            'margin': margin,
            'limited': False,
            'timeframe': timeframe
        }
    
    def get_position_info_for_display(self, total_capital: float) -> Dict:
        """
        Get position sizing information for dashboard display.
        
        Args:
            total_capital: Total account capital
            
        Returns:
            Dict with display information
        """
        max_size = self.get_max_position_size(total_capital)
        is_small_account = total_capital < self.SMALL_ACCOUNT_THRESHOLD
        
        if is_small_account:
            status = f"Small account mode (< ${self.SMALL_ACCOUNT_THRESHOLD:,.0f})"
        else:
            status = f"Large account mode (≥ ${self.SMALL_ACCOUNT_THRESHOLD:,.0f})"
        
        return {
            'capital': total_capital,
            'is_small_account': is_small_account,
            'max_position_size': max_size,
            'max_position_pct': (max_size / total_capital * 100) if total_capital > 0 else 0,
            'threshold': self.SMALL_ACCOUNT_THRESHOLD,
            'rule': f'${self.MAX_POSITION_SMALL_ACCOUNT} max' if is_small_account else f'{self.MAX_POSITION_PCT_LARGE_ACCOUNT*100}% of capital',
            'status': status,
            'stats': self.get_stats()
        }


# Global instance for consistent use across system
_global_limiter = None

def get_position_limiter() -> PositionSizeLimiter:
    """
    Get global position size limiter instance.
    
    Returns:
        PositionSizeLimiter instance
    """
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = PositionSizeLimiter()
    return _global_limiter


def reset_position_limiter():
    """Reset global position limiter (useful for testing)."""
    global _global_limiter
    _global_limiter = None


if __name__ == '__main__':
    # Demo
    import json
    
    print("=" * 70)
    print("POSITION SIZE LIMITER - DEMO")
    print("=" * 70)
    
    limiter = PositionSizeLimiter()
    
    # Test scenarios
    scenarios = [
        (150.0, 1000.0, "15m"),   # Small account, over limit
        (50.0, 1000.0, "1h"),     # Small account, within limit
        (200.0, 10000.0, "4h"),   # Large account, within limit (2% = $200)
        (500.0, 10000.0, "1h"),   # Large account, over limit
    ]
    
    print("\nTest Scenarios:")
    print("-" * 70)
    
    for requested, capital, tf in scenarios:
        limited, was_limited, info = limiter.limit_position_size(requested, capital, tf)
        
        print(f"\nCapital: ${capital:,.2f} | Requested: ${requested:.2f} | TF: {tf}")
        print(f"Result: ${limited:.2f} | Limited: {was_limited}")
        if was_limited:
            print(f"Reason: {info['reason']} | Reduction: {info['reduction_pct']:.1f}%")
    
    print("\n" + "=" * 70)
    print("STATISTICS")
    print("=" * 70)
    
    stats = limiter.get_stats()
    print(json.dumps(stats, indent=2))
