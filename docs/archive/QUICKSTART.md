# HARVEST Quick Start Guide

## Installation

```bash
cd /Users/TheRustySpoon/harvest
pip install -r requirements.txt
```

## Running the System

### 1. Run Backtest on Bitcoin

```bash
python backtester.py
```

This will:
- Fetch 30 days of BTC/USDT data from Binance
- Classify market regimes
- Check for entry signals from both engines
- Generate execution intents (test mode - no real trades)
- Export results to `harvest_backtest_results.json`

### 2. Run Debug Test (Both BTC and ETH)

```bash
python test_system.py
```

This will test the system on both BTCUSDT and ETHUSDT with detailed debug output showing:
- Data fetch statistics
- Regime classification results
- Active engine selection
- Execution intent generation (if any)

## Understanding the Output

### Normal Operation

```
✅ 2025-11-24 21:00 | ER-90  | long  | Entry: $93,450.00 | Stop: $91,800.00 | TP1: $93,820.00 | Leverage: 15.0x | Risk: 0.38%
```

This means:
- ✅ = Execution intent passed risk validation
- ER-90 = Exhaustion Reversion engine
- Entry, Stop, TP1 = Price levels
- Leverage = Dynamic leverage based on conditions
- Risk = Percentage of equity at risk

### No Signals (Expected)

```
⚠️  No execution intents generated during backtest period
   This is expected behavior - the strategies have strict entry criteria.
   The system is working correctly by NOT forcing trades.
```

This is **correct behavior**. The system will not trade unless ALL entry conditions are met.

## Results Files

### harvest_backtest_results.json

Contains:
- `config`: System configuration and parameters
- `execution_intents`: Array of all generated trading signals
- `regime_history`: Market regime classifications over time
- `summary`: Aggregate statistics

Example:
```json
{
  "config": {
    "symbol": "BTCUSDT",
    "initial_equity": 10000.0
  },
  "execution_intents": [...],
  "regime_history": [...],
  "summary": {
    "total_execution_intents": 5,
    "by_engine": {"ER90": 3, "SIB": 2},
    "by_side": {"long": 2, "short": 3},
    "average_metrics": {
      "leverage": 18.5,
      "risk_pct": 0.425,
      "notional_usd": 2500.0
    }
  }
}
```

## Configuration

Edit `harvest/core/models.py` to modify system parameters:

```python
@dataclass
class Config:
    # Account
    initial_equity: float = 10000.0
    max_daily_drawdown_pct: float = 2.0
    max_consecutive_losses: int = 2
    
    # ER-90 parameters
    er90_leverage_min: float = 10.0
    er90_leverage_max: float = 20.0
    er90_risk_pct_min: float = 0.25
    er90_risk_pct_max: float = 0.5
    # ... etc
```

## Safety Features (Always Active)

1. ✅ **Stop-Loss Mandatory**: Every trade has stop loss
2. ✅ **Risk Governor**: Cannot be bypassed
3. ✅ **Account Limits**: 2% daily drawdown, 2 consecutive losses
4. ✅ **Liquidation Buffer**: 10% margin between stop and liquidation
5. ✅ **Mutual Exclusivity**: Only one engine active at a time
6. ✅ **Test Mode**: No real transactions in backtest

## Interpreting Regimes

The system classifies markets into 4 regimes:

- **RANGE**: Sideways, choppy markets → ER-90 active
- **WEAK_TREND**: Moderate trend → ER-90 active (conservative)
- **STRONG_TREND**: Clear breakout + trend → SIB active
- **DRAWDOWN**: Risk limits breached → IDLE mode

## Common Questions

### Q: Why are no execution intents being generated?

**A**: This is normal! The system has very strict entry criteria designed for high win-rate (ER-90) or high reward (SIB) trades. It will remain idle until conditions justify risk.

### Q: Can I adjust the entry criteria to be less strict?

**A**: Yes, but this defeats the purpose. The strict criteria are what give the system its edge. Loosening them will degrade performance and increase drawdowns.

### Q: How do I enable live trading?

**A**: The current implementation is TEST MODE ONLY. Live trading requires:
1. WalletConnect integration with MetaMask
2. Order execution module
3. Position monitoring
4. Extensive paper trading validation
5. User acceptance testing

See `VALIDATION_REPORT.md` for the complete roadmap.

### Q: What if I want to test on different assets?

Modify the backtester initialization:

```python
backtester = Backtester(symbol="SOLUSDT", initial_equity=10000.0)
```

Any Binance perpetual futures symbol should work.

## Monitoring the System

### Key Metrics to Watch

1. **Regime Distribution**: Are regimes being classified correctly?
2. **Engine Selection**: Is the right engine active for each regime?
3. **Risk Breaches**: Should always be 0
4. **Execution Intent Quality**: Check stop distance, leverage, risk %

### Red Flags

🚨 If you see any of these, the system has a bug:
- Both engines active simultaneously
- Execution intent without stop loss
- Risk breach not triggering IDLE mode
- Liquidation price closer than stop loss

## Next Steps

1. **Review Results**: Examine `harvest_backtest_results.json`
2. **Understand Behavior**: Read `VALIDATION_REPORT.md`
3. **Extend Testing**: Increase backtest period, test more assets
4. **Study Code**: Review strategy logic in `strategies/` folder

## Support Files

- `README.md` - Full system documentation
- `VALIDATION_REPORT.md` - Test results and validation
- `requirements.txt` - Python dependencies

---

**Remember**: HARVEST is designed to survive, not to trade frequently. Patience is part of the strategy.
