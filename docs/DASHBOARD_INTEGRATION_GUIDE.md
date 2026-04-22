# Dashboard Integration Guide

## Overview
This guide shows how to integrate the HARVEST dashboard into `backtest_90_complete.py` and other trading systems.

## Quick Start

### 1. Add Command-Line Arguments
In `backtest_90_complete.py`, add dashboard flags to the argument parser:

```python
parser.add_argument('--dashboard', action='store_true',
                   help='Enable live terminal dashboard')
parser.add_argument('--dashboard-refresh', type=float, default=0.5,
                   help='Dashboard refresh interval in seconds (default: 0.5 = 2 Hz)')
```

### 2. Initialize Dashboard (Optional)
At the start of your backtest, check if dashboard is requested:

```python
if args.dashboard:
    from dashboard.live_monitor import create_monitor
    from dashboard.terminal_ui import TerminalDashboard
    
    # Create dashboard
    dashboard = TerminalDashboard(refresh_interval=int(1.0 / args.dashboard_refresh))
    
    # Create monitor (connects to backtest engine)
    monitor = create_monitor(self, refresh_interval=args.dashboard_refresh)
    
    # Register dashboard update callback
    monitor.register_callback(lambda data: dashboard.update_all_data(data))
    
    print("📊 Dashboard initialized")
```

### 3. Update on Trade Events
After each trade execution, notify the dashboard:

```python
# After closing a trade
if hasattr(self, 'dashboard'):
    self.dashboard.update_trade(trade_data)
```

### 4. Clean Shutdown
At the end of backtest:

```python
if hasattr(self, 'dashboard'):
    self.dashboard.stop()
```

## Full Integration Example

### backtest_90_complete.py Integration

```python
class Backtester:
    def __init__(self, initial_balance=10.0, data_file='data/eth_90days.json', 
                 enable_dashboard=False, dashboard_refresh=0.5):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.data_file = data_file
        
        # ... other initialization ...
        
        # Dashboard setup
        self.dashboard = None
        self.monitor = None
        
        if enable_dashboard:
            self._init_dashboard(dashboard_refresh)
    
    def _init_dashboard(self, refresh_interval):
        """Initialize dashboard and monitor"""
        try:
            from dashboard.live_monitor import create_monitor
            from dashboard.terminal_ui import TerminalDashboard
            
            # Create dashboard
            self.dashboard = TerminalDashboard(
                refresh_interval=int(1.0 / refresh_interval)
            )
            
            # Create monitor
            self.monitor = create_monitor(self, refresh_interval=refresh_interval)
            
            # Register callback
            def update_dashboard(data):
                self.dashboard.update_seed_data(data.get('seed', {}))
                self.dashboard.update_bot_data(data.get('bot', {}))
                self.dashboard.update_performance_data(data.get('performance', {}))
                self.dashboard.update_system_data(data.get('system', {}))
            
            self.monitor.register_callback(update_dashboard)
            
            print("📊 Dashboard enabled")
        
        except Exception as e:
            print(f"⚠️  Could not initialize dashboard: {e}")
            self.dashboard = None
            self.monitor = None
    
    def run_backtest(self):
        """Main backtest loop"""
        # ... existing backtest code ...
        
        # After each trade
        if self.monitor:
            self.monitor.update_trade(trade_data)
        
        # ... continue backtest ...
    
    def cleanup(self):
        """Clean shutdown"""
        if self.monitor:
            self.monitor.stop()
        
        if self.dashboard:
            self.dashboard.stop()
```

### Usage

```bash
# Run backtest with dashboard
python backtest_90_complete.py --dashboard

# Custom refresh rate (4 Hz)
python backtest_90_complete.py --dashboard --dashboard-refresh 0.25

# With specific seed
python backtest_90_complete.py --dashboard --seed 777
```

## Advanced Integration

### 1. Add Seed System Integration

```python
from ml.seed_system_unified import UnifiedSeedSystem

class Backtester:
    def __init__(self, ...):
        # ... existing init ...
        
        # Add seed system
        self.seed_system = UnifiedSeedSystem()
    
    def run_backtest(self):
        # Before starting backtest
        if hasattr(self, 'seed') and self.seed:
            seed_info = self.seed_system.generate_and_register_seed(
                input_seed=self.seed,
                timeframe='15m'  # or detect from strategy
            )
            
            if seed_info['status'] == 'blacklisted':
                print(f"⛔ {seed_info['message']}")
                return
            
            self.current_seed = seed_info['strategy_seed']
        
        # ... run backtest ...
        
        # After backtest completes
        if hasattr(self, 'current_seed'):
            results = self._calculate_results()
            self.seed_system.record_backtest_results(
                strategy_seed=self.current_seed,
                timeframe='15m',
                backtest_results=results,
                metadata={'data_file': self.data_file}
            )
```

### 2. Add Backtest Controller Integration

```python
from dashboard.backtest_control import BacktestController

# At module level or in main
backtest_controller = BacktestController()

def run_backtest(...):
    # Start tracking
    backtest_controller.start_backtest(
        seed=args.seed,
        skip_check=args.skip_check,
        data_file=args.data_file
    )
    
    try:
        # Run backtest
        backtester = Backtester(...)
        results = backtester.run_backtest()
        
        # Record completion
        backtest_controller.record_completion(results)
    
    except Exception as e:
        # Record failure
        backtest_controller.stop_backtest()
        raise
```

## Data Structure Reference

### Dashboard Data Format

```python
{
    'seed': {
        'total_tested': int,
        'whitelisted': int,
        'blacklisted': int,
        'top_performer': {
            'seed': int,
            'win_rate': float,  # 0.0 - 1.0
            'pnl': float
        },
        'current_seed': {
            'seed': int,
            'timeframe': str  # '15m', '1h', '4h'
        }
    },
    'bot': {
        'status': str,  # 'running', 'stopped', 'paused'
        'mode': str,  # 'BACKTEST', 'LIVE', 'PAPER'
        'seed_info': {
            'strategy_seed': int,
            'timeframe': str,
            'input_seed': int
        },
        'balance': {
            'initial': float,
            'current': float
        },
        'active_positions': [
            {
                'timeframe': str,
                'side': str,  # 'LONG', 'SHORT'
                'entry_price': float,
                'opened_at': datetime
            }
        ],
        'max_positions': int,
        'last_trade': {
            'outcome': str,  # 'TP', 'SL', etc.
            'timeframe': str,
            'pnl': float,
            'closed_at': datetime
        }
    },
    'performance': {
        'wins': int,
        'losses': int,
        'pnl': float,
        'max_drawdown': float,
        'by_timeframe': {
            '15m': {
                'wins': int,
                'losses': int,
                'pnl': float
            },
            # ... other timeframes
        }
    },
    'system': {
        'data_status': {
            'fresh': bool,
            'updated_ago': str  # '2h ago'
        },
        'connections': str,  # 'operational', 'degraded', 'failed'
        'warnings': [str]  # List of warning messages
    }
}
```

## Testing

### Test Dashboard Standalone
```bash
# Test with mock data
python dashboard/terminal_ui.py --test

# Test specific refresh rate
python dashboard/terminal_ui.py --test --refresh 1
```

### Test All Components
```bash
python test_dashboard_components.py
```

### Test Integration (after integration)
```bash
# Run backtest with dashboard
python backtest_90_complete.py --dashboard --skip-check

# Check for errors in monitor
# Dashboard should update in real-time
# Press 'H' to see help screen
# Press 'Q' to quit
```

## Performance Considerations

### Refresh Rates
- **Default**: 0.5s (2 Hz) - Good balance
- **Fast**: 0.25s (4 Hz) - More responsive, higher CPU
- **Slow**: 1.0s (1 Hz) - Lower overhead, less responsive

### Memory Usage
- Dashboard: ~5-10 MB
- Monitor thread: ~2-5 MB
- Total overhead: ~15 MB typical

### CPU Impact
- At 2 Hz: <1% CPU on modern systems
- At 4 Hz: <2% CPU
- Rendering: ~5-10ms per frame

## Troubleshooting

### Dashboard Not Showing
1. Check rich is installed: `pip install rich>=13.0.0`
2. Verify monitor started: Look for "📡 Dashboard monitor started"
3. Check for exceptions in console

### Data Not Updating
1. Verify monitor is running: `self.monitor.running` should be True
2. Check backtest engine has required attributes
3. Add debug prints in `_collect_data()`

### High CPU Usage
1. Increase refresh interval: `--dashboard-refresh 1.0`
2. Reduce update frequency in monitor
3. Check for tight loops in callbacks

### Keyboard Not Working
1. Dashboard uses rich.Live which captures input differently
2. For full keyboard support, implement with `pynput` or similar
3. Current implementation is display-only (testing mode)

## Next Steps

1. **Implement Full Keyboard Input**: Add `pynput` or `curses` for live keyboard handling
2. **Add Live Trading Mode**: Connect to live trader instead of backtest
3. **Persist Dashboard State**: Save/restore dashboard preferences
4. **Add Alerts**: Desktop notifications for important events
5. **Web Dashboard**: Create Flask/FastAPI version for remote monitoring

## Files Modified

When integrating, you'll modify:
- `backtest_90_complete.py` - Add dashboard arguments and initialization
- `requirements.txt` - Ensure rich and psutil are listed

## Files Created

Dashboard system includes:
- `dashboard/__init__.py`
- `dashboard/formatters.py`
- `dashboard/panels.py`
- `dashboard/ml_control.py`
- `dashboard/help_screen.py`
- `dashboard/seed_browser.py`
- `dashboard/backtest_control.py`
- `dashboard/terminal_ui.py`
- `dashboard/live_monitor.py`

## Support

For issues or questions:
1. Check `DASHBOARD_IMPLEMENTATION.md` for component details
2. Run component tests individually
3. Check monitor logs for data collection errors
4. Verify backtest engine exposes required attributes

---

**Status**: Ready for integration
**Version**: 1.0.0
**Last Updated**: 2024-12-17
