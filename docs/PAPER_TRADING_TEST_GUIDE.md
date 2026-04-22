# Paper Trading Dashboard Integration - Test Guide

## ✅ What's Been Fixed

1. **Removed arbitrary batching** - No more "every 5 wins" nonsense
2. **Correct ETH→BTC funding fees** based on slot allocation:
   - $100 (10 slots) = $2.00 setup fees (fund 5 BTC slots with $50)
   - $20 (2 slots) = $0.40 setup fees (fund 1 BTC slot with $10)
   - $10 (1 slot) = $0.00 setup fees (ETH only, no BTC)
3. **Enhanced status bar** - Shows: duration, trades, P&L with +/- sign
4. **Graceful error handling** - Dashboard doesn't crash if tracker unavailable
5. **Clear fee display** - Always shows gross → fees → net breakdown

## 🧪 Test Scenarios

### Test 1: Dashboard → Paper Trading Status (Static)

**Goal**: Verify dashboard reads existing paper trading session

```bash
# Terminal 1: Start paper trading session
python3 test_paper_trading_live.py
# Let it run for 30 seconds, then Ctrl+C

# Terminal 2: Launch dashboard
python3 dashboard.py
```

**Expected**: 
- Status bar shows: `📄 Paper: 0.0h/48h • XT • $X.XX`
- Balance shown correctly (started at $100.00)
- P&L reflects setup fees (-$2.00 initially)

---

### Test 2: Live Streaming (Terminal → Dashboard)

**Goal**: Verify dashboard updates in real-time as trades happen

```bash
# Terminal 1: Start dashboard FIRST
python3 dashboard.py

# Terminal 2: Start paper trading
python3 test_paper_trading_live.py
```

**Expected**:
- Dashboard refreshes every 10s and shows updated:
  - Trade count increasing
  - P&L changing
  - Duration incrementing
- Status bar updates: `📄 Paper: 0.0h/48h • 5T • +$0.50`

---

### Test 3: Terminal Stops → Dashboard Continues

**Goal**: Dashboard handles paper trading session stopping gracefully

```bash
# Terminal 1: Dashboard running
# Terminal 2: Paper trading running

# Stop paper trading (Ctrl+C in Terminal 2)
```

**Expected**:
- Dashboard continues running
- Status still shows last known paper trading state
- No crash, no errors
- Paper trading session saved and can resume

---

### Test 4: Dashboard Stops → Terminal Continues

**Goal**: Paper trading continues when dashboard closes

```bash
# Terminal 1: Dashboard running
# Terminal 2: Paper trading running

# Close dashboard (Ctrl+C in Terminal 1)
```

**Expected**:
- Paper trading continues in Terminal 2
- Data continues saving to `data/paper_trading_tracker.json`
- Can restart dashboard and see updated status

---

### Test 5: Missing Tracker File

**Goal**: Dashboard handles missing data gracefully

```bash
# Remove tracker file
rm data/paper_trading_tracker.json

# Launch dashboard
python3 dashboard.py
```

**Expected**:
- Dashboard starts normally
- No paper trading status shown (graceful degradation)
- No crash or error messages

---

### Test 6: Corrupt Tracker File

**Goal**: Dashboard handles corrupt data gracefully

```bash
# Create corrupt file
echo "{ corrupt json" > data/paper_trading_tracker.json

# Launch dashboard
python3 dashboard.py
```

**Expected**:
- Dashboard starts normally
- Falls back to no paper trading status
- No crash

---

## 📊 What to Check in Status Bar

The status bar should show:

### When Paper Trading Active:
```
📄 Paper: 0.3h/48h • 5T • +$1.25
```
- `0.3h/48h` = Duration progress
- `5T` = 5 trades recorded
- `+$1.25` = Net P&L (with + or - sign, color coded)

### When Requirements Met:
```
📄 Paper: READY
```
- Green "READY" indicator
- Still shows trades and P&L

### When Completed:
```
🟢 Live: APPROVED
```
- Green indicator
- Ready for live trading

---

## 🔍 Detailed Checks

### 1. Fee Transparency ($100 Start)

**Check in terminal output:**
```
Paper trading started with $100.00 (10 slots active)
BTC funding: $50.00 (fees: $2.00)
Starting P&L: -$2.00 (must overcome to be profitable)
```

**Per trade:**
```
Trade recorded: win $+0.50 (gross: $1.00 - gas: $0.50)
```

### 2. Requirements Display

**Check `run_paper_trading.py --stats`:**
```
Requirements:
  Duration (48h): ❌ 0.3h / 48h
  Min Trades (1): ✅ 5 / 1
  Positive P&L: ❌ $-1.50 (started at -$2.00)
    Need $1.50 more to break even
  All Met: ❌ NOT READY
```

### 3. Dashboard Refresh

- Dashboard refreshes every 10 seconds
- Paper trading data updates automatically
- No manual refresh needed

---

## 🚦 Success Criteria

✅ **Dashboard shows paper trading status** when session active  
✅ **Status updates in real-time** as trades happen  
✅ **Terminal can be stopped** without breaking dashboard  
✅ **Dashboard can be stopped** without breaking paper trading  
✅ **Graceful degradation** when tracker missing/corrupt  
✅ **Fee display is clear** - always shows gross → fees → net  
✅ **Setup fees explained** - user knows they start at -$2.00  
✅ **Requirements clear** - shows what's needed to be profitable  

---

## 🐛 Known Issues to Watch For

1. **Dashboard not updating** - Check refresh interval (10s)
2. **Status bar doesn't show paper trading** - Check `data/paper_trading_tracker.json` exists
3. **Fees seem wrong** - Verify: $2.00 setup for $100, $0.50 gas/trade
4. **Dashboard crashes** - Should NEVER crash, graceful degradation required

---

## 📝 Testing Checklist

Run through each test scenario and mark:

- [ ] Test 1: Static status display
- [ ] Test 2: Live streaming
- [ ] Test 3: Terminal stops
- [ ] Test 4: Dashboard stops  
- [ ] Test 5: Missing tracker file
- [ ] Test 6: Corrupt tracker file
- [ ] Fee display correct
- [ ] Requirements display clear
- [ ] Status bar updates in real-time
- [ ] No crashes or errors

---

## 🎯 Quick Test Command

For a quick end-to-end test:

```bash
# Terminal 1
python3 dashboard.py

# Terminal 2  
python3 test_paper_trading_live.py

# Watch dashboard status bar update every 10 seconds
# After ~30 seconds, stop paper trading (Ctrl+C)
# Dashboard should continue showing last status
```

Expected in status bar: `📄 Paper: 0.0h/48h • 10T • +$2.35`
