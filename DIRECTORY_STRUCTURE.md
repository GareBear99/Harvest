# HARVEST Trading Bot - Directory Structure

## 📁 Project Organization

```
harvest/
├── README.md                          # Main documentation
├── CHANGELOG.md                       # ✅ Change tracking (NEW Dec 26)
├── QUICK_START.md                     # Quick start guide
├── USER_TESTING_GUIDE.md              # User testing instructions
├── requirements.txt                   # Python dependencies
├── __init__.py                        # Package initialization
│
├── 📋 SYSTEM REVIEWS & STATUS
├── COMPREHENSIVE_SYSTEM_REVIEW_DEC26_2024.md  # Full system analysis
├── FIXES_AND_REMAINING_TASKS.md       # Implementation tracking
├── DIRECTORY_STRUCTURE.md             # This file
│
├── 🔧 CORE SCRIPTS (Root Level)
├── backtest_90_complete.py            # ✅ Main backtest system (5 timeframes)
├── pre_trading_check.py               # ✅ System validation & data checks
├── cli.py                             # ✅ Command-line interface
├── live_trader.py                     # ✅ Live trading execution
├── trading_pairs_config.py            # ✅ Trading pair configurations
│
├── 📊 core/                           # Core trading logic
│   ├── indicators_backtest.py         # Technical indicators
│   ├── tier_manager.py                # Risk tier management
│   ├── profit_locker.py               # Profit locking system
│   ├── leverage_scaler.py             # Dynamic leverage
│   ├── processing_manager.py          # Multi-timeframe coordinator
│   └── system_state.py                # ✅ State tracking dictionary
│
├── 🤖 ml/                             # Machine learning & strategies
│   ├── base_strategy.py               # BASE_STRATEGY configurations (5 timeframes)
│   ├── strategy_config_logger.py      # ✅ Strategy config transparency (NEW Dec 26)
│   ├── seed_tester.py                 # ✅ Seed testing & BASE_STRATEGY management
│   ├── seed_system_unified.py         # Unified seed system (4-layer tracking)
│   ├── seed_tracker.py                # Whitelist/blacklist management
│   ├── seed_registry.py               # Seed registry
│   ├── seed_catalog.py                # Trade-by-trade catalog
│   ├── strategy_seed_generator.py     # Deterministic seed generation
│   ├── timeframe_strategy_manager.py  # Per-timeframe strategy management
│   ├── intelligent_learner.py         # Adaptive learning
│   ├── ml_config.py                   # ML enable/disable per asset
│   ├── strategy_pool.py               # Proven strategies pool
│   │
│   ├── 📄 Data Files
│   ├── seed_registry.json             # Complete seed configurations
│   ├── seed_snapshots.json            # SHA-256 verified snapshots
│   ├── seed_catalog.json              # Trade history catalog
│   ├── seed_performance_tracker.json  # Performance tracking
│   ├── seed_whitelist.json            # Whitelisted seeds
│   ├── seed_blacklist.json            # Blacklisted seeds
│   ├── base_strategy_backup.json      # Original BASE_STRATEGY backup
│   ├── base_strategy_overrides.json   # Current overrides
│   ├── system_state.json              # ✅ System state dictionary
│   └── backtest_history.json          # Backtest execution history
│
├── 🎨 dashboard/                      # Terminal dashboard
│   ├── terminal_ui.py                 # Main dashboard UI
│   ├── panels.py                      # Dashboard panels (4 panels)
│   ├── formatters.py                  # Data formatting utilities
│   ├── backtest_control.py            # Backtest control panel
│   ├── ml_control.py                  # ML enable/disable control
│   ├── seed_browser.py                # Interactive seed viewer
│   ├── help_screen.py                 # Help & documentation
│   ├── live_monitor.py                # Real-time monitoring
│   └── timeout_manager.py             # ✅ Timeout & error handling
│
├── 📈 strategies/                     # Trading strategies
│   └── timeframe_strategy.py          # Strategy classes (1m, 5m, 15m, 1h, 4h)
│
├── 📉 analysis/                       # Analysis tools
│   ├── ml_confidence_model.py         # Confidence scoring
│   ├── prediction_tracker.py          # Prediction tracking
│   ├── high_accuracy_filter.py        # 10-criteria filter
│   └── reversal_detector.py           # Reversal detection
│
├── 💾 data/                           # Market data
│   ├── eth_90days.json                # ETH 90-day data
│   └── btc_90days.json                # BTC 90-day data
│
├── 📚 docs/                           # Documentation (moved from root)
│   ├── 📖 Active Guides
│   ├── PAPER_TRADING_READY.md         # Paper trading readiness
│   ├── PAPER_TRADING_TEST_GUIDE.md    # Paper trading instructions
│   ├── WALLET_CONNECT_GUIDE.md        # Wallet connection guide
│   ├── WALLET_SYSTEM_GUIDE.md         # Complete wallet guide
│   ├── WALLET_CONNECT_QUICKSTART.md   # Quick wallet setup
│   │
│   ├── 📖 System Documentation
│   ├── IMPLEMENTATION_SUMMARY.md      # Complete feature summary
│   ├── SEED_TESTING_GUIDE.md          # Seed testing guide
│   ├── SEED_COMMANDS_QUICK_REF.md     # Quick reference
│   ├── TIMEFRAME_EXPANSION.md         # 1m & 5m timeframe details
│   ├── FINAL_VERIFICATION.md          # System verification
│   ├── DASHBOARD_COMPLETE.md          # Dashboard documentation
│   ├── SEED_TRACKING_VERIFICATION.md  # Seed system details
│   ├── MATHEMATICS.md                 # Math explanations
│   ├── USER_MANUAL.md                 # User manual
│   ├── TRON_INTEGRATION.md            # Future blockchain integration
│   │
│   └── 📦 archive/                    # Completed validation docs
│       ├── COMPLETE_SYSTEM_VALIDATION.md
│       ├── FINAL_VALIDATION_COMPLETE.md
│       ├── VALIDATION_COMPLETE.md
│       ├── PAPER_TRADING_VERIFIED.md
│       ├── WALLET_CONNECTION_TEST_RESULTS.md
│       ├── DOCUMENTATION_AND_ORGANIZATION_COMPLETE.md
│       └── FINAL_RESULTS.txt
│
├── 📦 documentation_package/          # HTML documentation
│   ├── index.html                     # ✅ Updated main page with credits
│   ├── USER_MANUAL.html
│   ├── MATHEMATICS.html
│   └── TRON_INTEGRATION.html
│
├── 🧪 tests/                          # Test files (moved from root)
│   ├── test_determinism.py
│   ├── test_seed_reproducibility.py
│   ├── test_dashboard_components.py
│   └── ... (33 test files total)
│
├── 🗄️ archive/                        # Archived/old files
│   ├── old_backtests/                 # Previous backtest versions
│   ├── utilities/                     # Utility scripts
│   └── grid_search/                   # Grid search experiments
│
├── 🛠️ utils/                          # Utility functions
├── 🌐 tron/                           # Tron blockchain integration (future)
├── 📊 grid_search_results/            # Optimization results
└── 📝 logs/                           # System logs
```

## 🎯 Core Files Quick Reference

### Essential Scripts (Keep in Root)

1. **backtest_90_complete.py** - Main backtest system
   - Tests all 5 timeframes (1m, 5m, 15m, 1h, 4h)
   - Supports batch seed testing
   - 90-day historical data

2. **pre_trading_check.py** - System validation
   - Checks data freshness
   - Validates configurations
   - Pre-flight checks

3. **cli.py** - Command-line interface
   - Interactive CLI
   - System commands

4. **live_trader.py** - Live trading
   - Real-time trading execution
   - Position management

5. **trading_pairs_config.py** - Trading pairs
   - ETH/BTC configurations

### New Core Components

6. **core/system_state.py** - State tracking dictionary
   - Tracks all operations
   - Records configurations
   - Performance metrics
   - Error tracking

7. **ml/seed_tester.py** - Seed management
   - Test all/top 10 seeds
   - Overwrite BASE_STRATEGY
   - Reset configurations

8. **dashboard/timeout_manager.py** - Timeout handling
   - Progress indicators
   - Error recovery
   - User feedback

### Dec 26, 2024 Updates

9. **ml/strategy_config_logger.py** - Strategy transparency
   - Shows which strategy config is active
   - Logs precedence order for all timeframes
   - No behavior changes, only visibility

10. **Dashboard MetaMask Fix** - Connection persistence
   - Fixed `dashboard/terminal_ui.py` to read from `data/wallet_config.json`
   - MetaMask connection now persists through refreshes
   - Single source of truth for wallet state

## 📊 System State Dictionary

The system now maintains a comprehensive state in `ml/system_state.json`:

```json
{
  "metadata": { ... },
  "timeframes": {
    "1m": { "enabled": true, "current_seed": null, ... },
    "5m": { "enabled": true, "current_seed": null, ... },
    "15m": { "enabled": true, "current_seed": null, ... },
    "1h": { "enabled": true, "current_seed": null, ... },
    "4h": { "enabled": true, "current_seed": null, ... }
  },
  "seed_system": { ... },
  "operations": { ... },
  "dashboard": { ... },
  "live_trading": { ... },
  "assets": { "ETH": { ... }, "BTC": { ... } },
  "files": { ... },
  "errors": { ... },
  "performance": { ... }
}
```

## 🚀 Quick Start

```bash
# Navigate to project
cd ~/Projects/harvest

# Check system status
python ml/seed_tester.py status

# View system state
python core/system_state.py

# Run pre-flight check
python pre_trading_check.py

# Run backtest
python backtest_90_complete.py

# Launch dashboard
python dashboard/terminal_ui.py
```

## 📁 What Was Archived

### Old Backtests (archive/old_backtests/)
- 18 deprecated backtest versions
- Historical optimization attempts
- Previous implementations

### Utilities (archive/utilities/)
- Data download scripts
- Debug tools
- Validation scripts
- System creation scripts

### Grid Search (archive/grid_search/)
- Optimization experiments
- Parameter search scripts

### Tests (tests/)
- 44 test files
- Unit tests
- Integration tests
- System validation

### Documentation (docs/)
- **Active docs** in `docs/` (paper trading, wallet guides)
- **Archived docs** in `docs/archive/` (completed validation reports)
- **Essential docs** in root (README, QUICK_START, USER_TESTING_GUIDE)

## ✅ Clean Structure Benefits

1. **Root Level** - Only essential scripts
2. **Organized** - Related files grouped
3. **Archived** - Old code preserved but separate
4. **Documented** - Clear structure guide
5. **Maintainable** - Easy to find files

## 🔧 System Statistics

- **Total Seeds Tracked**: 37.6 billion combinations
- **Timeframes**: 5 (1m, 5m, 15m, 1h, 4h)
- **Target Win Rate**: 72%+
- **Expected Trades**: 20-40+ per day
- **4-Layer Tracking**: Registry, Snapshots, Catalog, Performance

## 📝 Created By

**Gary Richard Doman**
- Founder: [Doman.ai](https://Doman.ai)
- Company: GareBearEnterprises
- Producer: TizWildin

---

Last Updated: December 26, 2024
Version: 3.1 (Post-v2.0 Fixes)
Location: ~/Projects/harvest
