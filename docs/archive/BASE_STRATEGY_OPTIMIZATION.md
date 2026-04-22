# BASE_STRATEGY Optimization Guide

## Overview

Now that ML/strategies are disabled, you can systematically refine BASE_STRATEGY through backtesting to find optimal parameter values.

## Current Status

✅ **ML Disabled**: All assets using BASE_STRATEGY only  
✅ **Optimization Tool**: `optimize_base_strategy.py` created  
✅ **Baseline Established**: Current performance documented  

### Current BASE_STRATEGY Performance

**Combined (ETH + BTC)**:
- Total Trades: 13
- Win Rate: 38.5%
- Total PnL: $-0.60
- Final Balance: $19.40 (from $20.00 start)

**By Asset**:
- ETH: 6 trades, 50.0% WR, $9.78 balance
- BTC: 7 trades, 28.6% WR, $9.63 balance

**By Timeframe**:
- 15m: Best performer (66.7% WR combined)
- 1h: Needs improvement (losing on both assets)
- 4h: Minimal trades (1 trade)

## Optimization Tool Usage

### Quick Commands

```bash
# 1. Quick test current strategy
python optimize_base_strategy.py --quick-test

# 2. Optimize single parameter for one timeframe
python optimize_base_strategy.py -t 15m -p min_confidence

# 3. Full scan for specific timeframe
python optimize_base_strategy.py --full-scan -t 15m

# 4. Full scan for all timeframes (takes ~5-10 minutes)
python optimize_base_strategy.py --full-scan
```

### Recommended Workflow

#### Step 1: Quick Test Baseline
```bash
python optimize_base_strategy.py --quick-test
```
This shows your starting point.

#### Step 2: Optimize Most Critical Timeframe First
Since 1h is performing worst, start there:

```bash
# Test each parameter individually
python optimize_base_strategy.py -t 1h -p min_confidence
python optimize_base_strategy.py -t 1h -p min_volume
python optimize_base_strategy.py -t 1h -p min_trend
python optimize_base_strategy.py -t 1h -p min_adx
```

#### Step 3: Full Scan for Best Results
```bash
python optimize_base_strategy.py --full-scan -t 1h
```

This tests all parameter combinations and shows:
- Best value for each parameter
- Complete optimized strategy
- Expected performance improvement

#### Step 4: Update BASE_STRATEGY
Once you find better values, manually update `ml/base_strategy.py`

#### Step 5: Verify Improvement
```bash
python optimize_base_strategy.py --quick-test
```

## Parameters to Optimize

### min_confidence (0.60 - 0.80)
**Current**: 15m=0.70, 1h=0.66, 4h=0.63

Higher = Fewer but higher quality signals  
Lower = More signals but potentially lower quality

**Test range**: 0.60, 0.63, 0.66, 0.70, 0.73, 0.76, 0.80

### min_volume (1.00 - 1.30)
**Current**: 15m=1.15, 1h=1.10, 4h=1.05

Volume multiplier vs average  
Higher = Requires stronger volume confirmation

**Test range**: 1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30

### min_trend (0.40 - 0.65)
**Current**: 15m=0.55, 1h=0.50, 4h=0.46

Trend consistency requirement  
Higher = Stronger trend needed

**Test range**: 0.40, 0.46, 0.50, 0.55, 0.60, 0.65

### min_adx (20 - 33)
**Current**: All timeframes = 25

ADX trend strength indicator  
Higher = Requires stronger trends

**Test range**: 20, 23, 25, 28, 30, 33

### atr_min / atr_max (ATR Range)
**Current**: All timeframes = 0.4 - 3.5

Volatility filter (ATR %)  
Narrower range = More selective

**Test ranges**:
- atr_min: 0.3, 0.4, 0.5
- atr_max: 3.0, 3.5, 4.0, 4.5

## Optimization Strategy

### Conservative Approach (Recommended)
1. Optimize one parameter at a time
2. Test changes on quick-test
3. Only update if significant improvement (>5% WR or >$0.50 PnL)
4. Keep changes minimal

### Aggressive Approach
1. Run full-scan on all timeframes
2. Implement all "best" values
3. Test complete system
4. Iterate if needed

### Focus Areas

Based on current results:

**Priority 1: Fix 1h Timeframe**
- Currently: 0% WR on BTC, 33.3% on ETH
- Losing $-1.06 combined
- Most trades happening here (6/13)

**Priority 2: Optimize 15m**
- Already performing well (66.7% WR)
- Small tweaks could improve further

**Priority 3: Increase 4h Activity**
- Only 1 trade total
- Filters may be too tight

## Example Optimization Session

```bash
# Start
$ python optimize_base_strategy.py --quick-test
Combined: 13 trades, 38.5% WR, $-0.60 PnL

# Optimize 1h min_confidence
$ python optimize_base_strategy.py -t 1h -p min_confidence

OPTIMIZING 1h - min_confidence
min_confidence=  0.60 → Trades:   8 | WR: 50.0% | PnL: $  -0.20
min_confidence=  0.63 → Trades:   7 | WR: 57.1% | PnL: $  +0.30
min_confidence=  0.66 → Trades:   6 | WR: 33.3% | PnL: $  -1.06 (current)
min_confidence=  0.70 → Trades:   5 | WR: 60.0% | PnL: $  +0.50
min_confidence=  0.73 → Trades:   4 | WR: 75.0% | PnL: $  +0.80 ✨

🏆 Best min_confidence for 1h: 0.73
   Trades: 4, WR: 75.0%, PnL: $+0.80

# Update ml/base_strategy.py
# Change 1h min_confidence from 0.66 to 0.73

# Verify
$ python optimize_base_strategy.py --quick-test
Combined: 11 trades, 54.5% WR, $+0.20 PnL ✅ Improved!
```

## Interpreting Results

### Good Signs
- ✅ Win rate increases
- ✅ PnL improves
- ✅ Reasonable trade count (not too few)
- ✅ Improvement on both ETH and BTC

### Warning Signs
- ⚠️ Very few trades (<5 total)
- ⚠️ Win rate improves but PnL decreases
- ⚠️ Works on ETH but breaks BTC (or vice versa)
- ⚠️ Overfitting to current data

### Trade-offs

**Higher Filters (stricter)**
- Pro: Higher win rate
- Pro: Better quality trades
- Con: Fewer opportunities
- Con: May miss good setups

**Lower Filters (looser)**
- Pro: More trades
- Pro: Catch more opportunities
- Con: Lower win rate
- Con: More false signals

**Sweet Spot**: 50-60% WR with steady volume of trades

## After Optimization

Once you've found better BASE_STRATEGY values:

### 1. Update BASE_STRATEGY
Edit `ml/base_strategy.py` with new values

### 2. Test Thoroughly
```bash
python optimize_base_strategy.py --quick-test
python tests/test_complete_system.py
```

### 3. Document Changes
Note what you changed and why

### 4. Re-enable ML (Optional)
```bash
python ml/configure_ml.py enable ETH
```

Now ML will build on top of your improved baseline!

## Tips & Best Practices

1. **One Change at a Time**
   - Don't change multiple parameters simultaneously
   - Test each change independently

2. **Focus on Problem Areas**
   - 1h timeframe needs most work
   - Optimize worst performers first

3. **Validate on Both Assets**
   - Changes should improve both ETH and BTC
   - Don't optimize for just one

4. **Consider Trade Count**
   - Too few trades = overfitting
   - 5-20 trades per timeframe is good range

5. **Document Everything**
   - Save optimization results
   - Track what you tried

6. **Test Different Market Conditions**
   - Current data is 21 days
   - Consider getting more data later

## Advanced: Custom Parameter Ranges

Edit `optimize_base_strategy.py` to test custom ranges:

```python
PARAM_RANGES = {
    'min_confidence': [0.60, 0.65, 0.70, 0.75, 0.80],  # Add your values
    'min_volume': [1.00, 1.10, 1.20, 1.30],
    # ... etc
}
```

## Troubleshooting

### "No trades" Result
- Filters too tight
- Try lowering thresholds

### Same Results for Different Values
- Parameter might not affect this timeframe
- Try different parameter

### Optimization Takes Too Long
- Use single parameter mode (-p)
- Optimize one timeframe at a time (-t)

## Summary

You now have:
- ✅ ML disabled (using BASE_STRATEGY only)
- ✅ Optimization tool ready
- ✅ Current baseline documented
- ✅ Clear optimization workflow

**Next Steps**:
1. Run quick-test to see current performance
2. Optimize 1h timeframe (worst performer)
3. Update BASE_STRATEGY with better values
4. Re-test to verify improvements
5. Optional: Re-enable ML to build on improved base

**Goal**: Improve from 38.5% WR to 50%+ WR before re-enabling ML
