#!/usr/bin/env python3
"""
Backtest Control Panel
Start/stop backtests and view history from dashboard
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from dashboard.formatters import format_currency, format_seed, format_time_ago, format_status_icon


class BacktestController:
    """Manage backtest execution and history"""
    
    def __init__(self):
        self.history_file = 'ml/backtest_history.json'
        self.progress_file = 'data/backtest_progress.json'
        self.active_backtest = None
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """Load backtest history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading backtest history: {e}")
            return []
    
    def _save_history(self):
        """Save backtest history to file"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving backtest history: {e}")
    
    def start_backtest(
        self,
        seed: Optional[int] = None,
        skip_check: bool = False,
        data_file: str = 'data/eth_90days.json'
    ) -> Dict:
        """
        Start a new backtest
        
        Args:
            seed: Input seed for strategy generation
            skip_check: Skip data file validation
            data_file: Path to data file
        
        Returns:
            Dict with status and message
        """
        if self.active_backtest:
            return {
                'status': 'error',
                'message': 'Backtest already running'
            }
        
        try:
            # Build command
            cmd = ['python', 'backtest_90_complete.py']
            
            if seed is not None:
                cmd.extend(['--seed', str(seed)])
            
            if skip_check:
                cmd.append('--skip-check')
            
            if data_file:
                cmd.extend(['--data-file', data_file])
            
            # Store active backtest info
            self.active_backtest = {
                'seed': seed,
                'data_file': data_file,
                'started_at': datetime.now().isoformat(),
                'status': 'running',
                'command': ' '.join(cmd)
            }
            
            return {
                'status': 'success',
                'message': f'Backtest started with seed {seed}' if seed else 'Backtest started',
                'command': ' '.join(cmd)
            }
        
        except Exception as e:
            self.active_backtest = None
            return {
                'status': 'error',
                'message': f'Failed to start backtest: {e}'
            }
    
    def stop_backtest(self) -> Dict:
        """
        Stop active backtest
        
        Returns:
            Dict with status and message
        """
        if not self.active_backtest:
            return {
                'status': 'error',
                'message': 'No active backtest'
            }
        
        try:
            # In a real implementation, this would send SIGTERM to the process
            # For now, just mark as stopped
            self.active_backtest['status'] = 'stopped'
            self.active_backtest['stopped_at'] = datetime.now().isoformat()
            
            # Add to history
            self.history.append(self.active_backtest)
            self._save_history()
            
            self.active_backtest = None
            
            return {
                'status': 'success',
                'message': 'Backtest stopped'
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to stop backtest: {e}'
            }
    
    def record_completion(self, results: Dict):
        """Record backtest completion with results"""
        if self.active_backtest:
            self.active_backtest['status'] = 'completed'
            self.active_backtest['completed_at'] = datetime.now().isoformat()
            self.active_backtest['results'] = results
            
            # Add to history
            self.history.append(self.active_backtest)
            self._save_history()
            
            self.active_backtest = None
    
    def get_status(self) -> Dict:
        """Get current backtest status with progress"""
        progress = self._load_progress()
        return {
            'active': self.active_backtest is not None,
            'backtest': self.active_backtest,
            'history_count': len(self.history),
            'progress': progress
        }
    
    def _load_progress(self) -> Optional[Dict]:
        """Load backtest progress from file"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    # Only return if recent (within last 60 seconds)
                    if 'timestamp' in data:
                        from datetime import datetime
                        ts = datetime.fromisoformat(data['timestamp'])
                        elapsed = (datetime.now() - ts).total_seconds()
                        if elapsed < 60:
                            return data
            return None
        except Exception:
            return None
    
    def get_recent_history(self, n: int = 10) -> List[Dict]:
        """Get recent backtest history"""
        return sorted(
            self.history,
            key=lambda x: x.get('started_at', ''),
            reverse=True
        )[:n]


def render_backtest_control(controller: BacktestController, view: str = 'status') -> Panel:
    """
    Render backtest control panel
    
    Args:
        controller: BacktestController instance
        view: 'status', 'history', or 'start'
    """
    try:
        if view == 'status':
            return _render_status_view(controller)
        elif view == 'history':
            return _render_history_view(controller)
        elif view == 'start':
            return _render_start_view(controller)
        else:
            return _render_status_view(controller)
    
    except Exception as e:
        return Panel(
            f"Error rendering backtest control: {e}",
            title="🔬 BACKTEST CONTROL",
            border_style="red",
            padding=(1, 2)
        )


def _render_status_view(controller: BacktestController) -> Panel:
    """Render status view with progress tracking"""
    status = controller.get_status()
    
    lines = []
    
    if status['active']:
        bt = status['backtest']
        progress = status.get('progress')
        
        lines.append(f"{format_status_icon('running')} BACKTEST RUNNING")
        lines.append("")
        lines.append(f"Seed: {format_seed(bt['seed']) if bt.get('seed') else 'Random'}")
        lines.append(f"Data: {bt.get('data_file', 'Unknown')}")
        
        started = datetime.fromisoformat(bt['started_at'])
        elapsed_sec = (datetime.now() - started).total_seconds()
        elapsed_min = int(elapsed_sec / 60)
        lines.append(f"Started: {format_time_ago(started)} ({elapsed_min}m {int(elapsed_sec % 60)}s)")
        
        # Progress information
        if progress:
            lines.append("")
            lines.append("━━━ PROGRESS ━━━")
            
            # Progress bar
            pct = progress.get('percent_complete', 0)
            bars_filled = int(pct / 5)  # 20 bars total (5% each)
            bars_empty = 20 - bars_filled
            progress_bar = "█" * bars_filled + "░" * bars_empty
            lines.append(f"{progress_bar} {pct:.1f}%")
            
            # Stats
            bars_proc = progress.get('bars_processed', 0)
            total_bars = progress.get('total_bars', 0)
            lines.append(f"Bars: {bars_proc:,} / {total_bars:,}")
            
            # Current stats
            if 'current_stats' in progress:
                stats = progress['current_stats']
                wins = stats.get('wins', 0)
                losses = stats.get('losses', 0)
                total_trades = wins + losses
                win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
                pnl = stats.get('pnl', 0)
                
                lines.append("")
                lines.append("━━━ CURRENT STATS ━━━")
                lines.append(f"Trades: {total_trades} (W:{wins} L:{losses})")
                lines.append(f"Win Rate: {win_rate:.1f}%")
                lines.append(f"P&L: {format_currency(pnl)}")
            
            # ETA
            if 'eta_seconds' in progress:
                eta = progress['eta_seconds']
                eta_min = int(eta / 60)
                eta_sec = int(eta % 60)
                lines.append(f"ETA: {eta_min}m {eta_sec}s")
        else:
            lines.append("")
            lines.append("⏳ Initializing...")
        
        lines.append("")
        lines.append("[X] Stop Backtest")
    else:
        lines.append(f"{format_status_icon('stopped')} NO ACTIVE BACKTEST")
        lines.append("")
        lines.append("Start a new backtest:")
        lines.append("  [N] New backtest (random seed)")
        lines.append("  [S] Select seed from whitelist")
        lines.append("  [I] Input custom seed")
        lines.append("")
        lines.append("Seed Testing:")
        lines.append("  [T] Test all whitelisted seeds")
        lines.append("  [K] Quick test (top 10 by WR)")
        lines.append("")
        lines.append("BASE_STRATEGY:")
        lines.append("  [O] Overwrite with best seed")
        lines.append("  [R] Reset to original")
    
    lines.append("")
    lines.append(f"History: {status['history_count']} backtests")
    lines.append("[H] View history  [ESC] Back")
    
    content = "\n".join(lines)
    
    return Panel(
        content,
        title="🔬 BACKTEST CONTROL",
        border_style="magenta",
        padding=(1, 2)
    )


def _render_history_view(controller: BacktestController) -> Panel:
    """Render history view"""
    history = controller.get_recent_history(n=10)
    
    if not history:
        content = "No backtest history\n\n[ESC] Back"
        return Panel(
            content,
            title="📜 BACKTEST HISTORY",
            border_style="cyan",
            padding=(1, 2)
        )
    
    # Build table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Seed", justify="right", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Win Rate", justify="right")
    table.add_column("Trades", justify="right")
    table.add_column("P&L", justify="right")
    table.add_column("Started", justify="left")
    
    for bt in history:
        seed = bt.get('seed', 'Random')
        seed_str = format_seed(seed) if isinstance(seed, int) else str(seed)
        
        status = bt.get('status', 'unknown')
        if status == 'completed':
            status_icon = format_status_icon('success')
        elif status == 'running':
            status_icon = format_status_icon('running')
        else:
            status_icon = format_status_icon('stopped')
        
        results = bt.get('results', {})
        win_rate = results.get('win_rate', 0) * 100 if results else 0
        trades = results.get('total_trades', 0) if results else 0
        pnl = results.get('total_pnl', 0) if results else 0
        
        started = bt.get('started_at', '')
        if started:
            try:
                started_dt = datetime.fromisoformat(started)
                started_str = format_time_ago(started_dt)
            except:
                started_str = 'Unknown'
        else:
            started_str = 'Unknown'
        
        table.add_row(
            seed_str,
            status_icon,
            f"{win_rate:.1f}%" if results else "N/A",
            str(trades) if results else "N/A",
            format_currency(pnl) if results else "N/A",
            started_str
        )
    
    return Panel(
        table,
        title=f"📜 BACKTEST HISTORY (Last {len(history)})",
        subtitle="\n[ESC] Back",
        border_style="cyan",
        padding=(1, 2)
    )


def _render_start_view(controller: BacktestController) -> Panel:
    """Render start new backtest view"""
    lines = []
    lines.append("START NEW BACKTEST")
    lines.append("")
    lines.append("Options:")
    lines.append("  1. Random seed (default)")
    lines.append("  2. Select from whitelist")
    lines.append("  3. Enter custom seed")
    lines.append("")
    lines.append("Data file:")
    lines.append("  [1] ETH 90 days (default)")
    lines.append("  [2] Custom file")
    lines.append("")
    lines.append("[Enter] Start with defaults")
    lines.append("[ESC] Cancel")
    
    content = "\n".join(lines)
    
    return Panel(
        content,
        title="🚀 START BACKTEST",
        border_style="green",
        padding=(1, 2)
    )


def handle_backtest_key(key: str, controller: BacktestController, current_view: str = 'status') -> tuple:
    """
    Handle keyboard input for backtest control
    
    Args:
        key: The pressed key
        controller: BacktestController instance
        current_view: Current view ('status', 'history', 'start')
    
    Returns:
        tuple: (should_close, message, new_view)
    """
    try:
        if key == 'escape' or key.lower() == 'q':
            return (True, None, current_view)
        
        if current_view == 'status':
            status = controller.get_status()
            
            if key.lower() == 'x' and status['active']:
                # Stop backtest
                result = controller.stop_backtest()
                return (False, result['message'], 'status')
            
            elif key.lower() == 'n' and not status['active']:
                # Start new backtest
                result = controller.start_backtest()
                return (False, result['message'], 'status')
            
            elif key.lower() == 't' and not status['active']:
                # Test all whitelisted seeds
                return (False, "Test all whitelisted seeds - Feature coming soon", 'status')
            
            elif key.lower() == 'i' and not status['active']:
                # Input custom seed
                return (False, "Input custom seed - Feature coming soon", 'status')
            
            elif key.lower() == 'o' and not status['active']:
                # Overwrite BASE_STRATEGY with best seed
                return (False, "Overwrite BASE_STRATEGY - Feature coming soon", 'status')
            
            elif key.lower() == 'r' and not status['active']:
                # Reset BASE_STRATEGY to original
                return (False, "Reset BASE_STRATEGY - Feature coming soon", 'status')
            
            elif key.lower() == 'k' and not status['active']:
                # Quick test (top 10 by win rate)
                return (False, "Quick test top 10 seeds - Feature coming soon", 'status')
            
            elif key.lower() == 'h':
                # View history
                return (False, None, 'history')
            
            elif key.lower() == 's':
                # Start view
                return (False, None, 'start')
        
        elif current_view == 'history':
            if key == 'escape':
                return (False, None, 'status')
        
        elif current_view == 'start':
            if key == 'escape':
                return (False, None, 'status')
            elif key == 'enter':
                # Start with defaults
                result = controller.start_backtest()
                return (False, result['message'], 'status')
        
        return (False, None, current_view)
    
    except Exception as e:
        return (False, f"Error: {e}", current_view)


def show_backtest_control_interactive():
    """Show backtest control in interactive mode (for testing)"""
    console = Console()
    controller = BacktestController()
    
    console.print("\n[bold]Backtest Control Test[/bold]\n")
    
    # Test different views
    for view in ['status', 'history', 'start']:
        panel = render_backtest_control(controller, view=view)
        console.print(panel)
        console.print()


if __name__ == "__main__":
    # Test the backtest control
    show_backtest_control_interactive()
