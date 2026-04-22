# User Testing Guide - Dashboard Enhancements

## Quick Start

### Launch Dashboard
```bash
cd /Users/TheRustySpoon/Desktop/Projects/Main\ projects/harvest
python3 run_dashboard.py
```

## What to Test

### 1. Status Bar (Bottom of Screen)

**What to look for:**
- Status bar should be visible at bottom
- Shows icon (ℹ️ ⏳ ✅ ❌) based on current state
- Displays your last keypress
- Shows ✓ (valid) or ✗ (invalid) indicator
- Displays command history

**Test steps:**
1. Launch dashboard
2. Look at bottom status bar - should show: `ℹ️  Dashboard ready. Press H for help.`
3. Press `H` - status should update to show `✅ Help screen opened │ Key: h ✓`
4. Press `x` (invalid) - should show `❌ Unknown command: 'x' - Press H for help │ Key: x ✗`
5. Press several valid commands - history should show last 3

### 2. Help Screen (Press H)

**What to look for:**
- Professional formatting with box characters
- 5 major sections:
  - Core Navigation
  - Main Features
  - Current System Status
  - Status Bar Guide
  - Tips & Tricks
- All commands documented with descriptions
- Exit instructions at bottom

**Test steps:**
1. Press `H` to open help
2. Scroll through content (should auto-fit screen)
3. Verify all sections present
4. Press `ESC` or `Q` to exit
5. Status bar should show: `✅ Closed help screen`

### 3. Command Validation

**Valid commands to test:**
- `Q` - Quit (should show exit message)
- `R` - Refresh (should show refresh in progress → success)
- `H` - Help (should open help screen)
- `ESC` - Exit modal (when in help/modal)
- `S` - Seeds browser (should open)
- `B` - Backtest control (should open)
- `W` - Wallet (should process)
- `D` - Documentation (should open browser)

**Invalid commands to test:**
- `X`, `Z`, `1`, `!` - Should show error with ✗ indicator

**Test steps:**
1. Try each valid command
2. Watch status bar update with ✓ indicator
3. Try invalid commands
4. Should see ✗ indicator and helpful error message

### 4. Modal Navigation

**Modals to test:**
- Help (H)
- Seed Browser (S)
- Backtest Control (B)

**Test steps:**
1. Open any modal (H, S, or B)
2. Status bar should remain visible at bottom
3. Press `ESC` to exit
4. Status bar should show success message
5. Should return to main dashboard

### 5. Command History

**Test steps:**
1. Press several keys in sequence: `h`, `s`, `r`, `x`, `q`
2. Watch status bar history section
3. Should show last 3 commands
4. Valid commands in green, invalid in red
5. History format: `Hist: q, x, r` (most recent first)

### 6. Operation Tracking

**Test steps:**
1. Press `R` to refresh
2. Watch status bar progression:
   - `⏳ Processing: Refresh`
   - `✅ Data refreshed successfully`
3. Try commands that might fail
4. Should see `❌` icon with error message

## Expected Behavior

### Status Bar States

#### Ready (Default)
```
ℹ️  Dashboard ready. Press H for help.
```

#### Processing
```
⏳ Processing: Refresh │ Key: r ✓ │ Op: Refresh
```

#### Success
```
✅ Data refreshed successfully │ Key: r ✓ │ Hist: r, h, s
```

#### Failed
```
❌ Unknown command: 'x' - Press H for help │ Key: x ✗
```

### Help Screen Content

Should include:
- ═══ separators for title/footer
- ┌─── box drawing for sections
- Command listings with [KEY] format
- Current system status (ML enabled/disabled, etc.)
- Status bar explanation
- Tips and tricks

## Troubleshooting

### Issue: Keys not registering
- Check terminal is in focus
- Try pressing keys more deliberately
- Status bar should update immediately

### Issue: Status bar not updating
- Verify you're looking at bottom of screen
- Check if panel is visible
- Try pressing `R` to force refresh

### Issue: Help screen not showing
- Press `H` again
- Check for error in status bar
- Try `ESC` first to clear any modal

### Issue: ESC not working
- Try pressing ESC key alone (not with other keys)
- Should work in all modals
- Status bar will confirm exit

## What Success Looks Like

✅ **Status bar visible and updating**
- Shows icons
- Validates commands
- Displays history
- Updates on every keypress

✅ **Help screen comprehensive**
- All 5 sections present
- Professional formatting
- Clear command descriptions
- Easy to read and navigate

✅ **Commands validated**
- Valid commands show ✓
- Invalid commands show ✗
- Error messages helpful
- History preserved

✅ **Modals work correctly**
- Open with keys (H, S, B)
- Exit with ESC or Q
- Status bar updates
- Return to dashboard

✅ **Operations tracked**
- Start → Processing → Success/Failed
- Clear status messages
- Error details when fails
- Icons match state

## Reporting Issues

If you find issues, note:
1. What command you pressed
2. What status bar showed
3. Expected vs actual behavior
4. Screenshot if helpful

## Running Automated Tests

Validate everything works:
```bash
# Full validation suite
python3 validate_enhancements.py

# Status tracking only
python3 test_status_tracking.py

# Help screen only
python3 dashboard/help_screen.py
```

All tests should show ✅ PASSED.

## Documentation Reference

For detailed information:
- `STATUS_BAR_GUIDE.md` - Complete status bar documentation
- `DASHBOARD_ENHANCEMENTS_SUMMARY.md` - Full change summary
- Help screen (press H in dashboard) - Quick reference

## Summary

The enhanced dashboard provides:
- **Real-time feedback** on every keypress
- **Command validation** with clear indicators
- **Comprehensive help** with all features documented
- **Operation tracking** from start to completion
- **Error reporting** with helpful messages
- **Command history** showing recent actions

Test all features and verify they work as expected!
