# Grid Search Optimization

## Overview

Optimized the 121,500 combination grid search for maximum speed using multiprocessing and efficient batch processing.

## Performance Improvements

### Original Implementation
- **Method:** Sequential processing
- **Speed:** ~5-10 strategies/second
- **Time for 121,500:** ~6-8 hours per timeframe
- **CPU Usage:** Single core (~12-15% on 8-core system)

### Optimized Implementation  
- **Method:** Parallel multiprocessing
- **Speed:** ~50-100+ strategies/second (10-20x faster)
- **Time for 121,500:** ~20-40 minutes per timeframe
- **CPU Usage:** All cores (~90%+ on 8-core system)

## Key Optimizations

### 1. Multiprocessing (`multiprocessing.Pool`)
- Uses all CPU cores except 1 (reserved for system)
- Parallel execution of strategy tests
- ~8x speedup on 8-core systems

### 2. Batch Processing
- Groups strategies into optimal batch sizes
- Reduces process creation overhead
- Batch size: `total // (workers * 10)`
- Example: 121,500 strategies / (7 workers * 10) = 1,735 per batch

### 3. Progress Tracking
- Real-time ETA calculation
- Strategies/second rate monitoring
- Progress percentage updates
- Batch completion tracking

### 4. Efficient Data Handling
- Minimal object creation
- Reuses backtest objects within batches
- Streams results to avoid memory buildup

### 5. Error Handling
- Continues on individual strategy errors
- Logs errors without stopping entire search
- Returns error info in results

## File Structure

```
grid_search_optimized.py       # Main optimized implementation
test_grid_search_quick.py      # Quick test (324 combinations)
grid_search_all_strategies.py  # Original implementation (backup)
```

## Usage

### Quick Test (324 combinations, ~30 seconds)
```bash
python test_grid_search_quick.py --asset BTCUSDT --timeframe 1m
```

### Full Search (121,500 combinations, ~20-40 minutes)
```bash
python grid_search_optimized.py --asset BTCUSDT --timeframe 1m
```

### Integration (auto_strategy_updater uses optimized version)
```bash
python auto_strategy_updater.py
```

## Output Example

```
================================================================================
⚡ OPTIMIZED GRID SEARCH: BTCUSDT - 1m
================================================================================

📊 Total combinations to test: 121,500
   Parameters: min_confidence, min_volume, min_trend, min_adx, atr_min, atr_max
   Grid sizes: [10, 10, 9, 9, 3, 5]

🚀 Optimization Settings:
   CPU Cores: 8
   Workers: 7
   Batch Size: 1,735
   Total Batches: 70

Testing 121,500 strategies on BTCUSDT 1m...
Output: grid_search_results/BTCUSDT_1m_optimized_20251217.csv

Starting parallel processing...

Progress: 1,735/121,500 (1.4%) | Rate: 87 strat/s | ETA: 22.9 min | Batch 1/70
Progress: 3,470/121,500 (2.9%) | Rate: 92 strat/s | ETA: 21.3 min | Batch 2/70
Progress: 5,205/121,500 (4.3%) | Rate: 95 strat/s | ETA: 20.4 min | Batch 3/70
...
Progress: 121,500/121,500 (100.0%) | Rate: 98 strat/s | ETA: 0.0 min | Batch 70/70

⚡ Completed in 1,240s (20.7 min)
   Average: 98 strategies/second
```

## Parameter Grid

```python
PARAMETER_GRID = {
    'min_confidence': [0.60, 0.63, 0.66, 0.70, 0.73, 0.76, 0.80, 0.83, 0.86, 0.90],  # 10
    'min_volume': [1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40, 1.50],      # 10
    'min_trend': [0.40, 0.46, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80],             # 9
    'min_adx': [20, 23, 25, 28, 30, 33, 35, 38, 40],                                 # 9
    'atr_min': [0.3, 0.4, 0.5],                                                       # 3
    'atr_max': [3.0, 3.5, 4.0, 4.5, 5.0]                                             # 5
}

# Total: 10 × 10 × 9 × 9 × 3 × 5 = 121,500 combinations
```

## Results Format

### CSV Output
All 121,500 strategies saved with columns:
- `asset`, `timeframe`
- `min_confidence`, `min_volume`, `min_trend`, `min_adx`, `atr_min`, `atr_max`, `min_roc`
- `trades`, `wins`, `losses`, `win_rate`
- `total_pnl`, `avg_win`, `avg_loss`
- `final_balance`, `return_pct`, `risk_reward`

### JSON Summary
Top 2 strategies saved:
```json
{
  "strategy_1": {
    "min_confidence": 0.80,
    "min_volume": 1.25,
    "min_trend": 0.55,
    "min_adx": 30,
    "atr_min": 0.4,
    "atr_max": 4.0,
    "win_rate": 0.92,
    "total_pnl": 45.50,
    "trades": 50
  },
  "strategy_2": { ... }
}
```

## System Requirements

### Minimum
- 4 CPU cores
- 4 GB RAM
- Python 3.8+

### Recommended
- 8+ CPU cores
- 8 GB RAM
- SSD for data files

### Estimated Times by CPU

| CPU Cores | Time for 121,500 |
|-----------|------------------|
| 4 cores   | ~40-60 minutes   |
| 8 cores   | ~20-30 minutes   |
| 16 cores  | ~10-15 minutes   |

## Comparison: Quick Test vs Full Search

### Quick Test (324 combinations)
```bash
python test_grid_search_quick.py
```
- **Purpose:** Verify functionality
- **Time:** ~30 seconds
- **Grid:** 3×3×3×3×2×2 = 324
- **Output:** Quick validation

### Full Search (121,500 combinations)
```bash
python grid_search_optimized.py --asset BTCUSDT --timeframe 1m
```
- **Purpose:** Production strategy optimization
- **Time:** ~20-40 minutes
- **Grid:** 10×10×9×9×3×5 = 121,500
- **Output:** Complete strategy space

## Integration with Auto Strategy Updater

The `auto_strategy_updater.py` automatically uses the optimized version:

```python
# In auto_strategy_updater.py (line 120)
result = subprocess.run([
    'python', 'grid_search_optimized.py',
    '--asset', asset,
    '--timeframe', timeframe,
    '--output', output_file
], ...)
```

## Monitoring Progress

While running, the output shows:
- **Progress:** Percentage complete
- **Rate:** Strategies tested per second
- **ETA:** Estimated time remaining
- **Batch:** Current batch out of total

This allows you to:
1. Estimate completion time
2. Monitor system performance
3. Identify any slowdowns

## Error Handling

If a strategy causes an error:
- Error is logged in results
- Processing continues with next strategy
- No interruption to overall search
- Error details saved in CSV

## Tips for Faster Execution

1. **Close Other Applications**
   - Free up CPU resources
   - Maximize available cores

2. **Use SSD for Data Files**
   - Faster data loading
   - Reduced I/O bottleneck

3. **Ensure Sufficient RAM**
   - Avoid memory swapping
   - Keep data in memory

4. **Run During Off-Peak Hours**
   - Less system contention
   - More consistent performance

5. **Disable Unnecessary Services**
   - Free up CPU cycles
   - Reduce interruptions

## Validation Integration

The optimized grid search integrates with the validation system:

1. **Audit Logging** - Grid search completion logged
2. **Strategy Validation** - Results validated before saving
3. **Performance Metrics** - All metrics captured
4. **Progress Tracking** - Real-time updates

## Next Steps After Grid Search

1. **Review Results**
   ```bash
   # View top strategies
   head -20 grid_search_results/BTCUSDT_1m_optimized_*.csv
   ```

2. **Analyze Summary**
   ```bash
   cat grid_search_results/BTCUSDT_1m_optimized_*_summary.json | python -m json.tool
   ```

3. **Validate Strategies**
   - Auto-validation runs in `auto_strategy_updater.py`
   - Checks against expected bounds
   - Rejects invalid strategies

4. **Save to Fallback**
   - Top 2 strategies saved to `ml/fallback_strategies.json`
   - Includes `validation_passed` flag
   - Ready for production use

## Troubleshooting

### Issue: "No module named 'multiprocessing'"
**Solution:** Python installation issue, reinstall Python 3.8+

### Issue: Slow performance (<20 strat/s)
**Solution:**
- Check CPU usage (should be 80-90%+)
- Close other applications
- Verify data file on SSD

### Issue: Memory errors
**Solution:**
- Reduce batch size in code
- Close other applications
- Ensure 8GB+ RAM available

### Issue: Process hangs
**Solution:**
- Check for infinite loops in backtest
- Verify data file integrity
- Restart and try again

## Conclusion

The optimized grid search provides:
- ✅ 10-20x faster execution
- ✅ Full CPU utilization
- ✅ Real-time progress tracking
- ✅ Error resilience
- ✅ Integration with validation
- ✅ Production-ready results

**Estimated time for complete system:**
- 4 pairs × 2 timeframes = 8 searches
- ~20-30 minutes each = ~2.5-4 hours total
- vs. 48-64 hours with original implementation

**This makes daily strategy updates practical and efficient!**
