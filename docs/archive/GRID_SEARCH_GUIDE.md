# Exhaustive Grid Search System

## Overview

The grid search system tests **EVERY possible combination** of strategy parameters to find the absolute best configurations. This maps the complete strategy space and shows you all possible outcomes.

## What It Does

Tests all combinations of:
- `min_confidence`: 10 values (0.60 to 0.90)
- `min_volume`: 10 values (1.00 to 1.50)
- `min_trend`: 9 values (0.40 to 0.80)
- `min_adx`: 9 values (20 to 40)
- `atr_min`: 3 values (0.3 to 0.5)
- `atr_max`: 5 values (3.0 to 5.0)

**Total**: 10 × 10 × 9 × 9 × 3 × 5 = **121,500 strategies per timeframe/asset**

## Quick Start

### Option 1: Test Single Timeframe (Fastest)

```bash
# Test ETH 15m (~15-30 minutes)
chmod +x grid_search_all_strategies.py
python grid_search_all_strategies.py -a ETH -t 15m

# This generates:
# - grid_search_ETH_15m_TIMESTAMP.csv (121,500 strategies)
# - grid_search_ETH_15m_TIMESTAMP_summary.json (top 3 configs)
```

### Option 2: Test Everything (Complete Analysis)

```bash
# Test all 6 combinations (~2-4 hours)
chmod +x run_complete_grid_search.sh
./run_complete_grid_search.sh

# This generates 6 CSV files with ~729,000 total strategies tested
```

## Understanding the Output

### CSV Columns

Each row is one tested strategy configuration:

| Column | Description |
|--------|-------------|
| `asset` | ETH or BTC |
| `timeframe` | 15m, 1h, or 4h |
| `trades` | Number of trades executed |
| `wins` | Number of winning trades |
| `losses` | Number of losing trades |
| `win_rate` | Win rate (0.0 to 1.0) |
| `total_pnl` | Total profit/loss |
| `avg_win` | Average profit per win |
| `avg_loss` | Average loss per loss |
| `final_balance` | Ending balance ($10 start) |
| `return_pct` | Return percentage |
| `risk_reward` | Risk/reward ratio |
| `min_confidence` | Confidence threshold used |
| `min_volume` | Volume threshold used |
| `min_trend` | Trend threshold used |
| `min_adx` | ADX threshold used |
| `atr_min` | Min ATR used |
| `atr_max` | Max ATR used |

### Terminal Output

During the run, you'll see:

```
🏆 TOP 10 BY WIN RATE:
 1. WR: 100.0% | Trades:   3 | PnL: $  +0.50 | Conf: 0.86 | Vol: 1.35 | Trend: 0.75 | ADX: 35
 2. WR:  83.3% | Trades:   6 | PnL: $  +0.80 | Conf: 0.80 | Vol: 1.25 | Trend: 0.65 | ADX: 30
 ...
```

```
💰 TOP 10 BY PROFIT:
 1. PnL: $  +1.20 | WR:  75.0% | Trades:   8 | Conf: 0.76 | Vol: 1.20 | Trend: 0.60 | ADX: 28
 ...
```

```
⚖️  TOP 10 BALANCED (WR × PnL):
 1. Score:   0.80 | WR:  80.0% | PnL: $  +1.00 | Trades:   5 | Conf: 0.83 | Vol: 1.30 | Trend: 0.70 | ADX: 33
 ...
```

## Analyzing Results

### Method 1: Excel/Numbers/Google Sheets (Recommended)

1. Open the CSV file in your spreadsheet app
2. Sort by `win_rate` descending
3. Filter `trades` >= 3 (need minimum sample size)
4. Look for strategies with 80%+ or 90%+ WR
5. Check `total_pnl` is positive
6. Note the parameter values

### Method 2: Command Line

```bash
# Find best win rate strategies
head -1 grid_search_ETH_15m_*.csv && \
  tail -n +2 grid_search_ETH_15m_*.csv | sort -t',' -k7 -rn | head -20

# Find most profitable
head -1 grid_search_ETH_15m_*.csv && \
  tail -n +2 grid_search_ETH_15m_*.csv | sort -t',' -k8 -rn | head -20

# Find strategies with 90%+ WR
awk -F',' '$7 >= 0.90 && $4 >= 3' grid_search_ETH_15m_*.csv
```

### Method 3: Python Analysis

```python
import pandas as pd

# Load results
df = pd.read_csv('grid_search_ETH_15m_20251217_000000.csv')

# Filter valid strategies (3+ trades)
valid = df[df['trades'] >= 3]

# Find 90%+ WR strategies
high_wr = valid[valid['win_rate'] >= 0.90]

print(f"Found {len(high_wr)} strategies with 90%+ WR:")
print(high_wr[['win_rate', 'trades', 'total_pnl', 'min_confidence', 'min_volume', 'min_trend', 'min_adx']])

# Best overall
best = valid.sort_values('win_rate', ascending=False).head(10)
print("\nTop 10 by WR:")
print(best)
```

## What to Look For

### Goal: 90% Win Rate

Filter for:
- `win_rate` >= 0.90 (90%+)
- `trades` >= 3 (minimum sample)
- `total_pnl` > 0 (profitable)

### Balanced Strategy

Look for:
- `win_rate` >= 0.70 (70%+)
- `trades` >= 5 (good sample)
- `total_pnl` >= $0.50 (solid profit)
- `risk_reward` >= 1.5 (good R:R)

### High Volume Strategy

Look for:
- `trades` >= 10 (many opportunities)
- `win_rate` >= 0.60 (60%+)
- `total_pnl` > 0 (net positive)

## Understanding Trade-offs

### Tight Filters (High Confidence/Volume/Trend/ADX)
**Pros:**
- Higher win rate
- Better quality trades
- Lower risk

**Cons:**
- Fewer trades
- May miss opportunities
- Small sample size risk

### Loose Filters (Low Thresholds)
**Pros:**
- More trades
- Better sample size
- More opportunities

**Cons:**
- Lower win rate
- More false signals
- Higher risk

## Example: Finding Your 90% WR Strategy

```bash
# 1. Run grid search for ETH 15m
python grid_search_all_strategies.py -a ETH -t 15m

# 2. Open CSV in Excel
# 3. Sort by 'win_rate' descending
# 4. Filter 'trades' >= 3
# 5. Find rows with win_rate >= 0.90

# Example result:
# win_rate: 1.00 (100%)
# trades: 3
# total_pnl: $0.60
# min_confidence: 0.86
# min_volume: 1.35
# min_trend: 0.75
# min_adx: 35

# 6. Update ml/base_strategy.py:
#    '15m': {
#        'min_confidence': 0.86,
#        'min_volume': 1.35,
#        'min_trend': 0.75,
#        'min_adx': 35,
#        'min_roc': -1.0,
#        'atr_min': 0.4,
#        'atr_max': 3.5
#    }

# 7. Test it:
python optimize_base_strategy.py --quick-test
```

## Performance Estimates

| Test | Combinations | Time (approx) |
|------|-------------|---------------|
| Single timeframe/asset | 121,500 | 15-30 min |
| Single asset (3 TFs) | 364,500 | 45-90 min |
| All (6 combinations) | 729,000 | 2-4 hours |

*Times vary based on CPU speed*

## Tips

1. **Start Small**: Test one timeframe first (ETH 15m)
2. **Check Progress**: Script shows progress every 100 strategies
3. **Run Overnight**: For complete search, run overnight
4. **Save Results**: CSV files are your complete strategy database
5. **Compare**: Run on both ETH and BTC to find robust strategies
6. **Validate**: Always test new configs with `--quick-test` before using

## Troubleshooting

### "Takes too long"
- Test single timeframe first
- Reduce parameter grid in script (fewer values)
- Use faster machine or run overnight

### "No 90%+ WR strategies found"
- Dataset too small (only 21 days)
- Try 80%+ WR strategies instead
- Get more historical data

### "Too many strategies with 0 trades"
- Normal! Tight filters = no trades
- Focus on strategies with 3+ trades
- Check filter ranges aren't too tight

## Next Steps

1. **Run ETH 15m first** (fastest, best performing timeframe)
2. **Find your 90% WR config** in the CSV
3. **Update BASE_STRATEGY** with those parameters
4. **Verify** with quick-test
5. **Repeat** for other timeframes/assets
6. **Enable ML** to build on your optimized base

## Summary

You now have a system that:
- ✅ Tests **ALL** possible strategy combinations
- ✅ Generates complete CSV database of results
- ✅ Shows top strategies by WR, PnL, and balance
- ✅ Lets you explore the entire strategy space
- ✅ Finds optimal parameters for 90%+ WR (if possible with your data)

**The CSV files are your complete strategy map - every possibility tested!**
