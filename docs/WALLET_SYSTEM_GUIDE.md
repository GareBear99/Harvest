# HARVEST Wallet System - Complete Guide

**Date**: December 18, 2024  
**Status**: ✅ Implemented and Ready

---

## 🔑 Overview

HARVEST uses a **dual-wallet system** for live trading:

1. **MetaMask Wallet** (Ethereum) - For founder fee payments
2. **BTC Trading Wallet** (Bitcoin) - For actual trading (auto-created)

**Important**: HARVEST does NOT use MetaMask directly for trading. It uses an auto-generated BTC wallet that is created on first run.

---

## 📊 Wallet Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    HARVEST Wallet System                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. MetaMask (ETH) - Browser Connection                     │
│     - Used for: Founder fee payments only                   │
│     - Connected via: Browser authentication                 │
│     - Stored: Address only (no private keys)                │
│     - Minimum: $10 USD equivalent for live trading          │
│                                                              │
│  2. BTC Trading Wallet - Auto-Generated                     │
│     - Used for: All trading operations                      │
│     - Created: Automatically on first run                   │
│     - Stored: BIP39 mnemonic (encrypted)                    │
│     - Type: P2PKH (Legacy Bitcoin address)                  │
│     - Funded: Automatically at $100 profit threshold        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 How It Works

### Phase 1: System Initialization ($0-$10)

**First Run**:
1. System generates unique Client ID
2. Creates wallet configuration file
3. Shows "Not ready for live trading" status

**What You Need**:
- Nothing yet - can start with paper trading/backtests

### Phase 2: Live Trading Setup ($10+)

**When you're ready for live trading**:

1. **Connect MetaMask** (for founder fees):
   ```bash
   # Dashboard will prompt or use command:
   python -c "from core.auto_wallet_manager import AutoWalletManager; \
              manager = AutoWalletManager(); \
              manager.connect_metamask_browser()"
   ```
   - Opens browser window
   - Click "Connect MetaMask"
   - Approve connection
   - Address saved automatically

2. **BTC Wallet Created Automatically**:
   - System generates secure BIP39 mnemonic
   - Creates Bitcoin address
   - Saves mnemonic to encrypted file
   - **YOU MUST BACKUP THIS MNEMONIC!**

3. **Fund MetaMask**:
   - Send minimum $10 USD equivalent in ETH
   - System validates balance via Web3
   - Must maintain minimum for live trading

### Phase 3: Trading & Fee Payments ($100+)

**At $100 Balance** (founder fee activation):
- First $10 fee becomes due at $110
- Send $10 in ETH to founder address via MetaMask
- Copy transaction hash
- System verifies on blockchain
- Position tier 2 unlocks (20 slots)

**At $210 Balance**:
- Second $10 fee due
- Repeat payment process
- Position tier 3 unlocks (30 slots MAXED)

**Every $100 profit thereafter**:
- Additional $10 fees due
- System stays at tier 3 (maxed)

---

## 🔐 Security & Storage

### Where Data is Stored

**Client ID**:
```
~/.harvest/.client_id
```
- Persistent unique identifier
- Never changes
- Used for wallet association

**Wallet Configuration**:
```
data/wallet_config.json
```
Contains:
- MetaMask address (NOT private key)
- BTC wallet address
- Connection status
- Balance tracking

**BTC Mnemonic** (CRITICAL):
```
data/.btc_mnemonic_<client_id>.enc
```
- 12-word BIP39 recovery phrase
- File permissions: Read-only (400)
- **BACKUP THIS FILE IMMEDIATELY**
- Needed to recover BTC wallet

### What's NOT Stored

❌ MetaMask private keys (you keep these in MetaMask)  
❌ MetaMask seed phrase  
❌ Passwords or passphrases  
❌ API keys in plain text

---

## ✅ Validation System

### Startup Validation

When dashboard launches, system checks:

1. **Client ID exists** ✅
   - Creates if missing
   - Links all wallets to this ID

2. **MetaMask connection** 🔍
   - Checks if previously connected
   - Verifies address stored
   - Tests Web3 connection (if RPC URL set)

3. **BTC wallet exists** 🔍
   - Creates if missing
   - Generates secure mnemonic
   - Saves address

4. **Balance check** 💰
   - Queries MetaMask balance via Web3
   - Converts ETH to USD
   - Validates minimum $10 for live trading

5. **Ready status** 🚀
   - All checks pass = Ready for live trading
   - Any fail = Shows required actions

### Balance Verification Process

**For founder fee payments**:
1. You send $10 ETH to founder address via MetaMask
2. Copy transaction hash from MetaMask
3. Call: `manager.confirm_fee_sent(tx_hash)`
4. System queries Ethereum blockchain
5. Verifies transaction:
   - Correct sender (your MetaMask)
   - Correct recipient (founder address)
   - Correct amount ($10 in ETH)
   - Transaction confirmed (min blocks)
6. If valid: Unlocks next position tier
7. If invalid: Shows error, tier stays locked

**Blockchain Verification**:
- Uses Web3.py to connect to Ethereum node
- Reads transaction data directly from blockchain
- Confirms via consensus (multiple blocks)
- No centralized validation needed

---

## 📱 Dashboard Display

### Wallet Panel Shows

**MetaMask Status**:
- ✅ Connected: `0x1234...5678`
- ❌ Not connected: "Click [W] to connect"

**BTC Wallet Status**:
- ✅ Created: `1A2B...3C4D`
- ⏳ Creating: "Generating secure wallet..."
- 💰 Funded: Shows balance

**Position Limits** (based on founder fees):
- Current tier (0/1/2)
- Positions per TF/asset (1/2/3)
- Total slots (10/20/30)
- Next fee threshold

**Capital & Profit**:
- Current balance
- Total profit
- Distance to next fee

---

## 🚀 Quick Start Commands

### Check Wallet Status
```bash
python check_wallet_status.py
```

### Connect MetaMask
```bash
python -c "from core.auto_wallet_manager import AutoWalletManager; \
           manager = AutoWalletManager(); \
           result = manager.connect_metamask_browser(); \
           print(result)"
```

### Validate System
```bash
python -c "from core.auto_wallet_manager import AutoWalletManager; \
           manager = AutoWalletManager(); \
           status = manager.validate_on_startup(); \
           print(status)"
```

### View BTC Wallet
```bash
cat data/wallet_config.json | grep -A5 btc_wallet
```

### Backup Mnemonic
```bash
# CRITICAL - Do this immediately after wallet creation
cp data/.btc_mnemonic_*.enc ~/safe_backup_location/
```

---

## ⚠️ Important Notes

### MetaMask vs Trading Wallet

**Common Misconception**: "I need to import my MetaMask wallet into HARVEST"

**Reality**:
- MetaMask is ONLY for fee payments
- Trading happens in separate BTC wallet
- NEVER share your MetaMask private key
- NEVER import MetaMask into any system

### Backtest Mode

In backtest mode (default):
- NO wallet connection needed
- NO MetaMask required
- NO fees collected
- Tiers upgrade automatically based on balance milestones

### Paper Trading Mode

For paper trading (test mode):
- MetaMask connection recommended (to test integration)
- BTC wallet created automatically
- NO real money used
- Simulates fee payments

### Live Trading Mode

**Requirements**:
- ✅ MetaMask connected
- ✅ BTC wallet created
- ✅ Minimum $10 in MetaMask
- ✅ All startup validations pass

---

## 🔧 Troubleshooting

### "MetaMask not connected"

**Check**:
1. Run `python check_wallet_status.py`
2. Look for "MetaMask Connection: Connected"
3. If disconnected, run connect command
4. Browser window should open
5. Click "Connect MetaMask" and approve

### "BTC wallet not found"

**Solution**:
- System creates automatically on first run
- Check `data/wallet_config.json`
- Look for `btc_wallet.created: true`
- If missing, run validation: `manager.validate_on_startup()`

### "Insufficient balance"

**Check**:
1. MetaMask has minimum $10 USD in ETH
2. RPC URL is set: `echo $ETH_RPC_URL`
3. Web3 can connect to network
4. Try manual balance check

### "Transaction not confirmed"

**When paying founder fees**:
1. Wait for blockchain confirmation (1-2 minutes)
2. Check transaction on Etherscan
3. Verify correct amount sent
4. Verify correct recipient address
5. Re-run `confirm_fee_sent(tx_hash)` after confirmation

---

## 📋 Pre-Flight Checklist

### Before Live Trading

- [ ] Client ID generated (check `~/.harvest/.client_id`)
- [ ] MetaMask wallet connected (address shown in dashboard)
- [ ] MetaMask funded with $10+ USD equivalent
- [ ] BTC wallet created (address shown in dashboard)
- [ ] BTC mnemonic backed up securely
- [ ] Web3 RPC URL configured (`ETH_RPC_URL` env var)
- [ ] Dashboard shows "Ready for live trading"
- [ ] Test wallet connection with small amount first

### Before First Fee Payment ($110)

- [ ] Balance reached $110
- [ ] Dashboard shows "Fee due"
- [ ] MetaMask has $10+ for fee payment
- [ ] Founder address verified in system
- [ ] Ready to copy transaction hash
- [ ] Know how to call `confirm_fee_sent()`

---

## 🎯 Summary

### What HARVEST Does

✅ **Generates** secure BTC trading wallet automatically  
✅ **Connects** to your MetaMask for fee payments only  
✅ **Validates** balances via blockchain  
✅ **Verifies** founder fee transactions on-chain  
✅ **Unlocks** position tiers after fee confirmation  
✅ **Displays** wallet status in dashboard  

### What You Need to Do

1. **Connect MetaMask** when ready for live trading
2. **Fund MetaMask** with minimum $10 USD
3. **Backup BTC mnemonic** immediately after creation
4. **Pay founder fees** at $110, $210, etc.
5. **Confirm transactions** by providing tx hash

### What You DON'T Need

❌ Import MetaMask private key  
❌ Share seed phrases with HARVEST  
❌ Install blockchain node locally  
❌ Manage wallet files manually  
❌ Calculate fees manually  

---

**System Status**: ✅ Wallet system fully implemented and ready for live trading

**Next Steps**: Connect MetaMask when you're ready to go live with real money!
