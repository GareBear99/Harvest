# Failsafe System Documentation

## Overview

The failsafe system ensures you always use working strategies by automatically resetting to BASE_STRATEGY when an unproven strategy fails to profit.

## Key Features

### 1. BASE_STRATEGY Restore Point ✅
- BASE_STRATEGY is saved as an immutable restore point in `ml/ml_config.json`
- Always available regardless of ML status (enabled/disabled)
- Never modified, only used as reference for resets

### 2. Automatic Failsafe Reset ✅
**Trigger**: 3 consecutive unprofitable trades (PnL ≤ 0)

**Action**:
- Resets current timeframe to BASE_STRATEGY thresholds
- Clears unproven strategy progress
- Starts building new strategy from base defaults
- Logs reset event with counter

**Protection**: Only applies to **unproven strategies**
- Proven strategies (72%+ WR, 20+ trades) are exempt
- BASE_STRATEGY itself never triggers failsafe

### 3. Independent Timeframe Tracking
- Each timeframe (15m, 1h, 4h) tracks its own unprofitable streak
- Failsafe resets are independent per timeframe
- One timeframe resetting doesn't affect others

## How It Works

### Trade Outcome Tracking

Every trade records its outcome:
```python
outcome = {
    'won': True/False,      # Did trade hit TP?
    'pnl': float,           # Actual profit/loss
    'duration_min': int,    # Trade duration
    'exit_type': str        # 'TP', 'SL', or 'TIME'
}
```

### Consecutive Unprofitable Counter

```
Trade 1: PnL = -0.05 → consecutive_unprofitable = 1
Trade 2: PnL = -0.03 → consecutive_unprofitable = 2
Trade 3: PnL = -0.02 → consecutive_unprofitable = 3 → FAILSAFE RESET!
```

**Reset on profit**:
```
Trade 1: PnL = -0.05 → consecutive_unprofitable = 1
Trade 2: PnL = +0.10 → consecutive_unprofitable = 0  ✅ Reset
```

### Strategy Proven Status

A strategy is **proven** if:
- Win rate ≥ 72%
- Trade count ≥ 20
- Stored in strategy pool

**Unproven** strategies:
- Base strategy being tested
- New strategies under 20 trades
- Strategies below 72% WR

## Failsafe Logic Flow

```
1. Trade completes
   ↓
2. Check PnL
   ↓
3. If PnL > 0:
     - Reset consecutive_unprofitable = 0
     - Continue
   
   If PnL ≤ 0:
     - Increment consecutive_unprofitable
     - Check failsafe trigger
   ↓
4. If consecutive_unprofitable == 3:
     - Check if strategy is proven
     
     If unproven:
       → TRIGGER FAILSAFE RESET
       → Load BASE_STRATEGY
       → Reset counter to 0
       → Log reset event
     
     If proven:
       → Skip reset (strategy is trusted)
       → Continue normal operation
```

## Configuration

### ML Config Settings

Located in `ml/ml_config.json`:

```json
{
  "global_settings": {
    "failsafe_unprofitable_threshold": 3
  },
  "base_strategy_restore_point": {
    "timestamp": "2025-12-16T...",
    "strategies": {
      "15m": { ... },
      "1h": { ... },
      "4h": { ... }
    }
  }
}
```

### Timeframe Statistics

Each timeframe tracks:
```python
{
  "consecutive_unprofitable": 0,  # Current streak
  "failsafe_resets": 0,           # Total resets (lifetime)
  "current_thresholds": { ... },  # Active strategy
  ...
}
```

## Examples

### Example 1: Unproven Strategy Failsafe

```
Timeframe: 15m
Strategy: Building new strategy (5 trades, 40% WR)
Status: UNPROVEN

Trade 1: ETH long, PnL = -$0.05 ❌
  → consecutive_unprofitable = 1

Trade 2: ETH long, PnL = -$0.03 ❌
  → consecutive_unprofitable = 2

Trade 3: ETH short, PnL = -$0.02 ❌
  → consecutive_unprofitable = 3
  → ⚠️  FAILSAFE TRIGGERED!
  → Reset to BASE_STRATEGY
  → Start fresh from base defaults
```

### Example 2: Proven Strategy Exempt

```
Timeframe: 1h
Strategy: strategy_1 (76% WR, 35 trades)
Status: PROVEN ✅

Trade 1: BTC long, PnL = -$0.05 ❌
  → consecutive_unprofitable = 1

Trade 2: BTC short, PnL = -$0.03 ❌
  → consecutive_unprofitable = 2

Trade 3: BTC long, PnL = -$0.02 ❌
  → consecutive_unprofitable = 3
  → Strategy is PROVEN (76% WR, 35 trades)
  → ✅ NO RESET - Continue with proven strategy
```

### Example 3: Profit Resets Counter

```
Timeframe: 4h
Strategy: Building new strategy
Status: UNPROVEN

Trade 1: ETH long, PnL = -$0.05 ❌
  → consecutive_unprofitable = 1

Trade 2: ETH long, PnL = +$0.10 ✅ PROFIT!
  → consecutive_unprofitable = 0 (reset)
  → Continue building strategy normally
```

## Logging & Monitoring

### Failsafe Reset Message

When failsafe triggers:
```
⚠️  FAILSAFE RESET [15m]: 3 unprofitable trades with unproven strategy
   → Reset to BASE_STRATEGY (reset #1)
   → Will build new strategy from BASE defaults
```

### Statistics Tracking

View failsafe stats:
```python
from ml.timeframe_strategy_manager import TimeframeStrategyManager

manager = TimeframeStrategyManager()
stats = manager.timeframe_stats['15m']

print(f"Consecutive unprofitable: {stats['consecutive_unprofitable']}")
print(f"Total failsafe resets: {stats['failsafe_resets']}")
```

## Benefits

1. **Prevents Runaway Losses**
   - Stops bad strategies before they drain capital
   - Automatic detection of non-working approaches

2. **Always Have a Baseline**
   - BASE_STRATEGY always available
   - Proven strategies never reset unnecessarily

3. **Independent Timeframes**
   - Each timeframe protected separately
   - One bad timeframe doesn't affect others

4. **Transparent & Logged**
   - All resets tracked and logged
   - Can review failsafe history

5. **No Manual Intervention**
   - Automatic protection 24/7
   - Works even when you're not watching

## Testing

Run the failsafe test:
```bash
python tests/test_failsafe.py
```

Expected output:
- ✅ BASE_STRATEGY restore point saved
- ✅ Failsafe threshold configured (3 trades)
- ✅ Tracking initialized for all timeframes
- ✅ BASE_STRATEGY consistency verified

## Integration with ML System

### When ML Disabled
- Uses BASE_STRATEGY exclusively
- No adaptive adjustments
- Failsafe still active (protects against bugs)

### When ML Enabled
- Builds strategies adaptively
- Failsafe protects unproven strategies
- Proven strategies immune to reset

## Best Practices

1. **Monitor Failsafe Resets**
   - Check `failsafe_resets` counter periodically
   - High reset count = need better base strategy

2. **Review Reset Events**
   - Investigate what caused 3 unprofitable trades
   - Adjust BASE_STRATEGY if needed

3. **Trust Proven Strategies**
   - Once strategy reaches 72%+ WR with 20+ trades
   - System won't reset it unnecessarily

4. **Combine with Strategy Switching**
   - Failsafe: Protects against unprofitable unproven strategies
   - Strategy switching: Rotates between proven strategies
   - Together: Complete protection system

## Summary

The failsafe system is your safety net:
- ✅ Saves BASE_STRATEGY as restore point
- ✅ Resets unproven strategies after 3 unprofitable trades
- ✅ Protects each timeframe independently
- ✅ Never resets proven strategies
- ✅ Fully automated protection

**You always have a working strategy to fall back on.**
