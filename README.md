<!-- ARC-Ecosystem-Hero-Marker -->
# Harvest — Multi-Timeframe Crypto Trading System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-production--oriented-green.svg)]()
[![Built on ARC-Core](https://img.shields.io/badge/built%20on-ARC--Core-5B6CFF)](https://github.com/GareBear99/ARC-Core)

> Automated crypto trading research platform focused on short-biased
> multi-timeframe strategies (15m / 1h / 4h) over BTCUSDT and ETHUSDT. Features
> freshness-gated data (no trading on stale data), 90-day grid-search strategy
> discovery (~121k combinations per run), blockchain-verified OHLCV,
> MetaMask wallet CLI, and a production-readiness audit trail.

## Why you might read this repo

-   **Operational discipline, not hype**: pre-trading checks, seed validation,
    production audit reports, paper-trading gates, data-freshness enforcement.
-   **Strategy engine**: grid-search finds two best strategies per timeframe;
    fallback strategies saved automatically.
-   **Everything documented**: user manual, math primer, TRON integration plan,
    paper-trading guide, validation reports, CHANGELOG.
-   **Safety**: 2:1 minimum R/R, profit-locking, conservative 25× leverage cap,
    refusal to trade on data > 30 days old.

## Part of the ARC ecosystem

Harvest is the "heavy-artillery" cousin of [BrokeBot](https://github.com/GareBear99/BrokeBot)
and [Charm](https://github.com/GareBear99/Charm). Emit decisions into the
**ARC-Core** spine for receipt-based trade audit and replay:

-   [ARC-Core](https://github.com/GareBear99/ARC-Core)
-   [omnibinary-runtime](https://github.com/GareBear99/omnibinary-runtime) +
    [Arc-RAR](https://github.com/GareBear99/Arc-RAR) — any-OS portability.
-   [Portfolio](https://github.com/GareBear99/Portfolio) — full project index.

## Keywords
`crypto trading system` · `multi-timeframe backtest` · `grid search strategies` ·
`quantitative finance python` · `metamask cli` · `btc eth trading bot` ·
`algorithmic trading` · `production-grade backtester` · `data freshness gate` ·
`seed validation` · `blockchain-verified ohlcv`

---

# Cryptocurrency Trading System
**Version 2.0+ | Production Ready | December 26, 2024**

---

## 🚀 Quick Start

```bash
# 1. Validate system and ensure data is fresh
python pre_trading_check.py

# 2. Run backtest to verify everything works
python backtest_90_complete.py

# 3. Check system health anytime
python pre_trading_check.py --check-only
```

**That's it!** The system will guide you through any needed setup.

---

## 📚 Documentation

### **Start Here**

**[QUICK_START.md](QUICK_START.md)** - Get started immediately  
**[USER_TESTING_GUIDE.md](USER_TESTING_GUIDE.md)** - Pre-live testing guide  
**[USER_MANUAL.md](docs/USER_MANUAL.md)** - Complete system guide
- What the system does and how it works
- How to use every feature
- Troubleshooting guide
- Command reference
- FAQ

### **Paper Trading**

**[docs/PAPER_TRADING_READY.md](docs/PAPER_TRADING_READY.md)** - Paper trading readiness  
**[docs/PAPER_TRADING_TEST_GUIDE.md](docs/PAPER_TRADING_TEST_GUIDE.md)** - How to run paper trading  
**[docs/WALLET_CONNECT_GUIDE.md](docs/WALLET_CONNECT_GUIDE.md)** - Wallet connection guide

### **Mathematics**

**[docs/MATHEMATICS.md](docs/MATHEMATICS.md)** - Math explained in simple terms
- Win rate, P&L, position sizing
- Leverage, risk/reward ratios
- All indicators explained with real examples
- Complete trade walkthrough

### **Future Plans**

**[docs/TRON_INTEGRATION.md](docs/TRON_INTEGRATION.md)** - Tron blockchain integration
- Why Tron? (speed, cost, throughput)
- Technical architecture
- Implementation timeline
- Economic analysis

### **System Status**

**[COMPREHENSIVE_SYSTEM_REVIEW_DEC26_2024.md](COMPREHENSIVE_SYSTEM_REVIEW_DEC26_2024.md)** - Full system analysis  
**[SEED_VALIDATION_SYSTEM_COMPLETE.md](SEED_VALIDATION_SYSTEM_COMPLETE.md)** - Seed system completion report  
**[PRODUCTION_READINESS_CHECKLIST.md](PRODUCTION_READINESS_CHECKLIST.md)** - Production status checklist  
**[PRODUCTION_AUDIT_REPORT_DEC26_2024.md](PRODUCTION_AUDIT_REPORT_DEC26_2024.md)** - Complete audit findings  
**[CHANGELOG.md](CHANGELOG.md)** - Recent improvements

**Dec 26, 2024 Updates:**
- ✅ **Seed Validation System Complete** - 4-layer tracking operational, all confusion eliminated
- ✅ **MetaMask Connection Persistence** - Wallet connection now persists through dashboard refreshes
- ✅ **Strategy Configuration Logging** - Real SHA-256 seeds displayed (1829669, 5659348, etc.)
- ✅ **Documentation Cleanup** - Organized docs, added historical notices to 6 files
- ✅ **Production Audit Complete** - Comprehensive code and documentation audit passed

---

## 🎯 What This System Does

This is an **automated cryptocurrency trading system** that:
- **Makes money** by predicting when crypto prices will drop (shorting)
- **Trades safely** with strict risk management and profit locking
- **Trades multiple timeframes** (15-minute, 1-hour, 4-hour) for 3-5+ trades per day
- **Learns and adapts** to find the best strategies

**Target:** 90%+ win rate (9 out of 10 trades profitable)

---

## ✅ Key Features

### Automated Workflow
- ✅ Checks data freshness before every trading session
- ✅ Auto-downloads fresh 90-day data if stale (>30 days)
- ✅ Runs grid search to find 2 best strategies per timeframe
- ✅ Saves fallback strategies automatically
- ✅ Never trades on stale data

### Trading Capabilities
- ✅ Multi-timeframe trading (15m, 1h, 4h simultaneously)
- ✅ High win rate strategies (85-95% in backtests)
- ✅ Strict risk management (2:1 reward/risk minimum)
- ✅ Profit locking system
- ✅ Leverage scaling (25× conservative)

### Data Management
- ✅ 90-day OHLCV data (ETHUSDT, BTCUSDT)
- ✅ Blockchain verification and auto-correction
- ✅ Automatic freshness checking
- ✅ Data integrity 100% validated

### Strategy System
- ✅ BASE_STRATEGY (always available, immutable)
- ✅ Fallback strategies (data-driven, auto-generated)
- ✅ Proven strategies (real-world tested)
- ✅ 121,500 combinations tested per optimization

---

## 🏗️ System Architecture

```
Pre-Trading Check
       ↓
Data Validation (<30 days)
       ↓
If Stale → Download + Grid Search → Save Fallbacks
       ↓
System Ready
       ↓
Backtest/Trade with Fresh Data
```

---

## 📊 Trading Pairs

Currently supported:
- **ETHUSDT** (Ethereum vs. USDT)
- **BTCUSDT** (Bitcoin vs. USDT)

**Want to add more pairs?**
1. Edit `trading_pairs_config.py`
2. Add pair to `ACTIVE_PAIRS`
3. Run `python pre_trading_check.py --force`

---

## 🎓 For New Users

1. **Quick start:** Open [QUICK_START.md](QUICK_START.md)
2. **Read the manual:** Check [docs/USER_MANUAL.md](docs/USER_MANUAL.md)
3. **Understand the math:** Review [docs/MATHEMATICS.md](docs/MATHEMATICS.md)
4. **Run validation:** `python pre_trading_check.py`
5. **Test the system:** `python backtest_90_complete.py`
6. **Paper trading:** Follow [USER_TESTING_GUIDE.md](USER_TESTING_GUIDE.md)
7. **You're ready!**

---

## 🛠️ Command Reference

### System Validation
```bash
# Full validation with interactive prompts
python pre_trading_check.py

# Check health only (no updates)
python pre_trading_check.py --check-only

# Auto-update without prompts
python pre_trading_check.py --non-interactive

# Force update all data
python pre_trading_check.py --force
```

### Backtesting
```bash
# Normal run with pre-flight validation
python backtest_90_complete.py

# Skip validation (for testing only)
python backtest_90_complete.py --skip-check

# Auto-update stale data
python backtest_90_complete.py --non-interactive
```

### Strategy Updates
```bash
# Check data freshness only
python auto_strategy_updater.py --check

# Force update all strategies
python auto_strategy_updater.py --force

# Normal auto-update
python auto_strategy_updater.py
```

### Data Management
```bash
# Download fresh 90-day data
python download_90day_data.py

# Verify data integrity
python blockchain_verifier.py

# Audit specific file
python audit_blockchain_data.py
```

### Wallet Connection
```bash
# Connect to MetaMask wallet and test
python cli.py wallet connect

# Connect with specific RPC URL
python cli.py wallet connect --rpc-url https://mainnet.infura.io/v3/YOUR-KEY

# Connect to testnet
python cli.py wallet connect --testnet

# Check wallet balance
python cli.py wallet balance

# View gas prices
python cli.py wallet gas

# Full wallet info
python cli.py wallet info
```

### Documentation
```bash
# Generate HTML documentation package
./generate_docs.sh

# Result: documentation_package/ folder with HTML files
# Open documentation_package/index.html in browser
```

---

## 📦 Project Structure

```
harvest/
├── README.md                    # This file
├── USER_MANUAL.md               # Complete user guide
├── MATHEMATICS.md               # Math explained simply
├── TRON_INTEGRATION.md          # Future plans
├── SYSTEM_COMPLETE_2024.md      # Delivery report
│
├── pre_trading_check.py         # Central validation
├── auto_strategy_updater.py     # Auto strategy updates
├── backtest_90_complete.py      # Enhanced backtest
├── generate_docs.sh             # Doc generator
│
├── data/                        # 90-day OHLCV data
│   ├── eth_90days.json
│   └── btc_90days.json
│
├── ml/                          # Strategy configs
│   ├── base_strategy.py
│   ├── fallback_strategies.json
│   └── ml_config.json
│
├── documentation_package/       # HTML docs
│   ├── index.html
│   └── [all documentation]
│
└── docs/
    └── archive/                 # Historical docs
        └── README.md
```

---

## 🔍 Troubleshooting

### Problem: "Data is stale"
```bash
python auto_strategy_updater.py
```

### Problem: "No fallback strategies"
```bash
python pre_trading_check.py
```

### Problem: Backtest shows 0 trades
Check data integrity:
```bash
python blockchain_verifier.py
```

### More Help
See **[USER_MANUAL.md](USER_MANUAL.md)** Troubleshooting section

---

## 🚀 Future Enhancements

### Coming in Q1-Q2 2025: Tron Network Integration
- **Ultra-fast transactions** (<3 seconds vs 15 min Ethereum)
- **Near-zero fees** (~$0.01 vs $20+ Ethereum)
- **Annual savings:** $215,000+ in transaction fees
- **DEX integration:** JustSwap, SunSwap
- **Smart contracts:** Automated on-chain trading

See **[TRON_INTEGRATION.md](TRON_INTEGRATION.md)** for complete roadmap

---

## 📈 Performance

### Backtested Results
- **Win Rate:** 85-95% (target: 90%+)
- **Trades/Day:** 3-5
- **Data Coverage:** 90 days
- **Risk/Reward:** Minimum 2:1
- **Strategy Combinations Tested:** 121,500

### System Reliability
- **Data Integrity:** 100% verified
- **Blockchain Verification:** Complete
- **Error Handling:** Comprehensive
- **Documentation:** Complete
- **Production Status:** Ready

---

## ⚠️ Important Notes

### Risk Warning
Cryptocurrency trading is highly risky. Only trade with money you can afford to lose. This system is a tool, not a guarantee of profit.

### System Safety
- Never trade on stale data (system enforces this)
- Always run pre-flight checks before trading
- Start with small amounts to test
- Monitor performance regularly

### Data Freshness
- System requires data <30 days old
- Automatic checks before each session
- Auto-download and strategy updates available
- Never skip validation in production

---

## 💡 Best Practices

### Daily Routine
1. Check system health: `python pre_trading_check.py --check-only`
2. Update if needed: `python pre_trading_check.py`
3. Run backtest: `python backtest_90_complete.py`

### Weekly Maintenance
```bash
# Force refresh all data and strategies
python pre_trading_check.py --force

# Run comprehensive backtest
python backtest_90_complete.py

# Review strategy performance
# Check ml/fallback_strategies.json
```

### Before Going Live
1. ✅ Run backtest on 90 days
2. ✅ Verify 90%+ win rate
3. ✅ Understand all commands
4. ✅ Read USER_MANUAL.md completely
5. ✅ Start with minimal capital

---

## 📞 Support

### System Health Check
```bash
python pre_trading_check.py --check-only
```

### Getting Help
1. Check **[USER_MANUAL.md](USER_MANUAL.md)** first
2. Review error messages (they're descriptive)
3. Run validation: `python pre_trading_check.py`
4. Check **[MATHEMATICS.md](MATHEMATICS.md)** for calculation questions

### Updating System
```bash
git pull origin main
python pre_trading_check.py --force
```

---

## 🏆 System Status

**Version:** 2.0  
**Status:** ✅ **Production Ready**  
**Last Updated:** December 17, 2024

### All Success Criteria Met ✅
- [x] Automatic data freshness validation
- [x] Auto-download when data is stale
- [x] Grid search finds 2 best strategies per timeframe
- [x] Fallback strategies saved automatically
- [x] Never trades on stale data
- [x] Comprehensive documentation in layman's terms
- [x] Mathematical explanations with real examples
- [x] Future enhancement plans documented

**The system is complete, tested, documented, and ready to use.**

---

## 📄 License

See LICENSE file for details.

---

## 🎉 Quick Links

- **[USER_MANUAL.md](USER_MANUAL.md)** - Start here
- **[MATHEMATICS.md](MATHEMATICS.md)** - Understand the math
- **[TRON_INTEGRATION.md](TRON_INTEGRATION.md)** - Future plans
- **[SYSTEM_COMPLETE_2024.md](SYSTEM_COMPLETE_2024.md)** - Delivery report
- **documentation_package/index.html** - Browse HTML docs
- **docs/archive/** - Historical documentation

---

**Ready to start? Read [USER_MANUAL.md](USER_MANUAL.md) and run `python pre_trading_check.py`**

*Trade safely! 🚀*

---

<!-- ARC-Trading-Fleet-Nav-Marker -->
## 🧭 ARC Trading Fleet

Six sibling repositories. Same ARC event-and-receipt doctrine. Each has its
own live GitHub Pages docs site, source, and README.

| Repo | One-liner | Source | Docs site |
|---|---|---|---|
| [BrokeBot](https://github.com/GareBear99/BrokeBot) | TRON Funding-Rate Arbitrage (CEX, Python) | [source](https://github.com/GareBear99/BrokeBot) | [https://garebear99.github.io/BrokeBot/](https://garebear99.github.io/BrokeBot/) |
| [Charm](https://github.com/GareBear99/Charm) | Uniswap v3 Spot Bot on Base (Node.js) | [source](https://github.com/GareBear99/Charm) | [https://garebear99.github.io/Charm/](https://garebear99.github.io/Charm/) |
| **Harvest** (you are here) | Multi-Timeframe Crypto Research Platform (Python) | [source](https://github.com/GareBear99/Harvest) | [https://garebear99.github.io/Harvest/](https://garebear99.github.io/Harvest/) |
| [One-Shot-Multi-Shot](https://github.com/GareBear99/One-Shot-Multi-Shot) | Binary-Options 3-Hearts Engine (JS) | [source](https://github.com/GareBear99/One-Shot-Multi-Shot) | [https://garebear99.github.io/One-Shot-Multi-Shot/](https://garebear99.github.io/One-Shot-Multi-Shot/) |
| [DecaGrid](https://github.com/GareBear99/DecaGrid) | Capital-Ladder Grid Trading Docs Pack | [source](https://github.com/GareBear99/DecaGrid) | [https://garebear99.github.io/DecaGrid/](https://garebear99.github.io/DecaGrid/) |
| [EdgeStack Currency](https://github.com/GareBear99/EdgeStack_Currency) | Event-Sourced Multi-Currency Execution Spec | [source](https://github.com/GareBear99/EdgeStack_Currency) | [https://garebear99.github.io/EdgeStack_Currency/](https://garebear99.github.io/EdgeStack_Currency/) |

### Upstream + meta
- [ARC-Core](https://github.com/GareBear99/ARC-Core) — governed event + receipt spine the fleet plugs into.
- [omnibinary-runtime](https://github.com/GareBear99/omnibinary-runtime) + [Arc-RAR](https://github.com/GareBear99/Arc-RAR) — any-OS portability for deployment.
- [Portfolio](https://github.com/GareBear99/Portfolio) — full project index (audio plugins, games, simulators, AI runtimes, robotics, trading).
