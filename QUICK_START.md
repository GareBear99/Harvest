# HARVEST Trading Bot - Quick Start Guide

**Status**: ✅ Slot Allocation System Ready | ✅ Seed System Validated  
**Last Updated**: December 26, 2024

---

## 🚀 Quick Commands

### Test Everything
```bash
# Run all validation tests (60 tests)
python test_slot_allocation_validation.py

# Test dashboard integration (2 tests)
python test_dashboard_slots.py
```

### Launch Dashboard
```bash
# Option 1: Python launcher (recommended)
python3 dashboard.py

# Option 2: Shell script
./dashboard.sh

# Option 3: Direct launch
python3 dashboard/terminal_ui.py --test
```

### Test Backtests at Different Balances
```bash
# Test slot 1 (ETH only, 1m)
python backtest_90_complete.py --balance 10 --skip-check

# Test slots 1-2 (ETH+BTC, 1m)
python backtest_90_complete.py --balance 25 --skip-check

# Test slots 1-4 (1m+5m unlocked)
python backtest_90_complete.py --balance 35 --skip-check

# Test slots 1-6 (1m+5m+15m)
python backtest_90_complete.py --balance 55 --skip-check

# Test full base system (all 10 slots)
python backtest_90_complete.py --balance 100 --skip-check

# Test position tier 2 (20 slots)
python backtest_90_complete.py --balance 150 --skip-check
```

---

## 📋 What to Check in Dashboard

When you launch `./dashboard.sh`, look for in the **Bot Status panel**:

```
💎 Slot Allocation: X/10 active
   ETH Slots: [1, 3, 5...]
   BTC Slots: [2, 4, 6...]
   Timeframes: 1m, 5m, ...
   Next: Slot X (ASSET) @ $XX ($X away)
```

### Expected Display at Different Balances

**$10 (Default)**:
- Slot Allocation: 1/10 active
- ETH Slots: [1]
- BTC Slots: []
- Timeframes: 1m
- Next: Slot 2 (BTC) @ $20

**$35**:
- Slot Allocation: 3/10 active
- ETH Slots: [1, 3]
- BTC Slots: [2]
- Timeframes: 1m, 5m
- Next: Slot 4 (BTC) @ $40

**$100**:
- Slot Allocation: 10/10 active
- ETH Slots: [1, 3, 5, 7, 9]
- BTC Slots: [2, 4, 6, 8, 10]
- Timeframes: 1m, 5m, 15m, 1h, 4h
- (No next unlock - full base system)

---

## ✅ Validation Checklist

### Phase 1: Code Validation (Complete ✅)
- [x] All 62 tests passing
- [x] Dashboard integration working
- [x] Panel rendering correctly
- [x] Documentation updated
- [x] KeyError bug fixed (TimeframeStrategyManager)

### Phase 2: Visual Validation (Next)
- [ ] Launch dashboard and observe slot display
- [ ] Verify ETH/BTC slots shown separately
- [ ] Check timeframe display
- [ ] Confirm "Next unlock" appears correctly

### Phase 3: Balance Testing (Recommended)
```bash
# Test these critical balance points
python backtest_90_complete.py --balance 19 --skip-check  # Just before BTC
python backtest_90_complete.py --balance 20 --skip-check  # BTC activation
python backtest_90_complete.py --balance 29 --skip-check  # Just before 5m
python backtest_90_complete.py --balance 30 --skip-check  # 5m unlock
python backtest_90_complete.py --balance 99 --skip-check  # Almost full base
python backtest_90_complete.py --balance 100 --skip-check # Full base system
```

### Phase 4: Paper Trading (48 hours REQUIRED)
- [ ] Start paper trading: `python3 core/paper_trading_tracker.py`
- [ ] Run for minimum 48 hours
- [ ] Complete at least 1 successful trade
- [ ] Maintain positive P&L
- [ ] Check requirements: `python3 pre_trading_check.py --live`
- [ ] Complete session before live trading

**Requirements for Live Trading:**
- ✅ 48 hours minimum duration
- ✅ At least 1 winning trade
- ✅ Positive total P&L (> $0.00)

### Phase 5: Live Trading (After Paper Trading)
- [ ] Validate: `python3 pre_trading_check.py --live`
- [ ] Start with $10 minimum
- [ ] Monitor first trade closely
- [ ] Validate $20 BTC activation
- [ ] Test each milestone ($30, $50, $100)
- [ ] Document any issues

---

## 🎯 Key Balance Milestones

| Balance | Slots | What Unlocks | Assets | Timeframes |
|---------|-------|--------------|--------|------------|
| $10 | 1 | First slot | ETH only | 1m |
| $20 | 2 | BTC asset | ETH+BTC | 1m |
| $30 | 3 | 5m timeframe | ETH+BTC | 1m, 5m |
| $50 | 5 | 15m timeframe | ETH+BTC | 1m, 5m, 15m |
| $70 | 7 | 1h timeframe | ETH+BTC | 1m, 5m, 15m, 1h |
| $90 | 9 | 4h timeframe | ETH+BTC | All 5 TFs |
| $100 | 10 | **FULL BASE** | ETH+BTC | All 5 TFs |
| $110 | 10 | **Tier 2** (20 slots) | ETH+BTC | All 5 TFs |
| $210 | 10 | **Tier 3** (30 MAXED) | ETH+BTC | All 5 TFs |

---

## 🔍 Troubleshooting

### Dashboard doesn't show slot info
**Check**: Is `slot_allocation` key in bot data?
```bash
python test_dashboard_slots.py
```
**Expected**: Both tests should pass

### Backtest shows wrong slots
**Check**: Is slot allocation strategy working?
```bash
python test_slot_allocation_validation.py
```
**Expected**: 60/60 tests pass

### Slot counts seem incorrect
**Check**: Slot calculation at specific balance
```bash
python -c "
from core.slot_allocation_strategy import get_slot_allocation_strategy
strategy = get_slot_allocation_strategy()
print(strategy.format_slot_summary(35))
"
```

### Dashboard won't launch
**Check**: Dependencies and wallet system
```bash
# Check wallet initialization
python -c "
from core.auto_wallet_manager import AutoWalletManager
manager = AutoWalletManager()
print(f'Client ID: {manager.client_id[:16]}...')
"
```

---

## 🌱 Seed System Validation (NEW - Dec 26, 2024)

### Verify Real SHA-256 Seeds Are Displayed

```bash
# Validate dashboard will show real seeds
python3 validate_dashboard_display.py

# Run backtest and check seed display at startup
python3 backtest_90_complete.py eth_90days.json
```

**What to look for:**
- Real SHA-256 seeds: **1829669** (1m), **5659348** (5m), **15542880** (15m), **60507652** (1h), **240966292** (4h)
- NOT prefix values: ~~1001~~, ~~5001~~, ~~15001~~, ~~60001~~, ~~240001~~

**Seed System Documentation:**
- `docs/SEED_SYSTEM_CRITICAL_NOTE.md` - Complete explanation of seed types
- `DASHBOARD_VALIDATION_REPORT.md` - Full validation report

---

## 📖 Documentation Quick Links

- **System Review**: `COMPREHENSIVE_SYSTEM_REVIEW_DEC26_2024.md`
- **Production Checklist**: `PRODUCTION_READINESS_CHECKLIST.md`
- **Seed System**: `docs/SEED_SYSTEM_CRITICAL_NOTE.md`
- **Dashboard Validation**: `DASHBOARD_VALIDATION_REPORT.md`
- **Technical Implementation**: `SLOT_ALLOCATION_IMPLEMENTATION.md`
- **User Documentation**: `documentation_package/index.html`

---

## 🛠️ Development Commands

### View Slot Demo
```bash
python core/slot_allocation_strategy.py
```

### View Data Provider Demo
```bash
python dashboard/slot_data_provider.py
```

### Test Specific Balance
```bash
python -c "
from dashboard.slot_data_provider import format_slot_allocation_for_console
print(format_slot_allocation_for_console(75))
"
```

---

## 💡 Tips

1. **Start Small**: Begin with $10 balance and work your way up
2. **Monitor Closely**: Watch the dashboard during first few trades
3. **Test Thresholds**: Pay special attention at $20, $30, $100 milestones
4. **Check Logs**: Review any errors or warnings immediately
5. **Document Issues**: Note any unexpected behavior for review

---

## 🎯 Success Indicators

✅ **System is working correctly when**:
- Dashboard shows slot allocation info
- Slot counts match balance ($10 = 1 slot, $100 = 10 slots)
- ETH/BTC alternation is correct (odd=ETH, even=BTC)
- Timeframes unlock progressively
- Next unlock info displays correctly
- No crashes or errors during transitions

❌ **Something needs attention if**:
- Slot info missing from dashboard
- Incorrect slot counts for balance
- Assets not alternating properly
- Timeframes unlock at wrong balance
- Crashes at balance thresholds

---

## 🚀 Ready to Start?

**Recommended First Steps**:

1. **Validate tests** (2 minutes):
   ```bash
   python test_dashboard_slots.py
   ```

2. **Launch dashboard** (visual check):
   ```bash
   ./dashboard.sh
   ```

3. **Test a backtest** (verify integration):
   ```bash
   python backtest_90_complete.py --balance 35 --skip-check
   ```

4. **Review results** and proceed to next phase

---

**System Status**: ✅ **READY FOR TESTING**

All code complete, all tests passing, dashboard integrated.  
Time to validate visually and begin paper trading! 🎊
