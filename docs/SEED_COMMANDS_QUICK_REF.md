# Seed Testing Commands - Quick Reference

## ✅ Implementation Complete

Both features are now fully implemented and working:

### 1. Seed Testing Commands
Test whitelisted seeds to find the best performers per timeframe.

### 2. BASE_STRATEGY Overwrite
Replace BASE_STRATEGY with proven seed configurations.

---

## Quick Commands

### Test All Whitelisted Seeds
```bash
# Generate test list
python ml/seed_tester.py test-all 15m

# Execute tests
python backtest_90_complete.py --test-seeds-file ml/test_whitelist_15m.json
```

### Quick Test (Top 10)
```bash
# Generate test list
python ml/seed_tester.py test-top10 1h

# Execute tests
python backtest_90_complete.py --test-seeds-file ml/test_top10_1h.json
```

### Overwrite BASE_STRATEGY
```bash
# Auto-select best seed
python ml/seed_tester.py overwrite 15m --use-best

# Use specific seed
python ml/seed_tester.py overwrite 1h --seed 60507652
```

### Reset BASE_STRATEGY
```bash
# Reset all timeframes
python ml/seed_tester.py reset

# Reset specific timeframe
python ml/seed_tester.py reset --timeframe 15m
```

### Check Status
```bash
python ml/seed_tester.py status
```

---

## Dashboard Integration

Press `B` to open Backtest Control panel, then:

- `T` - Test all whitelisted seeds
- `Q` - Quick test (top 10)
- `O` - Overwrite BASE_STRATEGY with best seed
- `R` - Reset BASE_STRATEGY
- `H` - View history
- `ESC` - Back to main

---

## Files Created

### By seed_tester.py
- `ml/test_whitelist_<timeframe>.json` - Test configuration
- `ml/test_top10_<timeframe>.json` - Quick test configuration
- `ml/base_strategy_backup.json` - Original BASE_STRATEGY (auto-created once)
- `ml/base_strategy_overrides.json` - Current overrides

### By backtest_90_complete.py
- `ml/batch_test_results_<timeframe>_<timestamp>.json` - Test results

---

## Workflow Example

```bash
# 1. Find best seed for 15m timeframe
python ml/seed_tester.py test-top10 15m
python backtest_90_complete.py --test-seeds-file ml/test_top10_15m.json

# 2. Deploy best seed
python ml/seed_tester.py overwrite 15m --use-best

# 3. Verify
python ml/seed_tester.py status

# 4. Rollback if needed
python ml/seed_tester.py reset --timeframe 15m
```

---

## Safety Features

✅ Automatic backup of original BASE_STRATEGY  
✅ Interactive confirmation before overwrite  
✅ Independent per-timeframe management  
✅ Easy rollback with reset command  
✅ Timestamped audit trail  

---

## Integration Points

### With Existing Systems
- **Seed Registry**: All tested seeds auto-recorded
- **Seed Tracker**: Whitelist/blacklist auto-updated
- **Dashboard**: Real-time status display
- **Live Trading**: New trades use overridden parameters

### Test Results Format
```json
{
  "seed": 15542880,
  "actual_wr": 0.763,
  "trades": 45,
  "pnl": 12.50,
  "final_balance": 22.50
}
```

---

## CLI Reference

```bash
# Testing
ml/seed_tester.py test-all <timeframe>
ml/seed_tester.py test-top10 <timeframe>

# Management
ml/seed_tester.py overwrite <timeframe> --use-best
ml/seed_tester.py overwrite <timeframe> --seed <number>
ml/seed_tester.py reset [--timeframe <timeframe>]
ml/seed_tester.py status

# Execution
backtest_90_complete.py --seed <number>
backtest_90_complete.py --test-seeds-file <json_file>
backtest_90_complete.py --test-seeds-file <file> --data-file <path>
```

---

## What's New

### ml/seed_tester.py (NEW)
Complete seed testing and BASE_STRATEGY management system:
- Batch seed testing (all whitelisted or top 10)
- BASE_STRATEGY overwrite with backup
- Reset functionality
- Status checking

### backtest_90_complete.py (UPDATED)
Added batch testing support:
- `--test-seeds-file` parameter
- `--seed` parameter for single seed tests
- Automatic result ranking and saving

### dashboard/backtest_control.py (UPDATED)
New keyboard commands:
- `T` - Test all whitelisted
- `Q` - Quick test top 10
- `O` - Overwrite BASE_STRATEGY
- `R` - Reset BASE_STRATEGY

---

## Documentation

Full guide: `SEED_TESTING_GUIDE.md`

---

## Status: ✅ READY TO USE

All features tested and operational.
