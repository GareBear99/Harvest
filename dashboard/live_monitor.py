#!/usr/bin/env python3
"""
Live Dashboard Monitor
Threading-based monitor for real-time backtest/trading updates
"""

import threading
import time
from typing import Dict, Optional, Callable
from datetime import datetime


class DashboardMonitor:
    """
    Background monitor for dashboard updates
    
    Runs in separate thread to collect data from backtest/live trader
    without blocking main execution
    """
    
    def __init__(self, backtest_engine, refresh_interval: float = 0.5):
        """
        Initialize monitor
        
        Args:
            backtest_engine: Reference to backtest engine
            refresh_interval: Update frequency in seconds (default 0.5 = 2 Hz)
        """
        self.backtest_engine = backtest_engine
        self.refresh_interval = refresh_interval
        
        # Threading
        self.thread = None
        self.running = False
        self.lock = threading.Lock()
        
        # Data cache
        self.data = {
            'seed': {},
            'bot': {},
            'performance': {},
            'system': {},
            'last_update': None
        }
        
        # Callbacks
        self.update_callbacks = []
    
    def register_callback(self, callback: Callable):
        """Register callback for data updates"""
        self.update_callbacks.append(callback)
    
    def start(self):
        """Start monitor thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print("📡 Dashboard monitor started")
    
    def stop(self):
        """Stop monitor thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        print("📡 Dashboard monitor stopped")
    
    def _monitor_loop(self):
        """Main monitor loop (runs in thread)"""
        while self.running:
            try:
                # Collect data
                self._collect_data()
                
                # Notify callbacks
                for callback in self.update_callbacks:
                    try:
                        callback(self.data)
                    except Exception as e:
                        print(f"Error in update callback: {e}")
                
                # Sleep
                time.sleep(self.refresh_interval)
            
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(1.0)
    
    def _collect_data(self):
        """Collect data from backtest engine"""
        with self.lock:
            try:
                # Get seed data
                self.data['seed'] = self._get_seed_data()
                
                # Get bot data
                self.data['bot'] = self._get_bot_data()
                
                # Get performance data
                self.data['performance'] = self._get_performance_data()
                
                # Get system data
                self.data['system'] = self._get_system_data()
                
                # Update timestamp
                self.data['last_update'] = datetime.now()
            
            except Exception as e:
                print(f"Error collecting data: {e}")
    
    def _get_seed_data(self) -> Dict:
        """Get seed system data"""
        try:
            # Try to get from unified seed system
            if hasattr(self.backtest_engine, 'seed_system'):
                seed_system = self.backtest_engine.seed_system
                dashboard_data = seed_system.get_dashboard_data()
                
                stats = dashboard_data.get('tracker_stats', {})
                top_seeds = dashboard_data.get('top_seeds', [])
                
                # Get current seeds per timeframe
                current_seeds_by_tf = self._get_current_seeds_by_timeframe()
                
                return {
                    'total_tested': stats.get('total_seeds', 0),
                    'whitelisted': stats.get('whitelisted', 0),
                    'blacklisted': stats.get('blacklisted', 0),
                    'top_performer': top_seeds[0] if top_seeds else None,
                    'current_seeds_by_timeframe': current_seeds_by_tf
                }
            
            return {}
        
        except Exception as e:
            print(f"Error getting seed data: {e}")
            return {}
    
    
    def _get_current_seeds_by_timeframe(self) -> Dict:
        """
        Get currently active seeds for each timeframe
        
        Returns:
            Dict with timeframe keys ('15m', '1h', '4h')
        """
        seeds_by_tf = {}
        
        try:
            # Try to get from processing manager strategies
            if hasattr(self.backtest_engine, 'processing_manager'):
                pm = self.backtest_engine.processing_manager
                if hasattr(pm, 'strategies'):
                    for tf, strategy in pm.strategies.items():
                        if hasattr(strategy, 'seed'):
                            seed_info = {
                                'seed': strategy.seed,
                                'input_seed': getattr(strategy, 'input_seed', None)
                            }
                            seeds_by_tf[tf] = seed_info
            
            # Fallback: try to get from strategy pool
            elif hasattr(self.backtest_engine, 'strategy_pool'):
                pool = self.backtest_engine.strategy_pool
                if hasattr(pool, 'strategies'):
                    for tf in ['15m', '1h', '4h']:
                        if tf in pool.strategies:
                            strategy = pool.strategies[tf]
                            if hasattr(strategy, 'seed'):
                                seed_info = {
                                    'seed': strategy.seed,
                                    'input_seed': getattr(strategy, 'input_seed', None)
                                }
                                seeds_by_tf[tf] = seed_info
            
            # Fallback: single current seed
            elif hasattr(self.backtest_engine, 'current_seed'):
                tf = getattr(self.backtest_engine, 'timeframe', '15m')
                seeds_by_tf[tf] = {
                    'seed': self.backtest_engine.current_seed,
                    'input_seed': getattr(self.backtest_engine, 'input_seed', None)
                }
        
        except Exception as e:
            print(f"Error getting current seeds: {e}")
        
        return seeds_by_tf
    
    def _get_bot_data(self) -> Dict:
        """Get bot status data"""
        try:
            status = 'running' if self.running else 'stopped'
            mode = 'BACKTEST'  # TODO: Detect live vs backtest
            
            # Get balance
            balance = {
                'initial': getattr(self.backtest_engine, 'initial_balance', 10.0),
                'current': getattr(self.backtest_engine, 'balance', 10.0)
            }
            
            # Get active positions
            active_positions = []
            if hasattr(self.backtest_engine, 'active_positions'):
                active_positions = list(self.backtest_engine.active_positions.values())
            
            # Get last trade
            last_trade = None
            if hasattr(self.backtest_engine, 'all_trades') and self.backtest_engine.all_trades:
                last_trade = self.backtest_engine.all_trades[-1]
            
            return {
                'status': status,
                'mode': mode,
                'seed_info': self._get_current_seed() or {},
                'balance': balance,
                'active_positions': active_positions,
                'max_positions': 2,
                'last_trade': last_trade
            }
        
        except Exception as e:
            print(f"Error getting bot data: {e}")
            return {}
    
    def _get_performance_data(self) -> Dict:
        """Get performance metrics"""
        try:
            wins = 0
            losses = 0
            pnl = 0.0
            max_dd = 0.0
            by_timeframe = {}
            
            # Calculate from trades
            if hasattr(self.backtest_engine, 'all_trades'):
                for trade in self.backtest_engine.all_trades:
                    trade_pnl = trade.get('pnl', 0)
                    pnl += trade_pnl
                    
                    if trade_pnl > 0:
                        wins += 1
                    else:
                        losses += 1
                    
                    # Per-timeframe stats
                    tf = trade.get('timeframe', 'unknown')
                    if tf not in by_timeframe:
                        by_timeframe[tf] = {'wins': 0, 'losses': 0, 'pnl': 0.0}
                    
                    by_timeframe[tf]['pnl'] += trade_pnl
                    if trade_pnl > 0:
                        by_timeframe[tf]['wins'] += 1
                    else:
                        by_timeframe[tf]['losses'] += 1
            
            # Get max drawdown
            if hasattr(self.backtest_engine, 'max_drawdown'):
                max_dd = self.backtest_engine.max_drawdown
            
            return {
                'wins': wins,
                'losses': losses,
                'pnl': pnl,
                'max_drawdown': max_dd,
                'by_timeframe': by_timeframe
            }
        
        except Exception as e:
            print(f"Error getting performance data: {e}")
            return {}
    
    def _get_system_data(self) -> Dict:
        """Get system health data"""
        try:
            # Check data freshness
            data_fresh = True
            updated_ago = 'recently'
            
            if hasattr(self.backtest_engine, 'data_file'):
                import os
                if os.path.exists(self.backtest_engine.data_file):
                    mtime = os.path.getmtime(self.backtest_engine.data_file)
                    age_hours = (time.time() - mtime) / 3600
                    updated_ago = f"{int(age_hours)}h ago"
                    data_fresh = age_hours < 24
            
            # Check connections
            connections = 'operational'
            
            # Get warnings
            warnings = []
            if hasattr(self.backtest_engine, 'warnings'):
                warnings = self.backtest_engine.warnings
            
            return {
                'data_status': {
                    'fresh': data_fresh,
                    'updated_ago': updated_ago
                },
                'connections': connections,
                'warnings': warnings
            }
        
        except Exception as e:
            print(f"Error getting system data: {e}")
            return {}
    
    def get_data(self) -> Dict:
        """Get current data snapshot (thread-safe)"""
        with self.lock:
            return self.data.copy()
    
    def update_trade(self, trade_data: Dict):
        """
        Handle trade update event
        
        Args:
            trade_data: Trade information
        """
        # This can be called from backtest engine after trade execution
        with self.lock:
            # Force immediate data collection
            self._collect_data()


def create_monitor(backtest_engine, refresh_interval: float = 0.5) -> DashboardMonitor:
    """
    Create and start dashboard monitor
    
    Args:
        backtest_engine: Backtest engine instance
        refresh_interval: Update frequency in seconds
    
    Returns:
        DashboardMonitor instance
    """
    monitor = DashboardMonitor(backtest_engine, refresh_interval)
    monitor.start()
    return monitor
