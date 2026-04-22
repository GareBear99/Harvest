# Comprehensive System Analysis - Harvest Trading System

## Current Performance (20 days, Dec 16 2025)
- **Combined**: 57.1% win rate, 7 trades, +2.73% return
- **ETH 15m**: 66.7% win rate, 3 trades, +$0.42
- **BTC 15m**: 66.7% win rate, 3 trades, +$0.57  
- **BTC 4h**: 0% win rate, 1 trade, -$0.45
- **Gap from target**: 72% - 57.1% = **14.9% below target**

## Existing Components

### 1. **intelligent_learner.py** (441 lines) ✅
**Status**: Operational - categorizes WHY trades fail
**Features**:
- 6 error categories: trend_reversal, false_breakout, volatility_spike, time_decay, wrong_confluence, premature_exit
- Tracks recurring vs new errors
- Identifies problematic features
- Adaptive weight adjustments (-0.10 first, -0.15 second, -0.25 persistent)
- Saves learning data to JSON

**Current Learning**:
- false_breakout: 4 occurrences (recurring)
- Worst features: volume_ratio (0% accuracy), roc_10 (0% accuracy)
- Recommendation: "Increase volume requirement or add momentum confirmation"

**Gap**: Does NOT auto-adjust filter thresholds - only suggests adjustments

### 2. **adaptive_optimizer.py** (294 lines) ⚠️
**Status**: Exists but NOT integrated into main system
**Features**:
- Records performance history
- Auto-adjusts thresholds based on win rate
- Target: 75-90% win rate, 5-15 trades/month
- Adjustment logic:
  - WR < 70%: tighten (+0.02 conf, +0.05 vol)
  - WR > 95% & <5 trades/month: loosen
  - >20 trades/month & WR<80%: tighten aggressively
  
**Adjustable Parameters**:
```python
'confidence': 0.69 (range 0.50-0.90)
'adx': 25.0 (range 15-40)
'roc': -1.0
'volume': 1.15 (range 1.0-2.0)
'trend_consistency': 0.55 (range 0.30-0.80)
'min_win_rate': 0.72 (range 0.65-0.85)
```

**Gap**: 
- Not connected to backtest_90_complete.py
- Adjusts ALL parameters together (not timeframe-specific)
- No severity-based scaling based on distance from target
- Doesn't integrate with intelligent_learner insights

### 3. **strategy_learner.py** (395 lines) ✅
**Status**: Operational - saves 80%+ strategies
**Features**:
- Records trades in sessions
- Analyzes when session complete
- Saves strategies with 80%+ win rate
- Tracks filter configurations
- Can suggest filters from best strategies

**Current State**: 0 saved strategies (system just built)

**Gap**: 
- Only saves AFTER achieving 80%
- Doesn't help BUILD toward 80% from current 57%
- No bootstrap/cold-start logic

### 4. **high_accuracy_filter.py** (updated today) ✅
**Status**: Operational with timeframe-specific thresholds
**Features**:
- 10 filter criteria
- Timeframe detection from candle intervals
- Dynamic thresholds per timeframe:
  - 15m: confidence 0.72, volume 1.20x, trend 0.60 (strictest)
  - 1h: confidence 0.68, volume 1.12x, trend 0.52 (moderate)
  - 4h: confidence 0.65, volume 1.05x, trend 0.48 (lenient)

**Gap**:
- Thresholds are HARDCODED
- No dynamic adjustment mechanism
- Doesn't accept updated thresholds from external system

### 5. **prediction_tracker.py** (437 lines) ✅
**Status**: Operational - tracks predictions
**Features**:
- Generates predictions with win probability
- Stores in SQLite database
- Calculates prediction errors
- Updates feature weights (NOT filter thresholds)
- Quality tier assignment (S/A/B/C)

**Gap**:
- Adjusts feature WEIGHTS for confidence calculation
- Does NOT adjust filter THRESHOLDS
- No per-timeframe tracking

### 6. **backtest_90_complete.py** (main engine) ✅
**Status**: Operational - core trading loop
**Features**:
- Multi-timeframe execution (15m, 1h, 4h)
- Integrated intelligent_learner (as of today)
- Leverage scaling (25x)
- Tier management
- Profit locking
- Trade validation

**Gap**:
- No win rate monitoring loop
- No automatic threshold adjustment
- No per-timeframe statistics tracking
- Only reports final results, not rolling windows

### 7. **database_schema.py** (TradeDatabase) ✅
**Status**: Operational - SQLite storage
**Features**:
- Stores predictions and outcomes
- Tracks feature weights
- Weight update history
- Similar trade lookup

**Gap**: 
- No per-timeframe strategy table
- No rolling window statistics
- No adjustment history tracking

## What's Missing for Adaptive Evolution

### Critical Gaps:
1. **No rolling win rate tracking per timeframe**
   - Need: Last 5, 10, 20, 50 trades windows
   - Current: Only total win rate at end

2. **No automatic threshold adjustment loop**
   - Need: After every N trades, check & adjust
   - Current: Manual adjustment only

3. **No severity-based adjustment scaling**
   - Need: Larger adjustments when further from 72%
   - Current: Fixed adjustment amounts

4. **No timeframe-independent strategy tracking**
   - Need: Each TF learns separately
   - Current: Global statistics only

5. **No bootstrap/cold-start logic**
   - Need: Start conservative, learn, optimize
   - Current: Fixed initial thresholds

6. **No connection between intelligent_learner and filter adjustments**
   - Need: false_breakout → auto-increase volume
   - Current: Manual interpretation of learning

7. **No strategy persistence per timeframe**
   - Need: Save/load proven TF-specific configs
   - Current: Only global strategy saving

## Proposed Solution Architecture

### New Components Needed:

#### 1. TimeframeStrategyManager
- Tracks each TF independently (15m, 1h, 4h)
- Rolling windows: last 5, 10, 20, 50 trades
- Current filter config per TF
- Adjustment history per TF
- Phase tracking (exploration → calibration → optimization → mastery)
- Strategy confidence score (builds with trade count)

#### 2. AdaptiveThresholdAdjuster
- Calculates distance from 72% target
- Severity formula: `severity = (72 - current_wr) / 100`
- Applies adjustments: `new_value = old_value * (1 + severity * direction)`
- Feature-specific adjustments from intelligent_learner
- Safety bounds to prevent extreme changes
- Integration with timeframe-specific thresholds

#### 3. BootstrapLearner
- Phase 1 (0-10 trades): Exploration - loose filters, gather data
- Phase 2 (10-30 trades): Calibration - analyze patterns, narrow ranges
- Phase 3 (30-100 trades): Optimization - fine-tune toward 72%
- Phase 4 (100+ trades): Mastery - maintain 72-80%, lock strategies

#### 4. RollingStatsTracker
- Per-timeframe windows
- Metrics: WR, avg duration, avg PnL, error types
- Trend detection (improving vs declining)
- Adjustment effectiveness tracking

### Integration Points:

#### Modify high_accuracy_filter.py:
```python
def update_thresholds(self, timeframe: str, new_thresholds: Dict):
    """Accept dynamic thresholds from TimeframeStrategyManager"""
    pass
```

#### Modify backtest_90_complete.py:
```python
# After each trade
self.strategy_manager.record_trade(timeframe, outcome)

# Every 5 trades per timeframe
if trade_count % 5 == 0:
    self.check_and_adjust_strategy(timeframe)
```

#### Connect intelligent_learner to adjustments:
```python
# When false_breakout identified
if error_category == 'false_breakout':
    adjustments = {
        'min_volume': +0.10,  # Increase 10%
        'min_roc': -0.3       # Stricter momentum
    }
    apply_adjustments(timeframe, adjustments)
```

## Adjustment Logic

### Win Rate Zones:
- **>80%**: Optimal - maintain (can slightly loosen for more trades)
- **72-80%**: Sweet spot - maintain, only adjust if trending down
- **65-72%**: Below target - gradual adjustment (5-10% tighter)
- **50-65%**: Significant gap - moderate adjustment (10-20% tighter)
- **<50%**: Critical - aggressive adjustment (20-30% tighter)

### Current System: 57.1% WR
- Zone: Significant gap
- Distance: 14.9% below target
- Recommended severity: 0.149 (15% adjustment)
- Action: Moderate tightening of filters

### Example Adjustments (57% → 72%):
```
15m timeframe:
  confidence: 0.72 → 0.72 * 1.15 = 0.83
  volume: 1.20 → 1.20 * 1.15 = 1.38
  trend: 0.60 → 0.60 * 1.10 = 0.66
  
Result: Stricter filters = fewer but higher quality trades
```

## Implementation Priority

### Phase 1 (Foundation): 
1. TimeframeStrategyManager class
2. RollingStatsTracker integration
3. Per-timeframe trade recording

### Phase 2 (Adjustment Logic):
1. AdaptiveThresholdAdjuster class
2. Severity-based calculation
3. Safety bounds

### Phase 3 (Integration):
1. Modify high_accuracy_filter.py for dynamic thresholds
2. Add adjustment loop to backtest_90_complete.py
3. Connect intelligent_learner to adjustments

### Phase 4 (Bootstrap):
1. BootstrapLearner class
2. Phase detection
3. Cold-start strategy

### Phase 5 (Persistence):
1. Save TF-specific strategies to database
2. Load best historical configs on restart
3. Strategy locking when 72%+ achieved

## Success Metrics
- ✅ Each timeframe learns independently
- ✅ Win rate converges toward 72-80% range
- ✅ Adjustments proportional to distance from target
- ✅ System builds from zero without saved strategies
- ✅ Strategies persist and reload correctly
- ✅ Intelligent learner insights auto-applied to filters
