# Automatic Strategy Updater System

## Overview

Intelligent system that ensures data is always fresh and automatically maintains fallback strategies.

**Before any trading**, the system:
1. ✅ Checks if data is < 30 days old
2. ✅ Re-downloads stale data automatically
3. ✅ Runs grid search to find 2 best strategies
4. ✅ Saves as fallback strategies per timeframe

---

## How It Works

### Data Freshness Check
- Checks last timestamp in data files
- Compares against 30-day threshold
- Auto-triggers re-download if stale

### Automatic Re-Download
- Downloads 90 days of fresh data
- Validates with blockchain verifier
- Audits for quality

### Fallback Strategy Generation
- Runs full grid search (121,500 combinations)
- Finds top 2 strategies by balanced score (WR × PnL)
- Saves to `ml/fallback_strategies.json`
- Used when no strategies meet WR sweet spot

---

## Usage

### Check Data Freshness
```bash
# Just check, don't update
python auto_strategy_updater.py --check
```

Output:
```
================================================================================
🔍 DATA FRESHNESS CHECK
================================================================================

ETHUSDT    ✅ FRESH    Age: 0 days    
           Last update: 2025-12-16 16:15:00

BTCUSDT    ✅ FRESH    Age: 2 days    
           Last update: 2025-12-15 08:30:00
```

### Automatic Update (Pre-Trading)
```bash
# Check and auto-update if needed
python auto_strategy_updater.py
```

This will:
1. Check all active pairs (ETHUSDT, BTCUSDT)
2. Re-download stale data (> 30 days old)
3. Run grid search for updated pairs
4. Save 2 best strategies as fallbacks

### Force Complete Update
```bash
# Force re-download and regenerate all strategies
python auto_strategy_updater.py --force
```

Use when:
- Market regime changed significantly
- Want to refresh all strategies
- Suspect data corruption

---

## Integration with Trading System

### Before Starting Trading

```python
from auto_strategy_updater import check_before_trading

# Call this before any trading session
updates = check_before_trading()

# Returns:
# {
#     'data_downloads': ['ETHUSDT'],  # Pairs that were updated
#     'strategies_updated': ['ETH_15m', 'ETH_1h', 'ETH_4h'],
#     'up_to_date': ['BTCUSDT']  # Pairs already fresh
# }
```

### Using Fallback Strategies

```python
import json

# Load fallback strategies
with open('ml/fallback_strategies.json', 'r') as f:
    fallbacks = json.load(f)

# Get fallback for ETH 15m
eth_15m_fallbacks = fallbacks['ETH_15m']['strategies']

# Use first fallback if no strategies meet WR threshold
if no_strategies_in_sweet_spot:
    strategy = eth_15m_fallbacks[0]
else:
    strategy = best_strategy_from_pool
```

---

## Fallback Strategy File Format

### Structure

```json
{
  "ETH_15m": {
    "strategies": [
      {
        "min_confidence": 0.83,
        "min_volume": 1.25,
        "min_trend": 0.65,
        "min_adx": 30,
        "min_roc": -1.0,
        "atr_min": 0.4,
        "atr_max": 4.0,
        "win_rate": 0.92,
        "trades": 15,
        "total_pnl": 12.45,
        "updated": "2025-12-17T01:00:00"
      },
      {
        "min_confidence": 0.80,
        "min_volume": 1.20,
        "min_trend": 0.60,
        "min_adx": 28,
        "min_roc": -1.0,
        "atr_min": 0.4,
        "atr_max": 3.5,
        "win_rate": 0.88,
        "trades": 18,
        "total_pnl": 10.25,
        "updated": "2025-12-17T01:00:00"
      }
    ],
    "updated_at": "2025-12-17T01:00:00",
    "data_period": "90_days"
  },
  "ETH_1h": { ... },
  "ETH_4h": { ... },
  "BTC_15m": { ... },
  "BTC_1h": { ... },
  "BTC_4h": { ... }
}
```

### Fields

- **strategies**: Array of 2 best strategies
- **updated_at**: When fallbacks were last generated
- **data_period**: Data window used (90_days)

Each strategy includes:
- All parameter thresholds
- Historical performance (WR, trades, PnL)
- Update timestamp

---

## Active Trading Pairs

System checks these pairs by default (from `trading_pairs_config.py`):

- **ETHUSDT** ✅ Active
- **BTCUSDT** ✅ Active

To add more pairs, update `ACTIVE_PAIRS` in `trading_pairs_config.py`.

---

## Data Freshness Threshold

**Default**: 30 days

**Why 30 days?**
- Market conditions change monthly
- Strategies need recent data to stay relevant
- 90-day window requires monthly refresh

**Adjust if needed**:
```python
# In auto_strategy_updater.py
DATA_FRESHNESS_DAYS = 30  # Change to 7, 14, 60, etc.
```

---

## Workflow Example

### Scenario: Starting Trading on Day 35

1. **System starts** →  Calls `check_before_trading()`
2. **Checks ETHUSDT data** → Last update: 35 days ago
3. **Data is stale** → Auto-triggers re-download
4. **Downloads fresh data** → Gets last 90 days
5. **Runs grid search** → Tests 121,500 combinations for 15m, 1h, 4h
6. **Finds best 2 strategies** → Saves to fallbacks
7. **Ready to trade** → Uses fresh data and updated fallbacks

---

## Performance Impact

### Check Only (`--check`)
- **Time**: < 1 second
- **Impact**: None (just reads files)

### Auto-Update (If Data Fresh)
- **Time**: < 5 seconds
- **Impact**: Minimal (just checks timestamps)

### Auto-Update (If Data Stale)
- **Download**: ~10 minutes per pair
- **Grid Search**: ~17 hours per timeframe
- **Total**: ~51 hours for complete update (3 timeframes × 17 hours)

**Recommendation**: Run overnight or on dedicated machine when update needed.

---

## Safety Features

### ✅ Non-Destructive
- Only updates stale data
- Doesn't touch fresh data
- Preserves existing strategies

### ✅ Verified Data
- Runs blockchain verifier after download
- Runs comprehensive audit
- Only uses validated data

### ✅ Fallback Protection
- Always maintains 2 fallback strategies
- Never removes old fallbacks without replacement
- Gradual strategy evolution

### ✅ Logging
- Logs all data downloads
- Logs all strategy updates
- Tracks update timestamps

---

## Integration Points

### 1. Before Strategy Selection
```python
# In your trading bot startup
from auto_strategy_updater import check_before_trading

# Ensure data is fresh and fallbacks are available
updates = check_before_trading()

# Then proceed with normal trading
```

### 2. Strategy Fallback Logic
```python
# In strategy selection
from ml.strategy_pool import get_best_strategy
import json

# Try to get strategy from pool
strategy = get_best_strategy(asset, timeframe)

# If no strategy meets WR threshold, use fallback
if strategy is None or strategy['win_rate'] < WR_THRESHOLD:
    with open('ml/fallback_strategies.json', 'r') as f:
        fallbacks = json.load(f)
    
    key = f"{asset}_{timeframe}"
    if key in fallbacks:
        # Use first (best) fallback
        strategy = fallbacks[key]['strategies'][0]
        print(f"Using fallback strategy for {key}")
```

### 3. Scheduled Updates
```bash
# Add to cron for monthly updates
# Run at 2 AM on 1st of each month
0 2 1 * * cd /path/to/harvest && python auto_strategy_updater.py
```

---

## Troubleshooting

### Data Shows as Stale But Is Recent
- Check file format (must have 'timestamp' field)
- Verify timezone consistency
- Check if file is corrupted

### Grid Search Takes Too Long
- Normal for 121,500 combinations (~17 hours)
- Run on dedicated machine
- Or reduce parameter grid (not recommended)

### No Fallback Strategies Generated
- Check if strategies had 3+ trades
- Verify grid search completed successfully
- Check `grid_search_results/` for CSV output

### Fallback File Missing
- Run initial update: `python auto_strategy_updater.py`
- System will generate fallbacks for all pairs
- File created at: `ml/fallback_strategies.json`

---

## Best Practices

1. **Run check before each trading session**
   ```python
   check_before_trading()
   ```

2. **Monitor data age**
   ```bash
   python auto_strategy_updater.py --check
   ```

3. **Force update monthly**
   ```bash
   python auto_strategy_updater.py --force
   ```

4. **Review fallbacks regularly**
   - Check `ml/fallback_strategies.json`
   - Verify WR and trade count
   - Update if market regime changed

5. **Keep logs**
   - Save grid search results
   - Track fallback performance
   - Monitor when fallbacks are used

---

## Summary

**Automatic Strategy Updater ensures**:
- ✅ Data is always < 30 days old
- ✅ Fresh data auto-downloaded when stale
- ✅ 2 best fallback strategies always available
- ✅ System never trades on outdated data
- ✅ Graceful degradation if no perfect strategies

**Call before trading**:
```python
from auto_strategy_updater import check_before_trading
check_before_trading()
```

**Your trading system now intelligently maintains itself!** 🎯
