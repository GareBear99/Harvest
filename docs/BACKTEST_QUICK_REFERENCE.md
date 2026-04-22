# HARVEST Backtest - Quick Reference Card

## 🚀 Most Used Commands

```bash
# Test with $100 starting balance (recommended)
python backtest_90_complete.py --balance 100 --seed 42

# Quick test (skip validation checks)
python backtest_90_complete.py --balance 100 --seed 42 --skip-check

# Test with different amounts
python backtest_90_complete.py --balance 50    # $50 per asset ($100 total)
python backtest_90_complete.py --balance 200   # $200 per asset ($400 total)
python backtest_90_complete.py --balance 500   # $500 per asset ($1000 total)
```

---

## 💰 Balance Parameter Cheat Sheet

| Command | Per Asset | Total | Active TFs | Assets | Position Slots |
|---------|-----------|-------|------------|--------|----------------|
| `--balance 10` | $10 | $20 | 1m | ETH | 10 |
| `--balance 20` | $20 | $40 | 1m, 5m | ETH | 10 |
| `--balance 50` | $50 | $100 | 4 TFs | ETH | 10 |
| `--balance 75` | $75 | $150 | 4 TFs | ETH, BTC | 10 |
| `--balance 100` | $100 | $200 | All 5 TFs | ETH, BTC | 10→20→30 |
| `--balance 200` | $200 | $400 | All 5 TFs | ETH, BTC | 20→30 |
| `--balance 500` | $500 | $1000 | All 5 TFs | ETH, BTC | 30 (maxed) |

---

## 🎯 Common Testing Scenarios

### Full System Test (Live Trading Simulation)
```bash
python backtest_90_complete.py --balance 100 --seed 42
```
**Result**: All systems active, position tiers, both assets, $200 total

---

### Minimal Test (Entry Level)
```bash
python backtest_90_complete.py --balance 10 --seed 42
```
**Result**: 1m only, ETH only, $20 total

---

### High Balance Test (Scaled Operation)
```bash
python backtest_90_complete.py --balance 500 --seed 42
```
**Result**: All systems, maxed capacity, $1000 total

---

### Quick No-Check Test (Development)
```bash
python backtest_90_complete.py --balance 100 --skip-check
```
**Result**: Faster start, skips data validation

---

## 📊 What You'll See

### Tier Upgrades (when profitable)
```
🎉 POSITION TIER UPGRADED: 1 → 2 positions per TF per asset
   Total Slots: 20 positions (5 TFs × 2 assets × 2)
   Balance: $115.50
```

### Tier Downgrades (on losses)
```
⚠️  POSITION TIER DOWNGRADED: 2 → 1 positions per TF per asset
   Balance: $95.00 (down from peak $120.00)
   Reason: Balance dropped below tier threshold
```

### Balance Depletion
```
⚠️  BALANCE DEPLETED: $0.00
   Trading PAUSED - waiting for funds
```

### Final Results
```
🎯 Position Tier System (BACKTEST):
Final Tier: 2
Max Concurrent Positions Used: 8

📈 Balance Milestones:
Peak Balance: $135.50
Lowest Balance: $92.30
Times Below $100: 2

🎯 Tier Changes:
  Upgrades: 1
    • 1 → 2 at $115.00
  Downgrades: 1
    • 2 → 1 at $95.00 (from peak $135.50)
```

---

## ⚙️ CLI Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--balance N` | Starting balance per asset | `--balance 100` |
| `--seed N` | Deterministic seed | `--seed 42` |
| `--skip-check` | Skip data validation | `--skip-check` |
| `--non-interactive` | Auto-update data | `--non-interactive` |
| `--data-file FILE` | Custom data file | `--data-file data/eth_21days.json` |

---

## 🎲 Seed Usage

**Same seed = same results**:
```bash
# These will produce identical trades
python backtest_90_complete.py --balance 100 --seed 42
python backtest_90_complete.py --balance 100 --seed 42  # Same!
```

**Different seeds = different strategies**:
```bash
# Each seed tests a different strategy variation
python backtest_90_complete.py --balance 100 --seed 1
python backtest_90_complete.py --balance 100 --seed 2
python backtest_90_complete.py --balance 100 --seed 3
```

---

## 🔍 Testing Strategies

### Compare Balance Levels (same seed)
```bash
python backtest_90_complete.py --balance 50 --seed 42
python backtest_90_complete.py --balance 100 --seed 42
python backtest_90_complete.py --balance 200 --seed 42
```

### Compare Strategies (different seeds)
```bash
python backtest_90_complete.py --balance 100 --seed 1
python backtest_90_complete.py --balance 100 --seed 2
python backtest_90_complete.py --balance 100 --seed 3
```

---

## 🎓 Quick Tips

✅ **Always use `--balance 100`** for full system validation  
✅ **Use `--seed 42`** for reproducible results  
✅ **Compare multiple seeds** to find best strategy  
✅ **Track tier changes** in output  
✅ **Watch balance milestones** for risk assessment  

❌ **Don't test below $10** (insufficient capital)  
❌ **Don't skip checks** in production testing  
❌ **Don't ignore downgrades** (risk signals)  

---

## 📁 Output Files

After running, check these for details:
- **Terminal output**: Complete results and stats
- **data/founder_fee_config.json**: Tier state (if live mode)
- **ml/strategy_pool.json**: Active strategies

---

## 🚨 Common Issues

### "ETH not active at this balance"
→ Use at least `--balance 10`

### "No trades executed"
→ Normal - market conditions or high filter standards

### Balance depleted to $0
→ Expected behavior - shows loss handling works

---

## 💡 Recommended First Test

```bash
python backtest_90_complete.py --balance 100 --seed 42
```

This command:
- ✅ Tests complete system ($200 total)
- ✅ Shows position tier progression
- ✅ Tests both ETH and BTC
- ✅ Uses all 5 timeframes
- ✅ Produces reproducible results
- ✅ Validates live trading readiness

**Perfect starting point for validation!**
