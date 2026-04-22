# MetaMask Integration Setup Guide

**HARVEST Trading System - ETH Wallet Connection**

---

## 🦊 Overview

The HARVEST system now supports direct integration with MetaMask for on-chain ETH trading. This allows you to:

- Connect your MetaMask wallet
- Check ETH balance
- Execute on-chain transactions
- Monitor gas prices
- Track transaction status

---

## 📦 Installation

### 1. Install Web3 Dependencies

```bash
pip install web3>=6.11.0
```

Or update all requirements:

```bash
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python3 -c "import web3; print('Web3 version:', web3.__version__)"
```

---

## 🔐 Security Setup

### **CRITICAL: Protect Your Private Keys**

⚠️ **NEVER commit private keys to git**  
⚠️ **NEVER share private keys**  
⚠️ **NEVER hard-code private keys**

### Setting Up Environment Variables

```bash
# Add to your ~/.bashrc or ~/.zshrc

# For Ethereum Mainnet (via Infura)
export ETH_RPC_URL='https://mainnet.infura.io/v3/YOUR-PROJECT-ID'

# For local development (Ganache)
# export ETH_RPC_URL='http://127.0.0.1:8545'

# Your MetaMask private key (KEEP SECRET!)
export ETH_PRIVATE_KEY='0xYOUR_PRIVATE_KEY_HERE'
```

Then reload your shell:

```bash
source ~/.bashrc  # or source ~/.zshrc
```

---

## 🌐 RPC Endpoint Options

### Option 1: Infura (Recommended for Production)

1. Go to [infura.io](https://infura.io)
2. Create free account
3. Create new project
4. Copy your project ID
5. Use: `https://mainnet.infura.io/v3/YOUR-PROJECT-ID`

### Option 2: Alchemy

1. Go to [alchemy.com](https://alchemy.com)
2. Create free account
3. Create new app
4. Copy your HTTP URL
5. Use: `https://eth-mainnet.g.alchemy.com/v2/YOUR-API-KEY`

### Option 3: Local Node (Advanced)

```bash
# Run local Ethereum node
geth --http --http.api eth,net,web3
```

Use: `http://127.0.0.1:8545`

### Option 4: Ganache (Testing)

```bash
# Install Ganache
npm install -g ganache

# Run Ganache
ganache --port 8545
```

Use: `http://127.0.0.1:8545`

---

## 🔑 Getting Your MetaMask Private Key

### **⚠️ WARNING: Exposing your private key gives full access to your wallet!**

**Only do this for:**
- Testing accounts with small amounts
- Development/testnet wallets
- Accounts you create specifically for trading

**Steps:**

1. Open MetaMask in Chrome
2. Click the three dots menu
3. Select "Account Details"
4. Click "Export Private Key"
5. Enter your MetaMask password
6. Copy the private key (starts with `0x`)

**IMMEDIATELY:**
- Store it in environment variable
- Never paste it in code
- Never commit it to git
- Consider using a separate trading account

---

## 🧪 Testing the Connection

### Test Script

```bash
python3 core/metamask_connector.py
```

Expected output:

```
======================================================================
HARVEST MetaMask Connector Test
======================================================================

📡 RPC URL: https://mainnet.infura.io/v3/...

🔌 Connecting to Ethereum network...
✅ Connected to Ethereum network
Chain ID: 1
Latest block: 18000000

✅ Connected successfully!

💰 Checking balance...
Address: 0xYourAddress...
Balance: 1.234567 ETH

⛽ Current gas prices:
  Slow: 25.00 Gwei
  Standard: 30.00 Gwei
  Fast: 35.00 Gwei
  Rapid: 45.00 Gwei

✅ MetaMask connector test complete
```

---

## 💻 Usage Examples

### Example 1: Check Balance

```python
from core.metamask_connector import setup_metamask_connection

# Connect
connector = setup_metamask_connection()

if connector and connector.account:
    balance = connector.get_eth_balance()
    print(f"Balance: {balance:.6f} ETH")
```

### Example 2: Send ETH

```python
from core.metamask_connector import setup_metamask_connection
from decimal import Decimal

# Connect
connector = setup_metamask_connection()

# Send 0.01 ETH
tx_hash = connector.send_eth(
    to_address='0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
    amount_eth=Decimal('0.01')
)

if tx_hash:
    print(f"Transaction sent: {tx_hash}")
    
    # Wait for confirmation
    receipt = connector.wait_for_transaction(tx_hash)
    
    if receipt and receipt['status'] == 1:
        print("✅ Transaction confirmed!")
    else:
        print("❌ Transaction failed")
```

### Example 3: Check Gas Prices

```python
from core.metamask_connector import setup_metamask_connection

connector = setup_metamask_connection()

gas_prices = connector.get_gas_price()

for speed, price_wei in gas_prices.items():
    gwei = price_wei / 10**9
    print(f"{speed}: {gwei:.2f} Gwei")
```

### Example 4: Monitor Transaction

```python
from core.metamask_connector import setup_metamask_connection

connector = setup_metamask_connection()

tx_hash = "0x..."  # Your transaction hash

status = connector.get_transaction_status(tx_hash)

print(f"Status: {status['status']}")
print(f"From: {status['from']}")
print(f"To: {status['to']}")
print(f"Value: {status['value']} ETH")
```

---

## 🔗 Integration with HARVEST

### Using MetaMask with Live Trading

The live trading daemon can be configured to use MetaMask for on-chain execution:

```python
# In live_trader.py
from core.metamask_connector import setup_metamask_connection

# Initialize MetaMask
metamask = setup_metamask_connection()

if metamask:
    print(f"Connected to wallet: {metamask.account.address}")
    balance = metamask.get_eth_balance()
    print(f"Balance: {balance:.6f} ETH")
```

---

## 🌍 Network Configurations

### Ethereum Mainnet

```bash
export ETH_RPC_URL='https://mainnet.infura.io/v3/YOUR-PROJECT-ID'
# Chain ID: 1
```

### Sepolia Testnet

```bash
export ETH_RPC_URL='https://sepolia.infura.io/v3/YOUR-PROJECT-ID'
# Chain ID: 11155111
```

### Goerli Testnet (Deprecated)

```bash
export ETH_RPC_URL='https://goerli.infura.io/v3/YOUR-PROJECT-ID'
# Chain ID: 5
```

### Polygon (MATIC)

```bash
export ETH_RPC_URL='https://polygon-rpc.com'
# Chain ID: 137
```

---

## 🛡️ Security Best Practices

### 1. Use Separate Trading Account

Create a dedicated MetaMask account for trading:
- Transfer only what you need
- Keep main holdings in separate wallet
- Use hardware wallet for large amounts

### 2. Environment Variables

```bash
# ~/.bashrc or ~/.zshrc
export ETH_RPC_URL='...'
export ETH_PRIVATE_KEY='...'

# Make file readable only by you
chmod 600 ~/.bashrc
```

### 3. .gitignore

Ensure these are in `.gitignore`:

```
.env
.env.local
*.key
private_keys/
```

### 4. Test on Testnet First

Always test with testnet ETH before using mainnet:

1. Get testnet ETH from faucet
2. Test all transactions
3. Verify everything works
4. Then switch to mainnet

---

## 🧪 Testing on Sepolia Testnet

### 1. Get Testnet ETH

- [Sepolia Faucet](https://sepoliafaucet.com/)
- [Alchemy Sepolia Faucet](https://sepoliafaucet.com/)

### 2. Configure for Sepolia

```python
from core.metamask_connector import setup_metamask_connection

connector = setup_metamask_connection(
    chain_id=11155111  # Sepolia
)
```

### 3. Test Transactions

Use testnet ETH to test all functionality before mainnet.

---

## 📊 Gas Optimization

### Understanding Gas

- **Gas Limit**: Maximum gas units for transaction
- **Gas Price**: Price per gas unit (in Gwei)
- **Total Cost**: Gas Limit × Gas Price

### Estimating Costs

```python
gas_prices = connector.get_gas_price()

# Simple transfer costs ~21,000 gas
gas_limit = 21000

for speed, price_wei in gas_prices.items():
    cost_wei = gas_limit * price_wei
    cost_eth = cost_wei / 10**18
    print(f"{speed}: {cost_eth:.6f} ETH")
```

### When to Trade

- **Low gas**: Night time UTC (2-6 AM)
- **High gas**: Business hours UTC (12-4 PM)
- Monitor: [ETH Gas Station](https://ethgasstation.info/)

---

## 🐛 Troubleshooting

### Error: "Not connected to Ethereum network"

**Solution:**
```bash
# Check RPC URL is set
echo $ETH_RPC_URL

# Test connection
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  $ETH_RPC_URL
```

### Error: "Insufficient funds"

**Solution:**
- Check balance: `connector.get_eth_balance()`
- Ensure you have ETH for gas fees
- Gas costs typically 0.001-0.01 ETH

### Error: "Nonce too low"

**Solution:**
```python
# Get current nonce
nonce = connector.w3.eth.get_transaction_count(connector.account.address)
print(f"Current nonce: {nonce}")
```

### Error: "Transaction underpriced"

**Solution:**
```python
# Use higher gas price
gas_prices = connector.get_gas_price()
tx_hash = connector.send_eth(
    to_address='0x...',
    amount_eth=Decimal('0.01'),
    gas_price=gas_prices['fast']  # Use fast instead of standard
)
```

---

## 📚 Additional Resources

### Documentation
- [Web3.py Docs](https://web3py.readthedocs.io/)
- [Ethereum JSON-RPC API](https://ethereum.org/en/developers/docs/apis/json-rpc/)
- [MetaMask Docs](https://docs.metamask.io/)

### Tools
- [Etherscan](https://etherscan.io/) - Transaction explorer
- [ETH Gas Station](https://ethgasstation.info/) - Gas prices
- [Infura](https://infura.io/) - RPC endpoints
- [Alchemy](https://alchemy.com/) - RPC endpoints

### Testing
- [Sepolia Faucet](https://sepoliafaucet.com/)
- [Ganache](https://trufflesuite.com/ganache/) - Local blockchain

---

## ⚠️ Important Warnings

1. **Private Keys**: Never share, commit, or expose
2. **Testnet First**: Always test before mainnet
3. **Gas Costs**: Can be expensive during high usage
4. **Irreversible**: Blockchain transactions cannot be undone
5. **Security**: Use hardware wallet for large amounts
6. **Scams**: Verify all addresses carefully

---

## 🚀 Quick Start Checklist

- [ ] Install web3.py: `pip install web3`
- [ ] Create Infura account and get project ID
- [ ] Set ETH_RPC_URL environment variable
- [ ] Export MetaMask private key (test account only!)
- [ ] Set ETH_PRIVATE_KEY environment variable
- [ ] Test connection: `python3 core/metamask_connector.py`
- [ ] Verify balance shows correctly
- [ ] Test on Sepolia testnet first
- [ ] Ready for mainnet trading

---

## 💡 Tips

1. **Start Small**: Test with small amounts first
2. **Monitor Gas**: Check gas prices before trading
3. **Set Limits**: Use stop losses and take profits
4. **Track Transactions**: Save all transaction hashes
5. **Backup Keys**: Store private keys securely offline

---

**🎉 You're now ready to use HARVEST with MetaMask!**

For questions or issues, see the main [README_FINAL.md](README_FINAL.md) or check the inline code documentation in `core/metamask_connector.py`.

---

**⚠️ FINAL REMINDER: This system executes real blockchain transactions with real money. Always test thoroughly on testnet before using mainnet. Trade responsibly!**
