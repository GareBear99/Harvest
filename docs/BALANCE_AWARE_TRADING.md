# Balance-Aware Trading System

## Overview
Dynamically activates timeframes and assets based on account balance with stair-step progression from $10 to $100+.

## Activation Tiers

### Tier 1: $10-20 (Bare Minimum)
**Active:**
- Timeframes: 1m only
- Assets: ETH only
- Max Position: $10

**Strategy:** Ultra-fast scalping on ETH 1-minute timeframe to build capital quickly.

**No BTC wallet required** - Pure capital building phase.

---

### Tier 2: $20-30 (BTC Activation)
**Active:**
- Timeframes: 1m
- Assets: ETH + BTC
- Max Position: $10 per asset

**Strategy:** Dual asset scalping with $10 positions on each.

**BTC wallet required** - Auto-created on dashboard startup.
**Profit threshold:** $100 profit → Transfer 50% to BTC wallet

---

### Tier 3: $30-40 (Add 5m)
**Active:**
- Timeframes: 1m, 5m
- Assets: ETH + BTC
- Max Position: $15 per asset

**Strategy:** Fast + medium scalping across 2 timeframes.

---

### Tier 4: $40-50 (Add 15m)
**Active:**
- Timeframes: 1m, 5m, 15m
- Assets: ETH + BTC  
- Max Position: $16 per asset

**Strategy:** Short-term + scalping combo.

---

### Tier 5: $50-75 (Add 1h)
**Active:**
- Timeframes: 1m, 5m, 15m, 1h
- Assets: ETH + BTC
- Max Position: $18 per asset

**Strategy:** Medium-term swing trades added to scalping mix.

---

### Tier 6: $75-100 (Add 4h)
**Active:**
- Timeframes: 1m, 5m, 15m, 1h, 4h (ALL)
- Assets: ETH + BTC
- Max Position: $20 per asset

**Strategy:** Full timeframe coverage with conservative sizing.

---

### Tier 7: $100+ (Full System)
**Active:**
- Timeframes: All (1m, 5m, 15m, 1h, 4h)
- Assets: ETH + BTC
- Max Position: Dynamic (uses position_size_limiter)

**Strategy:** Full system with dynamic position sizing based on capital.

**Profit threshold:** $500 profit → Transfer 40% to BTC wallet (medium accounts)

---

## Implementation

### Core File: `core/balance_aware_strategy.py`

**Key Functions:**

```python
from core.balance_aware_strategy import get_balance_aware_strategy

strategy = get_balance_aware_strategy()

# Get active timeframes for balance
timeframes = strategy.get_active_timeframes(balance=35.0)
# Returns: ['1m', '5m']

# Get active assets
assets = strategy.get_active_assets(balance=35.0)
# Returns: [Asset.ETH, Asset.BTC]

# Check if specific timeframe is active
is_active = strategy.is_timeframe_active(balance=15.0, timeframe='5m')
# Returns: False (only 1m active at $15)

# Get max position size
max_pos = strategy.get_max_position_size(balance=45.0, asset=Asset.ETH)
# Returns: 16.0

# Validate trading requirements
validation = strategy.validate_trading_requirements(
    balance=25.0,
    has_btc_wallet=True,
    connected_metamask=False
)
# Returns: {'can_trade': True, 'tier': ..., 'issues': [], ...}
```

### Backtest Integration

**Command line with balance chooser:**

```bash
# Test with $10 balance (1m ETH only)
python backtest_90_complete.py --balance 10

# Test with $35 balance (1m+5m ETH+BTC)
python backtest_90_complete.py --balance 35

# Test with $100 balance (full system)
python backtest_90_complete.py --balance 100
```

**What happens:**
1. Balance-aware strategy validates requirements
2. Shows active timeframes and assets for that balance
3. Runs backtest with only those timeframes/assets active
4. Applies tier-appropriate position sizing

### Live Trader Integration

**File: `live_trader.py`** (needs implementation)

```python
from core.balance_aware_strategy import get_balance_aware_strategy

class LiveTrader:
    def __init__(self, ...):
        self.balance_strategy = get_balance_aware_strategy()
        
    def run(self):
        # Validate on startup
        validation = self.balance_strategy.validate_trading_requirements(
            balance=self.account.equity,
            has_btc_wallet=self.wallet_manager.config.get('btc_wallet_generated', False),
            connected_metamask=self.wallet_manager.config.get('metamask_connected', False)
        )
        
        if not validation['can_trade']:
            self.logger.error("Cannot start trading:")
            for issue in validation['issues']:
                self.logger.error(f"  - {issue}")
            return
        
        # In trading loop
        while self.running:
            # Only analyze active timeframes
            active_timeframes = self.balance_strategy.get_active_timeframes(
                self.account.equity
            )
            
            # Only trade active assets
            active_assets = self.balance_strategy.get_active_assets(
                self.account.equity
            )
            
            # Check BTC wallet funding at tier thresholds
            if self.account.equity >= 20.0 and not has_btc_wallet:
                self.logger.warning("BTC wallet required - run dashboard.sh to create")
            
            # Apply tier-appropriate position sizing
            max_position = self.balance_strategy.get_max_position_size(
                balance=self.account.equity,
                asset=current_asset
            )
```

### Dashboard Integration

**Show current tier in dashboard:**

```python
from core.balance_aware_strategy import get_balance_aware_strategy

strategy = get_balance_aware_strategy()
current_balance = 35.0

# Get tier info
tier = strategy.get_tier(current_balance)
summary = strategy.get_tier_summary(current_balance)

# Display in Wallet panel or Bot Status panel
lines.append(f"Tier: {tier.description}")
lines.append(f"Active TFs: {', '.join(tier.active_timeframes)}")
lines.append(f"Next Tier: ${tier.max_balance:.0f} (+${tier.max_balance - current_balance:.0f})")
```

## Examples

### Example 1: Starting with $10

```bash
./dashboard.sh
# BTC wallet: Not created (not required yet)
# Active: 1m ETH only
# Max position: $10
```

Trade 1m ETH until balance reaches $20.

---

### Example 2: Reaching $20

```bash
# Dashboard auto-creates BTC wallet
# Active: 1m ETH + BTC
# Max position: $10 per asset
```

Now trading both assets on 1m timeframe.

---

### Example 3: Reaching $35

```bash
# Active: 1m + 5m on ETH + BTC
# Max position: $15 per asset
# BTC wallet: Ready for funding at $100 profit
```

Can now scalp on 1m and 5m across both assets.

---

### Example 4: Reaching $100+

```bash
# Active: ALL timeframes on ETH + BTC
# Max position: Dynamic (position_size_limiter takes over)
# BTC wallet: Funded at $500 profit (40% transfer)
```

Full system active with dynamic position sizing.

---

## Stair-Step Progression

```
$10  → 1m ETH only
      ↓ +$10
$20  → 1m ETH+BTC + BTC wallet created
      ↓ +$10  
$30  → Add 5m timeframe
      ↓ +$10
$40  → Add 15m timeframe
      ↓ +$10
$50  → Add 1h timeframe
      ↓ +$25
$75  → Add 4h timeframe (ALL active)
      ↓ +$25
$100 → Dynamic position sizing
```

## Testing

**Test the balance-aware system:**

```bash
# Show all tiers
python core/balance_aware_strategy.py

# Test specific balances
python -c "
from core.balance_aware_strategy import get_balance_aware_strategy
s = get_balance_aware_strategy()
print(s.get_tier_summary(25.0))
"

# Backtest with specific balance
python backtest_90_complete.py --balance 25

# Expected output:
# Balance: $25.00
# Tier: 1m Both Assets + BTC Wallet Funded
# Active Timeframes: 1m
# Active Assets: ETH + BTC
# Max Position/Asset: $10
```

## Safety Features

### 1. Minimum Balance Enforcement
- Cannot trade with < $10 balance
- Clear error messages if insufficient

### 2. BTC Wallet Requirements
- Tier 2+ requires BTC wallet
- Auto-created on dashboard startup
- Validation before live trading

### 3. Position Size Limits
- Tier-appropriate max positions
- Prevents over-leverage at small balances
- Smooth transition to dynamic sizing at $100+

### 4. Timeframe Gating
- Only active timeframes analyzed
- Prevents unnecessary computation
- Focuses capital on proven strategies

## Benefits

### 1. Capital Efficiency
- Start small ($10) and scale up
- No wasted compute on inactive timeframes
- Focus on fastest timeframes when capital-limited

### 2. Risk Management
- Conservative sizing at small balances
- Gradual increase as capital grows
- BTC wallet security kicks in at $20+

### 3. Performance Optimization
- Less timeframes = faster execution
- More trades per timeframe at small balances
- Better position management

### 4. Clear Progression Path
- User knows exactly what unlocks when
- Motivation to reach next tier
- Transparent requirements

## Next Steps

### Immediate
- [x] Create balance_aware_strategy.py
- [x] Add --balance arg to backtest
- [x] Test tier validation logic
- [ ] Integrate into backtest engine (filter timeframes)
- [ ] Integrate into live_trader.py
- [ ] Add tier display to dashboard

### Near-Term
- [ ] Dynamic timeframe filtering in backtest
- [ ] Live trader balance validation on startup
- [ ] Dashboard tier status panel
- [ ] Automatic tier upgrades during live trading

### Testing
- [ ] Backtest each tier independently
- [ ] Verify position sizing per tier
- [ ] Test BTC wallet creation at $20
- [ ] Validate tier transitions work smoothly
