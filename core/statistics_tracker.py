#!/usr/bin/env python3
"""
Statistics Tracker for HARVEST
Tracks historical trading statistics, daily metrics, and timeframe-specific performance
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class TradeRecord:
    """Record of a single trade"""
    timestamp: str
    timeframe: str
    strategy: str  # 'ER90' or 'SIB'
    side: str  # 'LONG' or 'SHORT'
    entry: float
    stop: float
    tp1: float
    notional: float
    outcome: Optional[str] = None  # 'WIN', 'LOSS', 'BREAKEVEN'
    pnl: Optional[float] = None
    duration_min: Optional[int] = None
    closed_at: Optional[str] = None


@dataclass
class DailyStats:
    """Statistics for a single day"""
    date: str
    trades_count: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0
    uptime_seconds: int = 0
    active_time_seconds: int = 0  # Time actually trading vs idle
    sessions: int = 0


class StatisticsTracker:
    """
    Track and persist trading statistics.
    
    Features:
    - Historical trade records
    - Daily metrics (trades, P&L, uptime)
    - Timeframe-specific performance
    - Session tracking
    - All-time statistics
    """
    
    def __init__(self, stats_file: str = "data/trading_statistics.json"):
        self.stats_file = Path(stats_file)
        self.stats_file.parent.mkdir(exist_ok=True)
        
        # Current session tracking
        self.session_start: Optional[datetime] = None
        self.session_end: Optional[datetime] = None
        self.session_trades: List[TradeRecord] = []
        
        # Load existing stats
        self.data = self._load_stats()
    
    def _load_stats(self) -> Dict:
        """Load statistics from file"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Initialize new stats structure
        return {
            'first_trade_date': None,
            'last_trade_date': None,
            'all_time': {
                'total_trades': 0,
                'total_wins': 0,
                'total_losses': 0,
                'total_pnl': 0.0,
                'total_uptime_hours': 0.0,
                'total_sessions': 0,
                'best_day_pnl': 0.0,
                'best_day_date': None,
                'worst_day_pnl': 0.0,
                'worst_day_date': None
            },
            'by_timeframe': {
                '1m': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'seed': None},
                '5m': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'seed': None},
                '15m': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'seed': None},
                '1h': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'seed': None},
                '4h': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'seed': None}
            },
            'by_strategy': {
                'ER90': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0},
                'SIB': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0}
            },
            'daily_history': {},  # date -> DailyStats
            'recent_trades': []  # Last 100 trades
        }
    
    def _save_stats(self):
        """Persist statistics to file"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save statistics: {e}")
    
    def start_session(self):
        """Mark session start time"""
        self.session_start = datetime.utcnow()
        self.session_trades = []
        self.data['all_time']['total_sessions'] += 1
    
    def end_session(self):
        """Mark session end and calculate session stats"""
        if not self.session_start:
            return
        
        self.session_end = datetime.utcnow()
        session_duration = (self.session_end - self.session_start).total_seconds()
        
        # Update daily stats
        today = self.session_start.strftime('%Y-%m-%d')
        if today not in self.data['daily_history']:
            self.data['daily_history'][today] = {
                'date': today,
                'trades_count': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl': 0.0,
                'uptime_seconds': 0,
                'active_time_seconds': 0,
                'sessions': 0
            }
        
        self.data['daily_history'][today]['uptime_seconds'] += int(session_duration)
        self.data['daily_history'][today]['sessions'] += 1
        
        # Update all-time uptime
        self.data['all_time']['total_uptime_hours'] = sum(
            day['uptime_seconds'] for day in self.data['daily_history'].values()
        ) / 3600.0
        
        self._save_stats()
    
    def record_signal(self, timeframe: str, strategy: str, side: str, 
                     entry: float, stop: float, tp1: float, notional: float,
                     seed: Optional[int] = None):
        """
        Record a trading signal (entry).
        
        Args:
            timeframe: Trading timeframe (1m, 5m, 15m, 1h, 4h)
            strategy: Strategy name (ER90, SIB)
            side: LONG or SHORT
            entry: Entry price
            stop: Stop loss
            tp1: Take profit 1
            notional: Position size USD
            seed: Strategy seed number (optional)
        """
        trade = TradeRecord(
            timestamp=datetime.utcnow().isoformat(),
            timeframe=timeframe,
            strategy=strategy,
            side=side,
            entry=entry,
            stop=stop,
            tp1=tp1,
            notional=notional
        )
        
        self.session_trades.append(trade)
        
        # Update timeframe stats
        if timeframe in self.data['by_timeframe']:
            self.data['by_timeframe'][timeframe]['trades'] += 1
            if seed:
                self.data['by_timeframe'][timeframe]['seed'] = seed
        
        # Update strategy stats
        if strategy in self.data['by_strategy']:
            self.data['by_strategy'][strategy]['trades'] += 1
        
        # Update all-time
        self.data['all_time']['total_trades'] += 1
        
        # Update dates
        today = datetime.utcnow().strftime('%Y-%m-%d')
        if not self.data['first_trade_date']:
            self.data['first_trade_date'] = today
        self.data['last_trade_date'] = today
        
        # Update daily history
        if today not in self.data['daily_history']:
            self.data['daily_history'][today] = {
                'date': today,
                'trades_count': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl': 0.0,
                'uptime_seconds': 0,
                'active_time_seconds': 0,
                'sessions': 0
            }
        
        self.data['daily_history'][today]['trades_count'] += 1
        self.data['daily_history'][today]['active_time_seconds'] += 60  # Assume 1 min active per trade
        
        # Add to recent trades
        self.data['recent_trades'].insert(0, asdict(trade))
        self.data['recent_trades'] = self.data['recent_trades'][:100]  # Keep last 100
        
        self._save_stats()
    
    def record_trade_result(self, timeframe: str, strategy: str, 
                           outcome: str, pnl: float, duration_min: int):
        """
        Record the result of a closed trade.
        
        Args:
            timeframe: Trading timeframe
            strategy: Strategy name
            outcome: 'WIN', 'LOSS', or 'BREAKEVEN'
            pnl: Profit/loss in USD
            duration_min: Trade duration in minutes
        """
        today = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Update timeframe stats
        if timeframe in self.data['by_timeframe']:
            if outcome == 'WIN':
                self.data['by_timeframe'][timeframe]['wins'] += 1
            elif outcome == 'LOSS':
                self.data['by_timeframe'][timeframe]['losses'] += 1
            self.data['by_timeframe'][timeframe]['pnl'] += pnl
        
        # Update strategy stats
        if strategy in self.data['by_strategy']:
            if outcome == 'WIN':
                self.data['by_strategy'][strategy]['wins'] += 1
            elif outcome == 'LOSS':
                self.data['by_strategy'][strategy]['losses'] += 1
            self.data['by_strategy'][strategy]['pnl'] += pnl
        
        # Update all-time
        if outcome == 'WIN':
            self.data['all_time']['total_wins'] += 1
        elif outcome == 'LOSS':
            self.data['all_time']['total_losses'] += 1
        self.data['all_time']['total_pnl'] += pnl
        
        # Update daily history
        if today not in self.data['daily_history']:
            self.data['daily_history'][today] = {
                'date': today,
                'trades_count': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl': 0.0,
                'uptime_seconds': 0,
                'active_time_seconds': 0,
                'sessions': 0
            }
        
        if outcome == 'WIN':
            self.data['daily_history'][today]['wins'] += 1
        elif outcome == 'LOSS':
            self.data['daily_history'][today]['losses'] += 1
        
        self.data['daily_history'][today]['total_pnl'] += pnl
        self.data['daily_history'][today]['active_time_seconds'] += duration_min * 60
        
        # Update best/worst day
        day_pnl = self.data['daily_history'][today]['total_pnl']
        if day_pnl > self.data['all_time']['best_day_pnl']:
            self.data['all_time']['best_day_pnl'] = day_pnl
            self.data['all_time']['best_day_date'] = today
        if day_pnl < self.data['all_time']['worst_day_pnl']:
            self.data['all_time']['worst_day_pnl'] = day_pnl
            self.data['all_time']['worst_day_date'] = today
        
        self._save_stats()
    
    def get_today_stats(self) -> Dict:
        """Get statistics for today"""
        today = datetime.utcnow().strftime('%Y-%m-%d')
        
        if today in self.data['daily_history']:
            stats = self.data['daily_history'][today].copy()
            # Calculate current session uptime
            if self.session_start:
                current_session = (datetime.utcnow() - self.session_start).total_seconds()
                stats['uptime_seconds'] += int(current_session)
            return stats
        
        return {
            'date': today,
            'trades_count': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0,
            'uptime_seconds': 0,
            'active_time_seconds': 0,
            'sessions': 0
        }
    
    def get_timeframe_stats(self) -> Dict:
        """Get statistics by timeframe with seed info"""
        return self.data['by_timeframe'].copy()
    
    def get_all_time_stats(self) -> Dict:
        """Get all-time statistics"""
        return self.data['all_time'].copy()
    
    def get_summary_for_dashboard(self) -> Dict:
        """Get formatted summary for dashboard display"""
        today_stats = self.get_today_stats()
        all_time = self.get_all_time_stats()
        
        # Calculate average daily uptime
        total_days = len(self.data['daily_history'])
        avg_daily_uptime_hours = 0.0
        if total_days > 0:
            total_uptime = sum(day['uptime_seconds'] for day in self.data['daily_history'].values())
            avg_daily_uptime_hours = (total_uptime / total_days) / 3600.0
        
        return {
            'today': {
                'trades': today_stats['trades_count'],
                'wins': today_stats['wins'],
                'losses': today_stats['losses'],
                'pnl': today_stats['total_pnl'],
                'uptime_hours': today_stats['uptime_seconds'] / 3600.0,
                'active_time_hours': today_stats['active_time_seconds'] / 3600.0
            },
            'all_time': {
                'total_trades': all_time['total_trades'],
                'total_wins': all_time['total_wins'],
                'total_losses': all_time['total_losses'],
                'total_pnl': all_time['total_pnl'],
                'total_uptime_hours': all_time['total_uptime_hours'],
                'total_sessions': all_time['total_sessions'],
                'avg_daily_uptime_hours': avg_daily_uptime_hours,
                'best_day': {
                    'pnl': all_time['best_day_pnl'],
                    'date': all_time['best_day_date']
                },
                'trading_days': total_days
            },
            'by_timeframe': self.get_timeframe_stats()
        }


# Singleton instance
_tracker_instance: Optional[StatisticsTracker] = None


def get_statistics_tracker() -> StatisticsTracker:
    """Get or create statistics tracker singleton"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = StatisticsTracker()
    return _tracker_instance


# Testing
if __name__ == '__main__':
    print("Testing StatisticsTracker...")
    
    # Create tracker
    tracker = StatisticsTracker(stats_file="data/test_stats.json")
    
    # Start session
    tracker.start_session()
    print("✅ Session started")
    
    # Record some signals
    tracker.record_signal('1h', 'ER90', 'LONG', 3500.0, 3450.0, 3600.0, 100.0, seed=12345)
    tracker.record_signal('4h', 'SIB', 'SHORT', 3520.0, 3570.0, 3420.0, 100.0, seed=67890)
    print("✅ Recorded 2 signals")
    
    # Record results
    tracker.record_trade_result('1h', 'ER90', 'WIN', 15.50, 45)
    tracker.record_trade_result('4h', 'SIB', 'LOSS', -8.25, 120)
    print("✅ Recorded trade results")
    
    # Get summary
    summary = tracker.get_summary_for_dashboard()
    print("\n📊 Summary:")
    print(f"Today: {summary['today']['trades']} trades, ${summary['today']['pnl']:.2f} P&L")
    print(f"All-time: {summary['all_time']['total_trades']} trades, ${summary['all_time']['total_pnl']:.2f} P&L")
    print(f"Total uptime: {summary['all_time']['total_uptime_hours']:.1f} hours")
    
    # End session
    tracker.end_session()
    print("\n✅ Session ended - stats saved")
