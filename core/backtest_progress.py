#!/usr/bin/env python3
"""
Backtest Progress Tracker
Utility for backtests to report progress in real-time
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional


class BacktestProgressTracker:
    """Track and report backtest progress"""
    
    def __init__(self, progress_file: str = 'data/backtest_progress.json'):
        self.progress_file = progress_file
        self.start_time = datetime.now()
        self.total_bars = 0
        self.bars_processed = 0
        self.current_stats = {
            'wins': 0,
            'losses': 0,
            'pnl': 0.0
        }
    
    def initialize(self, total_bars: int):
        """Initialize progress tracking"""
        self.total_bars = total_bars
        self.bars_processed = 0
        self.start_time = datetime.now()
        self._write_progress()
    
    def update(self, bars_processed: int, wins: int = 0, losses: int = 0, pnl: float = 0.0):
        """Update progress with current stats"""
        self.bars_processed = bars_processed
        self.current_stats = {
            'wins': wins,
            'losses': losses,
            'pnl': pnl
        }
        self._write_progress()
    
    def _write_progress(self):
        """Write progress to file"""
        try:
            # Calculate progress
            percent_complete = (self.bars_processed / self.total_bars * 100) if self.total_bars > 0 else 0
            
            # Calculate ETA
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if self.bars_processed > 0:
                rate = self.bars_processed / elapsed
                remaining_bars = self.total_bars - self.bars_processed
                eta_seconds = remaining_bars / rate if rate > 0 else 0
            else:
                eta_seconds = 0
            
            progress = {
                'timestamp': datetime.now().isoformat(),
                'percent_complete': round(percent_complete, 2),
                'bars_processed': self.bars_processed,
                'total_bars': self.total_bars,
                'elapsed_seconds': round(elapsed, 1),
                'eta_seconds': round(eta_seconds, 1),
                'current_stats': self.current_stats
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
            
            # Write atomically
            temp_file = f"{self.progress_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(progress, f, indent=2)
            os.replace(temp_file, self.progress_file)
        
        except Exception as e:
            # Fail silently - progress tracking shouldn't break backtest
            pass
    
    def complete(self):
        """Mark backtest as complete and cleanup"""
        try:
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
        except:
            pass


def get_progress_tracker(progress_file: str = 'data/backtest_progress.json') -> BacktestProgressTracker:
    """Get a progress tracker instance"""
    return BacktestProgressTracker(progress_file)
