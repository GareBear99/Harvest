# HARVEST Quick Start Guide - From Testing to Live Trading

**Complete roadmap for going from zero to live trading safely**

---

## ✅ Step 1: Test on Paper for 7+ Days

### Why This Matters
- See actual signal frequency in current market conditions
- Verify system works as expected
- Build confidence before risking money
- Understand position sizing with your capital

### How to Run

**Option A: Quick Test (1-2 hours)**
```bash
cd /Users/TheRustySpoon/harvest

# Test for 2 hours with $10, checking every 15 minutes
python3 run_paper_trading_test.py --capital 10 --days 0.08 --interval 15
```

**Option B: Overnight Test (8 hours)**
```bash
# Run overnight, checking hourly
python3 run_paper_trading_test.py --capital 10 --days 0.33 --interval 60
```

**Option C: Full 7-Day Test (Recommended)**
```bash
# Full week test
python3 run_paper_trading_test.py --capital 10 --days 7 --interval 60

# Or run in background
nohup python3 run_paper_trading_test.py --capital 10 --days 7 --interval 60 > paper_test.log 2>&1 &
```

### What to Expect
- **December 2024**: 0-2 signals (range-bound market)
- **Volatile markets**: 3-7 signals per week
- **Trending markets**: 5-10 signals per week

### Review Results
```bash
# Check the log file
ls -lt paper_trading_test_*.json | head -1

# View results
cat paper_trading_test_*.json | python3 -m json.tool
```

**Decision point:** If you see reasonable signals (even if 0 in December), proceed to Step 2.

---

## ✅ Step 2: Get Testnet Funds

### Why This Matters
- Practice with real protocol (Hyperliquid)
- Test actual order execution
- Verify wallet connectivity
- NO RISK - testnet funds are free

### How to Get Testnet Funds

**Method 1: Hyperliquid Testnet Faucet**

1. Visit: https://app.hyperliquid-testnet.xyz/
2. Connect your MetaMask wallet
3. Request testnet funds
4. Wait 5-10 minutes for funds to arrive

**Method 2: Bridge Test ETH**

If faucet doesn't work, you can bridge test ETH:
1. Get Arbitrum Goerli test ETH from https://goerlifaucet.com/
2. Bridge to Hyperliquid testnet
3. Use for testing

### Set Up Wallet Connection

```bash
# Export your MetaMask private key (testnet wallet only!)
export ETH_PRIVATE_KEY='0xYOUR_TESTNET_PRIVATE_KEY'

# Save to shell config
echo "export ETH_PRIVATE_KEY='0xYOUR_TESTNET_PRIVATE_KEY'" >> ~/.bashrc
source ~/.bashrc
```

### Test Connection

```bash
cd /Users/TheRustySpoon/harvest

# Test Hyperliquid connection (testnet)
python3 core/hyperliquid_connector.py
```

Expected output:
```
✅ Connected to Hyperliquid
Address: 0xYourAddress...
Account Value: $100.00 (testnet)
Available Balance: $100.00
Current ETH Price: $3,950
```

**Decision point:** Once you have testnet funds and connection works, proceed to Step 3.

---

## ✅ Step 3: Start Tiny ($10-20)

### Why This Matters
- Minimize risk while learning
- Test with smallest viable amount
- Can afford to lose it entirely
- Learn from real execution

### Before You Start

**Safety checklist:**
- [ ] Tested on paper for at least 24 hours
- [ ] Successfully executed 2+ testnet trades
- [ ] Understand leverage risks (5% move = liquidation at 20x)
- [ ] Ready to lose entire $10-20
- [ ] Have emergency close command ready

### Fund Your Hyperliquid Account

**Option 1: Bridge from Arbitrum**

```bash
# 1. Get ETH on Arbitrum mainnet
# 2. Go to https://app.hyperliquid.xyz/
# 3. Connect wallet
# 4. Click "Deposit"
# 5. Bridge $10-20 worth of ETH
```

**Option 2: Direct Deposit**

```bash
# Send ETH directly to Hyperliquid
# Your address: [check in Hyperliquid app]
# Amount: $10-20 worth of ETH
```

### Configure for Live Trading

Edit your config or create a script:

```python
# live_trade_tiny.py
from core.models import Config
from core.hyperliquid_connector import setup_hyperliquid_connection
from core.leverage_executor import LeverageExecutor

# Create config for tiny capital
config = Config(
    initial_equity=10.0,  # Your actual balance
    small_capital_mode=True,
    small_capital_risk_pct=5.0,  # 5% risk per trade
    enable_paper_leverage=False,  # LIVE MODE
    use_hyperliquid=True,
    hyperliquid_testnet=False,  # MAINNET
    min_position_size_usd=10.0,
    max_position_size_usd=20.0
)

# Connect to Hyperliquid mainnet
hyperliquid = setup_hyperliquid_connection(testnet=False)

if hyperliquid:
    print(f"✅ Connected to Hyperliquid mainnet")
    print(f"Balance: ${hyperliquid.get_available_balance()}")
    
    # Create executor
    executor = LeverageExecutor(config=config, hyperliquid=hyperliquid)
    print(f"Mode: {'PAPER' if executor.paper_mode else 'LIVE'}")
    print("🚀 Ready for live trading!")
else:
    print("❌ Failed to connect")
```

### Run Live (Manually for First Trades)

```bash
# Check balance
python3 -c "from core.hyperliquid_connector import setup_hyperliquid_connection; h = setup_hyperliquid_connection(); print(f'Balance: \${h.get_available_balance()}')"

# Monitor for signals (manual execution)
python3 run_paper_trading_test.py --capital 10 --days 1 --interval 30
```

**Decision point:** After 3-5 successful live trades, proceed to Step 4.

---

## ✅ Step 4: Monitor Closely

### Why This Matters
- Catch issues early
- Understand actual execution
- Learn from real trades
- Build confidence

### What to Monitor

**Every Trade (First 3-5):**
- [ ] Entry price matches signal
- [ ] Stop-loss is set correctly
- [ ] Position size is appropriate
- [ ] Leverage is correct
- [ ] Can close manually if needed

**Daily:**
- [ ] Account balance
- [ ] Open positions
- [ ] PnL tracking
- [ ] Gas costs
- [ ] System errors/warnings

### Monitoring Tools

**Check Balance**
```bash
python3 cli.py wallet info
```

**Check Positions**
```bash
# View on Hyperliquid
# https://app.hyperliquid.xyz/

# Or programmatically
python3 -c "from core.hyperliquid_connector import setup_hyperliquid_connection; h = setup_hyperliquid_connection(); print(h.get_positions())"
```

**Emergency Close All**
```python
from core.hyperliquid_connector import setup_hyperliquid_connection
from core.leverage_executor import LeverageExecutor
from core.models import Config

config = Config(use_hyperliquid=True, hyperliquid_testnet=False)
hyperliquid = setup_hyperliquid_connection(testnet=False)
executor = LeverageExecutor(config=config, hyperliquid=hyperliquid)

# Close all positions
executor.close_all_positions(reason="emergency")
```

### Red Flags to Watch For

**Stop immediately if:**
- Positions opening with wrong size
- Stop-losses not triggering
- Unexpected leverage amounts
- System errors on every trade
- Losing more than 20% in a day

### Keep a Trading Journal

```bash
# Create trading log
echo "Date,Signal,Entry,Exit,PnL,Notes" > trading_journal.csv

# After each trade, log:
# - What signal triggered
# - Entry and exit prices
# - Profit or loss
# - What you learned
```

**Decision point:** After 5+ trades and feeling confident, proceed to Step 5.

---

## ✅ Step 5: Scale Slowly

### Why This Matters
- Preserve capital while learning
- Compound gains gradually
- Don't blow up account with overconfidence
- Sustainable growth

### Scaling Strategy

**Phase 1: $10 → $20 (Double)**
- Stay at $10 position sizes
- Let profits accumulate
- Don't withdraw
- Goal: 2-3 months

**Phase 2: $20 → $50 (2.5x)**
- Increase to $15-20 positions
- Still conservative
- Withdraw 20% if desired
- Goal: 3-6 months

**Phase 3: $50 → $100 (2x)**
- Increase to $30-40 positions
- More sustainable trading
- Gas costs become negligible
- Goal: 3-6 months

**Phase 4: $100 → $500+ (5x)**
- Professional-grade trading
- Optimal risk management
- Can trade more frequently
- Goal: 6-12 months

### When to Add More Capital

**✅ Good reasons:**
- Profitable for 3+ months
- Win rate matches expectations (70%+)
- Comfortable with the process
- Have extra money to risk

**❌ Bad reasons:**
- Just had one good trade
- Want to "get rich quick"
- Trying to recover losses
- Using money you need

### When to Withdraw

**Guidelines:**
- Withdraw profits after doubling
- Keep base capital in system
- Never withdraw during drawdown
- Celebrate wins (but don't get greedy)

### Position Size Scaling

| Capital | Position Size | Leverage | Risk/Trade | Margin Used |
|---------|--------------|----------|------------|-------------|
| $10 | $10-20 | 20x | 5-10% | $0.50-1.00 |
| $20 | $20-40 | 20x | 5% | $1.00-2.00 |
| $50 | $50-100 | 20x | 3-5% | $2.50-5.00 |
| $100 | $100-200 | 20x | 2-5% | $5-10 |
| $500 | $500-1000 | 20x | 1-2% | $25-50 |

---

## 🚨 Risk Management Rules

### Never Break These Rules

1. **Never risk more than you can afford to lose**
   - If losing $10-20 hurts, don't trade
   - Only use "fun money"
   - Never trade with rent/bill money

2. **Never increase leverage beyond 30x**
   - 20x is already extreme
   - 30x = 3.3% adverse move = liquidation
   - Higher leverage = faster losses

3. **Never override stop-losses**
   - System sets them for a reason
   - "Hoping" doesn't work
   - Take the loss and move on

4. **Never revenge trade**
   - After a loss, step away
   - Don't try to "win it back"
   - System will signal when ready

5. **Never trade emotionally**
   - Follow the system
   - Don't force trades
   - Patience wins

### Emergency Procedures

**If losing >20% in a day:**
```bash
# Close all positions immediately
python3 -c "from core.leverage_executor import *; from core.hyperliquid_connector import *; executor = LeverageExecutor(Config(use_hyperliquid=True), setup_hyperliquid_connection()); executor.close_all_positions('emergency')"

# Stop trading for 48 hours
# Review what went wrong
# Adjust strategy if needed
```

**If system is malfunctioning:**
```bash
# Close all via Hyperliquid UI
# https://app.hyperliquid.xyz/

# Or manually via connector
python3 core/hyperliquid_connector.py
# Use the close functions
```

---

## 📊 Expected Timeline

**Realistic expectations for each phase:**

### Week 1: Paper Trading
- Run system 24/7
- See 0-2 signals (December)
- Build confidence
- Learn the interface

### Week 2: Testnet
- Get testnet funds
- Execute 2-3 test trades
- Verify everything works
- Understand the flow

### Week 3-4: Live Tiny ($10-20)
- Start with $10-20
- Execute first live trade
- Monitor closely
- Learn from experience

### Month 2-3: Building Confidence
- Execute 5-10 trades
- Track win rate
- Adjust if needed
- Stay disciplined

### Month 4-6: Scaling Up
- If profitable, add capital
- $10 → $20 → $50
- Withdraw some profits
- Maintain discipline

### Month 7-12: Sustainable Trading
- $50 → $100 → $200
- Consistent strategy
- Regular withdrawals
- Professional approach

---

## 🎯 Success Metrics

### How to Know You're Ready for Next Phase

**Ready for Testnet:**
- [ ] Ran paper trading for 24+ hours
- [ ] Understand how signals generate
- [ ] Comfortable with leverage concept
- [ ] Know how to close positions

**Ready for Live Tiny:**
- [ ] 2+ successful testnet trades
- [ ] Wallet connection working
- [ ] Have $10-20 you can afford to lose
- [ ] Emergency close procedure ready

**Ready to Scale:**
- [ ] 10+ live trades executed
- [ ] Win rate >60%
- [ ] Profitable over 1+ month
- [ ] Comfortable with process
- [ ] Following all rules

---

## 🆘 Troubleshooting

### Common Issues

**No signals generating:**
- Normal in December (range-bound)
- System is working correctly
- Just being conservative
- Be patient

**Trades not executing:**
- Check balance
- Verify connectivity
- Try smaller position size
- Check logs for errors

**Losing trades:**
- Expected (15-30% loss rate)
- One loss doesn't mean failure
- System needs winning trades to offset
- Stay disciplined

**System errors:**
- Check API keys
- Verify internet connection
- Review error messages
- Restart if needed

---

## 💡 Pro Tips

1. **Start smaller than you think**
   - If planning $20, start with $10
   - You can always add more
   - Can't un-lose lost money

2. **Journal everything**
   - Track all trades
   - Note what you learned
   - Review weekly
   - Adjust strategy

3. **Take breaks**
   - Don't watch 24/7
   - Trust the system
   - Enjoy your life
   - Avoid burnout

4. **Celebrate small wins**
   - First profitable trade
   - First profitable week
   - Doubling your capital
   - But don't get cocky

5. **Learn from losses**
   - Every loss teaches something
   - Review what happened
   - Adjust if pattern emerges
   - Don't take personally

---

## ✅ Checklist: Ready to Go Live?

Before starting live trading with real money:

- [ ] Tested on paper for 7+ days (or at least 24 hours)
- [ ] Successfully executed 2+ testnet trades
- [ ] Have $10-20 you can afford to lose entirely
- [ ] Understand leverage risks (5% move = liquidation)
- [ ] Know how to close positions manually
- [ ] Have emergency close procedure ready
- [ ] Read all risk warnings
- [ ] Not trading with money you need
- [ ] Ready to start tiny and scale slowly
- [ ] Committed to following the rules

If you checked all boxes: **You're ready!**

If not: **Keep testing until you are.**

---

## 🎉 You're Ready!

The complete system is built, tested, and ready. Now it's about:

1. **Patience** - Don't rush
2. **Discipline** - Follow the plan
3. **Learning** - Every trade teaches
4. **Scaling** - Compound slowly
5. **Surviving** - Don't blow up

**Good luck, and trade responsibly!** 🚀

---

**Remember:** The goal isn't to get rich quick. It's to build a sustainable trading system that grows your capital slowly over time while you learn and improve.
