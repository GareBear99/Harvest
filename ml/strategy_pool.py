"""
Strategy Pool - Manages multiple proven strategies per timeframe
Handles automatic switching based on performance (58% WR or 5 consecutive losses)
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Optional, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.base_strategy import BASE_STRATEGY, STRATEGY_EVALUATION, get_base_strategy
from ml.strategy_seed_generator import generate_strategy_seed


class StrategyPool:
    """
    Manages up to 3 proven strategies per timeframe
    
    Features:
    - Stores up to 3 strategies per timeframe (72%+ WR, 20+ trades)
    - Automatic switching when performance degrades
    - Switch triggers: WR < 58% or 5 consecutive losses
    - Rotation: base → strategy_1 → strategy_2 → strategy_3 → base
    """
    
    def __init__(self, active_timeframes: List[str] = None, pool_file: str = "ml/strategy_pool.json"):
        self.pool_file = pool_file
        
        # Default to all timeframes if none specified
        if active_timeframes is None:
            active_timeframes = ['15m', '1h', '4h']
        
        self.active_timeframes = active_timeframes
        
        # Initialize pool structure ONLY for active timeframes
        self.pools = {}
        for tf in active_timeframes:
            self.pools[tf] = self._init_timeframe_pool(tf)
        
        # Load saved state
        self.load_state()
        
        print("💼 StrategyPool initialized")
        for tf in self.active_timeframes:
            active = self.get_active_strategy_id(tf)
            count = len([s for s in self.pools[tf]['strategies'].keys() if s != 'base'])
            print(f"   {tf}: {count} proven strategies, active='{active}'")
    
    def _init_timeframe_pool(self, timeframe: str) -> Dict:
        """Initialize pool structure for a timeframe"""
        base_thresholds = get_base_strategy(timeframe)
        base_seed = generate_strategy_seed(timeframe, base_thresholds)
        
        return {
            'active_strategy_id': 'base',
            'strategies': {
                'base': {
                    'thresholds': base_thresholds,
                    'seed': base_seed,
                    'proven_wr': None,
                    'proven_trades': 0,
                    'created_at': datetime.now().isoformat(),
                    'last_used': datetime.now().isoformat(),
                    'is_base': True
                }
            },
            'consecutive_losses': 0,
            'switch_history': []
        }
    
    def add_proven_strategy(
        self,
        timeframe: str,
        thresholds: Dict[str, float],
        win_rate: float,
        trade_count: int,
        data_source: str = "unknown"
    ) -> bool:
        """
        Add a proven strategy to the pool (max 3 per timeframe)
        
        Args:
            timeframe: '15m', '1h', or '4h'
            thresholds: Strategy threshold values
            win_rate: Proven win rate (should be 72%+)
            trade_count: Number of trades (should be 20+)
            data_source: Dataset where strategy was proven
        
        Returns:
            True if added, False if pool full or duplicate
        """
        if timeframe not in self.pools:
            return False
        
        pool = self.pools[timeframe]
        
        # Check if strategy already exists (compare thresholds)
        if self._strategy_exists(timeframe, thresholds):
            return False
        
        # Count non-base strategies
        strategy_count = len([s for s in pool['strategies'].keys() if s != 'base'])
        max_strategies = STRATEGY_EVALUATION['max_strategies_per_timeframe']
        
        if strategy_count >= max_strategies:
            # Pool full - replace worst performing strategy
            self._replace_worst_strategy(timeframe, thresholds, win_rate, trade_count, data_source)
            return True
        
        # Add new strategy
        strategy_id = f"strategy_{strategy_count + 1}"
        strategy_seed = generate_strategy_seed(timeframe, thresholds)
        
        pool['strategies'][strategy_id] = {
            'thresholds': thresholds.copy(),
            'seed': strategy_seed,
            'proven_wr': win_rate,
            'proven_trades': trade_count,
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'proven_on_data': data_source,
            'is_base': False
        }
        
        self.save_state()
        return True
    
    def _strategy_exists(self, timeframe: str, thresholds: Dict[str, float]) -> bool:
        """Check if strategy with these thresholds already exists"""
        pool = self.pools[timeframe]
        
        for strategy in pool['strategies'].values():
            if self._thresholds_match(strategy['thresholds'], thresholds):
                return True
        
        return False
    
    def _thresholds_match(self, thresh1: Dict, thresh2: Dict, tolerance: float = 0.01) -> bool:
        """Check if two threshold sets are essentially identical"""
        for key in thresh1.keys():
            if key not in thresh2:
                return False
            if abs(thresh1[key] - thresh2[key]) > tolerance:
                return False
        return True
    
    def _replace_worst_strategy(
        self,
        timeframe: str,
        new_thresholds: Dict,
        new_wr: float,
        new_trades: int,
        data_source: str
    ):
        """Replace worst performing strategy with new one"""
        pool = self.pools[timeframe]
        
        # Find worst non-base strategy
        worst_id = None
        worst_wr = 1.0
        
        for sid, strategy in pool['strategies'].items():
            if sid == 'base':
                continue
            if strategy['proven_wr'] < worst_wr:
                worst_wr = strategy['proven_wr']
                worst_id = sid
        
        if worst_id and new_wr > worst_wr:
            # Replace worst with new
            new_seed = generate_strategy_seed(timeframe, new_thresholds)
            
            pool['strategies'][worst_id] = {
                'thresholds': new_thresholds.copy(),
                'seed': new_seed,
                'proven_wr': new_wr,
                'proven_trades': new_trades,
                'created_at': datetime.now().isoformat(),
                'last_used': None,
                'proven_on_data': data_source,
                'is_base': False
            }
            print(f"   ♻️  Replaced worst {timeframe} strategy ({worst_wr:.1%}) with new ({new_wr:.1%})")
    
    def get_active_strategy(self, timeframe: str) -> Dict[str, float]:
        """Get thresholds for currently active strategy"""
        pool = self.pools[timeframe]
        active_id = pool['active_strategy_id']
        return pool['strategies'][active_id]['thresholds'].copy()
    
    def get_active_strategy_id(self, timeframe: str) -> str:
        """Get ID of currently active strategy"""
        return self.pools[timeframe]['active_strategy_id']
    
    def get_best_strategy(self, timeframe: str) -> Optional[Dict]:
        """Get best strategy from pool (highest proven WR)"""
        pool = self.pools[timeframe]
        
        best_strategy = None
        best_wr = 0.0
        
        for sid, strategy in pool['strategies'].items():
            if sid == 'base':
                continue
            if strategy['proven_wr'] and strategy['proven_wr'] > best_wr:
                best_wr = strategy['proven_wr']
                best_strategy = strategy.copy()
                best_strategy['strategy_id'] = sid
        
        return best_strategy
    
    def switch_strategy(self, timeframe: str, reason: str) -> str:
        """
        Switch to next strategy in rotation
        
        Rotation order: base → strategy_1 → strategy_2 → strategy_3 → base
        
        Args:
            timeframe: '15m', '1h', or '4h'
            reason: Why we're switching (e.g. "wr_below_58", "5_consecutive_losses")
        
        Returns:
            ID of new active strategy
        """
        pool = self.pools[timeframe]
        current_id = pool['active_strategy_id']
        
        # Define rotation order
        rotation = ['base', 'strategy_1', 'strategy_2', 'strategy_3']
        
        try:
            current_idx = rotation.index(current_id)
        except ValueError:
            current_idx = 0
        
        # Find next available strategy
        for i in range(1, len(rotation)):
            next_idx = (current_idx + i) % len(rotation)
            next_id = rotation[next_idx]
            
            if next_id in pool['strategies']:
                # Found next strategy - switch to it
                pool['active_strategy_id'] = next_id
                pool['strategies'][next_id]['last_used'] = datetime.now().isoformat()
                
                # Record switch in history
                pool['switch_history'].append({
                    'timestamp': datetime.now().isoformat(),
                    'from_strategy': current_id,
                    'to_strategy': next_id,
                    'reason': reason,
                    'consecutive_losses_at_switch': pool['consecutive_losses']
                })
                
                # Keep only last 50 switches
                if len(pool['switch_history']) > 50:
                    pool['switch_history'] = pool['switch_history'][-50:]
                
                # Save state
                self.save_state()
                
                print(f"\n🔄 STRATEGY SWITCH: {timeframe}")
                print(f"   {current_id} → {next_id}")
                print(f"   Reason: {reason}")
                
                return next_id
        
        # No other strategies available - stay on current
        print(f"⚠️  No alternative strategies available for {timeframe}, staying on {current_id}")
        return current_id
    
    def switch_to_base(self, timeframe: str, reason: str = "failsafe_reset"):
        """Switch to base strategy (for failsafe)"""
        pool = self.pools[timeframe]
        old_id = pool['active_strategy_id']
        
        # Don't record switch if already on base
        if old_id == 'base':
            return 'base'
        
        pool['active_strategy_id'] = 'base'
        pool['consecutive_losses'] = 0
        pool['strategies']['base']['last_used'] = datetime.now().isoformat()
        
        pool['switch_history'].append({
            'timestamp': datetime.now().isoformat(),
            'from_strategy': old_id,
            'to_strategy': 'base',
            'reason': reason,
            'consecutive_losses_at_switch': pool['consecutive_losses']
        })
        
        # Keep only last 50 switches
        if len(pool['switch_history']) > 50:
            pool['switch_history'] = pool['switch_history'][-50:]
        
        self.save_state()
        return 'base'
    
    def reset_to_base(self, timeframe: str, reason: str = "manual_reset"):
        """Reset timeframe to base strategy (manual)"""
        self.switch_to_base(timeframe, reason)
        print(f"🔁 {timeframe} reset to base strategy")
    
    def record_consecutive_loss(self, timeframe: str):
        """Increment consecutive loss counter"""
        self.pools[timeframe]['consecutive_losses'] += 1
    
    def reset_consecutive_losses(self, timeframe: str):
        """Reset consecutive loss counter (called on win)"""
        self.pools[timeframe]['consecutive_losses'] = 0
    
    def get_consecutive_losses(self, timeframe: str) -> int:
        """Get current consecutive loss count"""
        return self.pools[timeframe]['consecutive_losses']
    
    def get_pool_stats(self, timeframe: str) -> Dict:
        """Get comprehensive pool statistics for timeframe"""
        pool = self.pools[timeframe]
        
        strategies_list = []
        for sid, strategy in pool['strategies'].items():
            strategies_list.append({
                'id': sid,
                'is_base': strategy.get('is_base', False),
                'proven_wr': strategy.get('proven_wr'),
                'proven_trades': strategy.get('proven_trades', 0),
                'last_used': strategy.get('last_used'),
                'is_active': sid == pool['active_strategy_id']
            })
        
        return {
            'timeframe': timeframe,
            'active_strategy_id': pool['active_strategy_id'],
            'consecutive_losses': pool['consecutive_losses'],
            'strategies': strategies_list,
            'total_switches': len(pool['switch_history']),
            'last_switch': pool['switch_history'][-1] if pool['switch_history'] else None
        }
    
    def save_state(self):
        """Save strategy pool to disk"""
        try:
            os.makedirs(os.path.dirname(self.pool_file), exist_ok=True)
            
            with open(self.pool_file, 'w') as f:
                json.dump(self.pools, f, indent=2)
            
        except Exception as e:
            print(f"⚠️  Error saving strategy pool: {e}")
    
    def load_state(self):
        """Load strategy pool from disk"""
        try:
            if not os.path.exists(self.pool_file):
                print("📝 No saved strategy pool - using base strategies")
                return
            
            with open(self.pool_file, 'r') as f:
                loaded_pools = json.load(f)
            
            # Merge loaded data with initialized structure
            for tf in ['15m', '1h', '4h']:
                if tf in loaded_pools:
                    self.pools[tf] = loaded_pools[tf]
                    # Ensure base strategy always present
                    if 'base' not in self.pools[tf]['strategies']:
                        self.pools[tf]['strategies']['base'] = {
                            'thresholds': get_base_strategy(tf),
                            'proven_wr': None,
                            'proven_trades': 0,
                            'created_at': datetime.now().isoformat(),
                            'last_used': datetime.now().isoformat(),
                            'is_base': True
                        }
            
            print(f"📂 Loaded strategy pool from {self.pool_file}")
            
        except Exception as e:
            print(f"⚠️  Error loading strategy pool: {e}")
            print("📝 Using default pool structure")


if __name__ == "__main__":
    # Test the strategy pool
    pool = StrategyPool()
    
    print("\n🧪 Testing StrategyPool...\n")
    
    # Test adding a proven strategy
    test_strategy = {
        'min_confidence': 0.75,
        'min_volume': 1.25,
        'min_trend': 0.60,
        'min_adx': 28,
        'min_roc': -1.2,
        'atr_min': 0.4,
        'atr_max': 3.5
    }
    
    added = pool.add_proven_strategy('15m', test_strategy, 0.76, 50, 'test_data')
    print(f"Add strategy result: {added}\n")
    
    # Get pool stats
    stats = pool.get_pool_stats('15m')
    print("15m Pool Stats:")
    print(f"  Active: {stats['active_strategy_id']}")
    print(f"  Consecutive losses: {stats['consecutive_losses']}")
    print(f"  Strategies: {len(stats['strategies'])}")
    for s in stats['strategies']:
        print(f"    {s['id']}: {'(active)' if s['is_active'] else ''} "
              f"WR={s['proven_wr']}")
    
    # Test switching
    print("\nTesting switch...")
    new_id = pool.switch_strategy('15m', 'test_switch')
    print(f"New active: {new_id}")
