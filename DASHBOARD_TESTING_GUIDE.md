# Dashboard Testing Guide
**Date**: December 26, 2024  
**Purpose**: Complete guide for testing the dashboard with all features including wallet connection

---

## 🚀 QUICK START

### Launch Dashboard
```bash
python3 dashboard.py
```

**What happens:**
1. Initializes wallet system (BTC wallet auto-creates if needed)
2. Shows client ID
3. Runs comprehensive system check (12+ validations)
4. Displays 4-panel layout
5. Auto-refreshes every 10 seconds

---

## 🎯 DASHBOARD FEATURES TO TEST

### 1. Main Display (4 Panels)

#### Panel 1: Seed Status (Top-Left, Green Border)
**What to verify:**
- [ ] Total seeds tested count
- [ ] Whitelist/Blacklist/Neutral breakdown with percentages
- [ ] Top performer shown with win rate and P&L
- [ ] Active seeds by timeframe (all 5 TFs)
- [ ] Real SHA-256 seeds displayed (not prefixes like 1001, 5001)
- [ ] Input seeds shown (555, 666, 777, 888, 999)

#### Panel 2: Bot Status (Top-Right, Blue Border)
**What to verify:**
- [ ] Status indicator (RUNNING/STOPPED with icon)
- [ ] Mode clearly shown (BACKTEST or LIVE)
- [ ] Uptime tracking
- [ ] Balance progression: Initial → Current
- [ ] Progress bar to $100 target
- [ ] Slot allocation showing stair-climbing system
- [ ] Next slot unlock information
- [ ] Today's and All-Time statistics
- [ ] Last trade details

#### Panel 3: Performance (Bottom-Left, Yellow Border)
**What to verify:**
- [ ] Mode header (BACKTEST RESULTS vs LIVE TRADING STATS)
- [ ] Overall win rate with wins/losses
- [ ] Total trades count
- [ ] Total P&L
- [ ] Max drawdown percentage
- [ ] Per-timeframe breakdown (all 5 TFs)
- [ ] Seed attribution per timeframe
- [ ] Win rates and P&L per timeframe

#### Panel 4: Wallet & Limits (Bottom-Right, Magenta Border)
**What to verify:**
- [ ] MetaMask connection status
- [ ] Clear action hint: "Press W to connect"
- [ ] BTC wallet status
- [ ] Profit tracking section
- [ ] Profit split explanation ($100 threshold, $50 to BTC)
- [ ] Current capital display
- [ ] Max position size per trade
- [ ] Strategy explanation (small/large account)

### 2. Status Bar (Above Command Bar)

**What to verify:**
- [ ] Status icon shows current state (ℹ️/⏳/✅/❌)
- [ ] Status message reflects current operation
- [ ] Last key pressed shown with validation (✓ or ✗)
- [ ] Command history (last 3 keys)
- [ ] Paper trading status (if session active)
- [ ] 48-hour progress bar
- [ ] Live approval indicator (when complete)

### 3. Command Bar (Bottom)

**Commands to test:**
- [ ] **Q** - Quit (should exit dashboard cleanly)
- [ ] **R** - Refresh (should update data immediately)
- [ ] **W** - Wallet connect (should open browser)
- [ ] **S** - Seeds browser (should open modal)
- [ ] **B** - Backtest control (should open modal)
- [ ] **X** - Debug terminal (should open modal)
- [ ] **D** - Docs (should open browser with docs)
- [ ] **H** - Help (should show help screen)
- [ ] **ESC** - Close modal (should exit any modal)

### 4. Auto-Refresh

**What to verify:**
- [ ] Countdown shows in command bar (10, 9, 8...)
- [ ] Data refreshes automatically at 0
- [ ] Manual refresh with R resets countdown
- [ ] Refresh updates all panels

---

## 🦊 WALLET CONNECTION TESTING

### Prerequisites
- MetaMask browser extension installed
- MetaMask unlocked with at least one account

### Step-by-Step Test

#### 1. Check Initial Status
```bash
# In dashboard, look at Wallet panel (bottom-right)
# Should show:
# MetaMask: ❌ Not connected
#   → Press 'W' to connect
```

#### 2. Press 'W' to Connect
**Expected:**
1. Status bar shows: "⏳ Processing: Wallet"
2. Browser opens to `http://localhost:8765/harvest_wallet_connect.html`
3. Terminal shows:
   ```
   🔑 Server started on port 8765
   ✅ Browser opened for MetaMask connection
   📥 After connecting, the JSON file will download automatically
   💡 Dashboard will auto-detect the connection in 10 seconds
   ```

#### 3. In Browser (MetaMask Connection Page)
**Expected:**
- Beautiful purple gradient page loads
- Title: "🦊 Connect MetaMask"
- Button: "Connect Wallet"

**Actions:**
1. Click "Connect Wallet" button
2. MetaMask popup appears
3. Select account to connect
4. Click "Connect" in MetaMask
5. Page shows: "✅ Connected: 0x1234567890..."
6. File downloads automatically: `harvest_wallet_response.json`
7. Page shows: "✅ Connection successful! You can close this window and return to HARVEST."

#### 4. Back in Dashboard
**Wait for auto-refresh (10 seconds) or press R**

**Expected changes in Wallet panel:**
```
MetaMask: ✅ Connected
  Address: 0x742d35...f0bEb
  Network: Ethereum
  → Press 'W' to disconnect
```

#### 5. Verify Connection Persistence
**Exit and restart dashboard:**
```bash
# Press Q to quit
python3 dashboard.py
```

**Expected:**
- Dashboard loads
- Wallet panel shows: "✅ Connected"
- Address persists from previous session

#### 6. Test Disconnect
**In dashboard:**
1. Press 'W' again
2. Status shows: "Wallet disconnected"
3. Wallet panel updates to: "❌ Not connected"

---

## 🐛 DEBUG TERMINAL TESTING

### Open Debug Terminal
**Press X in dashboard**

**Expected:**
- Modal opens with title: "🐛 Debug Terminal - Live Log"
- Cyan border
- Shows recent action logs
- Footer shows: [1] Live Log [2] Summary [3] Errors [ESC/Q] Close

### Test View Switching

#### View 1: Live Log (Default)
**Press 1**
- Should show scrolling log of recent actions
- Format: `[HH:MM:SS.mmm] 🔵 ACTION A000001: action_name`
- Validation checks shown with ✅/❌/⚠️
- Last 30 lines visible

#### View 2: Summary
**Press 2**
- Should show session summary
- Session ID and duration
- Statistics (actions, validations, meta-validations)
- Errors and anomalies count
- Success rates (percentages)
- System health status

#### View 3: Errors
**Press 3**
- Should show errors section (last 10)
- Should show anomalies section (last 10)
- Format: `[HH:MM:SS] error_message`
- Should show "No errors logged ✅" if clean

### Close Debug Terminal
**Press ESC or Q**
- Should return to main dashboard
- Status bar shows: "Debug terminal closed"

---

## 📊 MODAL TESTING

### Help Screen (Press H)
**Expected:**
- Full-screen modal with help content
- Shows all keyboard commands
- Shows modal-specific controls
- Documentation link
- ESC or Q exits back to dashboard

### Seed Browser (Press S)
**Expected:**
- Shows list of tested seeds
- Filter options: [W]hitelist [B]lacklist [A]ll
- Pagination: Left/Right arrows
- Seed details: win rate, P&L, trades
- ESC or Q exits

### Backtest Control (Press B)
**Expected:**
- Shows available backtest files
- Control options: [N]ew [X]Kill [T]ail
- View options: [I]Status [O]Results
- ESC or Q exits

---

## ✅ COMPLETE TEST CHECKLIST

### Dashboard Core
- [ ] Dashboard launches without errors
- [ ] All 4 panels render correctly
- [ ] Status bar shows system check results
- [ ] Command bar displays all commands
- [ ] Auto-refresh countdown works
- [ ] Manual refresh (R) updates data

### Navigation
- [ ] All keyboard commands respond correctly
- [ ] Invalid keys show error message
- [ ] Key validation system working (✓/✗ indicators)
- [ ] Command history tracking (last 3 keys)
- [ ] ESC exits all modals

### Wallet Connection
- [ ] Initial status shows "Not connected"
- [ ] Press W opens browser correctly
- [ ] MetaMask connection page loads
- [ ] Connect button triggers MetaMask
- [ ] JSON file downloads automatically
- [ ] Dashboard detects connection (after refresh)
- [ ] Wallet panel updates with address
- [ ] Connection persists across restarts
- [ ] Disconnect (W again) works correctly

### Debug Terminal
- [ ] Press X opens debug terminal
- [ ] Live log shows action history
- [ ] Summary view shows statistics
- [ ] Errors view shows issues (or none)
- [ ] View switching (1/2/3) works
- [ ] ESC exits debug terminal

### Modals
- [ ] Help screen (H) opens and closes
- [ ] Seed browser (S) opens and closes
- [ ] Backtest control (B) opens and closes
- [ ] Debug terminal (X) opens and closes
- [ ] All modals respect ESC key

### Data Display
- [ ] Real SHA-256 seeds shown (not prefixes)
- [ ] All 5 timeframes represented
- [ ] Balance tracking shows progression
- [ ] Slot allocation displays correctly
- [ ] Paper trading progress (if session active)
- [ ] Performance stats by timeframe

### System Health
- [ ] System check passes on startup
- [ ] No errors in status bar (unless expected)
- [ ] Memory usage reasonable
- [ ] No crashes or freezes
- [ ] Clean exit with Q command

---

## 🚨 TROUBLESHOOTING

### Wallet Connection Issues

#### Browser doesn't open
**Possible causes:**
- Port 8765 blocked
- No default browser set

**Solutions:**
```bash
# Check if port is in use
lsof -i :8765

# Manually open URL
open http://localhost:8765/harvest_wallet_connect.html
```

#### MetaMask not detected
**Check:**
- MetaMask extension installed
- MetaMask unlocked
- Browser allows extensions on local pages

#### JSON doesn't download
**Check:**
- Browser download settings
- Pop-up blocker disabled
- Try different browser

#### Connection not detected
**Solutions:**
1. Press R to force refresh
2. Check Downloads folder for `harvest_wallet_response.json`
3. Manually move file to `/tmp/` directory
4. Restart dashboard

### Debug Terminal Issues

#### No logs showing
**Cause:** No actions performed yet  
**Solution:** Navigate dashboard, trigger some actions

#### Logs not updating
**Cause:** View frozen  
**Solution:** Press 1 to refresh live log view

### General Issues

#### Dashboard won't start
**Check:**
```bash
# Test Python version
python3 --version  # Should be 3.8+

# Test dependencies
pip3 list | grep rich

# Check for errors
python3 dashboard.py 2>&1 | grep -i error
```

#### Panels not rendering
**Check:**
- Terminal size (resize window)
- Color support (use modern terminal)
- Font supports Unicode

#### Keys not responding
**Check:**
- Terminal in focus
- No key conflicts with terminal emulator
- Check status bar for key validation

---

## 📝 TEST RESULTS TEMPLATE

```
# Dashboard Test Results
Date: _______________
Tester: _______________

## Core Functionality
- Dashboard Launch: ☐ Pass ☐ Fail
- 4-Panel Display: ☐ Pass ☐ Fail
- Status Bar: ☐ Pass ☐ Fail
- Command Bar: ☐ Pass ☐ Fail
- Auto-Refresh: ☐ Pass ☐ Fail

## Wallet Connection
- Browser Opens: ☐ Pass ☐ Fail
- MetaMask Connects: ☐ Pass ☐ Fail
- JSON Downloads: ☐ Pass ☐ Fail
- Dashboard Detects: ☐ Pass ☐ Fail
- Connection Persists: ☐ Pass ☐ Fail

## Debug Terminal
- Opens Correctly: ☐ Pass ☐ Fail
- Live Log Works: ☐ Pass ☐ Fail
- Summary Works: ☐ Pass ☐ Fail
- Errors Works: ☐ Pass ☐ Fail
- Closes Correctly: ☐ Pass ☐ Fail

## Modals
- Help Screen: ☐ Pass ☐ Fail
- Seed Browser: ☐ Pass ☐ Fail
- Backtest Control: ☐ Pass ☐ Fail
- ESC Exit: ☐ Pass ☐ Fail

## Overall Status
Status: ☐ All Pass ☐ Some Failures ☐ Major Issues

Notes:
_______________________________________
_______________________________________
_______________________________________
```

---

## 🎯 EXPECTED BEHAVIOR SUMMARY

### Wallet Connection Flow
1. **User presses W** → Browser opens to localhost:8765
2. **User clicks Connect** → MetaMask popup appears
3. **User approves** → JSON downloads automatically
4. **Dashboard refreshes** → Connection detected and displayed
5. **User restarts** → Connection persists

### Debug Terminal Flow
1. **User presses X** → Debug modal opens
2. **Logs populate** → Shows action history with validations
3. **User switches views** → 1/2/3 keys change views
4. **User presses ESC** → Returns to main dashboard

### Key Validation Flow
1. **User presses key** → System checks if valid
2. **Valid key** → Shows with ✓ in status bar
3. **Invalid key** → Shows with ✗ and error message
4. **History tracks** → Last 3 keys shown

---

**Testing Guide Complete** ✅  
**Ready for User Testing**

All features documented and ready to test. Follow the checklist systematically to verify all functionality.
