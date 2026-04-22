# Timeframe Expansion: 1m and 5m Added

> ⚠️ **HISTORICAL DOCUMENT NOTICE**: This document shows `'seed': 1001` and `'seed': 5001` in BASE_STRATEGY examples. These are timeframe prefixes (internal identifiers), NOT real deterministic seeds.
>
> **Real SHA-256 seeds:** 1829669 (1m), 5659348 (5m) - See `docs/SEED_SYSTEM_CRITICAL_NOTE.md` for details.

## Overview

The HARVEST trading bot now supports **5 timeframes** for maximum trading opportunities:

- **1m** - Ultra-fast scalping (NEW)
- **5m** - Fast scalping (NEW)
- **15m** - Short-term swing
- **1h** - Medium-term swing
- **4h** - Long-term swing

This expansion enables **high-frequency trading** while maintaining the proven multi-timeframe strategy.

---

## New Timeframe Configurations

### 1-Minute (1m) - Ultra-Fast Scalping

```python
'1m': {
    'aggregation_minutes': 1,
    'tp_multiplier': 1.2,           # Quick 20% profit target
    'sl_multiplier': 0.6,           # Tight stop loss
    'time_limit_minutes': 30,       # Max 30 min hold time
    'position_size_multiplier': 0.3, # Small positions (30% of baseline)
    'confidence_threshold': 0.82     # Very high confidence required
}
```

**BASE_STRATEGY for 1m:**
```python
'1m': {
    'seed': 1001,
    'min_confidence': 0.82,  # Very high confidence
    'min_volume': 1.35,      # Strong volume essential
    'min_trend': 0.68,       # Very strong trend
    'min_adx': 32,           # Very strong trend strength
    'min_roc': -1.05,        # Tight momentum
    'atr_min': 0.50,
    'atr_max': 3.0
}
```

**Characteristics:**
- ✅ Ultra-fast entries and exits (30 min max)
- ✅ High confidence filter (82%+)
- ✅ Small position sizes for risk management
- ✅ Ideal for scalping volatile moves
- ⚠️  Requires very strong signals

**Expected Trade Frequency:** 10-20 trades/day

---

### 5-Minute (5m) - Fast Scalping

```python
'5m': {
    'aggregation_minutes': 5,
    'tp_multiplier': 1.3,           # Quick 30% profit target
    'sl_multiplier': 0.65,          # Tight stop loss
    'time_limit_minutes': 60,       # Max 1 hour hold time
    'position_size_multiplier': 0.4, # Small positions (40% of baseline)
    'confidence_threshold': 0.80     # High confidence required
}
```

**BASE_STRATEGY for 5m:**
```python
'5m': {
    'seed': 5001,
    'min_confidence': 0.80,  # High confidence
    'min_volume': 1.30,      # Strong volume
    'min_trend': 0.65,       # Strong trend
    'min_adx': 30,           # Strong trend strength
    'min_roc': -1.1,         # Strict momentum
    'atr_min': 0.45,
    'atr_max': 3.2
}
```

**Characteristics:**
- ✅ Fast entries and exits (1 hour max)
- ✅ High confidence filter (80%+)
- ✅ Moderate position sizes
- ✅ Balance between speed and reliability
- ⚠️  Requires strong signals

**Expected Trade Frequency:** 6-12 trades/day

---

## Complete Timeframe Hierarchy

### Position Sizing Strategy

Each timeframe has a position size multiplier relative to baseline:

| Timeframe | Multiplier | Rationale |
|-----------|------------|-----------|
| 1m | 0.3x | Ultra-fast, highest risk |
| 5m | 0.4x | Fast, high risk |
| 15m | 0.5x | Short-term, moderate risk |
| 1h | 1.0x | Baseline, balanced |
| 4h | 1.5x | Long-term, highest conviction |

### Confidence Thresholds

Higher frequency = higher confidence requirement:

| Timeframe | Threshold | Description |
|-----------|-----------|-------------|
| 1m | 0.82 | Very high confidence |
| 5m | 0.80 | High confidence |
| 15m | 0.75 | Strong confidence |
| 1h | 0.75 | Strong confidence |
| 4h | 0.63 | Conservative baseline |

### Time Limits

Maximum hold time per trade:

| Timeframe | Max Hold | Candles |
|-----------|----------|---------|
| 1m | 30 min | ~30 candles |
| 5m | 1 hour | ~12 candles |
| 15m | 3 hours | ~12 candles |
| 1h | 12 hours | ~12 candles |
| 4h | 24 hours | ~6 candles |

---

## Trading Strategy Impact

### Before (3 Timeframes)

- **15m, 1h, 4h**
- Expected: 3-5 trades/day
- Coverage: Medium to long-term moves

### After (5 Timeframes)

- **1m, 5m, 15m, 1h, 4h**
- Expected: 15-30+ trades/day
- Coverage: Ultra-fast to long-term moves

### Simultaneous Position Limits

The system still maintains **max 2 simultaneous positions** across ALL timeframes:

```python
def can_open_position(self, timeframe: str) -> bool:
    # Max 1 position per timeframe
    if timeframe in self.active_positions:
        return False
    
    # Max 2 simultaneous positions total (across all 5 timeframes)
    if len(self.active_positions) >= 2:
        return False
    
    return True
```

This prevents over-leveraging while allowing quick rotation through opportunities.

---

## Seed Testing Support

All seed testing commands now support 1m and 5m:

### Test All Whitelisted Seeds

```bash
# 1-minute
python ml/seed_tester.py test-all 1m
python backtest_90_complete.py --test-seeds-file ml/test_whitelist_1m.json

# 5-minute
python ml/seed_tester.py test-all 5m
python backtest_90_complete.py --test-seeds-file ml/test_whitelist_5m.json
```

### Quick Test (Top 10)

```bash
# 1-minute
python ml/seed_tester.py test-top10 1m
python backtest_90_complete.py --test-seeds-file ml/test_top10_1m.json

# 5-minute
python ml/seed_tester.py test-top10 5m
python backtest_90_complete.py --test-seeds-file ml/test_top10_5m.json
```

### Overwrite BASE_STRATEGY

```bash
# 1-minute with best seed
python ml/seed_tester.py overwrite 1m --use-best

# 5-minute with specific seed
python ml/seed_tester.py overwrite 5m --seed 5002001
```

---

## Dashboard Integration

The dashboard now shows active seeds for **all 5 timeframes**:

```
┌─────────────────────────────┐
│ 🌱 SEED STATUS              │
├─────────────────────────────┤
│ Active Seeds:               │
│  1m:  1002345               │
│  5m:  5012678               │
│  15m: 15542880              │
│  1h:  60507652              │
│  4h:  240966292             │
├─────────────────────────────┤
│ Whitelisted: 25             │
│ Blacklisted: 3              │
└─────────────────────────────┘
```

---

## Performance Expectations

### Expected Results (90-day backtest)

| Timeframe | Est. Trades | Target WR | Avg Duration |
|-----------|-------------|-----------|--------------|
| 1m | 900-1800 | 70%+ | 10-20 min |
| 5m | 540-720 | 72%+ | 20-40 min |
| 15m | 270-360 | 75%+ | 1-2 hours |
| 1h | 90-135 | 75%+ | 4-8 hours |
| 4h | 30-45 | 65%+ | 12-18 hours |

**Combined:** 1,830-3,060 trades over 90 days (20-34 trades/day)

### Risk Profile

| Timeframe | Risk Level | Position Size | Win Rate Requirement |
|-----------|------------|---------------|---------------------|
| 1m | Very High | 30% | 82%+ confidence |
| 5m | High | 40% | 80%+ confidence |
| 15m | Moderate | 50% | 75%+ confidence |
| 1h | Moderate | 100% | 75%+ confidence |
| 4h | Lower | 150% | 63%+ confidence |

---

## Best Practices

### 1. Start Conservative

Begin with only **15m, 1h, 4h** to establish baseline performance. Add 1m and 5m after proving profitability.

### 2. Monitor High-Frequency Performance

1m and 5m trades happen quickly. Watch for:
- Execution slippage
- Win rate degradation
- Over-trading

### 3. Adjust Position Sizes

The default multipliers are conservative. Adjust based on your risk tolerance and account size.

### 4. Test Before Live

Always backtest new timeframes:

```bash
# Test all 5 timeframes
python backtest_90_complete.py --seed 42
```

### 5. Use Seed Testing

Find optimal seeds for each timeframe:

```bash
# Find best 1m seed
python ml/seed_tester.py test-top10 1m
python backtest_90_complete.py --test-seeds-file ml/test_top10_1m.json

# Deploy if results are good
python ml/seed_tester.py overwrite 1m --use-best
```

---

## Updated Files

### Core Configuration

- ✅ `ml/base_strategy.py` - Added 1m BASE_STRATEGY
- ✅ `backtest_90_complete.py` - Added 1m and 5m TIMEFRAME_CONFIGS
- ✅ `ml/seed_tester.py` - Support for all 5 timeframes

### Seed System

All seed tracking automatically supports new timeframes:
- `ml/seed_registry.json` - Tracks 1m and 5m seeds
- `ml/seed_catalog.json` - Records all trades per timeframe
- `ml/seed_whitelist.json` - Separate whitelist per timeframe
- `ml/seed_blacklist.json` - Separate blacklist per timeframe

### Dashboard

- `dashboard/panels.py` - Shows all 5 timeframes
- `dashboard/backtest_control.py` - Test/overwrite for all timeframes

---

## Migration Guide

### For Existing Users

Your existing system will continue to work. To enable new timeframes:

1. **No code changes needed** - 1m and 5m are already configured
2. **Backtest to validate:**
   ```bash
   python backtest_90_complete.py
   ```
3. **Generate seeds for new timeframes:**
   ```bash
   # Run multiple backtests with different seeds
   for seed in {1..10}; do
       python backtest_90_complete.py --seed $seed
   done
   ```
4. **Check whitelisted seeds:**
   ```bash
   python ml/seed_tester.py status
   ```

### Selective Timeframe Usage

To use only specific timeframes, edit `TIMEFRAME_CONFIGS` in `backtest_90_complete.py`:

```python
# Example: Use only 1m, 5m, 15m (disable 1h and 4h)
TIMEFRAME_CONFIGS = {
    '1m': { ... },
    '5m': { ... },
    '15m': { ... },
    # Comment out or remove:
    # '1h': { ... },
    # '4h': { ... },
}
```

---

## CLI Reference

All commands now accept 1m and 5m:

```bash
# Seed Testing
python ml/seed_tester.py test-all <1m|5m|15m|1h|4h>
python ml/seed_tester.py test-top10 <1m|5m|15m|1h|4h>

# BASE_STRATEGY Management
python ml/seed_tester.py overwrite <1m|5m|15m|1h|4h> --use-best
python ml/seed_tester.py overwrite <1m|5m|15m|1h|4h> --seed <number>
python ml/seed_tester.py reset [--timeframe <1m|5m|15m|1h|4h>]
python ml/seed_tester.py status

# Backtesting
python backtest_90_complete.py --seed <number>
python backtest_90_complete.py --test-seeds-file <json_file>
```

---

## Summary

✅ **1m and 5m timeframes fully integrated**  
✅ **All seed testing commands support new timeframes**  
✅ **BASE_STRATEGY configured for ultra-fast trading**  
✅ **Dashboard displays all 5 timeframes**  
✅ **Position sizing optimized per timeframe**  
✅ **Conservative defaults with high confidence filters**  

The system now supports **ultra-high-frequency trading** while maintaining risk controls and proven methodology.

**Estimated daily trades: 15-30+ opportunities across all timeframes**
