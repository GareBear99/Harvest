# Wallet Connect - Quick Start

## ⚡ TL;DR

```bash
# Set your RPC endpoint
export ETH_RPC_URL='https://mainnet.infura.io/v3/YOUR-PROJECT-ID'

# Optional: Add private key for transactions (KEEP SECRET!)
export ETH_PRIVATE_KEY='0xYOUR_PRIVATE_KEY'

# Connect!
python cli.py wallet connect
```

## 📋 Command Options

```bash
# Basic connection (uses environment variables)
python cli.py wallet connect

# Specify RPC URL directly
python cli.py wallet connect --rpc-url https://eth-mainnet.g.alchemy.com/v2/YOUR-KEY

# Connect to testnet
python cli.py wallet connect --testnet

# Connect to specific chain
python cli.py wallet connect --chain-id 137  # Polygon
```

## 🌐 Popular RPC Providers

| Provider | Free Tier | URL Format |
|----------|-----------|------------|
| **Infura** | 100K req/day | `https://mainnet.infura.io/v3/YOUR-KEY` |
| **Alchemy** | 300M CU/month | `https://eth-mainnet.g.alchemy.com/v2/YOUR-KEY` |
| **Ankr** | Limited | `https://rpc.ankr.com/eth` |
| **Local Node** | Unlimited | `http://127.0.0.1:8545` |

## ✅ What You'll See

**With RPC URL only (read-only):**
- ✅ Network info (chain ID, latest block)
- ✅ Gas prices (slow/standard/fast/rapid)
- ⚠️ No wallet address or balance

**With RPC URL + Private Key (full access):**
- ✅ Network info
- ✅ Gas prices
- ✅ Your wallet address
- ✅ Your ETH balance
- ✅ Ready to trade

## 🔐 Security Checklist

- [ ] Never commit `.env` files or private keys to git
- [ ] Use environment variables, not hardcoded values
- [ ] Test on testnet before mainnet
- [ ] Keep backup of private keys in secure location
- [ ] Use hardware wallet for large amounts

## 🆘 Quick Troubleshooting

**"No RPC URL provided"**
```bash
export ETH_RPC_URL='https://mainnet.infura.io/v3/YOUR-KEY'
```

**"Connection failed"**
- Check RPC URL is correct
- Verify internet connection
- Try different RPC provider

**"Missing dependencies"**
```bash
pip install web3
```

## 🎯 Next Commands

After connecting:

```bash
# Check your balance
python cli.py wallet balance

# View current gas prices
python cli.py wallet gas

# Full wallet info
python cli.py wallet info

# Run a backtest
python cli.py backtest --symbol ETHUSDT --days 30

# Paper trading
python cli.py live --mode paper
```

## 📚 Full Documentation

- **Detailed Guide:** [WALLET_CONNECT_GUIDE.md](WALLET_CONNECT_GUIDE.md)
- **Setup Instructions:** [METAMASK_SETUP.md](METAMASK_SETUP.md)
- **Trading Docs:** [README.md](README.md)

---

**Need Help?** Run `python cli.py wallet connect --help`
