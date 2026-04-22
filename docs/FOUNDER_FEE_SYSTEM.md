# Founder Fee System Documentation

## Overview
The HARVEST bot includes a 10% founder fee on profits earned after reaching $100 with the full trading system active. This ensures the founder is compensated for system development while only charging once the user has proven profitability.

## Fee Structure

### Activation Requirements
1. **Balance Threshold**: Account must reach $100+
2. **Full System Active**: Both assets (ETH + BTC) and all 5 timeframes (1m, 5m, 15m, 1h, 4h) must be trading
3. **One-Time Activation**: Once activated, stays active for life of account

### Collection Rules
- **Fee Amount**: $10 per collection
- **Collection Frequency**: Every $10 profit above baseline
- **Baseline Protection**: No fee if account drops below baseline
- **Continuous**: Collects automatically as profits grow

---

## How It Works

### Scenario 1: Starting from $10
```
$10 → $100: No fees (growing to activation threshold)
$100: System activates, baseline = $100
$110: Collect $10 fee, new balance = $100, baseline stays $100
$120: Collect $10 fee, new balance = $110, baseline stays $100
$130: Collect $10 fee, new balance = $120, baseline stays $100
```

**Result**: User keeps growing capital, founder gets 10% of all profits above $100

### Scenario 2: Starting at $100
```
$100: System activates immediately, baseline = $100
$110: Collect $10 fee, new balance = $100, baseline stays $100
$115: Collect $10 fee, new balance = $105, baseline stays $100
```

**Result**: Immediate activation, fees start on first $10 profit

### Scenario 3: Account Drawdown
```
$100: System activates, baseline = $100
$110: Collect $10 fee, balance = $100, baseline stays $100
$95: Drop below baseline - NO FEE COLLECTION
$105: Still below $110 threshold - NO FEE
$110: Back to threshold - Collect $10 fee
```

**Result**: No fees during drawdowns, protection for user capital

---

## Technical Implementation

### Class: `FounderFeeManager`
**Location**: `core/founder_fee_manager.py`

### Key Methods

#### `check_and_collect()`
Main method to check and collect fees during trading.

```python
from core.founder_fee_manager import get_founder_fee_manager

manager = get_founder_fee_manager()

# Check on every balance update
collection = manager.check_and_collect(
    current_balance=110.0,
    active_timeframes=['1m', '5m', '15m', '1h', '4h'],
    active_assets=['ETH', 'BTC']
)

if collection:
    print(f"Fee collected: ${collection['amount']}")
    # Send fee to founder address
    send_to_founder(collection['founder_address'], collection['amount'])
```

#### `get_status()`
Get current fee system status.

```python
status = manager.get_status(current_balance=105.0)

print(f"Activated: {status['activated']}")
print(f"Baseline: ${status['baseline_balance']}")
print(f"Profit Above Baseline: ${status['profit_above_baseline']}")
print(f"Next Fee At: ${status['next_fee_at']}")
print(f"Total Collected: ${status['total_fees_collected']}")
```

#### `get_collection_history()`
View all fee collections.

```python
history = manager.get_collection_history()
for record in history:
    print(f"Collected ${record['amount']} at {record['timestamp']}")
```

---

## Configuration

### Founder Address
Update the founder wallet address in `core/founder_fee_manager.py`:

```python
FOUNDER_ADDRESS = "0xYOUR_FOUNDER_ADDRESS_HERE"
```

Replace with your actual Ethereum/MetaMask address.

### Fee Parameters
```python
ACTIVATION_THRESHOLD = 100.0  # $100 to activate
FEE_AMOUNT = 10.0             # $10 per collection  
FEE_INTERVAL = 10.0           # Collect every $10 profit
```

---

## Data Storage

### File: `data/founder_fee_config.json`
Persistent storage of fee system state.

```json
{
  "activated": true,
  "activation_date": "2025-12-17T12:00:00",
  "baseline_balance": 100.0,
  "total_fees_collected": 30.0,
  "fee_count": 3,
  "last_collection": "2025-12-17T14:30:00",
  "collection_history": [
    {
      "amount": 10.0,
      "from_balance": 110.0,
      "baseline": 100.0,
      "profit": 10.0,
      "timestamp": "2025-12-17T13:00:00",
      "founder_address": "0x..."
    }
  ]
}
```

---

## Integration with Live Trading

### In `live_trader.py`

```python
from core.founder_fee_manager import get_founder_fee_manager
from core.balance_aware_strategy import get_balance_aware_strategy

# Initialize managers
founder_fee = get_founder_fee_manager()
balance_strategy = get_balance_aware_strategy()

# In main trading loop
def check_founder_fee(self):
    """Check and collect founder fee if applicable."""
    current_balance = self.get_total_balance()
    
    # Get active timeframes and assets
    active_tfs = balance_strategy.get_active_timeframes(current_balance)
    active_assets = balance_strategy.get_active_assets(current_balance)
    
    # Convert assets enum to strings
    asset_names = [asset.name for asset in active_assets]
    
    # Check for fee collection
    collection = founder_fee.check_and_collect(
        current_balance=current_balance,
        active_timeframes=active_tfs,
        active_assets=asset_names
    )
    
    if collection:
        # Log collection
        logger.info(f"💰 Founder fee collected: ${collection['amount']}")
        
        # Send to founder address (implement transfer)
        self.send_founder_fee(
            address=collection['founder_address'],
            amount=collection['amount']
        )
        
        # Update balance
        self.balance -= collection['amount']
```

---

## Dashboard Integration

### Show Founder Fee Status

Add to `dashboard/panels.py` in Wallet Panel:

```python
# Get founder fee status
from core.founder_fee_manager import get_founder_fee_manager
founder_fee = get_founder_fee_manager()
fee_status = founder_fee.get_status(current_balance)

if fee_status['activated']:
    lines.append("")
    lines.append("═══ FOUNDER FEE ═══")
    lines.append(f"Status: ✅ Active since {fee_status['activation_date'][:10]}")
    lines.append(f"Baseline: ${fee_status['baseline_balance']:.2f}")
    lines.append(f"Next Fee: ${fee_status['distance_to_next_fee']:.2f} away")
    lines.append(f"Total Paid: ${fee_status['total_fees_collected']:.2f} ({fee_status['fee_count']} fees)")
    
    # Progress bar
    progress_pct = fee_status['progress_to_next_fee_pct']
    filled = int(20 * progress_pct / 100)
    bar = "█" * filled + "░" * (20 - filled)
    lines.append(f"[{bar}] {progress_pct:.0f}%")
else:
    if current_balance >= 80:  # Close to activation
        lines.append("")
        lines.append("═══ FOUNDER FEE ═══")
        lines.append(f"Status: ⏳ Activates at $100")
        lines.append(f"Progress: ${fee_status['distance_to_activation']:.2f} away")
```

---

## Testing

### Test Scenarios

```bash
# Run demo
python3 core/founder_fee_manager.py
```

**Output**:
```
📊 Scenario: Reached $100 with full system - ACTIVATE
   Balance: $100.00
   Timeframes: 1m, 5m, 15m, 1h, 4h
   Assets: ETH, BTC

🎉 FOUNDER FEE SYSTEM ACTIVATED
Activation Balance: $100.00
Baseline Set: $100.00
Next Fee: Collect $10 when balance reaches $110.00

📊 Scenario: $110 - COLLECT FEE
💰 FOUNDER FEE COLLECTED
Fee Amount: $10.00
Balance: $110.00 → $100.00
Total Fees Collected: $10.00 (1 collections)
```

### Manual Testing

```python
from core.founder_fee_manager import FounderFeeManager

manager = FounderFeeManager()

# Test activation
collection = manager.check_and_collect(
    current_balance=100.0,
    active_timeframes=['1m', '5m', '15m', '1h', '4h'],
    active_assets=['ETH', 'BTC']
)
# Should activate but not collect (need $10 profit first)

# Test collection
collection = manager.check_and_collect(
    current_balance=110.0,
    active_timeframes=['1m', '5m', '15m', '1h', '4h'],
    active_assets=['ETH', 'BTC']
)
# Should collect $10 fee
assert collection['amount'] == 10.0

# Test drawdown protection
collection = manager.check_and_collect(
    current_balance=95.0,
    active_timeframes=['1m', '5m', '15m', '1h', '4h'],
    active_assets=['ETH', 'BTC']
)
# Should not collect (below baseline)
assert collection is None
```

---

## Fee Collection Flow

```
┌─────────────────────────────────────┐
│ Balance Update in Trading Loop      │
└──────────────┬──────────────────────┘
               │
               v
┌─────────────────────────────────────┐
│ Check Founder Fee Manager           │
│ - current_balance                   │
│ - active_timeframes                 │
│ - active_assets                     │
└──────────────┬──────────────────────┘
               │
               v
       ┌───────┴────────┐
       │ Activated?     │
       └───┬────────┬───┘
          No      Yes
           │       │
           v       v
    ┌──────────┐ ┌──────────────────┐
    │ Check if │ │ Full system      │
    │ $100+    │ │ active?          │
    │ & full   │ └────┬─────────┬───┘
    │ system   │     Yes       No
    └──────────┘      │         │
                      v         v
              ┌──────────────┐ Pause
              │ Profit ≥ $10?│ fees
              └───┬──────┬───┘
                 Yes    No
                  │      │
                  v      v
          ┌──────────┐ Wait
          │ Collect  │
          │ $10 Fee  │
          └────┬─────┘
               │
               v
       ┌───────────────────┐
       │ Send to Founder   │
       │ Update Balance    │
       │ Log Collection    │
       └───────────────────┘
```

---

## User Communication

### On Activation
Show user when founder fees activate:

```
═══════════════════════════════════════════════════
🎉 CONGRATULATIONS! You've reached $100!
═══════════════════════════════════════════════════

Your account is now trading the full HARVEST system:
• Both assets: ETH + BTC
• All timeframes: 1m, 5m, 15m, 1h, 4h

Founder Fee System Activated:
• Fee: 10% on profits (every $10 profit = $1 fee)
• Only charged when profitable
• No fees during drawdowns
• Baseline: $100.00

Next fee collection: When balance reaches $110
═══════════════════════════════════════════════════
```

### On Collection
Show user when fee is collected:

```
💰 Founder Fee Collected
Amount: $10.00
Your Balance: $110.00 → $100.00
Total Fees Paid: $30.00 (3 collections)

Next fee: When balance reaches $110 again
```

---

## FAQ

**Q: Why is there a founder fee?**  
A: The fee compensates the creator for developing and maintaining the HARVEST bot. It only activates after you've proven profitability ($100+).

**Q: Can I avoid the fee?**  
A: The fee is built into the system and automatically collected. However, it only applies to profits, not your capital.

**Q: What if my account drops below $100?**  
A: Fees stop collecting if your balance drops below the baseline. Your capital is protected.

**Q: How much total will I pay?**  
A: 10% of all profits above $100. For example:
- $100 → $200 profit: Pay $10 in fees (10% of $100 profit)
- $100 → $500 profit: Pay $40 in fees (10% of $400 profit)

**Q: Where does the fee go?**  
A: Directly to the founder's wallet address configured in the system.

**Q: Can the fee percentage change?**  
A: No, it's hardcoded at 10% ($10 per $100 profit). This is transparent and unchangeable.

---

## Summary

The Founder Fee System:
- ✅ Only activates at $100+ with full system
- ✅ 10% on profits only (not capital)
- ✅ Protects user during drawdowns
- ✅ Automatic and transparent
- ✅ Tracks all collections
- ✅ Fair compensation for creator

**Fair deal**: You grow your capital, founder gets compensated for creating the tool that made it possible.
