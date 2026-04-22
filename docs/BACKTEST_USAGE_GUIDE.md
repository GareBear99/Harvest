# HARVEST Backtest Usage Guide

## Quick Start

### Basic Usage
```bash
# Default: $10 starting balance per asset ($20 total)
python backtest_90_complete.py

# Skip pre-flight data checks (faster, but data may be stale)
python backtest_90_complete.py --skip-check
```

---

## Custom Starting Balance

### Set Any Starting Amount
```bash
# Test with $50 starting balance per asset ($100 total)
python backtest_90_complete.py --balance 50

# Test with $100 starting balance per asset ($200 total)
python backtest_90_complete.py --balance 100

# Test with $500 starting balance per asset ($1000 total)
python backtest_90_complete.py --balance 500
```

**Important**: The `--balance` parameter specifies **per-asset** balance. Total starting capital is `balance × 2` (ETH + BTC).

---

## Balance-Aware Strategy Activation

### What Happens With `--balance`
When you specify `--balance`, the system activates the **Balance-Aware Strategy** which:
- Filters timeframes based on balance tier
- Activates assets progressively
- Shows tier summary before starting
- Validates trading requirements

### Balance Tiers
| Balance | Tier | Timeframes | Assets | Total Capital |
|---------|------|------------|--------|---------------|
| $10 | 1 | 1m only | ETH only | $20 |
| $20 | 2 | 1m, 5m | ETH only | $40 |
| $30 | 3 | 1m, 5m, 15m | ETH only | $60 |
| $50 | 4 | 1m, 5m, 15m, 1h | ETH only | $100 |
| $75 | 5 | 1m, 5m, 15m, 1h | ETH, BTC | $150 |
| $100 | 6 | All 5 TFs | ETH, BTC | $200 |

---

## Position Tier System (≥$100)

### Founder Fee Position Tiers
When starting with $100+, the **position tier system** activates:

```bash
# Test position tier progression from $100
python backtest_90_complete.py --balance 100
```

**Position Capacity**:
- **$100-109**: 10 slots (1 per TF per asset)
- **$110-209**: 20 slots (2 per TF per asset)
- **$210+**: 30 slots (3 per TF per asset - MAXED)

**Tier Changes**:
- ✅ **Upgrades**: When balance crosses $110, $210
- ⚠️ **Downgrades**: When balance drops below thresholds
- 🛑 **Depletion**: Trading halts at $0

---

## Deterministic Testing

### Use Seeds for Reproducibility
```bash
# Run with specific seed for deterministic results
python backtest_90_complete.py --seed 42

# Same seed always produces identical results
python backtest_90_complete.py --balance 100 --seed 42
```

**Why Use Seeds?**
- Compare different balance starting points
- Reproduce exact trade sequences
- Validate strategy modifications
- Debug specific scenarios

---

## Complete Examples

### Example 1: Test $10 Tier (Minimal)
```bash
python backtest_90_complete.py --balance 10 --seed 123
```
**Result**: 1m timeframe only, ETH only, $20 total starting capital

---

### Example 2: Test $50 Tier (Medium)
```bash
python backtest_90_complete.py --balance 50 --seed 456
```
**Result**: 4 timeframes (1m, 5m, 15m, 1h), ETH only, $100 total starting capital

---

### Example 3: Test $100 Full System
```bash
python backtest_90_complete.py --balance 100 --seed 789
```
**Result**: 
- All 5 timeframes active
- Both ETH and BTC trading
- Position tier system active (10→20→30 slots)
- Balance tracking with upgrades/downgrades
- $200 total starting capital

---

### Example 4: Test High Balance ($500)
```bash
python backtest_90_complete.py --balance 500 --seed 999
```
**Result**:
- All systems active from start
- Tier 3 position capacity (30 slots)
- $1000 total starting capital
- Track performance at scale

---

### Example 5: Quick Test (Skip Checks)
```bash
python backtest_90_complete.py --balance 100 --seed 42 --skip-check
```
**Result**: Faster start, skips data freshness validation

---

## CLI Parameters

### All Available Options
```
--balance BALANCE         Starting balance per asset (default: 10)
--seed SEED              Deterministic seed for reproducibility
--skip-check             Skip pre-flight validation (faster)
--non-interactive        Auto-update stale data without prompting
--data-file FILE         Custom data file (default: eth_90days.json)
--test-seeds-file FILE   Batch test multiple seeds from JSON
```

---

## Output Interpretation

### Standard Output
```
MULTI-TIMEFRAME DAILY PROFIT SYSTEM
Backtest Seed: 42
Balance-Aware Mode: Enabled ($200.00 total)
```

### Position Tier Results
```
🎯 Position Tier System (BACKTEST):
Final Tier: 2
Final Position Limit: 2 per TF per asset
Final Total Slots: 20 positions
Max Concurrent Positions Used: 8

📈 Balance Milestones:
Peak Balance: $135.50
Lowest Balance: $92.30
Times Below $100: 2
```

### Combined Portfolio Results
```
COMBINED PORTFOLIO RESULTS
Starting Capital: $200.00
ETH Final: $115.20
BTC Final: $108.40
Total Final: $223.60
Combined Return: +11.80%
Total Trades: 47
Combined Win Rate: 68.1%
```

---

## Testing Strategies

### 1. Tier Progression Test
Test how system behaves as it grows through tiers:
```bash
# Start at baseline
python backtest_90_complete.py --balance 100 --seed 42

# Start already upgraded
python backtest_90_complete.py --balance 200 --seed 42
```

---

### 2. Risk Management Test
Test drawdown handling and tier downgrades:
```bash
# Start high, see if system protects on losses
python backtest_90_complete.py --balance 150 --seed 123
```

---

### 3. Seed Comparison
Compare performance across different strategy variations:
```bash
python backtest_90_complete.py --balance 100 --seed 100
python backtest_90_complete.py --balance 100 --seed 200
python backtest_90_complete.py --balance 100 --seed 300
```

---

### 4. Balance Depletion Test
Start low to test recovery mechanics:
```bash
# Test near-depletion scenario
python backtest_90_complete.py --balance 15 --seed 789
```

---

## Interpreting Results

### Key Metrics to Watch

**Balance Journey**:
- Peak: Highest balance reached
- Lowest: Worst drawdown point
- Final: Ending balance

**Tier Changes**:
- Upgrades: Successful growth milestones
- Downgrades: Loss protection activations

**Performance**:
- Win Rate: Target is 60-72%
- Trades/Day: Frequency of opportunities
- Profit/Day: Daily earnings rate

---

## Common Use Cases

### Use Case 1: Validate Live Trading Readiness
```bash
# Test with your actual starting capital
python backtest_90_complete.py --balance 100 --seed 42
```

---

### Use Case 2: Test Different Starting Points
```bash
# Compare performance at different scales
python backtest_90_complete.py --balance 50 --seed 1
python backtest_90_complete.py --balance 100 --seed 1
python backtest_90_complete.py --balance 200 --seed 1
```

---

### Use Case 3: Stress Test System
```bash
# Start with minimal balance to test limits
python backtest_90_complete.py --balance 10 --seed 999
```

---

### Use Case 4: Verify Position Capacity
```bash
# Test full 30-slot capacity
python backtest_90_complete.py --balance 250 --seed 42
```

---

## Tips & Best Practices

### ✅ Do's
- **Use seeds** for reproducible results
- **Test multiple balances** to understand scaling
- **Run full 90-day** backtests for statistical significance
- **Compare with/without** balance-aware mode
- **Track tier changes** to validate position system

### ❌ Don'ts
- **Don't skip checks** unless testing (data may be stale)
- **Don't test below $10** (insufficient for position sizing)
- **Don't compare different seeds** directly (different strategies)
- **Don't ignore balance milestones** (shows risk exposure)

---

## Troubleshooting

### Issue: "ETH not active at this balance"
**Solution**: Balance too low for balance-aware mode. Use at least $10.

### Issue: "BTC not active at this balance"
**Solution**: BTC requires $75+ balance. ETH-only below that.

### Issue: No trades executed
**Possible Causes**:
- Market conditions (no opportunities in test period)
- Balance too low for position sizing
- High-confidence filter rejecting all setups

### Issue: Balance depleted to $0
**Explanation**: Normal in backtest - shows loss handling works. Check:
- Times depleted counter
- Drawdown from peak
- Recovery if balance grows again

---

## Advanced Usage

### Batch Seed Testing
Test multiple seeds from a JSON file:
```bash
python backtest_90_complete.py --test-seeds-file seeds.json
```

### Custom Data File
Use different data periods:
```bash
python backtest_90_complete.py --balance 100 --data-file data/eth_21days.json
```

---

## Summary

**Most Common Command**:
```bash
python backtest_90_complete.py --balance 100 --seed 42
```

This tests the complete system with:
- ✅ Full balance-aware mode
- ✅ Position tier system (10→20→30)
- ✅ Both ETH and BTC trading
- ✅ All 5 timeframes active
- ✅ Deterministic results (seed 42)
- ✅ Balance tracking & tier changes
- ✅ $200 total starting capital

**Perfect for validating live trading readiness!**
