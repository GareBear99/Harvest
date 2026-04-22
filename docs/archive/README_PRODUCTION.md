# HARVEST - Dual-Engine Leveraged Trading Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

> **⚠️ CRITICAL WARNING**: This system uses leverage (10-40×) which can result in losses exceeding your initial capital. Trade at your own risk. This software is provided "AS IS" without warranty of any kind.

## 📊 Overview

HARVEST is an automated, terminal-based leveraged trading system featuring two complementary strategies:

- **ER-90 (Exhaustion Reversion)**: High win-rate mean reversion (85-92% target)
- **SIB (Single Impulse Breakout)**: Trend-following breakout strategy

The system uses regime classification to determine which strategy is active, ensuring only one engine trades at a time.

## 🛡️ Safety Features

- ✅ **Risk Governor**: Mandatory checks that cannot be bypassed
- ✅ **Stop-Loss Required**: Every trade must have a stop loss
- ✅ **2% Daily Drawdown Limit**: System pauses if exceeded
- ✅ **Max 2 Consecutive Losses**: Forced cooldown after breaches
- ✅ **Liquidation Buffer**: 10% safety margin validation
- ✅ **Position Sizing**: Calculated from stop distance, not arbitrary

## 🚀 Quick Start

### Option 1: Local Installation

```bash
# Clone repository
git clone https://github.com/yourusername/harvest.git
cd harvest

# Run installer
./install.sh

# Test the CLI
python3 cli.py info
```

### Option 2: Docker

```bash
# Build image
docker build -t harvest-trading .

# Run commands
docker run harvest-trading status
docker run harvest-trading backtest --symbol ETHUSDT --days 30

# Or use docker-compose
docker-compose up
```

## 📋 CLI Commands

### Information Commands

```bash
# System information
python3 cli.py info

# Current configuration
python3 cli.py status

# Show help
python3 cli.py --help
```

### Testing Commands

```bash
# Run validation tests
python3 cli.py validate

# Run backtest on ETHUSDT (30 days)
python3 cli.py backtest

# Custom backtest
python3 cli.py backtest --symbol BTCUSDT --days 90 --output results.json
```

### Trading Commands

```bash
# Paper trading mode (safe, no real money)
python3 cli.py live --mode paper

# Live trading (⚠️ REAL MONEY - NOT YET IMPLEMENTED)
python3 cli.py live --mode live --symbol ETHUSDT
```

## 📦 Requirements

- Python 3.11+
- 2GB RAM minimum
- Internet connection (for market data)
- Minimum capital: **$100-1000** recommended ($10 will generate very few trades)

## 🔧 Configuration

Edit `core/models.py` to adjust parameters:

```python
# Account settings
initial_equity: float = 10000.0
max_daily_drawdown_pct: float = 2.0
max_consecutive_losses: int = 2

# ER-90 settings
er90_rsi_upper: float = 70.0  # Overbought threshold
er90_rsi_lower: float = 30.0  # Oversold threshold
er90_leverage_min: float = 10.0
er90_leverage_max: float = 20.0

# SIB settings
sib_adx_threshold: float = 20.0
sib_leverage_min: float = 20.0
sib_leverage_max: float = 40.0
```

## 📊 System Architecture

```
┌─────────────────┐
│  Data Ingestion │ ← Binance API
└────────┬────────┘
         │
┌────────▼────────┐
│   Indicators    │ → RSI, ATR, EMA, ADX
└────────┬────────┘
         │
┌────────▼────────┐
│ Regime Classify │ → Range / Trend / Drawdown
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───┐
│ ER-90│  │  SIB │  (Mutually Exclusive)
└───┬──┘  └──┬───┘
    │        │
    └────┬───┘
         │
┌────────▼────────┐
│  Risk Governor  │ → Validation
└────────┬────────┘
         │
┌────────▼────────┐
│Execution Intent │ → Output (Test Mode)
└─────────────────┘
```

## 🎯 Strategy Details

### ER-90 (Exhaustion Reversion)

**Market**: Range-bound, non-trending
**Win Rate Target**: 85-92%
**Entry Conditions** (ALL required):
- RSI(5) > 70 (overbought) or < 30 (oversold)
- 1h RSI confirmation
- Price failed to extend recent high/low

**Risk Parameters**:
- Leverage: 10-20×
- Risk per trade: 0.25-0.5% of equity
- Take Profit: 0.2-0.4%
- Stop Loss: 1.2-1.8%
- Max losses per day: 1

### SIB (Single Impulse Breakout)

**Market**: Strong directional trends
**Win Rate Target**: 45-55% (but large wins)
**Entry Conditions** (ALL required):
- 4H EMA50 > EMA200 (long) or inverse (short)
- ADX(14) > 20
- 12-24h range breakout
- Volume ≥ 1.5× average
- Active liquidity window (UTC 07-16)

**Risk Parameters**:
- Leverage: 20-40× (dynamically calculated)
- Risk per trade: 0.5-1% of equity
- TP1: +1.5R (50% position)
- Runner: 3R-5R
- Max trades per day: 1

## 📈 Performance Expectations

**ER-90**:
- Daily: +0.3-1%
- Weekly: +2-6%
- Characteristics: High frequency, small wins

**SIB**:
- Individual trades: +5-15% equity
- Low frequency (1-2 per week)
- Characteristics: "Home run" trades

**Combined**:
- Monthly target: +10-40% (favorable conditions)
- System may pause during adverse conditions

## 🔍 Validation Status

```
Test Coverage: 87.5% (14/16 tests passing)
Critical Bugs: Fixed
Status: Beta - Use with caution
```

Run `python3 cli.py validate` to check current test status.

## ⚠️ Known Limitations

1. **Low Signal Frequency**: With small capital ($10-100), expect 0-2 trades per month
2. **Conservative by Design**: System prioritizes survival over activity
3. **Capital Requirements**: $100-1000 minimum recommended for reasonable activity
4. **Market Dependent**: Performance varies with market conditions

## 🐛 Troubleshooting

### No trades generated
**Expected behavior**. The system has strict entry criteria. This is safety-first design.
- Solution 1: Increase capital to $100-1000
- Solution 2: Accept low frequency (1-2 trades/month)
- Solution 3: Run longer backtests (90+ days)

### API errors
Check internet connection and Binance API status.
```bash
curl https://api.binance.com/api/v3/ping
```

### Test failures
Some indicator tests may fail - this is documented and non-critical for basic usage.

## 📚 Documentation

- [Installation Guide](./docs/INSTALL.md) - Detailed setup instructions
- [Validation Report](./VALIDATION_PROGRESS.md) - Test results and known issues
- [Trading Strategies](./docs/STRATEGIES.md) - Deep dive into ER-90 and SIB
- [Risk Management](./docs/RISK.md) - Safety features explained
- [API Reference](./docs/API.md) - For developers

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## ⚖️ Legal Disclaimer

**THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.**

- Trading involves substantial risk of loss
- Past performance does not guarantee future results
- You can lose more than your initial investment when using leverage
- The authors are not responsible for any financial losses
- This is not financial advice
- Always consult a licensed financial advisor before trading

By using this software, you acknowledge and accept these risks.

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/harvest/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/harvest/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/harvest/wiki)

## 🙏 Acknowledgments

Built with:
- Python 3.11+
- NumPy for calculations
- Requests for API calls
- Docker for containerization

---

**Remember**: HARVEST is designed to survive long enough for leverage to matter. Patience is part of the strategy.

*Version 1.0.0 | Last Updated: 2025-12-16*
