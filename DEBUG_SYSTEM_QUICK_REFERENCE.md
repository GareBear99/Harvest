# Debug System - Quick Reference Guide

**For Live Paper Trading Monitoring**

---

## Dashboard Commands

| Key | Action | Description |
|-----|--------|-------------|
| **X** | Debug Terminal | Open debug logging terminal |
| **R** | Refresh | Manual data refresh |
| **Q** | Quit | Exit dashboard (auto-saves session) |
| **H** | Help | Show help screen |
| **S** | Seeds | Browse seed database |
| **W** | Wallet | Connect/disconnect wallet |
| **B** | Backtest | Backtest controls |

---

## Debug Terminal (Press X)

### Views
- **1** - Live Action Log (real-time tracking)
- **2** - Session Summary (stats & health)
- **3** - Errors & Anomalies (troubleshooting)

### Navigation
- **↑/↓** - Page up/down (15 items per page)
- **Tab** - Cycle through sessions (current + last 2 historical)
- **ESC/Q** - Close debug terminal

---

## Status Bar Indicators

### Debug Stats
```
🐛 42A·0E·2W
   │  │  └─ Warnings (anomalies)
   │  └──── Errors (MUST be 0)
   └────── Actions logged
```

### Paper Trading
```
📄 Paper: 12.5/48h • 23T • +$45.67
          │       │     └─ P&L
          │       └────── Trades
          └───────────── Hours/Required
```

### Status Icons
- **ℹ️** Ready
- **⏳** Processing
- **✅** Success
- **❌** Failed

---

## Health Monitoring

### ✅ Healthy System
```
🐛 42A·0E·0W  📄 Paper: 12.5/48h • 23T • +$45.67
```
- Errors at 0 ✓
- Warnings low (<10) ✓
- Trading progressing ✓

### ⚠️ Warning Signs
```
🐛 156A·0E·15W  📄 Paper: 12.5/48h • 23T • -$12.34
```
- Warnings elevated (15) → Check anomalies (press X, then 3)
- Negative P&L → Normal during learning phase

### ❌ Critical Alert
```
🐛 89A·3E·5W  ❌ Operation failed: Wallet Connect
```
- Errors > 0 → IMMEDIATE REVIEW REQUIRED
- Press X to open debug terminal
- Review errors (press 3)
- Check failed action details

---

## Common Scenarios

### Scenario 1: First Launch
```
✅ Dashboard ready
🐛 6A·0E·0W  📄 Paper: 0.0/48h • 0T • +$0.00
```
**Action:** Normal startup, system check complete

### Scenario 2: Active Trading
```
⏳ Processing: Data Refresh
🐛 42A·0E·2W  📄 Paper: 8.5/48h • 15T • +$23.45
```
**Action:** System operating normally, 15 trades executed

### Scenario 3: Wallet Connection
```
⏳ Processing: Wallet Connect
🐛 48A·0E·0W
```
**Action:** Wait for MetaMask popup (browser should open)

### Scenario 4: Error Detected
```
❌ Wallet command failed
🐛 52A·2E·3W
```
**Action:**
1. Press **X** to open debug terminal
2. Press **3** to view errors
3. Check error messages for issue
4. Use Tab to review historical sessions

---

## Log File Locations

### Current Session
```
logs/debug_daemon/
├── actions_{session_id}.jsonl      # All actions
├── validations_{session_id}.jsonl  # Validations
├── errors_{session_id}.jsonl       # Errors only
```

### After Session Closes
```
logs/debug_daemon/
├── session_{session_id}_summary.json  # Final stats
```

**Note:** System keeps last 3 sessions automatically

---

## Troubleshooting

### Problem: Errors showing in status bar
**Solution:**
1. Press **X** to open debug terminal
2. Press **3** to view errors
3. Look for red ❌ entries with error messages
4. Note the action_id and timestamp
5. Check if retry resolved issue

### Problem: Operations timing out
**Look for:**
```
❌ Operation timeout: {operation}
elapsed_time: 35.5s > 30s threshold
```
**Solution:**
- Network issue (retry operation with R key)
- API rate limiting (wait 1 minute, try again)
- System overload (restart dashboard)

### Problem: Can't see recent actions
**Solution:**
- Actions shown in pages of 15
- Use ↑/↓ to navigate pages
- Check page indicator: "Page 2/5"
- Current page shows most recent by default

### Problem: Need to review old session
**Solution:**
1. Press **X** to open debug terminal
2. Press **Tab** to cycle sessions
3. Watch header: [Historical Session 2/3]
4. Review actions from that session
5. Press Tab again to return to current

---

## Best Practices

### During Paper Trading (First 48 Hours)

**Every 15 Minutes:**
- ✅ Check status bar: `🐛 XA·YE·ZW`
- ✅ Verify E (errors) = 0
- ✅ Monitor W (warnings) < 10

**Every Hour:**
- ✅ Press **X** to open debug terminal
- ✅ Press **2** for session summary
- ✅ Verify "HEALTHY" status
- ✅ Check validation success rates > 95%

**After Each Trade:**
- ✅ Look for ✅ success icon in status bar
- ✅ Confirm trade count increases
- ✅ Verify P&L updates

**End of Session:**
- ✅ Press **Q** to quit (auto-saves debug logs)
- ✅ Review `logs/debug_daemon/session_*_summary.json`
- ✅ Check for any anomalies

---

## Emergency Procedures

### If Errors Spike (E > 5)
1. **STOP** - Don't continue trading
2. Press **X**, then **3** to view all errors
3. Screenshot error messages
4. Press **Q** to quit dashboard
5. Review logs before restarting

### If System Unresponsive
1. Press **Q** to attempt graceful shutdown
2. If no response after 5 seconds, Ctrl+C
3. Check `logs/debug_daemon/` for last session
4. Review session summary for cause

### If Memory Warning
```
⚠️ Actions > 1000
```
1. Normal after 8+ hours of continuous operation
2. Press **Q** to quit
3. Restart dashboard
4. Session logs preserved automatically

---

## Quick Diagnostic Checklist

Before reporting issues, gather:

- [ ] Status bar snapshot: `🐛 XA·YE·ZW`
- [ ] Paper trading status: hours/trades/P&L
- [ ] Last operation shown
- [ ] Debug terminal view (press X)
- [ ] Error count and details (press 3 in debug terminal)
- [ ] Session ID from debug terminal
- [ ] Timestamp of issue

---

## Contact Information

**Log Location:** `/logs/debug_daemon/`  
**Session Format:** `session_{12_char_id}_summary.json`  
**Action Format:** `actions_{12_char_id}.jsonl`

**Include in reports:**
- Session ID (12 characters)
- Timestamp (ISO format)
- Action ID (A000XXX format)
- Error message (if any)

---

**Remember:** The debug system is always watching. Every action is logged. Every validation is checked. If something goes wrong, the logs will tell you exactly what happened and when. 🐛✅
