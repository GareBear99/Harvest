# Bulletproof Seed System - Complete Implementation

## ✅ COMPLETE: Two Critical Features

### 1. **Versioned Seeds** - Adding Parameters Won't Break Old Seeds
### 2. **Seed Registry** - Database Tracking Every Seed's Performance

---

## Feature 1: Versioned Seed System

**Problem**: What happens when we add new parameters like `rsi_threshold`? Old seeds become invalid!

**Solution**: Seeds include version numbers. v1 seeds stay v1 forever.

### Implementation: `ml/seed_versioning.py`

```python
PARAMETER_VERSIONS = {
    'v1': [
        'min_confidence',
        'min_volume',
        'min_trend',
        'min_adx',
        'min_roc',
        'atr_min',
        'atr_max'
    ],
    # Future: v2 with new parameters
    'v2': [
        'min_confidence',
        ...  # v1 params (NEVER reorder!)
        'rsi_threshold',  # New param
        'macd_threshold'  # New param
    ]
}
```

### How It Works

1. **Seed includes version**: `15m:v1:min_confidence=0.78|...`
2. **v1 parameters locked**: Order never changes
3. **v2 adds new params**: At end of list, v1 unchanged
4. **Old seeds work forever**: v1 seed always uses v1 parameters

### Usage

```python
from ml.seed_versioning import generate_versioned_seed

# Generate v1 seed
seed_info = generate_versioned_seed('15m', params)
# Returns: {'seed': 15542880, 'version': 'v1', ...}

# Later: Add RSI parameter → v2 seed
params['rsi_threshold'] = 70
seed_info_v2 = generate_versioned_seed('15m', params)
# Returns: {'seed': 15999123, 'version': 'v2', ...}

# Original v1 seed still works!
seed_info_v1_check = generate_versioned_seed('15m', old_params, version='v1')
# Returns: {'seed': 15542880, 'version': 'v1', ...} ✓ Same!
```

### Rules for Adding Parameters

**DO**:
1. Create new version (v2, v3, etc.)
2. Copy ALL v1 parameters first
3. Add new parameters at END
4. Update `CURRENT_VERSION = 'v2'`

**DON'T**:
- Never reorder existing parameters
- Never remove parameters
- Never change parameter names

### Migration

```python
from ml.seed_versioning import migrate_seed_to_new_version

# Migrate old v1 seed to v2
old_seed_info = {'seed': 15542880, 'version': 'v1', ...}
new_params = old_params.copy()
new_params['rsi_threshold'] = 70

migrated = migrate_seed_to_new_version(old_seed_info, new_params)
# Returns: {
#   'seed': 15999123,
#   'version': 'v2',
#   'migrated_from': {'old_seed': 15542880, 'old_version': 'v1'}
# }
```

---

## Feature 2: Seed Registry Database

**Problem**: Need to track which seeds perform well/poorly across all tests.

**Solution**: Database logging every seed tested with full performance stats.

### Implementation: `ml/seed_registry.py`

Tracks for each seed:
- Win rate, trade count, P&L
- All parameters used
- Test history (multiple backtests)
- Best/worst WR across tests
- Input seed (if generated from `seed_to_strategy`)

### Usage

#### Register Seed Before Testing
```python
from ml.seed_registry import SeedRegistry

registry = SeedRegistry()  # Loads ml/seed_registry.json

# Register seed before backtest
registry.register_seed(
    seed=15542880,
    timeframe='15m',
    parameters={'min_confidence': 0.78, ...},
    version='v1',
    input_seed=42  # Optional: if generated from input seed
)
```

#### Record Backtest Results
```python
# After backtest completes
registry.record_test_result(15542880, {
    'win_rate': 0.75,
    'trades': 20,
    'wins': 15,
    'losses': 5,
    'pnl': 12.50,
    'dataset': 'ETH_90days',
    'test_date': '2025-12-17'
})
```

#### Query Performance
```python
# Get top performers
top_seeds = registry.get_top_performers(n=10, min_trades=10)
# Returns list of seed info, sorted by win rate

# Get worst performers
worst_seeds = registry.get_worst_performers(n=5, min_trades=10)

# Get all seeds for a timeframe
seeds_15m = registry.get_by_timeframe('15m')

# Get specific seed info
info = registry.get_seed_info(15542880)
```

#### View Summary
```python
registry.print_summary()
```

**Output**:
```
================================================================================
SEED REGISTRY SUMMARY
================================================================================

Total Seeds Tracked: 25
Total Tests Run: 48
Total Trades: 534

Seeds by Timeframe:
  15m: 12 seeds
  1h: 8 seeds
  4h: 5 seeds

🏆 Top 5 Performers (min 10 trades):
  1. Seed 15913535 (15m): 83.3% WR, 18 trades, $+18.30 PnL
  2. Seed 15542880 (15m): 75.0% WR, 20 trades, $+12.50 PnL
  ...

📉 Worst 3 Performers (min 10 trades):
  1. Seed 60507652 (1h): 46.7% WR, 15 trades, $-3.20 PnL
  ...
```

#### Export to CSV
```python
registry.export_to_csv('seed_performance.csv')
```

**CSV format**:
```csv
seed,timeframe,version,input_seed,total_tests,total_trades,avg_wr,best_wr,worst_wr,total_pnl,registered_at
15542880,15m,v1,42,3,60,0.7500,0.8000,0.7000,25.40,2025-12-17T10:30:00
...
```

### Registry File: `ml/seed_registry.json`

```json
{
  "seeds": {
    "15542880": {
      "seed": 15542880,
      "timeframe": "15m",
      "parameters": {
        "min_confidence": 0.78,
        "min_volume": 1.30,
        ...
      },
      "version": "v1",
      "input_seed": 42,
      "registered_at": "2025-12-17T10:30:00",
      "test_history": [
        {
          "test_date": "2025-12-17T10:45:00",
          "dataset": "ETH_90days",
          "win_rate": 0.75,
          "trades": 20,
          "wins": 15,
          "losses": 5,
          "pnl": 12.50
        }
      ],
      "stats": {
        "total_tests": 1,
        "total_trades": 20,
        "total_wins": 15,
        "total_losses": 5,
        "total_pnl": 12.50,
        "best_wr": 0.75,
        "worst_wr": 0.75,
        "avg_wr": 0.75
      }
    }
  },
  "last_updated": "2025-12-17T10:45:00",
  "total_seeds": 1
}
```

---

## Integration Workflow

### Testing Random Seeds

```python
# 1. Generate parameters from input seed
from ml.seed_to_strategy import seed_to_strategy

input_seed = 777
params = seed_to_strategy('15m', input_seed)
# params = {'min_confidence': 0.73, 'min_volume': 1.22, ...}

# 2. Calculate strategy seed
from ml.strategy_seed_generator import generate_strategy_seed

strategy_seed = generate_strategy_seed('15m', params)
# strategy_seed = 15913535

# 3. Register in database
from ml.seed_registry import SeedRegistry

registry = SeedRegistry()
registry.register_seed(
    seed=strategy_seed,
    timeframe='15m',
    parameters=params,
    version='v1',
    input_seed=input_seed
)

# 4. Run backtest with these params
# ... backtest code ...

# 5. Record results
registry.record_test_result(strategy_seed, {
    'win_rate': 0.82,
    'trades': 18,
    'wins': 15,
    'losses': 3,
    'pnl': 18.30,
    'dataset': 'ETH_90days'
})

# 6. If it performs well, save input_seed=777 for reproduction!
```

### Finding Best Seeds

```python
registry = SeedRegistry()

# Get top 10 seeds
top = registry.get_top_performers(n=10, min_trades=20)

for seed_info in top:
    print(f"Seed: {seed_info['seed']}")
    print(f"  Input seed: {seed_info.get('input_seed')}")  # Use this to reproduce!
    print(f"  Win rate: {seed_info['stats']['avg_wr']:.1%}")
    print(f"  Trades: {seed_info['stats']['total_trades']}")
    print(f"  Parameters: {seed_info['parameters']}")
```

---

## Files Created

1. **`ml/seed_versioning.py`** - Versioned seed system
2. **`ml/seed_registry.py`** - Performance database
3. **`ml/seed_to_strategy.py`** - Input seed → parameters
4. **`ml/strategy_seed_generator.py`** - Parameters → strategy seed

## Data Files

1. **`ml/seed_registry.json`** - Performance database (auto-created)
2. **`seed_registry.csv`** - Exported performance data (optional)

---

## Benefits

### ✅ Bulletproof Evolution
- Add new parameters anytime without breaking old seeds
- v1 seeds work forever
- Migration tracked automatically

### ✅ Complete History
- Every seed tested is logged
- Full performance stats across multiple tests
- Can identify best/worst performers

### ✅ Reproducibility
- Input seed → generates same params always
- Strategy seed → identifies exact configuration
- Can reproduce any configuration anytime

### ✅ Analytics Ready
- Export to CSV for analysis
- Query by timeframe, version, performance
- Track performance evolution over time

---

## Example: Complete Testing Workflow

```python
from ml.seed_to_strategy import seed_to_strategy
from ml.strategy_seed_generator import generate_strategy_seed
from ml.seed_registry import SeedRegistry

# Initialize registry
registry = SeedRegistry()

# Test 100 random input seeds
for input_seed in range(1, 101):
    # Generate params
    params = seed_to_strategy('15m', input_seed)
    
    # Get strategy seed
    strategy_seed = generate_strategy_seed('15m', params)
    
    # Register
    registry.register_seed(
        seed=strategy_seed,
        timeframe='15m',
        parameters=params,
        version='v1',
        input_seed=input_seed
    )
    
    # Run backtest (simplified)
    result = run_backtest(params)
    
    # Record results
    registry.record_test_result(strategy_seed, {
        'win_rate': result.win_rate,
        'trades': result.total_trades,
        'wins': result.wins,
        'losses': result.losses,
        'pnl': result.pnl,
        'dataset': 'ETH_90days'
    })

# Find best performers
print("Top 10 seeds tested:")
top = registry.get_top_performers(n=10, min_trades=10)
for i, seed_info in enumerate(top, 1):
    input_seed = seed_info.get('input_seed')
    strategy_seed = seed_info['seed']
    wr = seed_info['stats']['avg_wr']
    
    print(f"{i}. Input seed: {input_seed} → Strategy seed: {strategy_seed}")
    print(f"   Win rate: {wr:.1%}")
    
    # To reproduce this seed:
    # params = seed_to_strategy('15m', input_seed)
```

---

## Next Steps

When you add new parameters in the future:

1. **Update `ml/seed_versioning.py`**:
   ```python
   PARAMETER_VERSIONS = {
       'v1': [...],  # Never change!
       'v2': [..., 'rsi_threshold', 'macd_threshold']  # Add new
   }
   CURRENT_VERSION = 'v2'
   ```

2. **Update `ml/seed_to_strategy.py`**:
   ```python
   base_ranges = {
       ...  # v1 params
       'rsi_threshold': (65, 75, False),  # New
       'macd_threshold': (0.01, 0.10, False)  # New
   }
   ```

3. **All old seeds continue working with v1!**

---

**Status**: ✅ Production ready, fully tested, bulletproof for parameter evolution
