# Statistics Tracking System

## Overview
The HARVEST trading bot now includes comprehensive statistics tracking that monitors:
- **Historical performance**: All-time trades, P&L, win rates
- **Daily metrics**: Trades per day, daily P&L, uptime tracking
- **Timeframe-specific stats**: Performance and seed info for each timeframe (1m, 5m, 15m, 1h, 4h)
- **Session tracking**: Uptime, active trading time, multiple sessions per day

## Architecture

### Core Component
**File**: `core/statistics_tracker.py`

The `StatisticsTracker` class provides:
- Persistent storage in `data/trading_statistics.json`
- Session start/stop tracking
- Signal recording with timeframe and strategy info
- Trade result recording (WIN/LOSS/BREAKEVEN)
- Real-time statistics aggregation

### Integration Points

#### 1. Live Trader
**File**: `live_trader.py`

The live trader:
- Initializes tracker on startup
- Calls `start_session()` when trading begins
- Records each signal with `record_signal()` including:
  - Timeframe
  - Strategy (ER90/SIB)
  - Entry/stop/TP prices
  - Position size
  - Seed number
- Calls `end_session()` on shutdown
- Exports statistics via `export_status()`

#### 2. Dashboard Display
**Files**: `dashboard/panels.py`, `dashboard/terminal_ui.py`

Statistics are displayed in two panels:

**Bot Status Panel** shows:
- Today's trades, P&L, uptime
- All-time trades and total P&L
- Total uptime hours across all sessions
- Average daily uptime
- Trading days count

**Performance Panel** shows:
- Per-timeframe statistics with seed numbers
- Win rate, trade count, P&L for each timeframe
- Active seed being used for each timeframe

## Statistics Structure

### Data File: `data/trading_statistics.json`

```json
{
  "first_trade_date": "2025-12-17",
  "last_trade_date": "2025-12-17",
  "all_time": {
    "total_trades": 125,
    "total_wins": 78,
    "total_losses": 47,
    "total_pnl": 245.50,
    "total_uptime_hours": 48.5,
    "total_sessions": 15,
    "best_day_pnl": 45.25,
    "best_day_date": "2025-12-15",
    "worst_day_pnl": -12.50,
    "worst_day_date": "2025-12-10"
  },
  "by_timeframe": {
    "1h": {
      "trades": 45,
      "wins": 28,
      "losses": 17,
      "pnl": 125.75,
      "seed": 12345678
    },
    "4h": {
      "trades": 32,
      "wins": 21,
      "losses": 11,
      "pnl": 98.25,
      "seed": 87654321
    }
  },
  "by_strategy": {
    "ER90": {
      "trades": 65,
      "wins": 42,
      "losses": 23,
      "pnl": 156.25
    },
    "SIB": {
      "trades": 60,
      "wins": 36,
      "losses": 24,
      "pnl": 89.25
    }
  },
  "daily_history": {
    "2025-12-17": {
      "date": "2025-12-17",
      "trades_count": 8,
      "wins": 5,
      "losses": 3,
      "total_pnl": 18.50,
      "uptime_seconds": 14400,
      "active_time_seconds": 2880,
      "sessions": 2
    }
  },
  "recent_trades": []
}
```

## API Reference

### StatisticsTracker Class

#### Methods

**`start_session()`**
- Call when trading session begins
- Increments total sessions counter
- Marks session start time

**`end_session()`**
- Call when trading session ends
- Calculates session duration
- Updates daily uptime statistics
- Persists data to file

**`record_signal(timeframe, strategy, side, entry, stop, tp1, notional, seed=None)`**
- Records a trading signal (entry)
- Updates trade counters
- Stores seed number for timeframe
- Increments daily trade count

**`record_trade_result(timeframe, strategy, outcome, pnl, duration_min)`**
- Records closed trade result
- Updates win/loss counters
- Accumulates P&L
- Tracks best/worst days

**`get_today_stats() -> Dict`**
- Returns statistics for current day
- Includes current session uptime

**`get_timeframe_stats() -> Dict`**
- Returns per-timeframe statistics
- Includes seed numbers

**`get_all_time_stats() -> Dict`**
- Returns all-time aggregate statistics

**`get_summary_for_dashboard() -> Dict`**
- Returns formatted data for dashboard display
- Includes today, all-time, and timeframe breakdowns

### Singleton Access

```python
from core.statistics_tracker import get_statistics_tracker

tracker = get_statistics_tracker()
```

## Dashboard Display

### Bot Status Panel

```
🤖 BOT STATUS
Status: ⚡ RUNNING
Mode: PAPER

Balance: $10.00 → $34.75
Target $100: [████████░░░░] 35%
P&L: $24.75 (+247.5%)

Positions: 0/2
  No active positions

Today: 8 trades | $18.50 | 4.0h uptime
All-Time: 125 trades | $245.50
Total Uptime: 48.5h (12 days)
Avg Daily: 4.0h/day
Last Trade: None yet
```

### Performance Panel

```
📊 PERFORMANCE
Win Rate: 62.4%
Total Trades: 125
P&L: $245.50
Max Drawdown: -8.5%

By Timeframe:
  1m: No data
  5m: No data
  15m: No data
  1h: 62% WR (45) $125.75 (Seed 12345678)
  4h: 66% WR (32) $98.25 (Seed 87654321)
```

## Usage Examples

### Recording a Signal

```python
from core.statistics_tracker import get_statistics_tracker

tracker = get_statistics_tracker()
tracker.start_session()

# When a trading signal is generated
tracker.record_signal(
    timeframe='1h',
    strategy='ER90',
    side='LONG',
    entry=3500.0,
    stop=3450.0,
    tp1=3600.0,
    notional=100.0,
    seed=12345678
)
```

### Recording a Trade Result

```python
# When trade closes
tracker.record_trade_result(
    timeframe='1h',
    strategy='ER90',
    outcome='WIN',  # or 'LOSS', 'BREAKEVEN'
    pnl=15.50,
    duration_min=45
)
```

### Getting Statistics

```python
# For dashboard
summary = tracker.get_summary_for_dashboard()

# Today's stats
today = summary['today']
print(f"Today: {today['trades']} trades, ${today['pnl']:.2f}")

# All-time stats
all_time = summary['all_time']
print(f"Total: {all_time['total_trades']} trades")
print(f"Total P&L: ${all_time['total_pnl']:.2f}")
print(f"Uptime: {all_time['total_uptime_hours']:.1f}h")

# Timeframe stats
tf_stats = summary['by_timeframe']['1h']
print(f"1h: {tf_stats['trades']} trades, Seed {tf_stats['seed']}")
```

## Features

### ✅ Implemented

1. **Persistent Storage**: All statistics saved to JSON file
2. **Session Tracking**: Multiple sessions per day with uptime calculation
3. **Daily Metrics**: Trades, P&L, uptime tracked per day
4. **Timeframe Performance**: Stats per timeframe with seed info
5. **Strategy Breakdown**: ER90 vs SIB performance tracking
6. **Best/Worst Days**: Automatic tracking of peak performance
7. **Dashboard Integration**: Real-time display of all metrics
8. **Auto-refresh**: Dashboard updates every 10 seconds

### 📊 Tracked Metrics

**Today:**
- Trades count
- Wins/losses
- Total P&L
- Uptime hours
- Active trading time

**All-Time:**
- Total trades
- Total wins/losses
- Total P&L
- Total uptime hours
- Total sessions
- Average daily uptime
- Trading days count
- Best day (P&L and date)
- Worst day (P&L and date)

**Per Timeframe:**
- Trade count
- Win/loss count
- Total P&L
- Active seed number

**Per Strategy:**
- Trade count
- Win/loss count
- Total P&L

## Testing

Run the standalone test:

```bash
python core/statistics_tracker.py
```

Expected output:
```
Testing StatisticsTracker...
✅ Session started
✅ Recorded 2 signals
✅ Recorded trade results

📊 Summary:
Today: 2 trades, $7.25 P&L
All-time: 2 trades, $7.25 P&L
Total uptime: 0.0 hours

✅ Session ended - stats saved
```

## Data Files

- **Main statistics**: `data/trading_statistics.json`
- **Live trader status**: `data/live_trader_status.json` (includes statistics export)
- **Test file**: `data/test_stats.json` (created by test script)

## Future Enhancements

Potential additions:
- **Sharpe ratio** calculation
- **Maximum consecutive wins/losses**
- **Average trade duration** per timeframe
- **Time-of-day** performance analysis
- **Weekly/monthly** aggregations
- **Export to CSV** for external analysis
- **Performance charts** (ASCII or HTML)
- **Alerts** for milestone achievements (100 trades, $1000 profit, etc.)

## Troubleshooting

### Statistics not updating
- Verify `data/trading_statistics.json` exists and is writable
- Check that `start_session()` is called when live trader starts
- Ensure signals are recorded with `record_signal()`

### Dashboard shows zero values
- Check that `data/live_trader_status.json` contains 'statistics' key
- Verify auto-refresh is working (every 10 seconds)
- Ensure live trader is running and exporting status

### Seed numbers not showing
- Confirm seed is passed to `record_signal()` method
- Check ExecutionIntent object has seed attribute
- Verify strategies are setting seed on intents
