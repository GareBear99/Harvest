# Machine Learning Configuration Guide

## Overview

The trading system now supports **per-asset ML configuration**, treating each asset (ETH, BTC) as a completely separate bot. You can enable/disable ML features individually for each asset.

**Key Benefit**: Test and refine the base strategy on one asset while using adaptive ML on another.

---

## Quick Start

### Check Current Status
```bash
python ml/configure_ml.py status
```

### Disable ML for All Assets (Use Base Strategy Only)
```bash
python ml/configure_ml.py disable-all
```

### Enable ML for Specific Asset
```bash
# Enable ETH ML
python ml/configure_ml.py enable ETH

# Enable specific features
python ml/configure_ml.py feature ETH adaptive_thresholds on
python ml/configure_ml.py feature ETH strategy_switching on
```

---

## ML Modes

### BASE MODE (ML Disabled)
When ML is disabled for an asset:
- ✅ Uses fixed `BASE_STRATEGY` thresholds only
- ✅ No adaptive adjustments
- ✅ No strategy switching
- ✅ No learning from errors
- ✅ Predictable, consistent behavior
- ✅ Perfect for testing and refining base strategy

**Use this mode when:**
- Testing new data
- Establishing baseline performance
- Debugging strategy logic
- Want predictable results

### ML MODE (ML Enabled)
When ML is enabled for an asset:
- 🤖 Adaptive threshold adjustments
- 🤖 Strategy pool management (up to 3 strategies)
- 🤖 Automatic strategy switching
- 🤖 Intelligent error learning
- 🤖 Improves over time

**Use this mode when:**
- Base strategy is performing well
- Ready for adaptive learning
- Want automated optimization
- Have enough data to learn from

---

## Configuration Commands

### Status Commands
```bash
# Show all assets
python ml/configure_ml.py status

# Show specific asset
python ml/configure_ml.py status ETH
python ml/configure_ml.py status BTC
```

### Enable/Disable ML
```bash
# Enable ML for asset
python ml/configure_ml.py enable ETH
python ml/configure_ml.py enable BTC

# Disable ML for asset  
python ml/configure_ml.py disable ETH
python ml/configure_ml.py disable BTC

# Enable/disable all assets
python ml/configure_ml.py enable-all
python ml/configure_ml.py disable-all
```

### Feature Control
```bash
# Enable specific feature
python ml/configure_ml.py feature ETH adaptive_thresholds on
python ml/configure_ml.py feature ETH strategy_switching on
python ml/configure_ml.py feature ETH intelligent_learning on
python ml/configure_ml.py feature ETH strategy_pool on

# Disable specific feature
python ml/configure_ml.py feature ETH adaptive_thresholds off
python ml/configure_ml.py feature BTC strategy_switching off
```

### Timeframe Control
```bash
# Enable ML for specific timeframe
python ml/configure_ml.py timeframe ETH 15m on
python ml/configure_ml.py timeframe ETH 1h on
python ml/configure_ml.py timeframe BTC 4h on

# Disable ML for specific timeframe
python ml/configure_ml.py timeframe ETH 15m off
```

### Reset
```bash
# Reset all to defaults (ML disabled)
python ml/configure_ml.py reset

# Reset specific asset
python ml/configure_ml.py reset ETH
python ml/configure_ml.py reset BTC
```

---

## ML Features

### 1. adaptive_thresholds
**Adjusts filter thresholds based on performance**
- Monitors win rate vs 72% target
- Calculates severity (distance from target)
- Applies phase-based adjustments
- Tightens when too many trades
- Loosens when too few wins

### 2. strategy_switching
**Switches between proven strategies**
- Saves up to 3 proven strategies per timeframe
- Switches when WR < 58%
- Switches after 5 consecutive losses
- Rotates through available strategies
- Falls back to base if no proven strategies

### 3. intelligent_learning
**Learns from failed predictions**
- Categorizes 6 error types
- Identifies recurring issues
- Tracks worst-performing features
- Guides threshold adjustments
- Prevents repeated mistakes

### 4. strategy_pool
**Manages multiple strategies per timeframe**
- Saves strategies with 72%+ WR and 20+ trades
- Loads best strategy on startup
- Tracks performance of each strategy
- Persistent storage in ml/strategy_pool.json
- Per-timeframe management (15m, 1h, 4h)

---

## Configuration File

Settings are saved in `ml/ml_config.json`:

```json
{
  "assets": {
    "ETH": {
      "ml_enabled": false,
      "features": {
        "adaptive_thresholds": false,
        "strategy_switching": false,
        "intelligent_learning": false,
        "strategy_pool": false
      },
      "timeframes": {
        "15m": {"enabled": true, "use_ml": false},
        "1h": {"enabled": true, "use_ml": false},
        "4h": {"enabled": true, "use_ml": false}
      }
    },
    "BTC": {
      "ml_enabled": false,
      "features": { ... },
      "timeframes": { ... }
    }
  }
}
```

---

## Usage Examples

### Example 1: Test Base Strategy on Both Assets
```bash
# Disable ML for all assets
python ml/configure_ml.py disable-all

# Run backtest
python backtest_90_complete.py

# Both ETH and BTC use BASE_STRATEGY only
```

### Example 2: Enable ML for ETH Only
```bash
# Disable all first
python ml/configure_ml.py disable-all

# Enable ETH with full features
python ml/configure_ml.py enable ETH
python ml/configure_ml.py feature ETH adaptive_thresholds on
python ml/configure_ml.py feature ETH strategy_switching on
python ml/configure_ml.py feature ETH intelligent_learning on
python ml/configure_ml.py feature ETH strategy_pool on

# Run backtest
python backtest_90_complete.py

# ETH: ML active, BTC: BASE_STRATEGY only
```

### Example 3: Gradual ML Enablement
```bash
# Start with just adaptive thresholds
python ml/configure_ml.py enable ETH
python ml/configure_ml.py feature ETH adaptive_thresholds on

# After stable performance, add strategy pool
python ml/configure_ml.py feature ETH strategy_pool on

# Then add switching
python ml/configure_ml.py feature ETH strategy_switching on

# Finally add learning
python ml/configure_ml.py feature ETH intelligent_learning on
```

### Example 4: Per-Timeframe ML Control
```bash
# Enable ML for ETH
python ml/configure_ml.py enable ETH
python ml/configure_ml.py feature ETH adaptive_thresholds on

# But only use ML on 15m timeframe
python ml/configure_ml.py timeframe ETH 15m on
python ml/configure_ml.py timeframe ETH 1h off
python ml/configure_ml.py timeframe ETH 4h off

# 15m adapts, 1h/4h use BASE_STRATEGY
```

---

## Recommended Workflow

### Phase 1: Establish Baseline (No ML)
```bash
# Disable all ML
python ml/configure_ml.py disable-all

# Run backtest to establish baseline
python backtest_90_complete.py

# Note: baseline win rates, trade counts
# Goal: Understand base strategy performance
```

### Phase 2: Enable Adaptive Thresholds (ETH)
```bash
# Enable just adaptive thresholds for ETH
python ml/configure_ml.py enable ETH
python ml/configure_ml.py feature ETH adaptive_thresholds on

# Run backtest
python backtest_90_complete.py

# Monitor: Does adaptive adjustment improve performance?
```

### Phase 3: Add Strategy Pool (ETH)
```bash
# Add strategy pool
python ml/configure_ml.py feature ETH strategy_pool on

# Run multiple backtests
# System will save proven strategies (72%+ WR, 20+ trades)
```

### Phase 4: Enable Strategy Switching (ETH)
```bash
# Add switching
python ml/configure_ml.py feature ETH strategy_switching on

# System now switches at 58% WR or 5 consecutive losses
```

### Phase 5: Enable Full ML (ETH)
```bash
# Add intelligent learning
python ml/configure_ml.py feature ETH intelligent_learning on

# Full ML pipeline active for ETH
```

### Phase 6: Enable ML for BTC
```bash
# After ETH ML is stable, enable BTC
python ml/configure_ml.py enable BTC
python ml/configure_ml.py feature BTC adaptive_thresholds on
python ml/configure_ml.py feature BTC strategy_pool on
# ... etc
```

---

## Troubleshooting

### ML Not Working
Check if ML is enabled:
```bash
python ml/configure_ml.py status
```

Ensure features are enabled:
```bash
python ml/configure_ml.py status ETH
```

### Want to Start Fresh
Reset to defaults:
```bash
python ml/configure_ml.py reset
```

### Separate Asset Configurations
Each asset is completely independent:
- ETH can have ML enabled with all features
- BTC can use BASE_STRATEGY only
- Or vice versa
- Or both ML enabled with different features

---

## Integration with Backtest

The backtest system automatically respects ML configuration:

```python
from backtest_90_complete import MultiTimeframeBacktest

# Run backtest - automatically checks ML config
backtest = MultiTimeframeBacktest('data/eth_21days.json', 10.0, seed=42)
backtest.run()

# ML config is checked for:
# - Whether to record trades in strategy_manager
# - Whether to adjust thresholds
# - Whether to learn from errors
# - Whether to switch strategies
```

**Output will show:**
```
📋 ETH: ML DISABLED - Using BASE_STRATEGY only
# or
🤖 ETH: ML ENABLED - Adaptive learning active
```

---

## Configuration Best Practices

1. **Start with BASE MODE** for all assets
2. **Enable ML for one asset** at a time
3. **Enable features gradually** (not all at once)
4. **Monitor performance** after each change
5. **Use validation tests** to ensure determinism
6. **Keep BTC on BASE MODE** while testing ETH ML
7. **Document what works** in your notes

---

## Files

- `ml/ml_config.py` - Configuration system
- `ml/configure_ml.py` - CLI tool
- `ml/ml_config.json` - Saved configuration
- `backtest_90_complete.py` - Integrated backtest

---

## Summary

The ML configuration system gives you fine-grained control over adaptive features per asset:

✅ **Complete separation** - Each asset is independent  
✅ **Gradual enablement** - Add features one at a time  
✅ **Easy management** - Simple CLI commands  
✅ **Persistent config** - Saved between runs  
✅ **Per-feature control** - Enable only what you need  
✅ **Per-timeframe control** - ML on some TFs, base on others  

**Default state: ML DISABLED for all assets (BASE_STRATEGY only)**

This allows you to establish a solid baseline before enabling adaptive features!

---

**Last Updated**: 2024-12-16  
**Status**: ✅ COMPLETE - Ready for use
