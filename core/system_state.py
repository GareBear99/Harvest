#!/usr/bin/env python3
"""
System State Tracker
Comprehensive dictionary-based tracking for all operations, configurations, and states
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class SystemStateTracker:
    """Tracks all system states, operations, and configurations"""
    
    def __init__(self, state_file: str = "ml/system_state.json"):
        self.state_file = state_file
        self.state = self._load_or_initialize()
    
    def _load_or_initialize(self) -> Dict:
        """Load existing state or create new one"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Initialize comprehensive state dictionary
        return {
            # System metadata
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'version': '3.0',
                'system_type': 'HARVEST Multi-Timeframe Trading Bot'
            },
            
            # Timeframe configurations
            'timeframes': {
                '1m': {
                    'enabled': True,
                    'aggregation_minutes': 1,
                    'confidence_threshold': 0.82,
                    'position_multiplier': 0.3,
                    'tp_multiplier': 1.2,
                    'sl_multiplier': 0.6,
                    'time_limit_minutes': 30,
                    'current_seed': None,
                    'base_strategy_overridden': False,
                    'last_backtest': None,
                    'best_known_seed': None,
                    'performance': {
                        'total_trades': 0,
                        'win_rate': 0.0,
                        'total_pnl': 0.0,
                        'best_wr': 0.0,
                        'best_seed_wr': None
                    }
                },
                '5m': {
                    'enabled': True,
                    'aggregation_minutes': 5,
                    'confidence_threshold': 0.80,
                    'position_multiplier': 0.4,
                    'tp_multiplier': 1.3,
                    'sl_multiplier': 0.65,
                    'time_limit_minutes': 60,
                    'current_seed': None,
                    'base_strategy_overridden': False,
                    'last_backtest': None,
                    'best_known_seed': None,
                    'performance': {
                        'total_trades': 0,
                        'win_rate': 0.0,
                        'total_pnl': 0.0,
                        'best_wr': 0.0,
                        'best_seed_wr': None
                    }
                },
                '15m': {
                    'enabled': True,
                    'aggregation_minutes': 15,
                    'confidence_threshold': 0.75,
                    'position_multiplier': 0.5,
                    'tp_multiplier': 1.5,
                    'sl_multiplier': 0.75,
                    'time_limit_minutes': 180,
                    'current_seed': None,
                    'base_strategy_overridden': False,
                    'last_backtest': None,
                    'best_known_seed': None,
                    'performance': {
                        'total_trades': 0,
                        'win_rate': 0.0,
                        'total_pnl': 0.0,
                        'best_wr': 0.0,
                        'best_seed_wr': None
                    }
                },
                '1h': {
                    'enabled': True,
                    'aggregation_minutes': 60,
                    'confidence_threshold': 0.75,
                    'position_multiplier': 1.0,
                    'tp_multiplier': 2.0,
                    'sl_multiplier': 1.0,
                    'time_limit_minutes': 720,
                    'current_seed': None,
                    'base_strategy_overridden': False,
                    'last_backtest': None,
                    'best_known_seed': None,
                    'performance': {
                        'total_trades': 0,
                        'win_rate': 0.0,
                        'total_pnl': 0.0,
                        'best_wr': 0.0,
                        'best_seed_wr': None
                    }
                },
                '4h': {
                    'enabled': True,
                    'aggregation_minutes': 240,
                    'confidence_threshold': 0.63,
                    'position_multiplier': 1.5,
                    'tp_multiplier': 2.5,
                    'sl_multiplier': 1.25,
                    'time_limit_minutes': 1440,
                    'current_seed': None,
                    'base_strategy_overridden': False,
                    'last_backtest': None,
                    'best_known_seed': None,
                    'performance': {
                        'total_trades': 0,
                        'win_rate': 0.0,
                        'total_pnl': 0.0,
                        'best_wr': 0.0,
                        'best_seed_wr': None
                    }
                }
            },
            
            # Seed system tracking
            'seed_system': {
                'total_seeds_tracked': 0,
                'whitelisted_seeds': 0,
                'blacklisted_seeds': 0,
                'seeds_tested_today': 0,
                'last_seed_test': None,
                'seed_combinations': 37600000000,  # 37.6 billion
                'registry_file': 'ml/seed_registry.json',
                'snapshot_file': 'ml/seed_snapshots.json',
                'catalog_file': 'ml/seed_catalog.json',
                'tracker_file': 'ml/seed_performance_tracker.json'
            },
            
            # Operations tracking
            'operations': {
                'backtests_run': 0,
                'last_backtest': None,
                'last_backtest_seed': None,
                'seed_tests_run': 0,
                'last_seed_test': None,
                'strategy_overwrites': 0,
                'last_overwrite': None,
                'errors_encountered': 0,
                'timeouts_encountered': 0,
                'successful_operations': 0
            },
            
            # Dashboard tracking
            'dashboard': {
                'sessions': 0,
                'last_session': None,
                'panels': {
                    'seed_status': True,
                    'bot_status': True,
                    'performance': True,
                    'system_health': True
                },
                'commands_used': {
                    'quit': 0,
                    'refresh': 0,
                    'seed_browser': 0,
                    'ml_control': 0,
                    'help': 0,
                    'docs': 0,
                    'backtest_control': 0,
                    'live_trading': 0
                }
            },
            
            # Live trading tracking
            'live_trading': {
                'enabled': False,
                'started_at': None,
                'total_trades': 0,
                'positions_opened': 0,
                'positions_closed': 0,
                'current_balance': 0.0,
                'starting_balance': 0.0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'best_trade': None,
                'worst_trade': None
            },
            
            # Assets tracking
            'assets': {
                'ETH': {
                    'ml_enabled': False,
                    'trades': 0,
                    'pnl': 0.0,
                    'win_rate': 0.0,
                    'active_strategy': 'BASE_STRATEGY'
                },
                'BTC': {
                    'ml_enabled': False,
                    'trades': 0,
                    'pnl': 0.0,
                    'win_rate': 0.0,
                    'active_strategy': 'BASE_STRATEGY'
                }
            },
            
            # Files tracking
            'files': {
                'core': {
                    'backtest_90_complete.py': True,
                    'pre_trading_check.py': True,
                    'ml/seed_tester.py': True,
                    'ml/base_strategy.py': True
                },
                'dashboard': {
                    'terminal_ui.py': True,
                    'panels.py': True,
                    'backtest_control.py': True,
                    'ml_control.py': True,
                    'seed_browser.py': True,
                    'timeout_manager.py': True
                },
                'data': {
                    'eth_90days.json': os.path.exists('data/eth_90days.json'),
                    'btc_90days.json': os.path.exists('data/btc_90days.json')
                },
                'ml': {
                    'seed_registry.json': os.path.exists('ml/seed_registry.json'),
                    'seed_catalog.json': os.path.exists('ml/seed_catalog.json'),
                    'seed_whitelist.json': os.path.exists('ml/seed_whitelist.json'),
                    'base_strategy_backup.json': os.path.exists('ml/base_strategy_backup.json'),
                    'base_strategy_overrides.json': os.path.exists('ml/base_strategy_overrides.json')
                }
            },
            
            # Error tracking
            'errors': {
                'last_error': None,
                'last_error_time': None,
                'error_count_by_type': {},
                'timeout_count_by_operation': {}
            },
            
            # Performance metrics
            'performance': {
                'total_runtime_seconds': 0,
                'avg_backtest_duration': 0,
                'avg_seed_test_duration': 0,
                'fastest_backtest': None,
                'slowest_backtest': None
            }
        }
    
    def save(self):
        """Save state to file"""
        self.state['metadata']['last_updated'] = datetime.now().isoformat()
        
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    # Timeframe methods
    def update_timeframe_seed(self, timeframe: str, seed: int):
        """Update current seed for a timeframe"""
        self.state['timeframes'][timeframe]['current_seed'] = seed
        self.state['timeframes'][timeframe]['last_backtest'] = datetime.now().isoformat()
        self.save()
    
    def mark_base_strategy_overridden(self, timeframe: str, seed: int):
        """Mark BASE_STRATEGY as overridden for timeframe"""
        self.state['timeframes'][timeframe]['base_strategy_overridden'] = True
        self.state['timeframes'][timeframe]['current_seed'] = seed
        self.state['operations']['strategy_overwrites'] += 1
        self.state['operations']['last_overwrite'] = {
            'timeframe': timeframe,
            'seed': seed,
            'timestamp': datetime.now().isoformat()
        }
        self.save()
    
    def update_timeframe_performance(self, timeframe: str, trades: int, win_rate: float, pnl: float):
        """Update performance metrics for timeframe"""
        perf = self.state['timeframes'][timeframe]['performance']
        perf['total_trades'] = trades
        perf['win_rate'] = win_rate
        perf['total_pnl'] = pnl
        
        # Update best if improved
        if win_rate > perf['best_wr']:
            perf['best_wr'] = win_rate
            perf['best_seed_wr'] = self.state['timeframes'][timeframe]['current_seed']
        
        self.save()
    
    def set_best_seed(self, timeframe: str, seed: int, win_rate: float):
        """Set best known seed for timeframe"""
        self.state['timeframes'][timeframe]['best_known_seed'] = seed
        self.state['timeframes'][timeframe]['performance']['best_seed_wr'] = seed
        self.state['timeframes'][timeframe]['performance']['best_wr'] = win_rate
        self.save()
    
    # Operations methods
    def record_backtest(self, seed: Optional[int] = None, duration: float = 0):
        """Record backtest execution"""
        self.state['operations']['backtests_run'] += 1
        self.state['operations']['last_backtest'] = datetime.now().isoformat()
        self.state['operations']['last_backtest_seed'] = seed
        self.state['operations']['successful_operations'] += 1
        
        # Update performance metrics
        if duration > 0:
            count = self.state['operations']['backtests_run']
            current_avg = self.state['performance']['avg_backtest_duration']
            self.state['performance']['avg_backtest_duration'] = (
                (current_avg * (count - 1) + duration) / count
            )
        
        self.save()
    
    def record_seed_test(self, timeframe: str, test_type: str, duration: float = 0):
        """Record seed test execution"""
        self.state['operations']['seed_tests_run'] += 1
        self.state['operations']['last_seed_test'] = {
            'timeframe': timeframe,
            'type': test_type,
            'timestamp': datetime.now().isoformat()
        }
        self.state['seed_system']['seeds_tested_today'] += 1
        self.state['operations']['successful_operations'] += 1
        
        # Update performance metrics
        if duration > 0:
            count = self.state['operations']['seed_tests_run']
            current_avg = self.state['performance']['avg_seed_test_duration']
            self.state['performance']['avg_seed_test_duration'] = (
                (current_avg * (count - 1) + duration) / count
            )
        
        self.save()
    
    def record_error(self, error_type: str, error_msg: str):
        """Record error occurrence"""
        self.state['errors']['last_error'] = error_msg
        self.state['errors']['last_error_time'] = datetime.now().isoformat()
        self.state['operations']['errors_encountered'] += 1
        
        # Track by type
        if error_type not in self.state['errors']['error_count_by_type']:
            self.state['errors']['error_count_by_type'][error_type] = 0
        self.state['errors']['error_count_by_type'][error_type] += 1
        
        self.save()
    
    def record_timeout(self, operation: str):
        """Record timeout occurrence"""
        self.state['operations']['timeouts_encountered'] += 1
        
        if operation not in self.state['errors']['timeout_count_by_operation']:
            self.state['errors']['timeout_count_by_operation'][operation] = 0
        self.state['errors']['timeout_count_by_operation'][operation] += 1
        
        self.save()
    
    # Dashboard methods
    def record_dashboard_session(self):
        """Record dashboard session start"""
        self.state['dashboard']['sessions'] += 1
        self.state['dashboard']['last_session'] = datetime.now().isoformat()
        self.save()
    
    def record_dashboard_command(self, command: str):
        """Record dashboard command usage"""
        if command in self.state['dashboard']['commands_used']:
            self.state['dashboard']['commands_used'][command] += 1
            self.save()
    
    # Seed system methods
    def update_seed_counts(self, total: int, whitelisted: int, blacklisted: int):
        """Update seed system counts"""
        self.state['seed_system']['total_seeds_tracked'] = total
        self.state['seed_system']['whitelisted_seeds'] = whitelisted
        self.state['seed_system']['blacklisted_seeds'] = blacklisted
        self.save()
    
    # Asset methods
    def update_asset_performance(self, asset: str, trades: int, pnl: float, win_rate: float):
        """Update asset performance"""
        if asset in self.state['assets']:
            self.state['assets'][asset]['trades'] = trades
            self.state['assets'][asset]['pnl'] = pnl
            self.state['assets'][asset]['win_rate'] = win_rate
            self.save()
    
    def set_ml_enabled(self, asset: str, enabled: bool):
        """Set ML enabled status for asset"""
        if asset in self.state['assets']:
            self.state['assets'][asset]['ml_enabled'] = enabled
            self.save()
    
    # Query methods
    def get_timeframe_info(self, timeframe: str) -> Dict:
        """Get complete info for a timeframe"""
        return self.state['timeframes'].get(timeframe, {})
    
    def get_all_timeframes(self) -> Dict:
        """Get info for all timeframes"""
        return self.state['timeframes']
    
    def get_operations_summary(self) -> Dict:
        """Get operations summary"""
        return self.state['operations']
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        return self.state['performance']
    
    def get_seed_system_status(self) -> Dict:
        """Get seed system status"""
        return self.state['seed_system']
    
    def get_full_state(self) -> Dict:
        """Get complete state dictionary"""
        return self.state.copy()
    
    def print_summary(self):
        """Print readable summary of system state"""
        print("\n" + "="*80)
        print("SYSTEM STATE SUMMARY")
        print("="*80)
        
        print("\n📊 TIMEFRAMES:")
        for tf, data in self.state['timeframes'].items():
            override = "⚠️  OVERRIDDEN" if data['base_strategy_overridden'] else "✅ Original"
            print(f"  {tf:3s}: {override} | Seed: {data['current_seed']} | "
                  f"WR: {data['performance']['win_rate']:.1%} | "
                  f"Trades: {data['performance']['total_trades']}")
        
        print("\n🔬 OPERATIONS:")
        ops = self.state['operations']
        print(f"  Backtests: {ops['backtests_run']}")
        print(f"  Seed Tests: {ops['seed_tests_run']}")
        print(f"  Strategy Overwrites: {ops['strategy_overwrites']}")
        print(f"  Errors: {ops['errors_encountered']}")
        print(f"  Timeouts: {ops['timeouts_encountered']}")
        
        print("\n🌱 SEED SYSTEM:")
        seeds = self.state['seed_system']
        print(f"  Tracked: {seeds['total_seeds_tracked']}")
        print(f"  Whitelisted: {seeds['whitelisted_seeds']}")
        print(f"  Blacklisted: {seeds['blacklisted_seeds']}")
        
        print("\n💰 ASSETS:")
        for asset, data in self.state['assets'].items():
            ml = "✅ ENABLED" if data['ml_enabled'] else "❌ DISABLED"
            print(f"  {asset}: ML {ml} | Trades: {data['trades']} | "
                  f"WR: {data['win_rate']:.1%} | P&L: ${data['pnl']:.2f}")
        
        print("\n⚡ PERFORMANCE:")
        perf = self.state['performance']
        if perf['avg_backtest_duration'] > 0:
            print(f"  Avg Backtest: {perf['avg_backtest_duration']:.1f}s")
        if perf['avg_seed_test_duration'] > 0:
            print(f"  Avg Seed Test: {perf['avg_seed_test_duration']:.1f}s")
        
        print("\n" + "="*80)


# Global instance
_state_tracker = None

def get_state_tracker() -> SystemStateTracker:
    """Get global state tracker instance"""
    global _state_tracker
    if _state_tracker is None:
        _state_tracker = SystemStateTracker()
    return _state_tracker


if __name__ == "__main__":
    # Test the tracker
    tracker = SystemStateTracker()
    
    # Simulate some operations
    tracker.record_backtest(seed=42, duration=120.5)
    tracker.update_timeframe_seed('15m', 15542880)
    tracker.update_timeframe_performance('15m', trades=45, win_rate=0.763, pnl=12.50)
    tracker.set_best_seed('15m', 15542880, 0.763)
    tracker.record_seed_test('15m', 'top10', duration=300.0)
    
    # Print summary
    tracker.print_summary()
    
    print(f"\n✅ State saved to: {tracker.state_file}")
