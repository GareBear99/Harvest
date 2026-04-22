"""
Timeframe Strategy Manager - Independent strategy tracking per timeframe
Handles rolling statistics, learning phases, and bootstrap cold-start
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.strategy_pool import StrategyPool


# Bootstrap defaults for cold start (no saved strategies)
BOOTSTRAP_THRESHOLDS = {
    '1m': {
        'min_confidence': 0.82,
        'min_volume': 1.35,
        'min_trend': 0.68,
        'min_adx': 32,
        'min_roc': -1.05,
        'atr_min': 0.50,
        'atr_max': 3.0
    },
    '5m': {
        'min_confidence': 0.80,
        'min_volume': 1.30,
        'min_trend': 0.65,
        'min_adx': 30,
        'min_roc': -1.1,
        'atr_min': 0.45,
        'atr_max': 3.2
    },
    '15m': {
        'min_confidence': 0.70,
        'min_volume': 1.15,
        'min_trend': 0.55,
        'min_adx': 25,
        'min_roc': -1.0,
        'atr_min': 0.4,
        'atr_max': 3.5
    },
    '1h': {
        'min_confidence': 0.66,
        'min_volume': 1.10,
        'min_trend': 0.50,
        'min_adx': 25,
        'min_roc': -1.0,
        'atr_min': 0.4,
        'atr_max': 3.5
    },
    '4h': {
        'min_confidence': 0.63,
        'min_volume': 1.05,
        'min_trend': 0.46,
        'min_adx': 25,
        'min_roc': -1.0,
        'atr_min': 0.4,
        'atr_max': 3.5
    }
}


class TimeframeStrategyManager:
    """
    Manages independent strategies for each timeframe
    Tracks rolling statistics, learning phases, and auto-adjustments
    """
    
    def __init__(self, active_timeframes: List[str] = None, state_file: str = "ml/timeframe_strategies.json"):
        self.state_file = state_file
        
        # Default to all timeframes if none specified
        if active_timeframes is None:
            active_timeframes = ['1m', '5m', '15m', '1h', '4h']
        
        self.active_timeframes = active_timeframes
        
        # Initialize strategy pool (only for active timeframes)
        self.strategy_pool = StrategyPool(active_timeframes=active_timeframes)
        
        # Initialize stats ONLY for active timeframes
        self.timeframe_stats = {}
        for tf in active_timeframes:
            self.timeframe_stats[tf] = self._init_timeframe_stats(tf)
        
        # Load saved state if exists
        self.load_state()
        
        # Load best strategies from pool on startup
        self._load_best_strategies_from_pool()
        
        print("📊 TimeframeStrategyManager initialized")
        for tf in self.active_timeframes:
            phase = self.get_current_phase(tf)
            trade_count = self.get_trade_count(tf)
            active = self.strategy_pool.get_active_strategy_id(tf)
            print(f"   {tf}: {trade_count} trades, phase={phase}, strategy={active}")
    
    def _init_timeframe_stats(self, timeframe: str) -> Dict:
        """Initialize statistics structure for a timeframe"""
        return {
            'trades': deque(maxlen=100),  # Last 100 trades
            'current_thresholds': BOOTSTRAP_THRESHOLDS[timeframe].copy(),
            'adjustments': [],  # History of adjustments
            'phase': 'exploration',
            'confidence': 0.0,  # Strategy confidence (0-1)
            'best_strategy': None,
            'consecutive_losses': 0,  # Track consecutive losses for strategy switching
            'consecutive_unprofitable': 0,  # Track unprofitable trades for failsafe
            'failsafe_resets': 0,  # Track how many times we've reset to BASE
            'created_at': datetime.now().isoformat()
        }
    
    def is_timeframe_active(self, timeframe: str) -> bool:
        """
        Check if timeframe is active
        
        Args:
            timeframe: Timeframe to check
            
        Returns:
            True if timeframe is active
        """
        return timeframe in self.active_timeframes
    
    def register_timeframe(self, timeframe: str, strategy) -> None:
        """
        Register a timeframe with its strategy
        
        Args:
            timeframe: Timeframe string
            strategy: Strategy instance
        """
        if timeframe not in self.active_timeframes:
            self.active_timeframes.append(timeframe)
            self.timeframe_stats[timeframe] = self._init_timeframe_stats(timeframe)
    
    def record_trade(self, timeframe: str, outcome: Dict[str, Any]):
        """
        Record a trade result for a timeframe
        
        Args:
            timeframe: '15m', '1h', or '4h'
            outcome: {
                'won': bool,
                'pnl': float,
                'duration_min': int,
                'exit_type': 'TP'|'SL'|'TIME'
            }
        """
        if not self.is_timeframe_active(timeframe):
            return
        
        # Add timestamp
        outcome['timestamp'] = datetime.now().isoformat()
        
        # Record trade
        self.timeframe_stats[timeframe]['trades'].append(outcome)
        
        # Update consecutive losses
        if outcome['won']:
            self.timeframe_stats[timeframe]['consecutive_losses'] = 0
        else:
            self.timeframe_stats[timeframe]['consecutive_losses'] += 1
        
        # Update consecutive unprofitable for failsafe
        if outcome['pnl'] > 0:
            self.timeframe_stats[timeframe]['consecutive_unprofitable'] = 0
        else:
            self.timeframe_stats[timeframe]['consecutive_unprofitable'] += 1
        
        # Check failsafe: reset to BASE_STRATEGY if using unproven strategy with 3 unprofitable trades
        self._check_failsafe_reset(timeframe)
        
        # Update phase
        self._update_phase(timeframe)
        
        # Update confidence score
        self._update_confidence(timeframe)
        
        # Check if we should switch strategies
        self._check_strategy_switch(timeframe)
    
    def get_trade_count(self, timeframe: str) -> int:
        """Get total number of trades for timeframe"""
        if not self.is_timeframe_active(timeframe):
            return 0
        return len(self.timeframe_stats[timeframe]['trades'])
    
    def get_win_rate(self, timeframe: str, window: int = 10) -> float:
        """
        Calculate win rate for specified window
        
        Args:
            timeframe: '15m', '1h', or '4h'
            window: Number of recent trades (5, 10, 20, 50, or 'all')
        """
        if not self.is_timeframe_active(timeframe):
            return 0.0
        
        trades = list(self.timeframe_stats[timeframe]['trades'])
        
        if not trades:
            return 0.0
        
        if window == 'all':
            window = len(trades)
        
        recent_trades = trades[-window:] if len(trades) >= window else trades
        
        if not recent_trades:
            return 0.0
        
        wins = sum(1 for t in recent_trades if t['won'])
        return wins / len(recent_trades)
    
    def get_rolling_win_rates(self, timeframe: str) -> Dict[str, float]:
        """Get win rates for all windows"""
        return {
            'last_5': self.get_win_rate(timeframe, 5),
            'last_10': self.get_win_rate(timeframe, 10),
            'last_20': self.get_win_rate(timeframe, 20),
            'last_50': self.get_win_rate(timeframe, 50),
            'all_time': self.get_win_rate(timeframe, 'all')
        }
    
    def get_current_phase(self, timeframe: str) -> str:
        """
        Determine learning phase based on trade count
        
        Phases:
        - exploration (0-10): Loose filters, gather data
        - calibration (10-30): Analyze patterns, adjust
        - optimization (30-100): Fine-tune toward 72%
        - mastery (100+): Maintain 72-80%, lock strategies
        """
        count = self.get_trade_count(timeframe)
        
        if count < 10:
            return 'exploration'
        elif count < 30:
            return 'calibration'
        elif count < 100:
            return 'optimization'
        else:
            return 'mastery'
    
    def get_phase_config(self, phase: str) -> Dict:
        """Get configuration for learning phase"""
        configs = {
            'exploration': {
                'adjustment_frequency': 5,
                'adjustment_magnitude': 1.0,  # 100% of calculated severity
                'min_trades_for_adjustment': 5
            },
            'calibration': {
                'adjustment_frequency': 5,
                'adjustment_magnitude': 0.8,  # 80%
                'min_trades_for_adjustment': 5
            },
            'optimization': {
                'adjustment_frequency': 10,
                'adjustment_magnitude': 0.5,  # 50%
                'min_trades_for_adjustment': 10
            },
            'mastery': {
                'adjustment_frequency': 20,
                'adjustment_magnitude': 0.3,  # 30%
                'min_trades_for_adjustment': 20,
                'lock_strategy_if_wr_72_80': True
            }
        }
        return configs.get(phase, configs['exploration'])
    
    def _update_phase(self, timeframe: str):
        """Update phase based on trade count"""
        if not self.is_timeframe_active(timeframe):
            return
        new_phase = self.get_current_phase(timeframe)
        self.timeframe_stats[timeframe]['phase'] = new_phase
    
    def _update_confidence(self, timeframe: str):
        """
        Update strategy confidence score (0-1)
        Based on trade count and consistency
        """
        if not self.is_timeframe_active(timeframe):
            return
        
        count = self.get_trade_count(timeframe)
        
        # Confidence grows with experience
        base_confidence = min(1.0, count / 100.0)
        
        # Bonus for good win rate
        wr = self.get_win_rate(timeframe, 'all')
        if 0.72 <= wr <= 0.80:
            base_confidence *= 1.2  # 20% boost for target range
        
        self.timeframe_stats[timeframe]['confidence'] = min(1.0, base_confidence)
    
    def should_adjust(self, timeframe: str, current_wr: float) -> bool:
        """
        Determine if strategy should be adjusted
        
        Returns True if:
        - Enough trades accumulated
        - Win rate below 72% OR trending down in mastery phase
        - Not locked in 72-80% sweet spot
        """
        phase = self.get_current_phase(timeframe)
        phase_config = self.get_phase_config(phase)
        trade_count = self.get_trade_count(timeframe)
        
        # Need minimum trades
        if trade_count < phase_config['min_trades_for_adjustment']:
            return False
        
        # Check adjustment frequency
        if trade_count % phase_config['adjustment_frequency'] != 0:
            return False
        
        # In mastery phase with 72-80% WR, lock strategy
        if phase == 'mastery' and 0.72 <= current_wr <= 0.80:
            # Only adjust if trending down
            if self._is_declining(timeframe):
                return True
            return False  # LOCKED
        
        # Always adjust if below 72%
        if current_wr < 0.72:
            return True
        
        # If above 80%, can slightly loosen for more trades
        if current_wr > 0.80 and trade_count > 20:
            return True
        
        return False
    
    def _is_declining(self, timeframe: str) -> bool:
        """Check if win rate is trending downward"""
        rolling = self.get_rolling_win_rates(timeframe)
        
        # Compare recent vs longer term
        if rolling['last_5'] < rolling['last_20'] * 0.90:  # 10% decline
            return True
        
        return False
    
    def get_thresholds(self, timeframe: str) -> Dict[str, float]:
        """Get current filter thresholds for timeframe"""
        # If timeframe not active yet, return bootstrap defaults
        if not self.is_timeframe_active(timeframe):
            return BOOTSTRAP_THRESHOLDS.get(timeframe, {}).copy()
        return self.timeframe_stats[timeframe]['current_thresholds'].copy()
    
    def set_thresholds(self, timeframe: str, new_thresholds: Dict[str, float], reason: str = "adjustment"):
        """
        Update thresholds for timeframe and save
        
        Args:
            timeframe: '15m', '1h', or '4h'
            new_thresholds: New threshold values
            reason: Reason for adjustment
        """
        # Skip if timeframe not active yet
        if not self.is_timeframe_active(timeframe):
            return
        
        old_thresholds = self.timeframe_stats[timeframe]['current_thresholds'].copy()
        
        # Update current thresholds
        self.timeframe_stats[timeframe]['current_thresholds'] = new_thresholds.copy()
        
        # Record adjustment in history
        adjustment = {
            'timestamp': datetime.now().isoformat(),
            'old': old_thresholds,
            'new': new_thresholds,
            'reason': reason,
            'trade_count': self.get_trade_count(timeframe),
            'win_rate': self.get_win_rate(timeframe, 10)
        }
        self.timeframe_stats[timeframe]['adjustments'].append(adjustment)
        
        # Keep only last 50 adjustments
        if len(self.timeframe_stats[timeframe]['adjustments']) > 50:
            self.timeframe_stats[timeframe]['adjustments'] = \
                self.timeframe_stats[timeframe]['adjustments'][-50:]
        
        # Check if this is a new best strategy
        current_wr = self.get_win_rate(timeframe, 'all')
        if current_wr >= 0.72:
            best = self.timeframe_stats[timeframe].get('best_strategy')
            if not best or current_wr > best.get('win_rate', 0):
                self.timeframe_stats[timeframe]['best_strategy'] = {
                    'win_rate': current_wr,
                    'trades': self.get_trade_count(timeframe),
                    'thresholds': new_thresholds.copy(),
                    'timestamp': datetime.now().isoformat()
                }
        
        # Try to add to strategy pool if it's performing well
        self._try_add_to_pool(timeframe, new_thresholds)
        
        # Persist to disk
        self.save_state()
    
    def _try_add_to_pool(self, timeframe: str, thresholds: Dict[str, float]):
        """Try to add current strategy to the pool if it qualifies"""
        trade_count = self.get_trade_count(timeframe)
        win_rate = self.get_win_rate(timeframe, 'all')
        
        # Check if strategy qualifies for pool (72% WR with 20+ trades)
        if self.strategy_pool.should_add_to_pool(win_rate, trade_count):
            success = self.strategy_pool.add_proven_strategy(
                timeframe=timeframe,
                strategy=thresholds,
                win_rate=win_rate,
                trade_count=trade_count
            )
            if success:
                print(f"✨ Added new proven strategy to {timeframe} pool: {win_rate:.1%} WR ({trade_count} trades)")
    
    def _check_failsafe_reset(self, timeframe: str):
        """Failsafe: Reset to BASE_STRATEGY if using unproven strategy with 3 unprofitable trades"""
        consecutive_unprofitable = self.timeframe_stats[timeframe]['consecutive_unprofitable']
        
        # Only trigger failsafe if we have 3 consecutive unprofitable trades
        if consecutive_unprofitable < 3:
            return
        
        # Check if current strategy is proven (in the pool with good WR)
        active_strategy_id = self.strategy_pool.get_active_strategy_id(timeframe)
        
        # If using 'base' strategy, don't reset (already at base)
        if active_strategy_id == 'base':
            self.timeframe_stats[timeframe]['consecutive_unprofitable'] = 0
            return
        
        # Check if the active strategy is proven (72%+ WR, 20+ trades)
        stats = self.strategy_pool.get_pool_stats(timeframe)
        active_strategy = None
        
        for strat in stats['strategies']:
            if strat['id'] == active_strategy_id:
                active_strategy = strat
                break
        
        # If strategy is unproven (not in pool or low stats), reset to BASE
        if not active_strategy or active_strategy.get('is_base', False):
            is_proven = False
        else:
            # Check if strategy meets proven criteria
            is_proven = (active_strategy.get('win_rate', 0) >= 0.72 and 
                        active_strategy.get('trade_count', 0) >= 20)
        
        if not is_proven:
            # FAILSAFE TRIGGERED: Reset to BASE_STRATEGY
            from ml.base_strategy import BASE_STRATEGY
            base_thresholds = BASE_STRATEGY[timeframe].copy()
            
            # Switch pool to base strategy
            self.strategy_pool.switch_to_base(timeframe)
            
            # Update thresholds to BASE_STRATEGY
            self.timeframe_stats[timeframe]['current_thresholds'] = base_thresholds
            self.timeframe_stats[timeframe]['consecutive_unprofitable'] = 0
            self.timeframe_stats[timeframe]['failsafe_resets'] += 1
            
            reset_count = self.timeframe_stats[timeframe]['failsafe_resets']
            print(f"⚠️  FAILSAFE RESET [{timeframe}]: 3 unprofitable trades with unproven strategy")
            print(f"   → Reset to BASE_STRATEGY (reset #{reset_count})")
            print(f"   → Will build new strategy from BASE defaults")
            
            # Save state
            self.save_state()
    
    def _check_strategy_switch(self, timeframe: str):
        """Check if we should switch strategies based on performance"""
        trade_count = self.get_trade_count(timeframe)
        win_rate = self.get_win_rate(timeframe, 'all')
        consecutive_losses = self.timeframe_stats[timeframe]['consecutive_losses']
        
        # Need minimum trades for switch consideration
        if trade_count < 10:
            return
        
        switch_reason = None
        
        # Check WR threshold (58%)
        if win_rate < 0.58:
            switch_reason = "wr_below_58"
        
        # Check consecutive losses (5)
        elif consecutive_losses >= 5:
            switch_reason = "5_consecutive_losses"
        
        if switch_reason:
            # Switch to next strategy in rotation
            new_strategy_id = self.strategy_pool.switch_strategy(
                timeframe=timeframe,
                reason=switch_reason
            )
            
            # Get new strategy thresholds
            new_thresholds = self.strategy_pool.get_active_strategy(timeframe)
            
            # Update thresholds
            self.timeframe_stats[timeframe]['current_thresholds'] = new_thresholds.copy()
            
            # Reset consecutive losses
            self.timeframe_stats[timeframe]['consecutive_losses'] = 0
            
            # Save state
            self.save_state()
    
    def _load_best_strategies_from_pool(self):
        """Load best strategies from pool on startup (only if strategy_pool feature enabled)"""
        # Note: This will be called but should be controlled by ML config in backtest
        # For now, just load without printing - backtest will control usage
        for tf in ['15m', '1h', '4h']:
            best_strategy = self.strategy_pool.get_best_strategy(tf)
            if best_strategy:
                # Store the proven strategy but don't activate it yet
                # The backtest will decide whether to use it based on ML config
                pass  # Don't auto-load strategies
    
    def get_stats(self, timeframe: str) -> Dict:
        """Get comprehensive stats for timeframe"""
        stats = self.timeframe_stats[timeframe]
        
        return {
            'timeframe': timeframe,
            'trade_count': self.get_trade_count(timeframe),
            'rolling_wr': self.get_rolling_win_rates(timeframe),
            'phase': stats['phase'],
            'confidence': stats['confidence'],
            'current_thresholds': stats['current_thresholds'].copy(),
            'best_strategy': stats.get('best_strategy'),
            'adjustment_count': len(stats['adjustments']),
            'last_adjustment': stats['adjustments'][-1] if stats['adjustments'] else None
        }
    
    def save_state(self):
        """Save all timeframe strategies to disk"""
        try:
            # Prepare data for JSON (deque -> list)
            save_data = {}
            for tf, stats in self.timeframe_stats.items():
                save_data[tf] = {
                    'trades': list(stats['trades']),
                    'current_thresholds': stats['current_thresholds'],
                    'adjustments': stats['adjustments'],
                    'phase': stats['phase'],
                    'confidence': stats['confidence'],
                    'best_strategy': stats['best_strategy'],
                    'created_at': stats['created_at'],
                    'last_updated': datetime.now().isoformat()
                }
            
            # Create directory if needed
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            # Save to file
            with open(self.state_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            
        except Exception as e:
            print(f"⚠️  Error saving strategy state: {e}")
    
    def load_state(self):
        """Load saved strategies from disk"""
        try:
            if not os.path.exists(self.state_file):
                print("📝 No saved strategies - using bootstrap defaults")
                return
            
            with open(self.state_file, 'r') as f:
                save_data = json.load(f)
            
            for tf in ['15m', '1h', '4h']:
                if tf in save_data:
                    data = save_data[tf]
                    
                    # Restore trades (list -> deque)
                    self.timeframe_stats[tf]['trades'] = deque(
                        data.get('trades', []), 
                        maxlen=100
                    )
                    
                    # Load best strategy if WR >= 70%
                    best = data.get('best_strategy')
                    if best and best.get('win_rate', 0) >= 0.70:
                        self.timeframe_stats[tf]['current_thresholds'] = best['thresholds'].copy()
                        print(f"✅ Loaded {tf} strategy: {best['win_rate']:.1%} WR ({best['trades']} trades)")
                    else:
                        # Use bootstrap defaults
                        self.timeframe_stats[tf]['current_thresholds'] = BOOTSTRAP_THRESHOLDS[tf].copy()
                    
                    # Restore other fields
                    self.timeframe_stats[tf]['adjustments'] = data.get('adjustments', [])
                    self.timeframe_stats[tf]['phase'] = data.get('phase', 'exploration')
                    self.timeframe_stats[tf]['confidence'] = data.get('confidence', 0.0)
                    self.timeframe_stats[tf]['best_strategy'] = best
                    self.timeframe_stats[tf]['created_at'] = data.get('created_at', datetime.now().isoformat())
            
            print(f"📂 Loaded saved strategies from {self.state_file}")
            
        except Exception as e:
            print(f"⚠️  Error loading strategy state: {e}")
            print("📝 Using bootstrap defaults")


if __name__ == "__main__":
    # Test the manager
    manager = TimeframeStrategyManager()
    
    # Simulate some trades
    print("\n🧪 Testing with simulated trades...\n")
    
    # 15m: Good performance
    for i in range(7):
        manager.record_trade('15m', {
            'won': i % 3 != 0,  # 66.7% win rate
            'pnl': 0.5 if i % 3 != 0 else -0.3,
            'duration_min': 45,
            'exit_type': 'TP' if i % 3 != 0 else 'SL'
        })
    
    # 4h: Poor performance
    manager.record_trade('4h', {
        'won': False,
        'pnl': -0.5,
        'duration_min': 400,
        'exit_type': 'SL'
    })
    
    # Print stats
    print("📊 TIMEFRAME STATISTICS\n")
    for tf in ['15m', '1h', '4h']:
        stats = manager.get_stats(tf)
        print(f"{tf}:")
        print(f"  Trades: {stats['trade_count']}")
        print(f"  Win Rate (L10): {stats['rolling_wr']['last_10']:.1%}")
        print(f"  Phase: {stats['phase']}")
        print(f"  Confidence: {stats['confidence']:.1%}")
        print(f"  Should adjust? {manager.should_adjust(tf, stats['rolling_wr']['last_10'])}")
        print()
