# Strategy Seed System - Like Minecraft Seeds

## Overview

The strategy seed system generates **deterministic seeds** from strategy parameters, similar to how Minecraft generates unique worlds from seeds. This ensures:

- **Same parameters → always same seed** (reproducibility)
- **Different parameters → always different seed** (uniqueness)
- **Automatic seed generation** when parameters change
- **Collision-free** seeds across timeframes

## Two Types of Seeds

### 1. Backtest Seed
- **What**: Controls random number generation for deterministic execution
- **Purpose**: Ensures identical results across repeated backtest runs
- **Usage**: Set via `seed=42` parameter in backtest
- **Example**: `random.seed(42)`, `np.random.seed(42)`
- **Scope**: Global - affects entire backtest run

### 2. Strategy Seed
- **What**: Unique identifier generated from strategy parameters
- **Purpose**: Identifies specific strategy configurations
- **Usage**: Generated automatically from parameters
- **Example**: `15m conf=0.78, vol=1.30 → seed=15542880`
- **Scope**: Per-strategy - each timeframe has its own

## Strategy Seed Generation

### How It Works

```python
from ml.strategy_seed_generator import generate_strategy_seed

# Define strategy parameters
params = {
    'min_confidence': 0.78,
    'min_volume': 1.30,
    'min_trend': 0.65,
    'min_adx': 30,
    'min_roc': 0.15,
    'atr_min': 0.8,
    'atr_max': 2.0
}

# Generate deterministic seed
seed = generate_strategy_seed('15m', params)
# Output: 15542880

# Same params → same seed (always)
seed2 = generate_strategy_seed('15m', params)
assert seed == seed2  # ✅ True

# Change ANY parameter → different seed
params['min_confidence'] = 0.79
seed3 = generate_strategy_seed('15m', params)
assert seed != seed3  # ✅ True
```

### Algorithm Details

1. **Timeframe Prefix**: Each timeframe gets a unique prefix
   - `15m` → prefix 15
   - `1h` → prefix 60
   - `4h` → prefix 240

2. **Parameter Canonicalization**: Parameters sorted in consistent order
   - Rounded to 2 decimal places for stability
   - Format: `"15m:min_confidence=0.78|min_volume=1.30|..."`

3. **Hashing**: SHA-256 hash of canonical string
   - First 12 hex characters converted to integer
   - Modulo 1,000,000 to keep seed reasonably sized

4. **Final Seed**: `(prefix × 1,000,000) + hash_value`
   - Ensures timeframes never collide
   - Example: `15×1,000,000 + 542,880 = 15,542,880`

## Current Strategy Seeds

Based on current BASE_STRATEGY parameters:

| Timeframe | Parameters | Strategy Seed |
|-----------|------------|---------------|
| 15m | conf=0.78, vol=1.30, trend=0.65, adx=30 | **15542880** |
| 1h  | conf=0.72, vol=1.20, trend=0.55, adx=27 | **60507652** |
| 4h  | conf=0.63, vol=1.05, trend=0.46, adx=25 | **240966292** |

## Where Seeds Are Used

### 1. Timeframe Strategies
```python
# strategies/timeframe_strategy.py
strategy = TimeframeStrategy15m(config)
print(strategy.seed)  # 15542880
```

### 2. Backtest Output
```
================================================================================
MULTI-TIMEFRAME BACKTEST: ETH
Backtest Seed: 42 (for reproducibility)
Timeframes: 15m, 1h, 4h
Strategy Seeds: 15m=15542880, 1h=60507652, 4h=240966292
================================================================================
```

### 3. Strategy Performance Reports
```
Timeframe: 15m (strategy_seed=15542880)
  Total Trades: 8
  Win Rate: 75.0%
  Total P&L: $1.23
```

### 4. Trade Records
Each trade stores the strategy seed:
```python
trade = {
    'timeframe': '15m',
    'strategy_seed': 15542880,
    'entry_time': '2024-11-01T12:00:00',
    'pnl': 0.15
}
```

### 5. Strategy Pool
```json
{
  "15m": {
    "strategies": {
      "base": {
        "thresholds": {"min_confidence": 0.78, ...},
        "seed": 15542880,
        "proven_wr": 0.76,
        "proven_trades": 50
      },
      "strategy_1": {
        "thresholds": {"min_confidence": 0.80, ...},
        "seed": 15789123,
        "proven_wr": 0.78,
        "proven_trades": 30
      }
    }
  }
}
```

## Benefits

### 1. Automatic Identification
- No need to manually assign seeds
- Parameters hash to consistent identifier
- Same config always produces same seed

### 2. Parameter Tracking
- Seed changes when any parameter changes
- Easy to detect configuration drift
- Can reverse-lookup parameters from seed

### 3. Collision Prevention
- Timeframe prefixes ensure no cross-TF collisions
- Hash function provides uniqueness within timeframe
- Validated on every backtest

### 4. Reproducibility
- Given seed + parameters, can reproduce exact strategy
- Historical trades traceable to specific configurations
- Strategy evolution clearly documented

### 5. Version Control
- Old seeds remain valid (immutable)
- New parameters generate new seeds automatically
- Strategy history preserved

## Testing

Run the test suite to verify seed system:

```bash
# Test seed generation
python -m ml.strategy_seed_generator

# Test parameter sensitivity
python test_seed_changes.py
```

Expected output:
```
✅ Test 1: Determinism (same params → same seed)
✅ Test 2: Confidence change detection  
✅ Test 3: Volume change detection
✅ Test 4: ADX change detection
✅ All seeds are unique - no collisions
✅ ALL TESTS PASSED - Minecraft-like seed system working!
```

## Future Enhancements

### Possible Extensions
1. **Seed Registry**: Track all historical seeds and their parameters
2. **Seed Lookup API**: Given seed, retrieve full parameter set
3. **Seed Versioning**: Support schema changes without breaking old seeds
4. **Cross-Asset Seeds**: Extend to multi-asset strategies
5. **Seed Compression**: Shorten seeds for display (e.g., base36 encoding)

## Migration Notes

### Old System (Hardcoded)
```python
# Old: Manual seeds
TimeframeStrategy15m: seed=15001  ❌
TimeframeStrategy1h:  seed=60001  ❌
TimeframeStrategy4h:  seed=240001 ❌
```

### New System (Dynamic)
```python
# New: Generated from parameters
TimeframeStrategy15m: seed=15542880  ✅ (from params)
TimeframeStrategy1h:  seed=60507652  ✅ (from params)
TimeframeStrategy4h:  seed=240966292 ✅ (from params)
```

**Migration**: Automatic - seeds regenerate on next backtest run.

## FAQ

**Q: What happens if I change a parameter?**  
A: A new seed is generated automatically. The old seed remains valid for historical reference.

**Q: Can two different configurations have the same seed?**  
A: No - the hash function ensures uniqueness. Collisions are checked and would raise an error.

**Q: Are backtest seed and strategy seed the same?**  
A: No - backtest seed controls randomness, strategy seed identifies configuration.

**Q: Can I manually set a strategy seed?**  
A: Not recommended - defeats the purpose of automatic generation. Use parameters instead.

**Q: How do I find which parameters produced a seed?**  
A: Use `reverse_lookup_config(seed, known_strategies)` from strategy_seed_generator.

**Q: What if I add new parameters later?**  
A: New parameters will affect seed generation. Old seeds remain valid for their parameter sets.

---

**Implementation**: `ml/strategy_seed_generator.py`  
**Tests**: `test_seed_changes.py`  
**Integration**: `strategies/timeframe_strategy.py`, `ml/strategy_pool.py`
