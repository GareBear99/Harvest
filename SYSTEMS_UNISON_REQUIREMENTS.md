# Systems That Must Work in Unison

**Critical:** These systems interact with shared state and must be coordinated to prevent conflicts, race conditions, and data corruption.

---

## 🔴 Critical Unison Requirements

### 1. **Wallet State Coordination**

**Systems Involved:**
- `dashboard/terminal_ui.py` (reads wallet status)
- `core/simple_wallet_connector.py` (manages MetaMask connection)
- `core/auto_wallet_manager.py` (creates BTC wallet, tracks profit)
- `data/wallet_config.json` (shared state file)

**Current Problem:**
```
User presses W → Opens MetaMask browser
↓
User connects in browser → Downloads JSON to ~/Downloads
↓
Dashboard polls ~/Downloads → Finds JSON
↓
auto_wallet_manager reads wallet_config.json
↓
Dashboard reads wallet_config.json
↓
Both write to wallet_config.json ← RACE CONDITION!
```

**Race Conditions:**
- Dashboard and auto_wallet_manager both read/write `wallet_config.json`
- No file locking mechanism
- No atomic updates
- MetaMask connection timestamp could be overwritten
- BTC wallet creation could happen while dashboard is reading

**Solution - File Locking:**
```python
# In core/file_lock.py (NEW)
import fcntl
import contextlib

@contextlib.contextmanager
def file_lock(filepath, mode='r+'):
    """Thread-safe file locking"""
    with open(filepath, mode) as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
        try:
            yield f
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock

# Usage in auto_wallet_manager.py
def _save_wallet_config(self):
    with file_lock(self.config_path, 'w') as f:
        json.dump(self.wallet_config, f, indent=2)

# Usage in terminal_ui.py
def refresh_data(self):
    with file_lock(wallet_config_path, 'r') as f:
        config = json.load(f)
```

---

### 2. **Paper Trading Session State**

**Systems Involved:**
- `core/paper_trading_tracker.py` (manages session)
- `dashboard/terminal_ui.py` (displays status)
- `data/paper_trading_tracker.json` (shared state)

**Current Problem:**
```
Paper trading running → Records trade
↓
Dashboard refreshes every 10s → Reads tracker file
↓
Trade recorded during read ← INCOMPLETE DATA READ
```

**Race Conditions:**
- Dashboard could read file while trade is being written
- Partial JSON read if file is corrupted mid-write
- Trade count mismatch between memory and disk

**Solution - Atomic Writes:**
```python
# In paper_trading_tracker.py
def _save_tracker(self):
    """Atomic write with temp file + rename"""
    temp_file = f"{self.tracker_file}.tmp"
    
    # Write to temp file first
    with open(temp_file, 'w') as f:
        json.dump(self.data, f, indent=2)
    
    # Atomic rename (POSIX guarantee)
    os.replace(temp_file, self.tracker_file)
```

---

### 3. **Backtest State Coordination**

**Systems Involved:**
- `dashboard/backtest_control.py` (BacktestController)
- Actual backtest process (runs in separate thread/process)
- `data/backtest_results/` (result files)

**Current Problem:**
```
User starts backtest → Background thread spawned
↓
Dashboard shows "Running..."
↓
User presses "Stop" → Sets stop flag
↓
Backtest writes partial results
↓
Dashboard tries to read results ← INCOMPLETE/CORRUPTED
```

**Race Conditions:**
- No inter-process communication
- Dashboard doesn't know when backtest actually completes
- Result files could be written while being read
- Stop signal not properly communicated

**Solution - State Machine with Locks:**
```python
# In backtest_control.py
import threading
from enum import Enum

class BacktestState(Enum):
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"

class BacktestController:
    def __init__(self):
        self.state = BacktestState.IDLE
        self.state_lock = threading.Lock()
        self.backtest_thread = None
        
    def start_backtest(self, seed, timeframe):
        with self.state_lock:
            if self.state != BacktestState.IDLE:
                raise ValueError(f"Cannot start: state is {self.state}")
            self.state = BacktestState.STARTING
        
        # Start in separate thread
        self.backtest_thread = threading.Thread(
            target=self._run_backtest,
            args=(seed, timeframe)
        )
        self.backtest_thread.start()
    
    def _run_backtest(self, seed, timeframe):
        with self.state_lock:
            self.state = BacktestState.RUNNING
        
        try:
            # Run backtest...
            result = execute_backtest(seed, timeframe)
            
            with self.state_lock:
                self.state = BacktestState.COMPLETED
        except Exception as e:
            with self.state_lock:
                self.state = BacktestState.FAILED
    
    def get_state(self):
        with self.state_lock:
            return self.state
```

---

### 4. **Debug Daemon Session Management**

**Systems Involved:**
- `core/debug_daemon.py` (singleton daemon)
- `dashboard/terminal_ui.py` (main dashboard)
- `dashboard/debug_terminal.py` (debug view)
- Multiple log files per session

**Current Problem:**
```
Dashboard logs action → daemon.actions_log.append()
↓
User opens debug terminal → Reads daemon.actions_log
↓
Dashboard logs another action while debug terminal rendering
↓
List modified during iteration ← RUNTIME ERROR
```

**Race Conditions:**
- `actions_log` list modified while being iterated
- Session cleanup could delete files while debug terminal reading
- Multiple threads accessing daemon singleton

**Solution - Thread-Safe Daemon:**
```python
# In debug_daemon.py
import threading
from copy import deepcopy

class DebugDaemon:
    def __init__(self):
        self._lock = threading.RLock()  # Reentrant lock
        self.actions_log = []
        self.validations_log = []
        # ... other logs ...
    
    def log_action(self, ...):
        with self._lock:
            # ... existing code ...
            self.actions_log.append(action_entry)
    
    def get_actions_snapshot(self):
        """Thread-safe snapshot for rendering"""
        with self._lock:
            return deepcopy(self.actions_log)
    
    def close_session(self):
        with self._lock:
            # ... existing close logic ...
            self._cleanup_old_sessions()

# In debug_terminal.py
def _render_live_log(daemon, page, selected_session):
    # Get snapshot instead of direct reference
    actions = daemon.get_actions_snapshot()
    # Now safe to iterate without lock
```

---

### 5. **Balance & Position State**

**Systems Involved:**
- `core/position_size_limiter.py` (calculates position limits)
- `core/slot_allocation_strategy.py` (determines active slots)
- `core/profit_locker.py` (locks profits)
- `dashboard/terminal_ui.py` (displays balance)
- Paper/Live trading systems (modify balance)

**Current Problem:**
```
Balance: $100
↓
Dashboard reads balance → Shows $100
↓
Trade executes → Balance becomes $95 (fee paid)
↓
Dashboard still shows $100
↓
Slot calculator uses $100 → Wrong slot count
↓
Position limiter uses $100 → Wrong limit
```

**Race Conditions:**
- Balance read from multiple places without coordination
- No "balance version" or timestamp
- Stale data used for critical decisions

**Solution - Balance Manager with Versioning:**
```python
# In core/balance_manager.py (NEW)
import threading
from datetime import datetime

class BalanceManager:
    """Single source of truth for balance"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._balance = 10.0
        self._version = 0
        self._last_updated = datetime.now()
    
    def get_balance(self):
        """Get current balance with version"""
        with self._lock:
            return {
                'balance': self._balance,
                'version': self._version,
                'updated_at': self._last_updated
            }
    
    def update_balance(self, new_balance, reason):
        """Atomic balance update"""
        with self._lock:
            old_balance = self._balance
            self._balance = new_balance
            self._version += 1
            self._last_updated = datetime.now()
            
            # Log to debug daemon
            daemon.log_action(
                action_name="Balance Update",
                category="balance_change",
                details={
                    'old_balance': old_balance,
                    'new_balance': new_balance,
                    'reason': reason,
                    'version': self._version
                },
                expected_outcome={'success': True}
            )
    
    def with_balance(self, func):
        """Execute function with locked balance"""
        with self._lock:
            return func(self._balance)

# Usage
balance_mgr = BalanceManager()

# In position_size_limiter.py
def get_max_position(self):
    return balance_mgr.with_balance(
        lambda balance: self._calculate_limit(balance)
    )
```

---

### 6. **Dashboard Refresh Cycle**

**Systems Involved:**
- `dashboard/terminal_ui.py` (auto-refresh every 10s)
- Manual refresh (R key)
- Data sources (wallet, balance, positions, seeds)

**Current Problem:**
```
Auto-refresh starts (t=0)
↓
Reads wallet (takes 2s)
↓
User presses R (t=1.5)
↓
Manual refresh starts
↓
Both refreshes running simultaneously
↓
Data sources accessed twice
↓
Status bar shows stale results
```

**Race Conditions:**
- Multiple refreshes can run concurrently
- No refresh "in progress" flag
- Status bar race condition (which refresh wins?)
- Wasted API calls / file reads

**Solution - Refresh Coordinator:**
```python
# In terminal_ui.py
class RefreshCoordinator:
    def __init__(self):
        self._lock = threading.Lock()
        self._refreshing = False
        self._last_refresh = 0
        self._min_interval = 0.5  # 500ms minimum between refreshes
    
    def should_refresh(self):
        """Check if refresh is allowed"""
        with self._lock:
            current_time = time.time()
            if self._refreshing:
                return False
            if current_time - self._last_refresh < self._min_interval:
                return False
            return True
    
    def start_refresh(self):
        """Mark refresh as started"""
        with self._lock:
            if self._refreshing:
                return False
            self._refreshing = True
            return True
    
    def end_refresh(self):
        """Mark refresh as completed"""
        with self._lock:
            self._refreshing = False
            self._last_refresh = time.time()

class TerminalDashboard:
    def __init__(self):
        # ... existing code ...
        self.refresh_coordinator = RefreshCoordinator()
    
    def refresh_data(self):
        if not self.refresh_coordinator.start_refresh():
            return  # Refresh already in progress
        
        try:
            # ... existing refresh logic ...
            pass
        finally:
            self.refresh_coordinator.end_refresh()
```

---

## 📊 Unison Coordination Matrix

| System | Writes To | Reads From | Needs Lock | Priority |
|--------|-----------|------------|------------|----------|
| Dashboard | None | wallet_config, paper_tracker, balance | ❌ | HIGH |
| Wallet Connector | wallet_config | None | ✅ | CRITICAL |
| Auto Wallet Manager | wallet_config | wallet_config | ✅ | CRITICAL |
| Paper Trading | paper_tracker | None | ✅ | HIGH |
| Backtest Controller | backtest_results/ | None | ✅ | MEDIUM |
| Debug Daemon | logs/debug_daemon/ | None | ✅ | HIGH |
| Balance Manager | (in-memory) | paper_tracker, live_trader | ✅ | CRITICAL |

---

## 🛠️ Implementation Plan

### Phase 1: Critical Locks (Immediate)
1. ✅ Add file locking to `wallet_config.json`
2. ✅ Implement atomic writes for `paper_trading_tracker.json`
3. ✅ Add refresh coordinator to dashboard
4. ✅ Make debug daemon thread-safe

### Phase 2: State Management (Next)
1. Create BalanceManager singleton
2. Add state machine to BacktestController
3. Implement balance versioning
4. Add state transition logging to daemon

### Phase 3: Integration (Final)
1. Update all systems to use BalanceManager
2. Add inter-process signals for backtest
3. Implement daemon snapshot API
4. Add unison validation tests

---

## 🧪 Testing Unison Issues

### Test 1: Concurrent Wallet Updates
```python
# Simulate race condition
def test_concurrent_wallet_write():
    threads = []
    for i in range(10):
        t = threading.Thread(target=update_wallet_config, args=(f"address_{i}",))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Verify: config should have one valid address, not corrupted
    config = load_wallet_config()
    assert config['metamask']['address'].startswith('address_')
```

### Test 2: Refresh Rate Limiting
```python
def test_rapid_refresh():
    dashboard = TerminalDashboard()
    
    # Trigger 10 rapid refreshes
    for i in range(10):
        dashboard.refresh_data()
    
    # Verify: Only 1-2 actually executed (debounced)
    assert dashboard.refresh_count <= 2
```

### Test 3: Debug Daemon Thread Safety
```python
def test_daemon_concurrent_access():
    daemon = get_daemon()
    
    # Log from multiple threads
    threads = []
    for i in range(100):
        t = threading.Thread(target=log_test_action, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Verify: All 100 actions logged, no corruption
    assert len(daemon.actions_log) == 100
```

---

## 📋 Checklist for Adding New Systems

Before adding ANY new system that accesses shared state:

- [ ] Identify all shared files/resources
- [ ] Determine if writes are atomic
- [ ] Add file locking if multiple writers
- [ ] Use coordinator pattern if multiple readers during write
- [ ] Add debug daemon logging for all state changes
- [ ] Write concurrent access tests
- [ ] Document in this file

---

## 🎯 Key Principle

**"Single Writer, Multiple Readers"**
- Each piece of state should have ONE authoritative writer
- All other systems are readers only
- Writers use locks
- Readers get snapshots
- All changes logged to debug daemon

**Examples:**
- ✅ `wallet_config.json` → AutoWalletManager writes, Dashboard reads
- ✅ `paper_trading_tracker.json` → PaperTradingTracker writes, Dashboard reads
- ✅ Balance → BalanceManager writes, Everyone reads
- ✅ Debug logs → DebugDaemon writes, DebugTerminal reads

---

## 🚨 Current Critical Issues

### CRITICAL - Must Fix Before Production
1. **wallet_config.json** - No file locking (data corruption risk)
2. **Dashboard refresh** - No rate limiting (wasted resources)
3. **Debug daemon** - Not thread-safe (runtime errors possible)

### HIGH - Should Fix Soon
1. **paper_trading_tracker.json** - No atomic writes (partial reads possible)
2. **Balance state** - No single source of truth (stale data risk)
3. **Backtest coordination** - No state machine (unclear status)

### MEDIUM - Nice to Have
1. **Session cleanup** - Could interfere with active reads
2. **Modal state** - No coordination between modals
3. **Seed browser** - Pagination state not protected

---

**Estimated Time to Fix Critical Issues:** 4-6 hours
**Estimated Time for Full Unison Implementation:** 10-12 hours
