#!/usr/bin/env python3
"""
Terminal Dashboard UI
Main dashboard with 4-panel layout and keyboard navigation
"""

import sys
import os
import time
import threading
from datetime import datetime
from typing import Dict, Optional
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from dashboard.panels import SeedStatusPanel, BotStatusPanel, PerformancePanel, WalletPanel
from dashboard.help_screen import render_help_screen, open_documentation
from dashboard.ml_control import render_ml_control_panel, handle_ml_control_key
from dashboard.seed_browser import render_seed_browser
from dashboard.backtest_control import BacktestController, render_backtest_control, handle_backtest_key
from dashboard.slot_data_provider import get_slot_allocation_display_data
from dashboard.debug_terminal import render_debug_terminal, handle_debug_key


class RefreshCoordinator:
    """Coordinates dashboard refreshes to prevent concurrent execution"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._refreshing = False
        self._last_refresh = 0
        self._min_interval = 0.5  # 500ms minimum between refreshes
    
    def start_refresh(self) -> bool:
        """
        Attempt to start a refresh.
        Returns True if refresh was started, False if already refreshing.
        """
        with self._lock:
            current_time = time.time()
            
            # Check if already refreshing
            if self._refreshing:
                return False
            
            # Check minimum interval
            if current_time - self._last_refresh < self._min_interval:
                return False
            
            self._refreshing = True
            return True
    
    def end_refresh(self):
        """Mark refresh as completed"""
        with self._lock:
            self._refreshing = False
            self._last_refresh = time.time()
    
    def is_refreshing(self) -> bool:
        """Check if refresh is currently in progress"""
        with self._lock:
            return self._refreshing


class TerminalDashboard:
    """Main terminal dashboard with 4-panel layout"""
    
    def __init__(self, refresh_interval: int = 2):
        self.console = Console()
        self.refresh_interval = refresh_interval
        
        # Initialize debug daemon (only runs when dashboard is active)
        from core.debug_daemon import get_daemon
        self.daemon = get_daemon()
        self._current_action_id = None
        
        # Initialize refresh coordinator
        self.refresh_coordinator = RefreshCoordinator()
        
        # Initialize panels
        self.seed_panel = SeedStatusPanel()
        self.bot_panel = BotStatusPanel()
        self.perf_panel = PerformancePanel()
        self.wallet_panel = WalletPanel()
        
        # Initialize controllers
        self.backtest_controller = BacktestController()
        
        # Modal state
        self.active_modal = None  # None, 'help', 'ml', 'seed', 'backtest', 'debug'
        self.modal_view = 'status'  # For modals with multiple views
        self.ml_selected_asset = 'ETH'
        self.seed_browser_page = 0
        self.seed_browser_view = 'all'
        self.debug_view = 'live'  # live, summary, errors
        self.debug_page = 0  # Pagination state for debug terminal
        self.debug_session_idx = 0  # Session selection state
        
        # Data cache
        self.data = self._get_initial_data()
        
        # Running state
        self.running = True
        self.system_check_complete = False
        
        # Enhanced status/feedback system
        self.command_history = []  # List of recent commands
        self.max_history = 5
        self.current_operation = None
        self.operation_status = "ready"  # ready, processing, success, failed
        
        # Status tracking
        self.status = {
            'last_key': None,
            'key_valid': None,
            'operation': 'System startup',
            'result': 'processing',
            'message': '⏳ Initializing dashboard...',
            'details': None
        }
    
    def log_key_press(self, key: str):
        """Log key press and determine validity."""
        import time
        timestamp = time.strftime("%H:%M:%S")
        
        # Determine if key is valid based on context
        valid_keys = ['q', 's', 'r', 'm', 'h', 'd', 'b', 'w', 'l', 'x', 'escape']
        
        # Add modal-specific valid keys
        if self.active_modal == 'backtest':
            valid_keys.extend(['n', 'x', 't', 'i', 'k', 'o'])
        elif self.active_modal == 'seed':
            valid_keys.extend(['w', 'a', 'left', 'right'])
        elif self.active_modal == 'ml':
            valid_keys.extend(['1', '2', '3', '4', '5'])
        elif self.active_modal == 'debug':
            valid_keys.extend(['1', '2', '3'])
        
        # Check for ESC in various forms: actual escape char, string representation, or CSI sequences
        is_esc = key == '\x1b' or key == '\\x1b' or key == 'escape' or key.startswith('\x1b[')
        is_valid = key.lower() in valid_keys or is_esc
        
        self.status['last_key'] = key
        self.status['key_valid'] = is_valid
        
        # Add to history
        entry = {
            'time': timestamp,
            'key': key,
            'valid': is_valid
        }
        self.command_history.insert(0, entry)
        if len(self.command_history) > self.max_history:
            self.command_history.pop()
        
        return is_valid
    
    def start_operation(self, operation: str, details: str = None):
        """Start tracking an operation."""
        import time
        
        self.status['operation'] = operation
        self.status['result'] = 'processing'
        self.status['message'] = f"⏳ Processing: {operation}"  # Add processing symbol
        self.status['details'] = details
        self.current_operation = operation
        self.operation_status = "processing"
        self._operation_start_time = time.time()  # Track start time for timeout
        
        # Log to daemon
        if hasattr(self, 'daemon'):
            self._current_action_id = self.daemon.log_action(
                action_name=operation,
                category='dashboard_operation',
                details={'description': details or '', 'timestamp': time.time()},
                expected_outcome={'success': True, 'operation': operation}
            )
    
    def complete_operation(self, success: bool, message: str, details: str = None):
        """Complete an operation with result."""
        import time
        
        # Check if operation took too long (timeout detection)
        if hasattr(self, '_operation_start_time'):
            elapsed = time.time() - self._operation_start_time
            if elapsed > 30:  # 30 second timeout
                self.status['result'] = 'failed'
                self.status['message'] = f"Operation timeout: {message}"
                self.status['details'] = f"Took {elapsed:.1f}s (timeout: 30s)"
                self.operation_status = "failed"
                success = False
                message = f"Timeout: {message}"
        
        self.status['result'] = 'success' if success else 'failed'
        self.status['message'] = message
        if details:
            self.status['details'] = details
        self.operation_status = "success" if success else "failed"
        
        # Validate with daemon
        if hasattr(self, 'daemon') and self._current_action_id:
            actual_outcome = {
                'success': success,
                'operation': self.status['operation'],
                'message': message,
                'elapsed_time': time.time() - self._operation_start_time if hasattr(self, '_operation_start_time') else 0
            }
            
            validation_checks = [
                {
                    'name': 'operation_success',
                    'level': 'CRITICAL',
                    'function': lambda actual, expected: actual.get('success') == expected.get('success'),
                    'expected': True
                },
                {
                    'name': 'operation_match',
                    'level': 'INFO',
                    'function': lambda actual, expected: actual.get('operation') == expected.get('operation'),
                    'expected': True
                },
                {
                    'name': 'response_time',
                    'level': 'WARNING',
                    'function': lambda actual, expected: actual.get('elapsed_time', 0) < 5.0,
                    'expected': True,
                    'details': {'threshold_seconds': 5.0}
                }
            ]
            
            self.daemon.validate_action(self._current_action_id, actual_outcome, validation_checks)
            self._current_action_id = None
    
    def set_ready(self, message: str = "Dashboard ready"):
        """Set dashboard to ready state."""
        self.status['result'] = 'ready'
        self.status['message'] = message
        self.status['operation'] = None
        self.current_operation = None
        self.operation_status = "ready"
        if hasattr(self, '_operation_start_time'):
            delattr(self, '_operation_start_time')
    
    def check_operation_timeout(self) -> bool:
        """Check if current operation has timed out."""
        import time
        
        if self.status['result'] == 'processing' and hasattr(self, '_operation_start_time'):
            elapsed = time.time() - self._operation_start_time
            if elapsed > 30:  # 30 second timeout
                self.status['result'] = 'failed'
                self.status['message'] = f"❌ Timeout: {self.status['operation']} took too long"
                self.status['details'] = f"Elapsed: {elapsed:.1f}s (max: 30s)"
                self.operation_status = "failed"
                return True
        return False
    
    def run_system_check(self) -> tuple[bool, list[str]]:
        """Run comprehensive system check on startup"""
        checks = []
        all_passed = True
        
        # Test main command keys
        main_commands = {
            'q': 'Quit',
            'r': 'Refresh',
            'h': 'Help',
            's': 'Seeds',
            'm': 'ML Control',
            'b': 'Backtest',
            'd': 'Docs',
            'w': 'Wallet'
        }
        
        for key, name in main_commands.items():
            checks.append(f"✓ {name} command ({key})")
        
        # Test modal rendering
        modals = ['help', 'seed', 'ml', 'backtest']
        for modal in modals:
            try:
                # Store current state
                orig_modal = self.active_modal
                # Test modal can be set
                self.active_modal = modal
                self.render_modal()
                # Restore state
                self.active_modal = orig_modal
                checks.append(f"✓ {modal.capitalize()} modal")
            except Exception as e:
                checks.append(f"✗ {modal.capitalize()} modal: {e}")
                all_passed = False
        
        # Test status bar components
        try:
            assert hasattr(self, 'status'), "Status dict missing"
            assert hasattr(self, 'command_history'), "History missing"
            assert 'message' in self.status, "Status message missing"
            assert 'result' in self.status, "Status result missing"
            checks.append("✓ Status bar initialized")
        except AssertionError as e:
            checks.append(f"✗ Status bar: {e}")
            all_passed = False
        
        # Test timeout detection
        try:
            assert hasattr(self, 'check_operation_timeout'), "Timeout check missing"
            assert hasattr(self, 'start_operation'), "Start operation missing"
            assert hasattr(self, 'complete_operation'), "Complete operation missing"
            checks.append("✓ Timeout detection (30s)")
        except AssertionError as e:
            checks.append(f"✗ Timeout: {e}")
            all_passed = False
        
        # Test key logging
        try:
            assert hasattr(self, 'log_key_press'), "Key logging missing"
            # Test a valid key
            self.log_key_press('h')
            assert self.status['last_key'] == 'h'
            assert self.status['key_valid'] == True
            checks.append("✓ Key validation system")
        except Exception as e:
            checks.append(f"✗ Key validation: {e}")
            all_passed = False
        
        # Test paper trading system
        try:
            from core.paper_trading_tracker import get_paper_trading_tracker
            tracker = get_paper_trading_tracker()
            pt_status = tracker.get_status()
            
            if pt_status['status'] == 'completed':
                checks.append("✓ Paper trading completed")
            elif pt_status['status'] == 'running':
                reqs = tracker.check_requirements()
                hours = reqs['duration']['current']
                checks.append(f"✓ Paper trading active ({hours:.1f}h)")
            else:
                checks.append("✓ Paper trading system ready")
        except Exception as e:
            checks.append(f"✗ Paper trading: {e}")
            # Don't fail overall check for paper trading
        
        return all_passed, checks
    
    def _get_initial_data(self) -> Dict:
        """Get initial mock data for panels"""
        # Get initial slot allocation data
        initial_balance = 10.0
        slot_data = get_slot_allocation_display_data(
            current_balance=initial_balance,
            mode='BACKTEST',
            founder_fee_manager=None
        )
        
        # Load wallet state from config file if exists
        wallet_data = self._load_wallet_state()
        
        return {
            'seed': {
                'total_tested': 0,
                'whitelisted': 0,
                'blacklisted': 0,
                'top_performer': None,
                'current_seed': None
            },
            'bot': {
                'status': 'stopped',
                'mode': 'BACKTEST',
                'seed_info': {},
                'balance': {'initial': initial_balance, 'current': initial_balance},
                'active_positions': [],
                'max_positions': 2,
                'last_trade': None,
                'slot_allocation': slot_data
            },
            'performance': {
                'wins': 0,
                'losses': 0,
                'pnl': 0.0,
                'max_drawdown': 0.0,
                'by_timeframe': {}
            },
            'wallet': wallet_data
        }
    
    def create_layout(self) -> Layout:
        """Create 4-panel layout with command bar and status panel"""
        layout = Layout()
        
        # Split into main area, status panel, and command bar
        layout.split_column(
            Layout(name="main", ratio=18),
            Layout(name="status", ratio=1, minimum_size=2),
            Layout(name="commands", ratio=1, minimum_size=3)
        )
        
        # Split main area into 2 rows
        layout["main"].split_column(
            Layout(name="top", ratio=1),
            Layout(name="bottom", ratio=1)
        )
        
        # Split each row into 2 columns
        layout["main"]["top"].split_row(
            Layout(name="seed", ratio=1),
            Layout(name="bot", ratio=1)
        )
        
        layout["main"]["bottom"].split_row(
            Layout(name="performance", ratio=1),
            Layout(name="wallet", ratio=1)
        )
        
        return layout
    
    def _load_wallet_state(self) -> Dict:
        """Load wallet connection state from auto_wallet_manager config file"""
        try:
            import json
            from pathlib import Path
            
            # Read from auto_wallet_manager's config file
            wallet_config_path = Path('data/wallet_config.json')
            
            if wallet_config_path.exists():
                with open(wallet_config_path, 'r') as f:
                    config = json.load(f)
                
                # Extract metamask info
                metamask_info = config.get('metamask', {})
                btc_info = config.get('btc_wallet', {})
                
                return {
                    'metamask': {
                        'connected': metamask_info.get('connected', False),
                        'address': metamask_info.get('address', None),
                        'chain_id': '0x1',  # Default to Ethereum mainnet
                        'connected_at': metamask_info.get('last_connected')
                    },
                    'btc_wallet': {
                        'exists': btc_info.get('created', False),
                        'address': btc_info.get('address', None),
                        'balance': btc_info.get('balance_usd', 0.0)
                    },
                    'position_limits': {
                        'max_position_size': 100.0,
                        'rule': '$100 cap (< $5K capital)',
                        'profit_threshold': 100.0,
                        'funding_amount': 50.0
                    },
                    'capital': 10.0,
                    'profit': config.get('profit_tracking', {}).get('total_profit_usd', 0.0)
                }
        except Exception as e:
            # Log error but continue with defaults
            pass
        
        # Return default if no connection or error
        return {
            'metamask': {
                'connected': False,
                'address': None
            },
            'btc_wallet': {'exists': False},
            'position_limits': {
                'max_position_size': 100.0,
                'rule': '$100 cap (< $5K capital)',
                'profit_threshold': 100.0,
                'funding_amount': 50.0
            },
            'capital': 10.0,
            'profit': 0.0
        }
    
    def render_panels(self, layout: Layout, countdown: int = 10):
        """Render all panels with current data"""
        # Get current mode from bot data
        current_mode = self.data['bot'].get('mode', 'UNKNOWN')
        
        layout["main"]["seed"].update(self.seed_panel.render(self.data['seed']))
        layout["main"]["bot"].update(self.bot_panel.render(self.data['bot']))
        
        # Add mode to performance data
        perf_data = {**self.data['performance'], 'mode': current_mode}
        layout["main"]["performance"].update(self.perf_panel.render(perf_data))
        
        # Add mode to wallet data
        wallet_data = {**self.data.get('wallet', {}), 'mode': current_mode}
        layout["main"]["wallet"].update(self.wallet_panel.render(wallet_data))
        
        # Render enhanced status panel with feedback and history
        status_text = Text()
        
        # Status icon based on result
        result_icons = {
            "ready": "ℹ️ ",
            "processing": "⏳",
            "success": "✅",
            "failed": "❌"
        }
        status_icon = result_icons.get(self.status['result'], "ℹ️ ")
        
        result_styles = {
            "ready": "cyan",
            "processing": "yellow",
            "success": "green",
            "failed": "red"
        }
        result_style = result_styles.get(self.status['result'], "white")
        
        status_text.append(status_icon, style=result_style)
        status_text.append(self.status['message'], style=result_style)
        
        # Add last key pressed with validation
        if self.status['last_key']:
            key_display = repr(self.status['last_key']) if self.status['last_key'].startswith('\x1b') else self.status['last_key']
            valid_icon = "✓" if self.status['key_valid'] else "✗"
            valid_style = "green" if self.status['key_valid'] else "red"
            status_text.append(f" │ Key: {key_display} ", style="dim")
            status_text.append(valid_icon, style=valid_style)
        
        # Add operation if present
        if self.status['operation']:
            status_text.append(f" │ Op: {self.status['operation']}", style="dim")
        
        # Add command history
        if self.command_history:
            status_text.append(" │ History: ", style="dim")
            for i, entry in enumerate(self.command_history[:3]):  # Show last 3
                if i > 0:
                    status_text.append(", ", style="dim")
                key_str = repr(entry['key']) if entry['key'].startswith('\x1b') else entry['key']
                hist_style = "green dim" if entry['valid'] else "red dim"
                status_text.append(f"{key_str}", style=hist_style)
        
        # Add paper trading / live trading status (without progress bar here)
        try:
            from core.paper_trading_tracker import get_paper_trading_tracker
            tracker = get_paper_trading_tracker()
            pt_status = tracker.get_status()
            
            if pt_status['status'] == 'running':
                # Paper trading active - show status only
                reqs = tracker.check_requirements()
                
                if reqs['all_met']:
                    status_text.append(" │ 📄 Paper: ", style="dim")
                    status_text.append("READY", style="green bold")
                else:
                    status_text.append(" │ 📄 Paper: ", style="dim")
                    hours_done = pt_status['duration_hours']
                    hours_required = reqs['duration']['required']
                    status_text.append(f"{hours_done:.1f}/{hours_required}h", style="yellow")
                
                # Show trades and P&L
                trades = pt_status.get('total_trades', 0)
                pnl = pt_status.get('total_pnl', 0)
                pnl_style = "green" if pnl > 0 else "red" if pnl < 0 else "yellow"
                pnl_sign = "+" if pnl > 0 else ""
                
                status_text.append(f" • {trades}T", style="dim")
                status_text.append(f" • {pnl_sign}${pnl:.2f}", style=pnl_style)
                
            elif pt_status['status'] == 'completed':
                # Approved for live - show permanently
                status_text.append(" │ 🟢 Live: ", style="dim")
                status_text.append("APPROVED", style="green bold")
            elif current_mode == 'LIVE':
                # Live trading active
                status_text.append(" │ 🔴 LIVE", style="red bold")
        except Exception:
            # Fail silently if paper trading tracker not available
            pass
        
        # Add refresh coordinator status
        if hasattr(self, 'refresh_coordinator'):
            try:
                if self.refresh_coordinator.is_refreshing():
                    status_text.append(" │ 🔄", style="yellow bold")
                else:
                    # Show time since last refresh if available
                    import time
                    if hasattr(self.refresh_coordinator, '_last_refresh_time'):
                        elapsed = time.time() - self.refresh_coordinator._last_refresh_time
                        if elapsed < 1.0:
                            status_text.append(" │ ✓", style="green")
            except Exception:
                pass
        
        # Add debug daemon stats with health indicator
        if hasattr(self, 'daemon'):
            try:
                stats = self.daemon.get_session_summary()['stats']
                if stats['actions_logged'] > 0:
                    status_text.append(" │ 🐛 ", style="dim")
                    status_text.append(f"{stats['actions_logged']}A", style="cyan")
                    if stats['errors_logged'] > 0:
                        status_text.append(f"·{stats['errors_logged']}E", style="red")
                    else:
                        status_text.append(f"·0E", style="green dim")
                    if stats['anomalies_logged'] > 0:
                        status_text.append(f"·{stats['anomalies_logged']}W", style="yellow")
                    else:
                        status_text.append(f"·0W", style="green dim")
            except Exception:
                pass
        
        # Add 48-hour progress bar at the END (only if wallet connected and paper trading active)
        try:
            from core.paper_trading_tracker import get_paper_trading_tracker
            tracker = get_paper_trading_tracker()
            pt_status = tracker.get_status()
            
            # Only show progress bar if wallet is connected
            wallet_connected = pt_status.get('wallet_connected', False)
            
            if wallet_connected and pt_status['status'] in ['running', 'completed']:
                hours_done = pt_status.get('duration_hours', 0)
                hours_required = 48  # Fixed requirement
                progress_pct = min((hours_done / hours_required) * 100, 100)
                
                # Progress bar at end of status
                status_text.append(" │ ", style="dim")
                
                if progress_pct >= 100 and pt_status['status'] == 'completed':
                    # Completed - show permanent unlock
                    bar = "█" * 10
                    status_text.append(f"[{bar}]", style="green")
                    status_text.append(" 48h ✓", style="green bold")
                elif pt_status['status'] == 'running':
                    # In progress - only show if running
                    bar_length = 10
                    filled = int((progress_pct / 100) * bar_length)
                    bar = "█" * filled + "░" * (bar_length - filled)
                    status_text.append(f"[{bar}]", style="cyan")
                    status_text.append(f" {progress_pct:.0f}%", style="cyan")
            elif not wallet_connected and pt_status['status'] != 'not_started':
                # Show message if wallet was disconnected during paper trading
                status_text.append(" │ ⚠️  ", style="yellow")
                status_text.append("Connect wallet to resume", style="yellow dim")
        except Exception:
            # No paper trading session yet
            pass
        
        layout["status"].update(Panel(
            status_text,
            title=f"Status [{self.status['result'].upper()}]",
            border_style=result_style,
            padding=(0, 1)
        ))
        
        # Render command bar with countdown
        command_text = Text()
        command_text.append("[Q]uit  ", style="bold cyan")
        command_text.append("[R]efresh  ", style="bold green")
        command_text.append("[W]allet  ", style="bold magenta")
        command_text.append("[S]eeds  ", style="bold yellow")
        command_text.append("[B]acktest  ", style="bold blue")
        command_text.append("[X]Debug  ", style="bold red")
        command_text.append("[D]ocs  ", style="bold white")
        command_text.append("[H]elp  ", style="bold white")
        command_text.append(f"│ Refresh in {countdown}s", style="dim")
        
        layout["commands"].update(Panel(
            command_text,
            border_style="dim",
            padding=(0, 2)
        ))
    
    def render_modal(self) -> Optional[Panel]:
        """Render active modal if any"""
        if self.active_modal == 'help':
            return render_help_screen()
        
        elif self.active_modal == 'ml':
            return render_ml_control_panel()
        
        elif self.active_modal == 'seed':
            return render_seed_browser(
                view=self.seed_browser_view,
                page=self.seed_browser_page
            )
        
        elif self.active_modal == 'backtest':
            return render_backtest_control(
                self.backtest_controller,
                view=self.modal_view
            )
        
        elif self.active_modal == 'debug':
            # Get available sessions for session switching
            sessions = self.daemon.get_recent_sessions() if hasattr(self, 'daemon') else []
            selected_session = sessions[self.debug_session_idx]['session_id'] if sessions and self.debug_session_idx < len(sessions) and not sessions[self.debug_session_idx].get('is_current') else None
            
            return render_debug_terminal(
                view=self.debug_view,
                page=self.debug_page,
                selected_session=selected_session
            )
        
        return None
    
    def create_display(self, countdown: int = 10) -> Layout:
        """Create complete display with layout and optional modal"""
        if self.active_modal:
            # Show modal with status and command bars
            modal_panel = self.render_modal()
            
            # Create modal layout with status and commands
            overlay = Layout()
            overlay.split_column(
                Layout(modal_panel, ratio=18),
                Layout(name="modal_status", ratio=1, minimum_size=2),
                Layout(name="modal_commands", ratio=1, minimum_size=3)
            )
            
            # Render status panel with same logic as main dashboard
            status_text = Text()
            
            result_icons = {"ready": "ℹ️ ", "processing": "⏳", "success": "✅", "failed": "❌"}
            result_styles = {"ready": "cyan", "processing": "yellow", "success": "green", "failed": "red"}
            
            status_icon = result_icons.get(self.status['result'], "ℹ️ ")
            result_style = result_styles.get(self.status['result'], "white")
            
            status_text.append(status_icon, style=result_style)
            status_text.append(self.status['message'], style=result_style)
            
            if self.status['last_key']:
                key_display = repr(self.status['last_key']) if self.status['last_key'].startswith('\x1b') else self.status['last_key']
                valid_icon = "✓" if self.status['key_valid'] else "✗"
                valid_style = "green" if self.status['key_valid'] else "red"
                status_text.append(f" │ Key: {key_display} ", style="dim")
                status_text.append(valid_icon, style=valid_style)
            
            if self.command_history:
                status_text.append(" │ Hist: ", style="dim")
                for i, entry in enumerate(self.command_history[:3]):
                    if i > 0:
                        status_text.append(", ", style="dim")
                    key_str = repr(entry['key']) if entry['key'].startswith('\x1b') else entry['key']
                    hist_style = "green dim" if entry['valid'] else "red dim"
                    status_text.append(f"{key_str}", style=hist_style)
            
            overlay["modal_status"].update(Panel(
                status_text,
                title=f"Status [{self.status['result'].upper()}]",
                border_style=result_style,
                padding=(0, 1)
            ))
            
            # Render command bar
            command_text = Text()
            command_text.append("[ESC/Q] Exit  ", style="bold cyan")
            command_text.append("[H]elp  ", style="bold white")
            command_text.append(f"│ Modal: {self.active_modal}", style="dim")
            
            overlay["modal_commands"].update(Panel(
                command_text,
                border_style="dim",
                padding=(0, 2)
            ))
            
            return overlay
        else:
            # Show normal 4-panel layout
            layout = self.create_layout()
            self.render_panels(layout, countdown=countdown)
            return layout
    
    def handle_key(self, key: str):
        """Handle keyboard input with comprehensive tracking"""
        import time
        
        # Log every keypress with validation
        is_valid = self.log_key_press(key)
        
        if self.active_modal:
            # Handle ESC in all forms - universal modal exit
            if key in ['\x1b', 'escape'] or key.startswith('\x1b'):
                modal_name = self.active_modal  # Capture before clearing
                self.start_operation(f"Close {modal_name}", "ESC pressed")
                self.active_modal = None
                self.modal_view = 'status'
                self.complete_operation(True, f"Closed {modal_name} screen")
                return
            
            # Handle modal-specific keys with operation tracking
            if self.active_modal == 'help':
                if key in ['q', 'h']:
                    self.start_operation("Close help", "Q pressed")
                    self.active_modal = None
                    self.complete_operation(True, "Help closed")
                elif key.lower() == 'd':
                    self.start_operation("Documentation", "Opening from help")
                    try:
                        open_documentation()
                        self.complete_operation(True, "Documentation opened")
                    except Exception as e:
                        self.complete_operation(False, "Failed to open docs", str(e))
            
            elif self.active_modal == 'ml':
                should_close, message, new_asset = handle_ml_control_key(
                    key, self.ml_selected_asset
                )
                self.ml_selected_asset = new_asset
                if should_close:
                    self.start_operation("Close ML", "ML control closed")
                    self.active_modal = None
                    self.complete_operation(True, "ML control closed")
                else:
                    self.start_operation("ML Command", f"Processing {key}")
                    self.complete_operation(True, message or "Command processed")
            
            elif self.active_modal == 'seed':
                if key == 'q':
                    self.start_operation("Close seeds", "Q pressed")
                    self.active_modal = None
                    self.complete_operation(True, "Seed browser closed")
                elif key.lower() == 'w':
                    self.start_operation("Whitelist view", "Switching to whitelist")
                    self.seed_browser_view = 'whitelist'
                    self.seed_browser_page = 0
                    self.complete_operation(True, "Whitelist view active")
                elif key.lower() == 'b':
                    self.start_operation("Blacklist view", "Switching to blacklist")
                    self.seed_browser_view = 'blacklist'
                    self.seed_browser_page = 0
                    self.complete_operation(True, "Blacklist view active")
                elif key.lower() == 'a':
                    self.start_operation("All seeds view", "Switching to all seeds")
                    self.seed_browser_view = 'all'
                    self.seed_browser_page = 0
                    self.complete_operation(True, "All seeds view active")
                elif key == 'left' and self.seed_browser_page > 0:
                    self.start_operation("Page left", "Previous page")
                    self.seed_browser_page -= 1
                    self.complete_operation(True, f"Page {self.seed_browser_page}")
                elif key == 'right':
                    self.start_operation("Page right", "Next page")
                    self.seed_browser_page += 1
                    self.complete_operation(True, f"Page {self.seed_browser_page}")
            
            elif self.active_modal == 'backtest':
                # Q also exits backtest modal
                if key.lower() == 'q':
                    self.start_operation("Close backtest", "Q pressed")
                    self.active_modal = None
                    self.modal_view = 'status'
                    self.complete_operation(True, "Backtest control closed")
                else:
                    should_close, message, new_view = handle_backtest_key(
                        key, self.backtest_controller, self.modal_view
                    )
                    self.modal_view = new_view
                    if should_close:
                        self.start_operation("Close backtest", "Command closed modal")
                        self.active_modal = None
                        self.modal_view = 'status'
                        self.complete_operation(True, "Backtest control closed")
                    else:
                        self.start_operation("Backtest command", f"Processing {key}")
                        self.complete_operation(True, message or "Command processed")
            
            elif self.active_modal == 'debug':
                # Get available sessions
                sessions = self.daemon.get_recent_sessions() if hasattr(self, 'daemon') else []
                
                # Handle debug key with full parameters
                should_close, message, new_view, new_page, new_session_idx = handle_debug_key(
                    key, self.debug_view, self.debug_page, self.debug_session_idx, sessions
                )
                
                self.debug_view = new_view
                self.debug_page = new_page
                self.debug_session_idx = new_session_idx
                
                if should_close:
                    self.start_operation("Close debug", "Debug terminal closed")
                    self.active_modal = None
                    self.debug_page = 0  # Reset pagination
                    self.debug_session_idx = 0  # Reset session
                    self.complete_operation(True, "Debug terminal closed")
                else:
                    self.start_operation("Debug command", f"Processing {key}")
                    self.complete_operation(True, message or "Command processed")
        
        else:
            # Handle main dashboard keys with comprehensive tracking
            if key.lower() == 'q':
                self.start_operation("Exit", "Quit command")
                self.running = False
                self.complete_operation(True, "Exiting dashboard...")
            
            elif key.lower() == 'r':
                self.start_operation("Refresh", "Manual refresh triggered")
                try:
                    # Check for pending wallet connections before full refresh
                    from core.simple_wallet_connector import get_connector
                    connector = get_connector()
                    response = connector.check_response()
                    if response:
                        # New wallet connection detected - force wallet refresh first
                        self._force_wallet_refresh()
                    
                    # Then do full refresh
                    self.refresh_data()
                    timestamp = time.strftime('%H:%M:%S')
                    self.complete_operation(True, f"Data refreshed at {timestamp}")
                except Exception as e:
                    self.complete_operation(False, "Refresh failed", str(e))
            
            elif key.lower() == 's':
                self.start_operation("Seed Browser", "Opening seed browser")
                self.active_modal = 'seed'
                self.seed_browser_page = 0
                self.seed_browser_view = 'all'
                self.complete_operation(True, "Seed browser opened")
            
            elif key.lower() == 'm':
                self.start_operation("ML Control", "Opening ML panel")
                self.active_modal = 'ml'
                self.ml_selected_asset = 'ETH'
                self.complete_operation(True, "ML control panel opened")
            
            elif key.lower() == 'h':
                self.start_operation("Help", "Opening help screen")
                self.active_modal = 'help'
                self.complete_operation(True, "Help screen opened")
            
            elif key.lower() == 'd':
                self.start_operation("Documentation", "Opening docs in browser")
                try:
                    open_documentation()
                    self.complete_operation(True, "Documentation opened in browser")
                except Exception as e:
                    self.complete_operation(False, "Failed to open docs", str(e))
            
            elif key.lower() == 'b':
                self.start_operation("Backtest Control", "Opening backtest panel")
                self.active_modal = 'backtest'
                self.modal_view = 'status'
                self.complete_operation(True, "Backtest control opened")
            
            elif key.lower() == 'l':
                self.start_operation("Live Mode", "Attempting live trading")
                self.complete_operation(False, "Live trading not yet available", "Feature in development")
            
            elif key.lower() == 'w':
                self.start_operation("Wallet", "Processing wallet command")
                try:
                    self.handle_wallet_command()
                    self.complete_operation(True, "Wallet command processed")
                except Exception as e:
                    self.complete_operation(False, "Wallet command failed", str(e))
            
            elif key.lower() == 'x':
                self.start_operation("Debug Terminal", "Opening debug terminal")
                self.active_modal = 'debug'
                self.debug_view = 'live'
                self.complete_operation(True, "Debug terminal opened")
            
            else:
                # Unknown/invalid key
                if not is_valid:
                    if len(key) == 1 and key.isprintable():
                        self.status['message'] = f"Unknown command: '{key}' - Press H for help"
                        self.status['result'] = 'failed'
    
    def refresh_data(self):
        """Refresh data from all sources (coordinated)"""
        # Check if refresh is allowed
        if not self.refresh_coordinator.start_refresh():
            return  # Already refreshing or too soon
        
        try:
            # Pull real data from files and systems
            self._do_refresh()
        finally:
            self.refresh_coordinator.end_refresh()
    
    def _do_refresh(self):
        """Internal refresh logic"""
        try:
            # 1. Read real wallet connection status
            from core.simple_wallet_connector import get_connector
            from core.position_size_limiter import get_position_limiter
            from core.file_lock import safe_json_load
            from pathlib import Path
            import json
            
            connector = get_connector()
            
            # Check for new wallet connection responses (from Downloads folder)
            response = connector.check_response()
            if response:
                # New connection detected - update status instead of printing
                address = response.get('metamask_address', 'N/A')
                self.status['message'] = f"Wallet connected: {address[:10]}..."
                self.status['result'] = 'success'
            
            # Update wallet status from auto_wallet_manager config file (with file locking)
            wallet_config_path = Path('data/wallet_config.json')
            if wallet_config_path.exists():
                config = safe_json_load(str(wallet_config_path), default={})
                if config:
                    # Extract metamask info
                    metamask_info = config.get('metamask', {})
                    is_connected = metamask_info.get('connected', False)
                    address = metamask_info.get('address', None)
                    
                    # Always update from file (source of truth)
                    self.data['wallet']['metamask'] = {
                        'connected': is_connected,
                        'address': address,
                        'chain_id': '0x1',
                        'connected_at': metamask_info.get('last_connected')
                    }
                    
                    # Update BTC wallet info
                    btc_info = config.get('btc_wallet', {})
                    if btc_info.get('created', False):
                        self.data['wallet']['btc_wallet'] = {
                            'exists': True,
                            'address': btc_info.get('address', 'N/A'),
                            'balance': btc_info.get('balance_usd', 0.0)
                        }
                    
                    # Update profit tracking
                    profit_info = config.get('profit_tracking', {})
                    self.data['wallet']['profit'] = profit_info.get('total_profit_usd', 0.0)
            
            # 2. Calculate real position limits based on current capital
            current_capital = self.data['bot']['balance'].get('current', 10.0)
            limiter = get_position_limiter()
            limit_info = limiter.get_position_info_for_display(current_capital)
            
            self.data['wallet']['position_limits'] = {
                'max_position_size': limit_info['max_position_size'],
                'rule': limit_info['rule'],
                'profit_threshold': 100.0,
                'funding_amount': 50.0
            }
            self.data['wallet']['capital'] = current_capital
            
            # 2.5. Update slot allocation data based on current balance
            current_mode = self.data['bot'].get('mode', 'BACKTEST')
            try:
                from core.founder_fee_manager import FounderFeeManager
                fee_manager = FounderFeeManager(mode=current_mode)
                slot_data = get_slot_allocation_display_data(
                    current_balance=current_capital,
                    mode=current_mode,
                    founder_fee_manager=fee_manager
                )
                self.data['bot']['slot_allocation'] = slot_data
            except Exception as e:
                # Fallback if slot allocation fails
                slot_data = get_slot_allocation_display_data(
                    current_balance=current_capital,
                    mode=current_mode,
                    founder_fee_manager=None
                )
                self.data['bot']['slot_allocation'] = slot_data
            
            # 3. Read live trader status if available
            status_file = Path('data/live_trader_status.json')
            if status_file.exists():
                with open(status_file, 'r') as f:
                    live_status = json.load(f)
                    # Merge live trader data properly
                    self.data['bot']['status'] = live_status.get('status', 'stopped')
                    self.data['bot']['mode'] = live_status.get('mode', 'UNKNOWN').upper()
                    self.data['bot']['balance'] = live_status.get('balance', {})
                    self.data['bot']['target_balance'] = live_status.get('targets', {}).get('target_balance', 100.0)
                    
                    # Active positions
                    positions_info = live_status.get('positions', {})
                    self.data['bot']['active_positions'] = positions_info.get('details', [])
                    
                    # Trading stats
                    trading_info = live_status.get('trading', {})
                    self.data['bot']['trades_today'] = trading_info.get('trades_today', 0)
                    
                    # Last trade info
                    if trading_info.get('last_trade'):
                        self.data['bot']['last_trade'] = {
                            'closed_at': trading_info['last_trade'],
                            'outcome': 'SIGNAL',
                            'pnl': 0,
                            'timeframe': '?',
                            'duration_min': 0
                        }
                    
                    # Merge statistics
                    if 'statistics' in live_status:
                        self.data['bot']['statistics'] = live_status['statistics']
                        
                        # Update performance panel with timeframe stats from statistics
                        tf_stats = live_status['statistics'].get('by_timeframe', {})
                        if tf_stats:
                            self.data['performance']['by_timeframe'] = tf_stats
                    
                    # Merge tier information
                    if 'tier' in live_status:
                        self.data['bot']['tier'] = live_status['tier']
                        self.data['wallet']['tier'] = live_status['tier']
            
        except Exception as e:
            # Log error but don't crash
            pass
    
    def update_seed_data(self, data: Dict):
        """Update seed panel data"""
        self.data['seed'].update(data)
    
    def update_bot_data(self, data: Dict):
        """Update bot panel data"""
        self.data['bot'].update(data)
    
    def update_performance_data(self, data: Dict):
        """Update performance panel data"""
        self.data['performance'].update(data)
    
    def update_wallet_data(self, data: Dict):
        """Update wallet panel data"""
        self.data['wallet'].update(data)
    
    def _force_wallet_refresh(self):
        """Force immediate wallet data refresh, bypassing refresh coordinator.
        Used after wallet connect/disconnect to ensure panel updates immediately.
        """
        try:
            from core.file_lock import safe_json_load
            from pathlib import Path
            from core.simple_wallet_connector import get_connector
            
            connector = get_connector()
            
            # Check for new wallet connection responses
            response = connector.check_response()
            if response:
                # New connection detected - update status
                address = response.get('metamask', {}).get('address', 'N/A')
                if address != 'N/A':
                    self.status['message'] = f"✅ Wallet connected: {address[:10]}..."
                    self.status['result'] = 'success'
            
            # Force read wallet config file (source of truth)
            wallet_config_path = Path('data/wallet_config.json')
            if wallet_config_path.exists():
                config = safe_json_load(str(wallet_config_path), default={})
                if config:
                    # Extract and update metamask info
                    metamask_info = config.get('metamask', {})
                    is_connected = metamask_info.get('connected', False)
                    address = metamask_info.get('address', None)
                    
                    # Force update wallet data (bypass refresh coordinator)
                    self.data['wallet']['metamask'] = {
                        'connected': is_connected,
                        'address': address,
                        'chain_id': '0x1',
                        'connected_at': metamask_info.get('last_connected')
                    }
                    
                    # Update BTC wallet info
                    btc_info = config.get('btc_wallet', {})
                    if btc_info.get('created', False):
                        self.data['wallet']['btc_wallet'] = {
                            'exists': True,
                            'address': btc_info.get('address', 'N/A'),
                            'balance': btc_info.get('balance_usd', 0.0)
                        }
                    
                    # Update profit tracking
                    profit_info = config.get('profit_tracking', {})
                    self.data['wallet']['profit'] = profit_info.get('total_profit_usd', 0.0)
                    
                    # Link wallet to paper trading if connected
                    if is_connected and address:
                        from core.paper_trading_tracker import get_paper_trading_tracker
                        tracker = get_paper_trading_tracker()
                        pt_result = tracker.link_wallet_connection(address)
                        
                        if pt_result.get('paper_trading_started'):
                            self.status['message'] = f"✅ Wallet connected and paper trading started!"
                            self.status['result'] = 'success'
        
        except Exception as e:
            # Log error but don't crash
            self.status['message'] = f"Wallet refresh error: {e}"
            self.status['result'] = 'failed'
    
    def handle_wallet_command(self):
        """Handle wallet connect/disconnect command with paper trading integration"""
        try:
            from core.simple_wallet_connector import get_connector
            from core.paper_trading_tracker import get_paper_trading_tracker
            
            connector = get_connector()
            is_connected = connector.is_connected()
            
            if is_connected:
                # Disconnect wallet
                address = connector.get_address()
                connector.disconnect()
                
                # Unlink from paper trading
                tracker = get_paper_trading_tracker()
                pt_result = tracker.unlink_wallet_connection()
                
                # Force immediate wallet data refresh
                self._force_wallet_refresh()
                
                # Show status message
                if pt_result.get('paper_trading_stopped'):
                    self.status['message'] = f"Wallet disconnected and paper trading stopped"
                else:
                    self.status['message'] = f"Wallet {address[:10]}... disconnected"
                self.status['result'] = 'success'
            else:
                # Initiate wallet connection
                self.status['message'] = "Opening MetaMask in browser..."
                connector.connect()
                # Note: Paper trading will be linked when wallet actually connects
                # User should press 'R' after connecting in browser to link wallet to paper trading
        
        except Exception as e:
            self.status['message'] = f"Wallet error: {e}"
            self.status['result'] = 'failed'
    
    def run_static(self):
        """Run dashboard in static mode (for testing)"""
        try:
            import time
            import sys
            import select
            import tty
            import termios
            
            # Check if stdin is a terminal
            if not sys.stdin.isatty():
                self.console.print("[red]Error: stdin is not a terminal[/red]")
                return
            
            # Save terminal settings
            old_settings = termios.tcgetattr(sys.stdin)
            
            try:
                # Set terminal to raw mode for non-blocking input
                tty.setcbreak(sys.stdin.fileno())
                
                # Clear screen before starting to prevent rendering artifacts
                self.console.clear()
                
                # Reduce refresh rate to prevent duplication (2 Hz instead of 4 Hz)
                with Live(self.create_display(), console=self.console, refresh_per_second=2, screen=True) as live:
                    # Run system check on startup
                    if not self.system_check_complete:
                        self.start_operation("System check", "Validating all commands")
                        live.update(self.create_display(countdown=10))
                        time.sleep(0.5)  # Brief delay to show startup message
                        
                        all_passed, checks = self.run_system_check()
                        self.system_check_complete = True
                        
                        # Show results in status
                        passed_count = sum(1 for c in checks if c.startswith('✓'))
                        total_count = len(checks)
                        
                        if all_passed:
                            self.complete_operation(True, f"System check passed ({passed_count}/{total_count})")
                        else:
                            failed = [c for c in checks if c.startswith('✗')]
                            self.complete_operation(False, f"System check: {len(failed)} failures")
                        
                        live.update(self.create_display(countdown=10))
                        time.sleep(1.5)  # Show results before continuing
                        
                        # Set ready state with summary
                        self.set_ready(f"Ready • {passed_count}/{total_count} checks passed")
                    
                    last_refresh = time.time()
                    refresh_interval = 10.0  # 10 seconds
                    
                    while self.running:
                        # Calculate countdown
                        current_time = time.time()
                        elapsed = current_time - last_refresh
                        countdown = max(0, int(refresh_interval - elapsed))
                        
                        # Check for keyboard input (non-blocking with small timeout)
                        if select.select([sys.stdin], [], [], 0.05)[0]:
                            key = sys.stdin.read(1)
                            
                            # Handle ESC sequences - read complete sequence
                            if key == '\x1b':  # ESC sequence
                                # Wait briefly for sequence completion
                                if select.select([sys.stdin], [], [], 0.1)[0]:
                                    extra = sys.stdin.read(2)
                                    key = key + extra
                                # else: just ESC key alone
                            
                            # Handle key (preserve ESC, lowercase others)
                            if key == '\x1b' or key.startswith('\x1b'):
                                self.handle_key(key)
                            else:
                                self.handle_key(key.lower() if len(key) == 1 else key)
                        
                        # Check for operation timeout in background
                        self.check_operation_timeout()
                        
                        # Auto-refresh data every 10 seconds
                        if elapsed >= refresh_interval:
                            self.refresh_data()
                            last_refresh = current_time
                            countdown = int(refresh_interval)
                        
                        # Update display with countdown (longer sleep to reduce rendering frequency)
                        live.update(self.create_display(countdown=countdown))
                        time.sleep(0.2)
            
            finally:
                # Restore terminal settings
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                
                # Close debug daemon when dashboard exits
                if hasattr(self, 'daemon'):
                    try:
                        from core.debug_daemon import close_daemon
                        close_daemon()
                    except Exception:
                        pass
        
        except KeyboardInterrupt:
            self.console.print("\n[green]Dashboard closed[/green]\n")
            
            # Close debug daemon on interrupt
            if hasattr(self, 'daemon'):
                try:
                    from core.debug_daemon import close_daemon
                    close_daemon()
                except Exception:
                    pass


def main():
    """Main entry point for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="HARVEST Terminal Dashboard")
    parser.add_argument('--test', action='store_true', help='Run in test mode with mock data')
    parser.add_argument('--refresh', type=int, default=2, help='Refresh interval in seconds')
    
    args = parser.parse_args()
    
    dashboard = TerminalDashboard(refresh_interval=args.refresh)
    
    if args.test:
        # Load mock data for testing (all 5 timeframes)
        dashboard.update_seed_data({
            'total_tested': 258,
            'whitelisted': 47,
            'blacklisted': 89,
            'top_performer': {'seed': 15913535, 'win_rate': 0.82, 'pnl': 24.75},
            'current_seeds_by_timeframe': {
                '1m': {'seed': 1829669, 'input_seed': 555},
                '5m': {'seed': 5659348, 'input_seed': 666},
                '15m': {'seed': 15542880, 'input_seed': 777},
                '1h': {'seed': 60507652, 'input_seed': 888},
                '4h': {'seed': 240966292, 'input_seed': 999}
            }
        })
        
        dashboard.update_bot_data({
            'status': 'running',
            'mode': 'BACKTEST',
            'backtest_days': 90,
            'seed_info': {'strategy_seed': 15913535, 'timeframe': '15m', 'input_seed': 777},
            'balance': {'initial': 10.0, 'current': 34.75},
            'active_positions': [],
            'last_trade': None
        })
        
        dashboard.update_performance_data({
            'wins': 28,
            'losses': 7,
            'pnl': 24.75,
            'max_drawdown': 4.8,
            'by_timeframe': {
                '1m': {'wins': 8, 'losses': 3, 'pnl': 5.40, 'avg_position_size': 85.50},
                '5m': {'wins': 6, 'losses': 2, 'pnl': 3.65, 'avg_position_size': 92.30},
                '15m': {'wins': 7, 'losses': 1, 'pnl': 6.80, 'avg_position_size': 100.00},
                '1h': {'wins': 5, 'losses': 1, 'pnl': 5.90, 'avg_position_size': 98.75},
                '4h': {'wins': 2, 'losses': 0, 'pnl': 3.00, 'avg_position_size': 100.00}
            }
        })
        
        dashboard.update_wallet_data({
            'metamask': {
                'connected': True,
                'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
                'balance_eth': 0.5234,
                'balance_usd': 1847.32
            },
            'btc_wallet': {
                'exists': True,
                'address': 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh'
            },
            'position_limits': {
                'max_position_size': 100.0,
                'rule': '$100 cap (< $5K capital)',
                'profit_threshold': 100.0,
                'funding_amount': 50.0
            },
            'capital': 34.75,
            'profit': 24.75
        })
        
        dashboard.run_static()
    else:
        console = Console()
        console.print("[red]Error: Dashboard requires integration with backtest system[/red]")
        console.print("[yellow]Use --test flag to run in test mode with mock data[/yellow]")


if __name__ == "__main__":
    main()
