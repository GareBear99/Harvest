"""
Timeframe Strategy Classes - Independent strategies per timeframe

Each timeframe (1m, 5m, 15m, 1h, 4h) has its own independent strategy instance:
- Unique seed for deterministic behavior
- Independent thresholds from BASE_STRATEGY
- Separate performance tracking
- Can be enabled/disabled independently
"""

import sys
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.base_strategy import BASE_STRATEGY
from ml.strategy_seed_generator import generate_strategy_seed


class TimeframeStrategy(ABC):
    """
    Abstract base class for timeframe-specific strategies
    Each timeframe gets its own independent strategy instance
    """
    
    def __init__(self, timeframe: str, config: Dict, seed: int):
        """
        Initialize timeframe strategy
        
        Args:
            timeframe: '1m', '5m', '15m', '1h', or '4h'
            config: Configuration dict from TIMEFRAME_CONFIGS
            seed: Unique seed for this timeframe strategy
        """
        self.timeframe = timeframe
        self.config = config
        self.seed = seed
        
        # Load thresholds from BASE_STRATEGY
        if timeframe not in BASE_STRATEGY:
            raise ValueError(f"No BASE_STRATEGY found for {timeframe}")
        
        self.thresholds = BASE_STRATEGY[timeframe].copy()
        
        # Track this strategy's performance
        self.trades = []
        self.wins = 0
        self.losses = 0
        
    def get_thresholds(self) -> Dict:
        """
        Get strategy thresholds
        
        Returns:
            Dictionary of threshold values
        """
        return self.thresholds.copy()
    
    def get_seed(self) -> int:
        """Get this strategy's unique seed"""
        return self.seed
    
    def record_trade(self, outcome: Dict) -> None:
        """
        Record a trade outcome
        
        Args:
            outcome: Trade result dictionary with 'pnl', 'won', etc.
        """
        self.trades.append(outcome)
        
        if outcome.get('won', False) or outcome.get('pnl', 0) > 0:
            self.wins += 1
        else:
            self.losses += 1
    
    def get_stats(self) -> Dict:
        """
        Get performance statistics
        
        Returns:
            Dictionary with wins, losses, win_rate, total_pnl
        """
        total_trades = len(self.trades)
        win_rate = self.wins / total_trades if total_trades > 0 else 0.0
        total_pnl = sum(t.get('pnl', 0) for t in self.trades)
        
        return {
            'timeframe': self.timeframe,
            'seed': self.seed,
            'trades': total_trades,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': win_rate,
            'total_pnl': total_pnl
        }
    
    def is_enabled(self) -> bool:
        """
        Check if this strategy is enabled
        
        Returns:
            True if enabled (default), False if disabled
        """
        return self.thresholds.get('enabled', True)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(seed={self.seed}, trades={len(self.trades)})"


class TimeframeStrategy1m(TimeframeStrategy):
    """
    1-minute timeframe strategy
    Ultra-fast scalping with very tight TP/SL
    """
    
    def __init__(self, config: Dict):
        """
        Initialize 1m strategy
        
        Args:
            config: Configuration dict from TIMEFRAME_CONFIGS['1m']
        """
        # Generate deterministic seed from config parameters
        seed = generate_strategy_seed('1m', BASE_STRATEGY.get('1m', config))
        
        super().__init__(
            timeframe='1m',
            config=config,
            seed=seed
        )
    
    def __repr__(self) -> str:
        enabled = "✓" if self.is_enabled() else "✗"
        return f"1m Strategy [{enabled}] (seed={self.seed}, trades={len(self.trades)})"


class TimeframeStrategy5m(TimeframeStrategy):
    """
    5-minute timeframe strategy
    Fast scalping with tight TP/SL
    """
    
    def __init__(self, config: Dict):
        """
        Initialize 5m strategy
        
        Args:
            config: Configuration dict from TIMEFRAME_CONFIGS['5m']
        """
        # Generate deterministic seed from config parameters
        seed = generate_strategy_seed('5m', BASE_STRATEGY.get('5m', config))
        
        super().__init__(
            timeframe='5m',
            config=config,
            seed=seed
        )
    
    def __repr__(self) -> str:
        enabled = "✓" if self.is_enabled() else "✗"
        return f"5m Strategy [{enabled}] (seed={self.seed}, trades={len(self.trades)})"


class TimeframeStrategy15m(TimeframeStrategy):
    """
    15-minute timeframe strategy
    Short-term trades with tight TP/SL
    """
    
    def __init__(self, config: Dict):
        """
        Initialize 15m strategy
        
        Args:
            config: Configuration dict from TIMEFRAME_CONFIGS['15m']
        """
        # Generate deterministic seed from config parameters (like Minecraft)
        seed = generate_strategy_seed('15m', BASE_STRATEGY.get('15m', config))
        
        super().__init__(
            timeframe='15m',
            config=config,
            seed=seed
        )
        
    def __repr__(self) -> str:
        enabled = "✓" if self.is_enabled() else "✗"
        return f"15m Strategy [{enabled}] (seed={self.seed}, trades={len(self.trades)})"


class TimeframeStrategy1h(TimeframeStrategy):
    """
    1-hour timeframe strategy
    Medium-term trades with balanced risk
    """
    
    def __init__(self, config: Dict):
        """
        Initialize 1h strategy
        
        Args:
            config: Configuration dict from TIMEFRAME_CONFIGS['1h']
        """
        # Generate deterministic seed from config parameters (like Minecraft)
        seed = generate_strategy_seed('1h', BASE_STRATEGY.get('1h', config))
        
        super().__init__(
            timeframe='1h',
            config=config,
            seed=seed
        )
    
    def __repr__(self) -> str:
        return f"1h Strategy (seed={self.seed}, trades={len(self.trades)})"


class TimeframeStrategy4h(TimeframeStrategy):
    """
    4-hour timeframe strategy
    Longer-term trades with wider TP/SL
    """
    
    def __init__(self, config: Dict):
        """
        Initialize 4h strategy
        
        Args:
            config: Configuration dict from TIMEFRAME_CONFIGS['4h']
        """
        # Generate deterministic seed from config parameters (like Minecraft)
        seed = generate_strategy_seed('4h', BASE_STRATEGY.get('4h', config))
        
        super().__init__(
            timeframe='4h',
            config=config,
            seed=seed
        )
    
    def __repr__(self) -> str:
        return f"4h Strategy (seed={self.seed}, trades={len(self.trades)})"


def create_strategy(timeframe: str, config: Dict) -> TimeframeStrategy:
    """
    Factory function to create appropriate strategy instance
    
    Args:
        timeframe: '1m', '5m', '15m', '1h', or '4h'
        config: Configuration dict from TIMEFRAME_CONFIGS
        
    Returns:
        Appropriate TimeframeStrategy instance
        
    Raises:
        ValueError: If timeframe is not supported
    """
    strategies = {
        '1m': TimeframeStrategy1m,
        '5m': TimeframeStrategy5m,
        '15m': TimeframeStrategy15m,
        '1h': TimeframeStrategy1h,
        '4h': TimeframeStrategy4h
    }
    
    if timeframe not in strategies:
        raise ValueError(f"Unsupported timeframe: {timeframe}. Must be '1m', '5m', '15m', '1h', or '4h'")
    
    return strategies[timeframe](config)


if __name__ == "__main__":
    # Demonstrate usage
    print("📊 TIMEFRAME STRATEGY DEMONSTRATION\n")
    
    # Mock configs
    mock_configs = {
        '1m': {'aggregation_minutes': 1, 'tp_multiplier': 1.2},
        '5m': {'aggregation_minutes': 5, 'tp_multiplier': 1.3},
        '15m': {'aggregation_minutes': 15, 'tp_multiplier': 1.5},
        '1h': {'aggregation_minutes': 60, 'tp_multiplier': 2.0},
        '4h': {'aggregation_minutes': 240, 'tp_multiplier': 2.5}
    }
    
    for tf in ['1m', '5m', '15m', '1h', '4h']:
        strategy = create_strategy(tf, mock_configs[tf])
        print(f"{strategy}")
        print(f"  Thresholds: {strategy.get_thresholds()}")
        print(f"  Enabled: {strategy.is_enabled()}")
        print()
