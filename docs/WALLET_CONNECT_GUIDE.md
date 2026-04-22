# MetaMask Wallet Connect Guide

## Quick Start

The `wallet connect` command tests your MetaMask wallet connection and displays comprehensive network and account information.

## Basic Usage

```bash
# Connect using environment variables
python cli.py wallet connect

# Connect with specific RPC URL
python cli.py wallet connect --rpc-url https://mainnet.infura.io/v3/YOUR-PROJECT-ID

# Connect to testnet (Sepolia)
python cli.py wallet connect --testnet

# Connect to specific chain
python cli.py wallet connect --chain-id 11155111
```

## Prerequisites

### 1. Set Environment Variables

**Required:**
```bash
export ETH_RPC_URL='https://mainnet.infura.io/v3/YOUR-PROJECT-ID'
```

**Optional (for transactions):**
```bash
export ETH_PRIVATE_KEY='0xYOUR_PRIVATE_KEY_HERE'
```

⚠️ **SECURITY WARNING:** Never commit private keys to git or share them publicly!

### 2. Install Dependencies

```bash
pip install web3
```

## Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--rpc-url` | Ethereum RPC endpoint | `ETH_RPC_URL` env var |
| `--chain-id` | Network chain ID | `1` (Mainnet) |
| `--testnet` | Auto-switch to Sepolia testnet | `false` |

## Supported Networks

| Network | Chain ID | Usage |
|---------|----------|-------|
| Ethereum Mainnet | 1 | `--chain-id 1` |
| Sepolia Testnet | 11155111 | `--testnet` or `--chain-id 11155111` |
| Goerli Testnet | 5 | `--chain-id 5` (deprecated) |
| Polygon Mainnet | 137 | `--chain-id 137` |
| Polygon Mumbai | 80001 | `--chain-id 80001` |

## Output Information

The connect command displays:

✅ **Network Information:**
- Chain ID and name
- Latest block number
- Sync status

💰 **Account Details** (if private key provided):
- Wallet address
- ETH balance
- Estimated USD value (requires price oracle)

⛽ **Gas Prices:**
- Slow, Standard, Fast, Rapid
- Cost per transaction estimate

## Examples

### Example 1: Test Connection (Read-Only)

```bash
export ETH_RPC_URL='https://mainnet.infura.io/v3/abc123'
python cli.py wallet connect
```

**Output:**
```
======================================================================
METAMASK WALLET CONNECT
======================================================================

🌐 Target Network: Ethereum Mainnet

📡 RPC URL: https://mainnet.infura.io/v3/abc123
🔑 Private Key: ⚠️  Not set (read-only mode)

⚠️  WARNING: No private key provided
   You can view balances but cannot send transactions.

🔌 Connecting to Ethereum network...

✅ Successfully connected to Ethereum network!

======================================================================
CONNECTION DETAILS
======================================================================

🌐 Network Information:
   Chain ID:      1
   Chain Name:    Ethereum Mainnet
   Latest Block:  18,950,123
   Syncing:       ✅ Synced

⛽ Current Gas Prices:
   Slow       12.50 Gwei  (~0.000263 ETH per tx)
   Standard   15.00 Gwei  (~0.000315 ETH per tx)
   Fast       18.00 Gwei  (~0.000378 ETH per tx)
   Rapid      22.50 Gwei  (~0.000473 ETH per tx)

📊 Gas estimate based on 21,000 gas (simple transfer)

======================================================================
✅ CONNECTION TEST COMPLETE
======================================================================

✓ Network connected (read-only mode)

💡 To enable transactions:
   export ETH_PRIVATE_KEY='0xYOUR_PRIVATE_KEY'
```

### Example 2: Full Connection with Wallet

```bash
export ETH_RPC_URL='https://mainnet.infura.io/v3/abc123'
export ETH_PRIVATE_KEY='0x...'
python cli.py wallet connect
```

**Additional Output:**
```
📍 Wallet Address:
   0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

💰 Account Balance:
   1.523000 ETH

💵 Estimated Value:
   ~$--- USD (requires price oracle)

...

✓ Wallet connected successfully
✓ Ready for trading operations

💡 Next steps:
   - Check balance: python cli.py wallet balance
   - View gas prices: python cli.py wallet gas
   - Run backtest: python cli.py backtest
```

### Example 3: Connect to Testnet

```bash
export ETH_RPC_URL='https://sepolia.infura.io/v3/abc123'
python cli.py wallet connect --testnet
```

**Output:**
```
🧪 Testnet mode: Using Sepolia (Chain ID 11155111)
🌐 Target Network: Sepolia Testnet
...
```

## Troubleshooting

### Connection Failed

**Problem:** `❌ Connection failed!`

**Solutions:**
1. Check RPC URL is valid and accessible
2. Verify network connectivity
3. Try alternative RPC endpoint
4. Check firewall settings

### Invalid Private Key

**Problem:** `❌ Connection error: Invalid private key format`

**Solutions:**
1. Ensure key starts with `0x`
2. Key should be 64 hex characters (plus `0x` prefix)
3. Verify key is not corrupted
4. Check for extra spaces or newlines

### Missing Dependencies

**Problem:** `❌ Missing dependencies: No module named 'web3'`

**Solution:**
```bash
pip install web3
```

### RPC Rate Limiting

**Problem:** Connection works but requests fail intermittently

**Solutions:**
1. Use a paid RPC service (Infura, Alchemy, QuickNode)
2. Reduce request frequency
3. Switch to different RPC provider

## RPC Providers

### Free Options (Rate Limited)

**Infura:**
- URL: `https://mainnet.infura.io/v3/YOUR-PROJECT-ID`
- Sign up: https://infura.io
- Rate limit: 100,000 requests/day

**Alchemy:**
- URL: `https://eth-mainnet.g.alchemy.com/v2/YOUR-API-KEY`
- Sign up: https://alchemy.com
- Rate limit: 300M compute units/month

**Public Endpoints (Not Recommended for Production):**
- `https://rpc.ankr.com/eth`
- `https://eth.public-rpc.com`

### Local Node

**Run Your Own Node:**
```bash
# Geth
geth --http --http.addr "127.0.0.1" --http.port 8545

# Use with:
export ETH_RPC_URL='http://127.0.0.1:8545'
```

## Security Best Practices

1. **Never commit private keys** to version control
2. **Use environment variables** for sensitive data
3. **Test on testnet first** before mainnet
4. **Use hardware wallets** for large amounts
5. **Keep private keys encrypted** at rest
6. **Limit API key permissions** to minimum required
7. **Rotate keys regularly** if compromised

## Next Steps

After successful connection:

1. **Check Balance:**
   ```bash
   python cli.py wallet balance
   ```

2. **Monitor Gas Prices:**
   ```bash
   python cli.py wallet gas
   ```

3. **View Full Wallet Info:**
   ```bash
   python cli.py wallet info
   ```

4. **Run a Backtest:**
   ```bash
   python cli.py backtest --symbol ETHUSDT --days 30
   ```

5. **Start Paper Trading:**
   ```bash
   python cli.py live --mode paper
   ```

## Related Documentation

- **Full Setup Guide:** [METAMASK_SETUP.md](METAMASK_SETUP.md)
- **Trading Documentation:** [README.md](README.md)
- **System Architecture:** [DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review [METAMASK_SETUP.md](METAMASK_SETUP.md)
3. Run with `--help` flag for command options
4. Check project issues on GitHub

---

**Version:** 1.0  
**Last Updated:** December 17, 2024  
**Compatible With:** HARVEST v2.0+
