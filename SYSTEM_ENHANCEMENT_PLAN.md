# System Enhancement Plan - Production Grade Unification

**Date:** December 26, 2025  
**Objective:** Unify all dashboard systems with comprehensive tracking and improve user experience

---

## Systems Requiring Unified Tracking

### ✅ Already Tracked by Debug Daemon
1. **Dashboard Operations** - All key presses, navigation, modal switching
2. **Data Refresh** - Manual (R key) and automatic (10s interval)
3. **Modal Operations** - Help, Seeds, ML, Backtest, Debug terminal

### ⚠️ Need Integration with Debug Daemon

#### 1. Wallet System (`core/simple_wallet_connector.py`, `core/auto_wallet_manager.py`)
**Current State:**
- Browser-based MetaMask connection
- Downloads JSON file to communicate back
- Auto-creates BTC wallet
- Tracks profit threshold ($100 → auto-fund $50 to BTC)

**Missing Tracking:**
- [ ] Wallet connection attempts (success/failure)
- [ ] MetaMask popup detection
- [ ] JSON file download verification
- [ ] BTC wallet creation events
- [ ] Profit threshold triggers
- [ ] Auto-funding events

**Recommendation:**
```python
# In simple_wallet_connector.py
def connect(self):
    action_id = daemon.log_action(
        action_name="Wallet Connect - MetaMask",
        category="wallet_operation",
        details={'method': 'browser_popup', 'port': 8765},
        expected_outcome={'success': True, 'browser_opened': True}
    )
    
    # Open browser...
    
    daemon.validate_action(action_id, 
        {'success': True, 'browser_opened': True},
        [{'name': 'browser_launch', 'level': 'CRITICAL', ...}]
    )
```

#### 2. Backtest System (`dashboard/backtest_control.py`)
**Current State:**
- Start/stop backtest operations
- View history and results
- Export reports

**Missing Tracking:**
- [ ] Backtest start timestamp
- [ ] Seed selection
- [ ] Execution duration
- [ ] Result generation time
- [ ] Export operations
- [ ] Backtest crashes/errors

**Recommendation:**
```python
# In BacktestController
def start_backtest(self, seed, timeframe):
    action_id = daemon.log_action(
        action_name=f"Backtest Start - Seed {seed}",
        category="backtest_operation",
        details={'seed': seed, 'timeframe': timeframe, 'mode': 'BACKTEST'},
        expected_outcome={'success': True, 'started': True}
    )
```

#### 3. Paper Trading System (`core/paper_trading_tracker.py`)
**Current State:**
- Tracks 48-hour paper trading period
- Records trades with gas fees
- Validates requirements (duration, trades, P&L)

**Missing Tracking:**
- [ ] Session start/stop events
- [ ] Trade execution logging
- [ ] Requirement check failures
- [ ] Approval/rejection for live trading
- [ ] BTC stair-climbing events

**Recommendation:**
```python
# In PaperTradingTracker
def start_paper_trading(self, starting_balance):
    action_id = daemon.log_action(
        action_name="Paper Trading Start",
        category="paper_trading",
        details={'balance': starting_balance, 'slots': active_slots},
        expected_outcome={'success': True, 'session_active': True}
    )
```

#### 4. Position & Risk Systems
**Systems:**
- `core/position_size_limiter.py` - $100 cap enforcement
- `core/risk_governor.py` - Risk assessment
- `core/slot_allocation_strategy.py` - Stair-climbing logic

**Missing Tracking:**
- [ ] Position limit calculations
- [ ] Risk governor decisions
- [ ] Slot allocation changes
- [ ] Limit violations

#### 5. Data Refresh System
**Current State:**
- Auto-refreshes every 10 seconds
- Manual refresh with R key
- Pulls from multiple sources (wallet, balance, positions, seeds)

**Missing Tracking:**
- [ ] Which data sources were accessed
- [ ] How long each source took
- [ ] Any data source failures
- [ ] Cache hits/misses

**Recommendation:**
```python
# In terminal_ui.py refresh_data()
action_id = daemon.log_action(
    action_name="Data Refresh",
    category="data_refresh",
    details={
        'triggered_by': 'user' if manual else 'automatic',
        'sources': ['wallet', 'balance', 'positions', 'seeds'],
        'timestamp': time.time()
    },
    expected_outcome={'success': True, 'all_sources_updated': True}
)

# Track each source
for source in sources:
    source_start = time.time()
    # ... fetch data ...
    source_time = time.time() - source_start
    
    # Log sub-action for each source
    if source_failed:
        daemon.log_error(f"Data source {source} failed", context={'elapsed': source_time})
```

---

## Help Screen Enhancement - Layman's Terms

### Current Issues
1. Too technical ("seed combinations", "ML control panel")
2. Assumes user knows trading concepts
3. Doesn't emphasize the "just connect MetaMask" simplicity
4. Missing quick-start instructions

### Proposed Simplified Help Screen

**Key Messages:**
1. "Connect MetaMask → We handle everything else"
2. "Watch your money grow automatically"
3. "We create wallets, manage trades, handle fees"
4. Plain English for all features

---

## Production-Grade Enhancements

### 1. Unified Action Categories
```python
# Standardize all action categories
ACTION_CATEGORIES = {
    'dashboard_operation': 'User navigation, key presses, modal switching',
    'wallet_operation': 'MetaMask connect, BTC wallet, profit tracking',
    'backtest_operation': 'Start/stop backtests, result exports',
    'paper_trading': 'Paper trading session management',
    'live_trading': 'Live trading operations (when enabled)',
    'data_refresh': 'Data loading from all sources',
    'system': 'Startup, shutdown, errors, crashes',
    'critical_operation': 'Operations requiring retry logic'
}
```

### 2. Standardized Validation Checks
```python
# Common validation patterns
VALIDATION_TEMPLATES = {
    'operation_success': {
        'name': 'operation_success',
        'level': 'CRITICAL',
        'function': lambda a, e: a.get('success') == e.get('success'),
        'expected': True
    },
    'response_time_5s': {
        'name': 'response_time',
        'level': 'WARNING',
        'function': lambda a, e: a.get('elapsed_time', 0) < 5.0,
        'expected': True,
        'details': {'threshold_seconds': 5.0}
    },
    'response_time_30s': {
        'name': 'timeout_check',
        'level': 'CRITICAL',
        'function': lambda a, e: a.get('elapsed_time', 0) < 30.0,
        'expected': True,
        'details': {'threshold_seconds': 30.0}
    },
    'data_updated': {
        'name': 'data_updated',
        'level': 'CRITICAL',
        'function': lambda a, e: a.get('data_updated') == True,
        'expected': True
    }
}
```

### 3. Enhanced Status Bar
**Current:**
```
🐛 42A·0E·2W  📄 Paper: 12.5/48h • 23T • +$45.67
```

**Proposed Enhancement:**
```
🐛 42A·0E·2W  📄 Paper: 12.5/48h • 23T • +$45.67  🔗 Wallet: 0x742d...  ⚡ Live: ON
   │  │  │                                          │                   └─ Trading status
   │  │  └─ Warnings                                └─ Wallet connection
   │  └──── Errors
   └────── Actions
```

### 4. Health Monitoring Dashboard
**Add "Y" key for System Health view:**
- Overall system status (HEALTHY/DEGRADED/CRITICAL)
- All system components status
- Recent errors (last 10)
- Response time metrics
- Memory usage
- Session age

### 5. Retry Logic Wrapper
**Create universal retry decorator:**
```python
def with_retry(max_attempts=3, category='critical_operation'):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                action_id = daemon.log_action(
                    action_name=f"{func.__name__} (Attempt {attempt+1}/{max_attempts})",
                    category=category,
                    details={'attempt': attempt+1, 'max_attempts': max_attempts},
                    expected_outcome={'success': True}
                )
                
                try:
                    result = func(*args, **kwargs)
                    daemon.validate_action(action_id, 
                        {'success': True, 'attempt': attempt+1},
                        [VALIDATION_TEMPLATES['operation_success']]
                    )
                    return result
                except Exception as e:
                    daemon.validate_action(action_id,
                        {'success': False, 'attempt': attempt+1, 'error': str(e)},
                        [VALIDATION_TEMPLATES['operation_success']]
                    )
                    if attempt < max_attempts - 1:
                        time.sleep(1.0 * (attempt + 1))  # Exponential backoff
                        continue
                    raise
        return wrapper
    return decorator

# Usage:
@with_retry(max_attempts=3, category='wallet_operation')
def connect_metamask():
    # ... connection logic ...
    pass
```

---

## Implementation Priority

### Phase 1: Critical Tracking (Immediate)
1. **Wallet operations** - User's first touchpoint
2. **Paper trading** - Core validation mechanism
3. **Backtest tracking** - Most-used feature

### Phase 2: Data & Risk (Next Sprint)
1. **Data refresh tracking** - Performance monitoring
2. **Position/Risk systems** - Safety critical
3. **Slot allocation** - Profit progression

### Phase 3: User Experience (Polish)
1. **Simplified help screen** - Lower barrier to entry
2. **System health dashboard** - Proactive monitoring
3. **Enhanced status bar** - More visibility

---

## Benefits

### For Users
- ✅ Complete transparency of what system is doing
- ✅ Immediate feedback on all actions
- ✅ Troubleshooting made easy (check debug terminal)
- ✅ Confidence through visibility

### For Developers
- ✅ Comprehensive audit trail
- ✅ Easy debugging with timestamped logs
- ✅ Performance metrics built-in
- ✅ Standardized retry/error handling

### For Production
- ✅ Zero-downtime monitoring
- ✅ Automatic error detection
- ✅ Historical session analysis
- ✅ Compliance-ready logging

---

## Next Steps

1. **Review this plan** - Validate approach
2. **Implement wallet tracking** - Highest user impact
3. **Update help screen** - Improve onboarding
4. **Add system health view** - Proactive monitoring
5. **Standardize retry logic** - Reduce failures

**Estimated Timeline:**
- Phase 1: 4-6 hours
- Phase 2: 3-4 hours
- Phase 3: 2-3 hours
- **Total: ~10-13 hours to production-grade unification**
