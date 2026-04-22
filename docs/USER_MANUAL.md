# Trading System User Manual
**Version 2.0**  
**Last Updated: December 17, 2024**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Overview](#system-overview)
3. [Core Concepts](#core-concepts)
4. [Components](#components)
5. [Daily Operations](#daily-operations)
6. [Command Reference](#command-reference)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Features](#advanced-features)
9. [Future Enhancements](#future-enhancements)
10. [FAQ](#faq)

---

## Quick Start

### Prerequisites
- Python 3.8 or higher
- Internet connection for data downloads
- 90 days of historical cryptocurrency data (auto-downloaded)

### First Run

```bash
# 1. Validate system and download fresh data
python pre_trading_check.py

# 2. Run backtest to verify system
python backtest_90_complete.py

# 3. Check data freshness anytime
python auto_strategy_updater.py --check
```

That's it! The system will guide you through any needed setup.

---

## System Overview

### What Is This System?

This is an **automated cryptocurrency trading system** designed to:
- **Make money** by predicting when crypto prices will go down (shorting)
- **Trade safely** with strict risk management and profit locking
- **Trade multiple timeframes** (15-minute, 1-hour, 4-hour) for 3-5+ trades per day
- **Learn and adapt** from each trade to improve over time

### How Does It Make Money?

The system **shorts cryptocurrency** (bets that the price will go down). When the price drops to our **take-profit target**, we make money. If the price goes up instead, we exit at our **stop-loss** to limit losses.

**Example Trade:**
- ETH price: $4,000
- We predict it will drop to $3,900 (2.5% down)
- We short at $4,000 with take-profit at $3,900
- Price drops → We capture $100 profit per unit

### Why Is It Better Than Manual Trading?

**Human traders struggle with:**
- Emotions (fear, greed, FOMO)
- Missing opportunities (sleeping, working)
- Inconsistent decision-making
- Limited analysis capacity

**This system:**
- ✅ **Never sleeps** – monitors markets 24/7
- ✅ **No emotions** – follows rules strictly
- ✅ **Fast analysis** – processes 20+ indicators instantly
- ✅ **Learns from mistakes** – adjusts strategies based on results
- ✅ **Strict risk management** – never risks more than configured limits

### Target Performance

**Goal:** 90%+ win rate (9 out of 10 trades profitable)

**How we achieve this:**
1. **Very high confidence threshold** – only trade when signals are extremely strong
2. **Multiple confirmation signals** – trend, momentum, volatility all must align
3. **Adaptive strategies** – system learns which conditions work best
4. **Strict filtering** – rejects 95%+ of opportunities, only takes the best

---

## Core Concepts

### Trading Pairs

Currently trading **2 pairs**:
- **ETHUSDT** – Ethereum vs. US Dollar Tether
- **BTCUSDT** – Bitcoin vs. US Dollar Tether

More pairs can be added in `trading_pairs_config.py`.

### Timeframes

The system trades on **3 timeframes simultaneously**:

#### 15-Minute Timeframe
- **Speed:** Fast trades (3-12 hours typical)
- **Frequency:** Most trades happen here
- **Risk:** Lower position size (faster = riskier)
- **Best for:** Quick scalping opportunities

#### 1-Hour Timeframe  
- **Speed:** Medium trades (12-48 hours typical)
- **Frequency:** Moderate
- **Risk:** Baseline position size
- **Best for:** Balanced risk/reward

#### 4-Hour Timeframe
- **Speed:** Slower trades (1-7 days typical)
- **Frequency:** Less frequent but higher confidence
- **Risk:** Higher position size (slower = more conviction)
- **Best for:** Strong trend following

### Strategies

The system uses a **3-tier strategy hierarchy**:

#### 1. BASE_STRATEGY (Always Available)
- **What:** Carefully optimized baseline parameters
- **When:** Used when no better strategies exist
- **Confidence:** Requires 66-70% confidence minimum
- **Purpose:** Guaranteed safe fallback

#### 2. Fallback Strategies (High-Confidence Backups)
- **What:** 2 best strategies found via grid search on fresh data
- **When:** Used when proven strategies underperform
- **Confidence:** Tested on 90 days of recent data
- **Purpose:** Data-driven alternatives to BASE

#### 3. Proven Strategies (Adaptive Learning)
- **What:** Strategies that have proven successful in live trading
- **When:** Used when they maintain 90%+ win rate
- **Confidence:** Real-world validated
- **Purpose:** Continuous improvement

### Data Freshness

**Critical Rule:** Never trade on stale data!

- **Fresh:** Data less than 30 days old ✅
- **Stale:** Data 30+ days old ❌

**Why it matters:**
- Market conditions change constantly
- Old data = outdated patterns
- Stale strategies = higher risk

**Automatic handling:**
- System checks data age before every trading session
- Prompts you to update if stale
- Auto-downloads fresh data for all active pairs
- Re-runs grid search to find new best strategies

---

## Components

### 1. Pre-Trading Check (`pre_trading_check.py`)

**Purpose:** Validates system is ready before any trading

**What it checks:**
- ✅ Data freshness (<30 days for all pairs)
- ✅ Fallback strategies exist
- ✅ BASE_STRATEGY loaded correctly
- ✅ All dependencies working

**When to use:**
- Before running backtests
- Before starting live trading
- After system updates
- If you suspect data issues

**Commands:**
```bash
# Full check with interactive updates
python pre_trading_check.py

# Check only (no updates)
python pre_trading_check.py --check-only

# Auto-update without prompts
python pre_trading_check.py --non-interactive

# Force update everything
python pre_trading_check.py --force
```

### 2. Auto Strategy Updater (`auto_strategy_updater.py`)

**Purpose:** Maintains data freshness and fallback strategies

**What it does:**
1. Checks each active pair's data age
2. Downloads fresh 90-day data if stale
3. Runs grid search (tests 121,500 combinations!)
4. Finds 2 best strategies per timeframe
5. Saves as fallback strategies

**Commands:**
```bash
# Check data freshness only
python auto_strategy_updater.py --check

# Force update all data
python auto_strategy_updater.py --force

# Normal update check (auto-download if stale)
python auto_strategy_updater.py
```

**When to run:**
- Automatically run by `pre_trading_check.py`
- Can run manually if you want fresh strategies
- System prompts you when data is stale

### 3. Backtest System (`backtest_90_complete.py`)

**Purpose:** Test strategies on historical data

**What it does:**
- Simulates trading with 90 days of historical data
- Tests both ETH and BTC simultaneously
- Shows which strategies would have worked
- Reports win rate, profit, and statistics

**Commands:**
```bash
# Normal run with pre-flight check
python backtest_90_complete.py

# Skip validation (not recommended)
python backtest_90_complete.py --skip-check

# Auto-update stale data
python backtest_90_complete.py --non-interactive
```

**What you'll see:**
- Pre-flight validation results
- Strategy status (BASE, fallbacks, ML state)
- Trade-by-trade results
- Win rate, profit, and statistics
- Which strategies were used

### 4. Blockchain Verifier (`blockchain_verifier.py`)

**Purpose:** Ensures data integrity and accuracy

**What it checks:**
- ✅ Timestamps in correct order
- ✅ No gaps in minute-by-minute data
- ✅ OHLC relationships valid (Open/High/Low/Close)
- ✅ Prices reasonable (no sudden 10x jumps)
- ✅ Volume data present

**Auto-corrections:**
- Fixes timestamp gaps by filling missing candles
- Sorts out-of-order timestamps
- Corrects invalid OHLC relationships
- Alerts on severe anomalies

**Commands:**
```bash
# Audit and fix all data
python blockchain_verifier.py

# Check specific file
python audit_blockchain_data.py
```

### 5. Grid Search (`grid_search_all_strategies.py`)

**Purpose:** Find optimal strategy parameters

**How it works:**
1. Tests every combination of 6 parameters:
   - **min_confidence:** How sure we must be (0.60-0.95)
   - **min_volume:** Minimum trading volume (1.5-6.0)
   - **min_trend:** Trend strength required (0.40-0.60)
   - **min_adx:** ADX indicator threshold (20-35)
   - **atr_min/max:** Volatility range (0.005-0.045)

2. Runs backtest for each combination
3. Filters for strategies with 3+ trades
4. Ranks by combined (win_rate × profit)
5. Saves top results to CSV

**Total combinations tested:** 121,500

**Commands:**
```bash
# Run for specific asset and timeframe
python grid_search_all_strategies.py --asset ETH --timeframe 15m

# Custom output file
python grid_search_all_strategies.py --asset BTC --timeframe 4h --output results.csv
```

**Results location:** `grid_search_results/` directory

### 6. ML Configuration (`ml/ml_config.json`)

**Purpose:** Control which assets use adaptive learning

**Structure:**
```json
{
  "ETH": {
    "ml_enabled": false,
    "locked_strategy": "BASE_STRATEGY",
    "reason": "Using immutable base strategy"
  },
  "BTC": {
    "ml_enabled": false,
    "locked_strategy": "BASE_STRATEGY",
    "reason": "Using immutable base strategy"
  }
}
```

**When ML is DISABLED:**
- ✅ System uses BASE_STRATEGY exclusively
- ✅ No adaptive adjustments made
- ✅ Completely predictable behavior
- ✅ Maximum safety

**When ML is ENABLED:**
- ⚙️ System learns from each trade
- ⚙️ Adjusts thresholds based on performance
- ⚙️ Can discover better strategies over time
- ⚠️ More complex, requires monitoring

**Default:** ML **DISABLED** for maximum safety

---

## Daily Operations

### Morning Routine

```bash
# 1. Check system health
python pre_trading_check.py --check-only

# 2. If data is stale, update it
python pre_trading_check.py

# 3. Run backtest to verify strategies
python backtest_90_complete.py
```

### Monitoring Live Trading

When running live (future feature):
- Check win rate hourly (target: 90%+)
- Monitor locked profit accumulation
- Watch for stale data warnings
- Review strategy performance by timeframe

### Weekly Maintenance

```bash
# 1. Force update all data (weekly refresh)
python pre_trading_check.py --force

# 2. Run comprehensive backtest
python backtest_90_complete.py

# 3. Review strategy performance
# Check ml/fallback_strategies.json for best strategies
```

### When Things Go Wrong

**Data is stale:**
```bash
python auto_strategy_updater.py
```

**Backtest fails:**
```bash
# Re-validate system
python pre_trading_check.py --force
```

**Suspicious results:**
```bash
# Check data integrity
python blockchain_verifier.py
```

---

## Command Reference

### Pre-Trading Check

| Command | What It Does |
|---------|-------------|
| `python pre_trading_check.py` | Full validation with interactive prompts |
| `python pre_trading_check.py --check-only` | Check health only, no updates |
| `python pre_trading_check.py --non-interactive` | Auto-update without prompts |
| `python pre_trading_check.py --force` | Force update all data |

### Strategy Updater

| Command | What It Does |
|---------|-------------|
| `python auto_strategy_updater.py` | Check and update stale data |
| `python auto_strategy_updater.py --check` | Check freshness only |
| `python auto_strategy_updater.py --force` | Force update all |

### Backtest

| Command | What It Does |
|---------|-------------|
| `python backtest_90_complete.py` | Run backtest with validation |
| `python backtest_90_complete.py --skip-check` | Skip pre-flight check |
| `python backtest_90_complete.py --non-interactive` | Auto-update data |

### Data Management

| Command | What It Does |
|---------|-------------|
| `python download_90day_data.py` | Download fresh 90-day data |
| `python blockchain_verifier.py` | Verify and fix data integrity |
| `python audit_blockchain_data.py` | Audit specific data file |

### Grid Search

| Command | What It Does |
|---------|-------------|
| `python grid_search_all_strategies.py --asset ETH --timeframe 15m` | Find best strategies |
| `python run_complete_optimization.py` | Run full optimization pipeline |

---

## Troubleshooting

### Problem: "Data is stale"

**Solution:**
```bash
python auto_strategy_updater.py
```

**Why:** Market conditions change. Fresh data = better strategies.

### Problem: "No fallback strategies found"

**Solution:**
```bash
python pre_trading_check.py
```

**Why:** First time running or data was updated. System will generate fallbacks.

### Problem: Backtest shows 0 trades

**Reasons:**
1. **Confidence thresholds too high** – No opportunities meet criteria
2. **Data issues** – Missing or corrupted data
3. **Market conditions** – No valid shorting opportunities in timeframe

**Solutions:**
1. Check data with `python blockchain_verifier.py`
2. Review BASE_STRATEGY thresholds in `ml/base_strategy.py`
3. Run longer backtest period

### Problem: Win rate below 90%

**Not necessarily a problem!**
- System prioritizes safety over frequency
- 85-89% win rate is still excellent
- Check if losses are small and wins are larger

**If consistently below 85%:**
1. Update data: `python pre_trading_check.py --force`
2. Review strategy thresholds
3. Check for data integrity issues

### Problem: "Import Error" or "Module Not Found"

**Solution:**
```bash
# Make sure you're in the correct directory
cd /path/to/harvest

# Check Python version
python --version  # Should be 3.8+

# Install dependencies if needed
pip install -r requirements.txt
```

### Problem: Grid search takes forever

**Expected!**
- 121,500 combinations to test
- Can take 8-20 hours depending on system
- Runs automatically in background
- Check progress in `grid_search_results/` folder

**To speed up (advanced):**
- Reduce parameter ranges in `grid_search_all_strategies.py`
- Test fewer combinations (not recommended)

---

## Advanced Features

### Custom Strategy Creation

Want to create your own strategy? Edit `ml/base_strategy.py`:

```python
BASE_STRATEGY = {
    '15m': {
        'min_confidence': 0.70,  # Increase for fewer, safer trades
        'min_volume': 2.5,       # Increase to require more volume
        'min_trend': 0.55,       # Increase for stronger trends only
        'min_adx': 25,           # Increase for clearer trends
        'atr_min': 0.010,        # Adjust volatility range
        'atr_max': 0.030,
        'min_roc': -1.0          # Rate of change threshold
    },
    # ... 1h and 4h similar
}
```

**Test your changes:**
```bash
python backtest_90_complete.py --skip-check
```

### Adding New Trading Pairs

Edit `trading_pairs_config.py`:

```python
ACTIVE_PAIRS = [
    'ETHUSDT',
    'BTCUSDT',
    'SOLUSDT',  # Add new pair
]
```

Then:
```bash
python pre_trading_check.py --force
```

System will download data and generate strategies for new pair.

### Adjusting Risk

Edit position size multipliers in `backtest_90_complete.py`:

```python
TIMEFRAME_CONFIGS = {
    '15m': {
        'position_size_multiplier': 0.5,  # Decrease for less risk
        # ...
    },
    '1h': {
        'position_size_multiplier': 1.0,  # Baseline
        # ...
    },
    '4h': {
        'position_size_multiplier': 1.5,  # Decrease for less risk
        # ...
    }
}
```

### Enabling ML Adaptive Learning

⚠️ **Advanced users only!**

Edit `ml/ml_config.json`:

```json
{
  "ETH": {
    "ml_enabled": true,
    "reason": "Testing adaptive learning"
  }
}
```

**Risks:**
- System will adjust strategies automatically
- May deviate from BASE_STRATEGY
- Requires monitoring
- Can improve OR hurt performance

---

## Future Enhancements

### Tron Network Integration (Coming Soon)

**What:** Support for TRON (TRX) blockchain

**Why:**
- ⚡ **Ultra-fast** transactions (<3 seconds)
- 💰 **Near-zero fees** (~$0.01 per transaction)
- 🌐 **High throughput** (2,000 TPS)
- 📊 **Growing DeFi ecosystem**

**How it will integrate:**
1. Add TRX/USDT trading pair
2. TronWeb.js integration for on-chain data
3. Smart contract deployment for automated trading
4. Direct DEX integration (JustSwap, SunSwap)

**Timeline:** Q1-Q2 2025

### Additional Planned Features

**Real-Time Trading**
- Live execution on Hyperliquid (infrastructure exists)
- Paper trading mode for testing
- Telegram notifications

**More Trading Pairs**
- SOL/USDT (Solana)
- MATIC/USDT (Polygon)
- AVAX/USDT (Avalanche)

**Enhanced ML**
- Pattern recognition
- Sentiment analysis integration
- Market regime detection

**Better Reporting**
- Web dashboard
- Performance analytics
- Trade journal with screenshots

See `TRON_INTEGRATION.md` for detailed roadmap.

---

## FAQ

### Q: How much money do I need to start?

**A:** System is designed to work with as little as $10-50. Backtests use $10 starting capital per asset ($20 total). More capital = more profit potential, but start small to test.

### Q: Is this system profitable?

**A:** Backtests show positive returns with 85-95% win rates. **However**, past performance doesn't guarantee future results. Cryptocurrency is highly volatile and risky.

### Q: Can I run this on a Raspberry Pi?

**A:** Yes! System is lightweight. Just needs Python 3.8+ and ~500MB storage for data.

### Q: How often should I update data?

**A:** System automatically checks before each trading session. Manual update recommended weekly or if data is 25+ days old.

### Q: What's the difference between backtest and live trading?

**Backtest:** Tests strategies on historical data (safe, no real money)  
**Live Trading:** Executes real trades with real money (risky!)

Always backtest first!

### Q: Why am I only seeing short positions?

**A:** System is optimized for shorting (betting prices go down) because:
1. Crypto markets trend down during corrections
2. Shorting in ranging markets is profitable
3. Current strategy focuses on downward moves

Long positions (betting up) can be added in future versions.

### Q: How do I know if my strategies are good?

**Key metrics:**
- **Win Rate:** 85%+ is excellent, 90%+ is outstanding
- **Profit Factor:** Total wins ÷ total losses (>2.0 is good)
- **Trades per day:** 3-5 is target for reasonable frequency
- **Max drawdown:** Should be <30% of starting capital

### Q: Can I use this for other cryptocurrencies?

**A:** Yes! Add them to `ACTIVE_PAIRS` in `trading_pairs_config.py`. System will auto-generate strategies.

### Q: What exchanges does this work with?

**Currently:** Designed for any exchange with REST API (Binance data used for backtests)  
**Live trading:** Infrastructure exists for Hyperliquid  
**Future:** More exchanges coming

### Q: How do I update the system?

```bash
# Pull latest code
git pull origin main

# Re-run validation
python pre_trading_check.py --force
```

### Q: Is my data secure?

**A:** All data is stored locally on your machine. No data is sent to external servers except for:
- Downloading market data from exchanges (public data)
- Future blockchain verification (read-only queries)

---

## Support & Resources

### Getting Help

**System Issues:**
1. Check this manual's Troubleshooting section
2. Run `python pre_trading_check.py` to diagnose
3. Review error messages carefully

**Strategy Questions:**
- See MATHEMATICS.md for calculation explanations
- Review ml/base_strategy.py for parameter meanings
- Check backtest output for performance metrics

### Important Files

| File/Directory | Purpose |
|---------------|---------|
| `USER_MANUAL.md` | This document |
| `MATHEMATICS.md` | Mathematical explanations |
| `TRON_INTEGRATION.md` | Future Tron plans |
| `ml/base_strategy.py` | Core strategy parameters |
| `ml/fallback_strategies.json` | Auto-generated fallback strategies |
| `ml/ml_config.json` | ML enable/disable controls |
| `data/` | 90-day historical data |
| `grid_search_results/` | Strategy optimization results |

### Understanding Output

**Backtest Output:**
- ✅ Green = Profitable trade (take-profit hit)
- ❌ Red = Loss (stop-loss hit) 
- ⏱️ Yellow = Time-exit (hit time limit)
- ⛔ Rejected = Failed confidence filters

**Confidence Scores:**
- 0.90-1.00 = Extremely high confidence
- 0.80-0.90 = High confidence  
- 0.70-0.80 = Good confidence
- <0.70 = Rejected (too risky)

---

## Conclusion

This system is designed to be:
- ✅ **Safe** – Multiple layers of risk management
- ✅ **Reliable** – Auto-checks data and strategies
- ✅ **Transparent** – You control everything
- ✅ **Educational** – Learn as you use it

**Remember:**
1. Always run pre-flight checks before trading
2. Never trade on stale data (>30 days)
3. Start with backtests, not live money
4. Monitor performance regularly
5. Update strategies weekly

**Most Important:**
Cryptocurrency trading is risky. Only trade with money you can afford to lose. This system is a tool, not a guarantee.

---

*For mathematical foundations and calculations, see MATHEMATICS.md*  
*For future Tron network plans, see TRON_INTEGRATION.md*  
*Last updated: December 17, 2024*
