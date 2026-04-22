# Changelog
All notable changes to the Harvest Trading System will be documented in this file.

## [Unreleased] - 2024-12-26

### Added
- **Live Paper Trading Readiness Suite**
  - `ml/bootstrap_tracking.py` - Initialize all tracking layers with BASE_STRATEGY seeds
  - `ml/validate_tracking.py` - Health check for tracking system
  - `validate_paper_trading_ready.py` - Comprehensive pre-flight validation (7 checks)
  - `validate_dashboard_display.py` - Dashboard display validation simulator
  - All 5 BASE_STRATEGY seeds registered (1829669, 5659348, 15542880, 60507652, 240966292)
  - Layer 3 (catalog) auto-creation verified
  - Seed confusion prevention validated
  - Dashboard display validated to show real SHA-256 seeds only

- **Strategy Configuration Logging with Real SHA-256 Seeds** (`ml/strategy_config_logger.py`)
  - Shows REAL SHA-256 deterministic seeds (e.g., 15542880) instead of timeframe prefixes (e.g., 15001)
  - Displays bidirectional traceability through 4-layer tracking system:
    - Layer 1: seed_registry.json (performance database)
    - Layer 2: seed_snapshots.json (SHA-256 verification)
    - Layer 3: seed_catalog.json (trade-by-trade records)
    - Layer 4: seed_performance_tracker.json (whitelist/blacklist)
  - Shows config hash for verification
  - Shows input seed (if available) for reproduction
  - Includes reproduction commands in output
  - Precedence order: User Override → Fallback Strategies → ML Learned → BASE_STRATEGY
  - Integrated into backtest startup for full transparency
  - No behavior changes, only visibility improvements

### Fixed
- **MetaMask Connection Persistence** 
  - Dashboard now correctly reads from `data/wallet_config.json` (single source of truth)
  - Connection status persists through dashboard refreshes and restarts
  - Fixed: `dashboard/terminal_ui.py` methods `_load_wallet_state()` and `refresh_data()`
  - Issue: Dashboard was reading from `simple_wallet_connector` while system uses `auto_wallet_manager`

### Changed
- **Documentation Organization**
  - Moved completed validation docs to `docs/archive/`
  - Moved active guides to `docs/`
  - Clean root directory with only essential files
  - Updated comprehensive system review (removed 21-day test references)
- **Seed Tracking Organization**
  - Moved demo/example files to `ml/seed_tracking_examples/`
  - Created README explaining example vs production files
  - Production files remain in `ml/` (registry, snapshots, whitelist, blacklist)
  - Clear separation between reference examples and active tracking

### Documentation
- Created `COMPREHENSIVE_SYSTEM_REVIEW_DEC26_2024.md` - Full system analysis
- Created `FIXES_AND_REMAINING_TASKS.md` - Implementation tracking
- Created `CHANGELOG.md` - Change tracking
- Created `DASHBOARD_VALIDATION_REPORT.md` - Complete dashboard validation report
  - Validates all user-facing displays show real SHA-256 seeds
  - Documents what users WILL and WON'T see
  - Provides verification steps for user testing
  - Confirms system ready for paper trading
- Created `docs/SEED_SYSTEM_CRITICAL_NOTE.md` - Critical clarification of seed system
  - Explains difference between timeframe prefixes (1001, 5001) vs real SHA-256 seeds
  - Documents bidirectional traceability system
  - Prevents future confusion about seed types
- Updated `ml/base_strategy.py` - Added clear comments explaining timeframe prefixes

---

## [2.0] - 2024-12-17

### Major Release: Production Ready
- 48-hour paper trading requirement system
- Balance-aware slot allocation (stair-climbing $10 per slot)
- Multi-timeframe support (1m, 5m, 15m, 1h, 4h)
- BASE_STRATEGY for all timeframes
- Grid search optimization system
- Auto wallet management
- Comprehensive dashboard
- Statistics tracking
- Founder fee system (position tiers)

---

## Recent History

### Documentation Improvements
- Cleaned up 21-day test references (system uses 90-day data only)
- Updated BASE_STRATEGY understanding (unoptimized fallback, not "failing")
- Comprehensive system review completed

### System Status
**Working**:
- ✅ Paper trading (48h requirement)
- ✅ Dashboard UI (all panels)
- ✅ Data pipeline (90-day)
- ✅ Slot allocation
- ✅ Statistics tracking
- ✅ BTC wallet auto-creation
- ✅ MetaMask persistence (FIXED Dec 26)
- ✅ Strategy config logging (NEW Dec 26)

**Not Working**:
- ❌ Live order execution (NotImplementedError)

**Needs Attention**:
- ⚠️  Missing fallback strategies (run grid search)
- ⚠️  Paper trading session stale (need fresh 48h)

---

## Roadmap

### Immediate (Before Paper Trading)
1. Generate optimized fallback strategies
2. Validate on 90-day backtest
3. Start fresh 48-hour paper trading session

### Short-term (Before Live Trading)
4. Complete 48-hour paper trading
5. Connect MetaMask for real
6. Verify end-to-end wallet flow

### Long-term (For Live Trading)
7. Implement live execution (`_execute_live_trade`)
8. Exchange API integration (Binance/Hyperliquid)
9. Testnet testing
10. Gradual scaling ($1-5 positions)

---

## Version History

- **v2.0** (Dec 17, 2024) - Production ready release
- **v1.x** (2024) - Development versions
- **Current** (Dec 26, 2024) - Post-v2.0 fixes and improvements

---

## Notes

### Breaking Changes
- None in recent updates (only additive changes)

### Deprecations
- Removed 21-day test data references
- Using 90-day data exclusively

### Migration Guide
- No migrations needed for recent changes
- Strategy logging is automatic (no config changes)
- MetaMask fix is transparent (no user action)

---

**Last Updated**: December 26, 2024  
**Maintainer**: GareBearEnterprises / TizWildin  
**Website**: https://Doman.ai
