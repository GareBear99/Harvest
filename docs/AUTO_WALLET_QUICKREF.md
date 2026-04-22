# Auto Wallet Quick Reference

## 🚀 Get Started in 3 Steps

```bash
# 1. Start API server (Terminal 1)
python core/wallet_api_server.py

# 2. Setup wallet (Terminal 2)
python cli.py wallet setup

# 3. Start trading
python cli.py live --mode live
```

## 📋 Common Commands

```bash
# Wallet management
python cli.py wallet setup      # Interactive setup
python cli.py wallet status     # Full wallet info
python cli.py wallet connect    # Test MetaMask
python cli.py wallet balance    # Check ETH balance

# Live trading
python cli.py live --mode paper # Paper trading
python cli.py live --mode live  # Live trading ($10 min)
```

## ⚙️ Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| Min Balance | $10 | Required to start live trading |
| Profit Threshold | $100 | Auto-fund BTC wallet at this profit |
| Funding Amount | $50 | Amount transferred to BTC wallet |

## 📁 Important Files

```
~/.harvest/.client_id                  # Your unique client ID
data/wallet_config.json                # Wallet configuration
data/.btc_mnemonic_*.enc               # BTC recovery phrase ⚠️ BACKUP!
data/auth/metamask_connect.html        # Browser auth page
data/metamask_connection.json          # Connection status
```

## 🔐 Security Checklist

- [ ] API server running (localhost only)
- [ ] MetaMask extension installed
- [ ] Backup BTC mnemonic offline
- [ ] Test on testnet first
- [ ] Start with minimum $10

## 🐛 Quick Troubleshooting

**MetaMask won't connect?**
```bash
# Check API server is running
curl http://localhost:5123/health
```

**Balance check fails?**
```bash
# Set RPC URL
export ETH_RPC_URL='https://mainnet.infura.io/v3/YOUR-KEY'
```

**Live trading blocked?**
```bash
# Check system status
python cli.py wallet status

# Re-run setup
python cli.py wallet setup
```

## 📊 System Flow

```
Startup → Validate Wallet → Check Balance → Trade
    ↓           ↓                 ↓            ↓
 Load ID   MetaMask?         ≥$10 ETH?    Monitor Profit
          BTC wallet?                           ↓
                                          ≥$100? → Fund BTC
```

## 💡 Pro Tips

1. **Always backup mnemonic** before trading
2. **Test with testnet** (Sepolia) first
3. **Start with minimum** capital ($10)
4. **Monitor first trades** closely
5. **Keep API server running** during trading

## 📚 Full Documentation

- **Complete Guide:** [AUTO_WALLET_SYSTEM.md](AUTO_WALLET_SYSTEM.md)
- **Main README:** [README.md](README.md)
- **Wallet Connect:** [WALLET_CONNECT_GUIDE.md](WALLET_CONNECT_GUIDE.md)

## 🆘 Need Help?

```bash
python cli.py wallet --help
python cli.py wallet setup --help
python cli.py wallet status
```

---

**Version:** 1.0 | **Updated:** Dec 17, 2024
