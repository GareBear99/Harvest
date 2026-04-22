"""
ProcessingManager - Coordinates independent timeframe strategy execution

Responsibilities:
- Manage independent strategies per timeframe (15m, 1h, 4h)
- Enforce position limits (max 1 per TF, max 2 total)
- Route entry checks to appropriate timeframe strategies
- Aggregate results across all active timeframes
"""

from typing import Dict, List, Optional, Any


class ProcessingManager:
    """
    Coordinates independent execution of timeframe strategies
    Ensures each timeframe operates independently while respecting global limits
    """
    
    def __init__(self, candles: List[Dict], timeframe_configs: Dict, seed: Optional[int] = None):
        """
        Initialize ProcessingManager
        
        Args:
            candles: Base 1-minute candle data
            timeframe_configs: Configuration dict for each timeframe
            seed: Random seed for deterministic behavior
        """
        self.candles = candles
        self.timeframe_configs = timeframe_configs
        self.seed = seed
        
        # Registered strategies per timeframe
        self.strategies: Dict[str, Any] = {}
        
        # Active positions per timeframe
        self.active_positions: Dict[str, Dict] = {}
        
        # Trade history per timeframe
        self.timeframe_trades: Dict[str, List[Dict]] = {
            '15m': [],
            '1h': [],
            '4h': []
        }
        
        # Global stats
        self.all_trades: List[Dict] = []
        
    def register_strategy(self, timeframe: str, strategy_instance):
        """
        Register a timeframe strategy
        
        Args:
            timeframe: '15m', '1h', or '4h'
            strategy_instance: Instance of TimeframeStrategy
        """
        if timeframe not in self.timeframe_configs:
            raise ValueError(f"Timeframe {timeframe} not in configs")
        
        self.strategies[timeframe] = strategy_instance
        print(f"  ✓ Registered {timeframe} strategy (seed={strategy_instance.seed})")
    
    def get_active_timeframes(self) -> List[str]:
        """
        Get list of active (registered) timeframes
        
        Returns:
            List of active timeframe strings (e.g., ['15m', '1h', '4h'])
        """
        return list(self.strategies.keys())
    
    def can_open_position(self, timeframe: str) -> bool:
        """
        Check if we can open a position on this timeframe
        
        Args:
            timeframe: Timeframe to check
            
        Returns:
            True if position can be opened
        """
        # Max 1 position per timeframe
        if timeframe in self.active_positions:
            return False
        
        # Max 2 simultaneous positions total (across all timeframes)
        if len(self.active_positions) >= 2:
            return False
        
        return True
    
    def process_minute(self, minute_index: int, backtest_instance) -> None:
        """
        Process a single minute across all active timeframes
        
        Args:
            minute_index: Current minute index in candles array
            backtest_instance: Reference to MultiTimeframeBacktest for position checks
        """
        # Check existing positions first
        backtest_instance.check_existing_positions(minute_index)
        
        # Check entry opportunities for each active timeframe
        for timeframe in self.get_active_timeframes():
            config = self.timeframe_configs[timeframe]
            
            # Check if it's time to evaluate this timeframe
            if minute_index % config['aggregation_minutes'] == 0:
                self.check_timeframe_entry(
                    timeframe, 
                    minute_index, 
                    backtest_instance
                )
    
    def check_timeframe_entry(
        self, 
        timeframe: str, 
        minute_index: int, 
        backtest_instance
    ) -> None:
        """
        Check entry opportunity for a specific timeframe
        Routes to the timeframe's independent strategy
        
        Args:
            timeframe: Timeframe to check
            minute_index: Current minute index
            backtest_instance: Reference to backtest for entry checks
        """
        # Delegate to the backtest's existing check_entry_opportunity method
        # This maintains compatibility with existing entry logic
        backtest_instance.check_entry_opportunity(minute_index, timeframe)
    
    def record_position(self, timeframe: str, position: Dict) -> None:
        """
        Record an active position for a timeframe
        
        Args:
            timeframe: Timeframe of the position
            position: Position dictionary
        """
        self.active_positions[timeframe] = position
    
    def close_position(self, timeframe: str, trade: Dict) -> None:
        """
        Close a position and record the trade
        
        Args:
            timeframe: Timeframe of the position
            trade: Trade result dictionary
        """
        if timeframe in self.active_positions:
            del self.active_positions[timeframe]
        
        # Record trade
        self.timeframe_trades[timeframe].append(trade)
        self.all_trades.append(trade)
    
    def get_position(self, timeframe: str) -> Optional[Dict]:
        """
        Get active position for a timeframe
        
        Args:
            timeframe: Timeframe to check
            
        Returns:
            Position dict or None
        """
        return self.active_positions.get(timeframe)
    
    def aggregate_results(self) -> Dict[str, Any]:
        """
        Aggregate results across all timeframes
        
        Returns:
            Dictionary containing aggregated statistics
        """
        results = {
            'total_trades': len(self.all_trades),
            'by_timeframe': {}
        }
        
        for tf in self.get_active_timeframes():
            tf_trades = self.timeframe_trades[tf]
            if tf_trades:
                wins = [t for t in tf_trades if t.get('pnl', 0) > 0]
                results['by_timeframe'][tf] = {
                    'trades': len(tf_trades),
                    'wins': len(wins),
                    'win_rate': len(wins) / len(tf_trades) if tf_trades else 0.0,
                    'total_pnl': sum(t.get('pnl', 0) for t in tf_trades)
                }
            else:
                results['by_timeframe'][tf] = {
                    'trades': 0,
                    'wins': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0
                }
        
        return results
    
    def get_active_position_count(self) -> int:
        """Get number of currently active positions"""
        return len(self.active_positions)
    
    def has_active_position(self, timeframe: str) -> bool:
        """Check if timeframe has an active position"""
        return timeframe in self.active_positions
