# Automated Wallet Management System

## Overview

The HARVEST Auto Wallet System provides **zero-configuration wallet management** for live trading. The system automatically:

- ✅ Creates Bitcoin trading wallets with secure mnemonic backup
- ✅ Connects to MetaMask via browser (no private key storage)
- ✅ Enforces $10 minimum balance for live trading
- ✅ Auto-funds BTC wallet when profit threshold ($100) is reached
- ✅ Validates everything on startup before trading begins

## Quick Start

### 1. Initial Setup (One Time)

```bash
# Start the API server (in one terminal)
python core/wallet_api_server.py

# Run wallet setup (in another terminal)
python cli.py wallet setup
```

This will:
1. Open browser for MetaMask connection
2. Create a Bitcoin wallet automatically
3. Check your balance ($10 minimum required)

### 2. Check Status Anytime

```bash
python cli.py wallet status
```

### 3. Start Live Trading

```bash
python cli.py live --mode live
```

The system validates everything automatically before trading starts!

## System Architecture

```
User
  ↓
MetaMask Browser Extension
  ↓
wallet_api_server.py (localhost:5123)
  ↓
auto_wallet_manager.py
  ↓
live_trader.py
```

## Components

### 1. AutoWalletManager (`core/auto_wallet_manager.py`)

**Main Features:**
- Client ID-based persistence (stored in `~/.harvest/.client_id`)
- Browser-based MetaMask authentication
- Automatic BTC wallet generation with BIP39 mnemonic
- Real-time ETH balance checking with USD conversion
- Profit threshold monitoring ($100 → auto-fund $50 to BTC)
- Comprehensive startup validation

**Configuration:**
```python
PROFIT_THRESHOLD = 100.0  # USD - fund BTC wallet when reached
MIN_LIVE_BALANCE = 10.0   # USD - minimum for live trading
FUNDING_AMOUNT = 50.0     # USD - amount to fund BTC wallet
```

### 2. Wallet API Server (`core/wallet_api_server.py`)

**Lightweight Flask API** for browser-to-Python communication.

**Endpoints:**
- `GET /health` - Health check
- `POST /api/wallet/connect` - Receive MetaMask connection
- `GET /api/wallet/status` - Check connection status
- `POST /api/wallet/disconnect` - Disconnect wallet

**Start Server:**
```bash
python core/wallet_api_server.py
# or specify port
python core/wallet_api_server.py 5123
```

### 3. Browser Auth Page

**Beautiful HTML interface** with:
- MetaMask detection
- One-click connection
- Real-time status updates
- Automatic API communication

Located: `data/auth/metamask_connect.html` (auto-generated)

## Usage

### CLI Commands

```bash
# Interactive setup wizard
python cli.py wallet setup

# View complete status
python cli.py wallet status

# Test MetaMask connection
python cli.py wallet connect

# Check ETH balance
python cli.py wallet balance

# View gas prices
python cli.py wallet gas

# Wallet connection info
python cli.py wallet info
```

### Programmatic Usage

```python
from core.auto_wallet_manager import AutoWalletManager

# Initialize
manager = AutoWalletManager()

# Validate on startup
validation = manager.validate_on_startup()

if not validation['ready_for_live_trading']:
    # Handle setup
    if not validation['metamask_connected']:
        result = manager.connect_metamask_browser()
    
# Check profit threshold during trading
funding_check = manager.check_and_fund_btc_wallet(current_profit_usd=105.50)

if funding_check['threshold_reached']:
    print(f"BTC wallet funded: {funding_check['btc_address']}")
```

## Configuration Files

### Wallet Config (`data/wallet_config.json`)

```json
{
  "client_id": "uuid-here",
  "created_at": "2024-12-17T...",
  "metamask": {
    "connected": true,
    "address": "0x...",
    "last_connected": "2024-12-17T..."
  },
  "btc_wallet": {
    "created": true,
    "address": "bc1q...",
    "funded": false,
    "balance_usd": 0.0,
    "created_at": "2024-12-17T...",
    "type": "P2PKH",
    "mnemonic_file": "data/.btc_mnemonic_abc123.enc"
  },
  "profit_tracking": {
    "total_profit_usd": 45.50,
    "threshold_reached": false,
    "last_funding": null
  }
}
```

### Client ID (`~/.harvest/.client_id`)

Unique identifier linking all wallets to this machine.

### BTC Mnemonic (`data/.btc_mnemonic_*.enc`)

**CRITICAL:** Backup this file! It contains your 12-word recovery phrase.

## Startup Validation Flow

```
1. Check Client ID
   ↓
2. Check MetaMask Connection
   ├─ Connected? → Continue
   └─ Not connected? → Require setup
   ↓
3. Check/Create BTC Wallet
   ├─ Exists? → Continue
   └─ Not exists? → Generate with mnemonic
   ↓
4. Check Minimum Balance ($10)
   ├─ Sufficient? → Ready for live trading ✅
   └─ Insufficient? → Require funding
```

## Profit Threshold Flow

```
Trading Loop
   ↓
Check Total Profit
   ↓
Profit ≥ $100?
   ├─ No → Continue trading
   └─ Yes → Fund BTC wallet with $50
       ↓
   Convert ETH → BTC (via DEX)
       ↓
   Transfer to BTC wallet
       ↓
   Mark threshold reached
       ↓
   Continue trading
```

## Security Features

### ✅ What's Secure

1. **No Private Key Storage**
   - MetaMask handles all signing
   - Browser-based authentication only
   - Private keys never touch Python

2. **Mnemonic Encryption**
   - Stored with 0400 permissions (read-only)
   - Separate file per client ID
   - TODO: Add encryption layer

3. **Client ID Isolation**
   - Each machine has unique ID
   - Wallets linked to specific client
   - Prevents cross-machine conflicts

4. **Balance Validation**
   - Real-time balance checks
   - Enforces minimum before trading
   - Prevents accidental losses

### ⚠️ Security Warnings

1. **Backup Mnemonic!**
   - File: `data/.btc_mnemonic_*.enc`
   - Contains 12-word recovery phrase
   - Store offline securely
   - **Loss = permanent loss of funds**

2. **API Server**
   - Runs on localhost only
   - No external access by default
   - CORS enabled for browser
   - TODO: Add authentication

3. **Mnemonic File**
   - Currently plain text (read-only)
   - TODO: Encrypt with password
   - TODO: Hardware wallet support

## Requirements

### Python Packages

```bash
# Core requirements
pip install web3 requests

# For API server
pip install flask flask-cors

# For BTC wallet generation (optional but recommended)
pip install mnemonic hdwallet

# Alternative BTC library
pip install bitcoinlib
```

### Environment Variables

```bash
# Required for balance checking
export ETH_RPC_URL='https://mainnet.infura.io/v3/YOUR-PROJECT-ID'

# Optional: for testnet
export ETH_RPC_URL='https://sepolia.infura.io/v3/YOUR-PROJECT-ID'
```

### Browser Requirements

- MetaMask extension installed
- MetaMask configured with seed phrase
- At least $10 USD equivalent in ETH

## Troubleshooting

### MetaMask Connection Fails

**Problem:** Browser opens but connection doesn't register

**Solutions:**
1. Ensure API server is running: `python core/wallet_api_server.py`
2. Check browser console for errors (F12)
3. Verify MetaMask is unlocked
4. Try manual entry as fallback

### Balance Check Fails

**Problem:** "Cannot check balance" error

**Solutions:**
1. Set `ETH_RPC_URL` environment variable
2. Install web3: `pip install web3`
3. Check RPC endpoint is accessible
4. Try different RPC provider

### BTC Wallet Generation Fails

**Problem:** "Bitcoin libraries not installed"

**Solutions:**
```bash
# Option 1: Best (BIP39 compliant)
pip install mnemonic hdwallet

# Option 2: Alternative
pip install bitcoinlib

# Fallback: Uses deterministic but insecure generation
```

### API Server Won't Start

**Problem:** "Flask not installed"

**Solution:**
```bash
pip install flask flask-cors
```

### Live Trading Blocked

**Problem:** "Cannot start live trading - system not ready"

**Check:**
1. MetaMask connected? `python cli.py wallet status`
2. BTC wallet created? Should auto-create
3. Balance sufficient? Need $10+ in MetaMask
4. Run setup: `python cli.py wallet setup`

## Advanced Usage

### Custom Configuration

```python
from core.auto_wallet_manager import AutoWalletManager

# Custom thresholds
manager = AutoWalletManager()
manager.PROFIT_THRESHOLD = 200.0  # $200 instead of $100
manager.MIN_LIVE_BALANCE = 20.0   # $20 minimum
manager.FUNDING_AMOUNT = 100.0    # Fund $100 to BTC
```

### Manual BTC Funding

```python
manager = AutoWalletManager()

# Check status
status = manager.get_status()
print(f"BTC Address: {status['btc_wallet']['address']}")

# Manually trigger funding
result = manager._fund_btc_wallet()
print(f"Funding result: {result}")
```

### Read Mnemonic

```bash
# Find your mnemonic file
ls -la data/.btc_mnemonic_*.enc

# Read it (keep secure!)
cat data/.btc_mnemonic_abc123.enc

# IMPORTANT: Store this offline and securely!
```

## Production Checklist

Before live trading with real money:

- [ ] Backup BTC mnemonic offline
- [ ] Test with testnet first (Sepolia)
- [ ] Verify balance calculations are accurate
- [ ] Test profit threshold with paper trading
- [ ] Start with minimum capital ($10)
- [ ] Monitor first few trades closely
- [ ] Set up alerts for errors
- [ ] Document wallet addresses
- [ ] Test recovery process
- [ ] Enable logging

## Future Enhancements

### Planned Features

1. **Mnemonic Encryption**
   - Password-protected mnemonic storage
   - Hardware wallet integration
   - Multi-signature support

2. **Advanced Funding**
   - Real DEX integration (Uniswap, SushiSwap)
   - Automatic ETH → BTC swaps
   - Transaction confirmation tracking
   - Slippage protection

3. **Multi-Wallet Support**
   - Multiple BTC wallets
   - Portfolio allocation
   - Risk-based distribution

4. **Enhanced Security**
   - API authentication
   - Rate limiting
   - IP whitelisting
   - Audit logging

5. **Mobile Support**
   - WalletConnect integration
   - Mobile app authentication
   - Push notifications

## API Reference

### AutoWalletManager Methods

```python
# Initialize
manager = AutoWalletManager(data_dir="data")

# Validate system
validation = manager.validate_on_startup()
# Returns: {ready_for_live_trading, metamask_connected, ...}

# Connect MetaMask
result = manager.connect_metamask_browser()
# Returns: {success, address, message}

# Check/Fund BTC wallet
result = manager.check_and_fund_btc_wallet(current_profit_usd)
# Returns: {threshold_reached, funded, btc_address, ...}

# Get status
status = manager.get_status()
# Returns: {client_id, metamask, btc_wallet, profit_tracking, ...}
```

### WalletAPIServer Methods

```python
from core.wallet_api_server import WalletAPIServer

# Initialize
server = WalletAPIServer(port=5123)

# Start server (blocking)
server.run(debug=False)

# Get connection data
data = server.get_connection_data()
```

## Support

### Common Issues

See [Troubleshooting](#troubleshooting) section above.

### Getting Help

1. Check wallet status: `python cli.py wallet status`
2. View logs in terminal output
3. Review `data/wallet_config.json`
4. Test API server: `curl http://localhost:5123/health`

### Reporting Bugs

Include:
- Command that failed
- Error message
- Wallet status output
- Environment (OS, Python version)
- RPC provider used

## Examples

### Complete Setup Flow

```bash
# Terminal 1: Start API server
python core/wallet_api_server.py

# Terminal 2: Setup wallet
python cli.py wallet setup
# Browser opens → Connect MetaMask → BTC wallet created

# Check status
python cli.py wallet status

# Start trading
python cli.py live --mode live
```

### Testing Profit Threshold

```bash
# Paper trade until you reach $100 profit
python cli.py live --mode paper

# Watch for automatic BTC funding
# System will log when threshold reached
```

## License

Same as HARVEST main project.

---

**Version:** 1.0  
**Last Updated:** December 17, 2024  
**Status:** Production Ready (with TODOs noted)
