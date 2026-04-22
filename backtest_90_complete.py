#!/usr/bin/env python3
"""
Multi-Timeframe Daily Profit System
Trades on 1m, 5m, 15m, 1h, and 4h timeframes simultaneously for high-frequency opportunities

Supports:
- Single seed testing: --seed <number>
- Batch seed testing: --test-seeds-file <json_file>
"""

import json
import sys
import os
import random
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.indicators_backtest import BacktestIndicators
from core.tier_manager import TierManager
from core.profit_locker import ProfitLocker
from core.leverage_scaler import LeverageScaler
from core.processing_manager import ProcessingManager
from core.position_size_limiter import get_position_limiter
from core.founder_fee_manager import FounderFeeManager
from analysis.ml_confidence_model import extract_features, calculate_rule_based_confidence
from analysis.prediction_tracker import PredictionTracker
from analysis.high_accuracy_filter import HighAccuracyFilter, get_position_size_multiplier
from analysis.reversal_detector import ReversalDetector
from ml.intelligent_learner import IntelligentLearner
from ml.timeframe_strategy_manager import TimeframeStrategyManager
from ml.adaptive_threshold_adjuster import AdaptiveThresholdAdjuster
from ml.ml_config import get_ml_config
from strategies.timeframe_strategy import create_strategy
from datetime import datetime
from collections import defaultdict


# Timeframe configurations
TIMEFRAME_CONFIGS = {
    '1m': {
        'aggregation_minutes': 1,
        'tp_multiplier': 1.2,
        'sl_multiplier': 0.6,
        'time_limit_minutes': 30,  # 30 minutes max hold
        'position_size_multiplier': 0.3,  # Smaller positions for ultra-fast trades
        'confidence_threshold': 0.82  # Very high confidence required
    },
    '5m': {
        'aggregation_minutes': 5,
        'tp_multiplier': 1.3,
        'sl_multiplier': 0.65,
        'time_limit_minutes': 60,  # 1 hour max hold
        'position_size_multiplier': 0.4,  # Small positions for fast trades
        'confidence_threshold': 0.80  # High confidence required
    },
    '15m': {
        'aggregation_minutes': 15,
        'tp_multiplier': 1.5,
        'sl_multiplier': 0.75,
        'time_limit_minutes': 180,  # 3 hours
        'position_size_multiplier': 0.5,
        'confidence_threshold': 0.75
    },
    '1h': {
        'aggregation_minutes': 60,
        'tp_multiplier': 2.0,
        'sl_multiplier': 1.0,
        'time_limit_minutes': 720,  # 12 hours
        'position_size_multiplier': 1.0,  # Baseline
        'confidence_threshold': 0.75
    },
    '4h': {
        'aggregation_minutes': 240,
        'tp_multiplier': 2.5,
        'sl_multiplier': 1.25,
        'time_limit_minutes': 1440,  # 24 hours
        'position_size_multiplier': 1.5,  # Higher conviction
        'confidence_threshold': 0.63
    }
}


class MultiTimeframeBacktest:
    def __init__(self, data_file: str, starting_balance: float = 10.0, seed: Optional[int] = None, 
                 balance_aware: bool = False):
        self.data_file = data_file
        self.symbol = data_file.split('/')[-1].split('_')[0].upper()
        self.starting_balance = starting_balance
        self.balance_aware = balance_aware
        
        # Set seed for deterministic behavior
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            self.seed = seed
            print(f"🎲 Deterministic mode: seed={seed}")
        else:
            self.seed = None
        
        # Load data (handle both formats)
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        # Handle both list format and dict format
        if isinstance(data, list):
            self.candles = data
        elif isinstance(data, dict) and 'candles' in data:
            self.candles = data['candles']
        else:
            raise ValueError(f"Unknown data format in {data_file}")
        
        # Load ML configuration
        self.ml_config = get_ml_config()
        
        # Print ML status for this asset
        ml_enabled = self.ml_config.is_ml_enabled(self.symbol)
        if ml_enabled:
            print(f"🤖 {self.symbol}: ML ENABLED - Adaptive learning active")
        else:
            print(f"📋 {self.symbol}: ML DISABLED - Using BASE_STRATEGY only")
        
        # Balance-aware slot allocation filtering
        if self.balance_aware:
            from core.slot_allocation_strategy import get_slot_allocation_strategy, Asset
            self.slot_strategy = get_slot_allocation_strategy()
            
            # Get slot allocation for starting balance
            slot_summary = self.slot_strategy.get_slot_summary(starting_balance)
            
            if slot_summary['status'] == 'INSUFFICIENT_BALANCE':
                print(f"\n⚠️  {slot_summary['message']}")
                self.active_timeframes = []
                return
            
            # Check if this asset is active
            asset_enum = Asset.ETH if self.symbol == 'ETH' else Asset.BTC
            active_assets = self.slot_strategy.get_active_assets(starting_balance)
            
            if asset_enum not in active_assets:
                print(f"\n⚠️  {self.symbol} not active at ${starting_balance:.2f} balance")
                print(f"   Active assets: {', '.join([a.name for a in active_assets])}")
                print(f"   Active slots: {slot_summary['active_slots']}/10")
                self.active_timeframes = []
                return
            
            # Get active timeframes from slot allocation
            active_tfs = slot_summary['active_timeframes']
            
            # Filter timeframe configs to only active ones
            filtered_configs = {tf: cfg for tf, cfg in TIMEFRAME_CONFIGS.items() if tf in active_tfs}
            
            # Get asset-specific slot numbers
            asset_slots = self.slot_strategy.get_active_slots_for_asset(starting_balance, asset_enum)
            
            print(f"\n💰 Slot-Based Allocation: ${starting_balance:.2f}")
            print(f"   Total Slots: {slot_summary['active_slots']}/10")
            print(f"   {self.symbol} Slots: {asset_slots}")
            print(f"   Active Timeframes: {', '.join(active_tfs)}")
            print(f"   Status: {slot_summary['message']}")
        else:
            filtered_configs = TIMEFRAME_CONFIGS
            self.slot_strategy = None
        
        # Initialize ProcessingManager for independent timeframe execution
        self.processing_manager = ProcessingManager(
            candles=self.candles,
            timeframe_configs=filtered_configs,
            seed=self.seed
        )
        
        # Create and register independent strategy instances for each timeframe
        print(f"\n⚙️  Initializing independent timeframe strategies:")
        for tf in filtered_configs.keys():
            strategy = create_strategy(tf, filtered_configs[tf])
            self.processing_manager.register_strategy(tf, strategy)
        
        self.active_timeframes = list(filtered_configs.keys())
        
        # Log strategy configuration sources (NEW: transparency logging)
        from ml.strategy_config_logger import log_strategy_config
        log_strategy_config(self.active_timeframes, self.symbol, seed_override=self.seed)
        
        # Initialize adaptive strategy systems (only used if ML enabled)
        active_tfs = self.processing_manager.get_active_timeframes()
        self.strategy_manager = TimeframeStrategyManager(active_timeframes=active_tfs)
        self.threshold_adjuster = AdaptiveThresholdAdjuster()
        
        # If ML is disabled, strategies use their BASE_STRATEGY independently
        if not ml_enabled:
            print(f"   📋 Each timeframe using independent BASE_STRATEGY (no cross-TF coupling)")
        else:
            print(f"   🤖 ML adaptive learning enabled (strategies can evolve)")
        
        # Initialize existing systems
        self.tier_mgr = TierManager()
        self.profit_locker = ProfitLocker(initial_balance=starting_balance)
        self.leverage_scaler = LeverageScaler()
        self.prediction_tracker = PredictionTracker()
        self.position_limiter = get_position_limiter()
        # Pass strategy_manager to filter for dynamic thresholds
        self.high_accuracy_filter = HighAccuracyFilter(strategy_manager=self.strategy_manager)
        self.reversal_detector = ReversalDetector()
        self.intelligent_learner = IntelligentLearner()
        
        # Initialize founder fee manager (BACKTEST mode - no fees collected)
        self.founder_fee = FounderFeeManager(mode='BACKTEST')
        self.current_position_tier = 1  # Track tier for reporting
        
        # State
        self.balance = starting_balance
        self.locked_profit = 0.0
        self.active_positions = {}  # {(timeframe, asset, slot_index): position_dict}
        self.all_trades = []
        self.daily_profits = defaultdict(lambda: {'pnl': 0.0, 'trades': 0, 'wins': 0})
        self.trade_durations = {tf: [] for tf in TIMEFRAME_CONFIGS.keys()}
        self.calculation_checks = []
        self.max_concurrent_positions = 0  # Track for reporting
        self.tier_upgrade_history = []  # Track tier changes
        self.tier_downgrade_history = []  # Track tier downgrades from losses
        self.balance_milestones = {  # Track balance movements
            'peak': starting_balance,
            'lowest': starting_balance,
            'times_below_100': 0,
            'times_below_50': 0,
            'times_depleted': 0  # Balance hit $0 or below
        }
        
        # Pre-aggregate all timeframes
        self.candles_by_tf = {}
        for tf, config in TIMEFRAME_CONFIGS.items():
            self.candles_by_tf[tf] = BacktestIndicators.aggregate_candles(
                self.candles, 
                config['aggregation_minutes']
            )
    
    def get_total_balance(self):
        return self.balance + self.locked_profit
    
    def can_open_position(self, timeframe: str, asset: str) -> bool:
        """Check if we can open a position on this timeframe and asset"""
        # Get current position tier limit (1, 2, or 3 positions per TF per asset)
        max_per_tf_per_asset = self.founder_fee.get_position_limit()
        
        # Count current positions for this timeframe and asset
        current_count = sum(1 for key in self.active_positions 
                          if key[0] == timeframe and key[1] == asset)
        
        # Check if we can open another position
        if current_count >= max_per_tf_per_asset:
            return False
        
        # Also check total position limit (10, 20, or 30 total slots)
        total_limit = self.founder_fee.get_total_position_limit()
        if len(self.active_positions) >= total_limit:
            return False
        
        return True
    
    def check_existing_positions(self, minute_index: int):
        """Check and update all active positions"""
        
        # Track max concurrent positions
        if len(self.active_positions) > self.max_concurrent_positions:
            self.max_concurrent_positions = len(self.active_positions)
        
        for key in list(self.active_positions.keys()):
            tf, asset, slot = key  # Unpack tuple key
            position = self.active_positions[key]
            config = TIMEFRAME_CONFIGS[tf]
            
            minutes_held = minute_index - position['entry_minute']
            current_candle = self.candles[minute_index]
            
            # Check TP
            direction = position.get('direction', 'SHORT')
            tp_hit = (current_candle['low'] <= position['tp_price'] if direction == 'SHORT' 
                      else current_candle['high'] >= position['tp_price'])
            
            if tp_hit:
                if direction == 'SHORT':
                    pnl = (position['entry_price'] - position['tp_price']) * position['position_size']
                else:  # LONG
                    pnl = (position['tp_price'] - position['entry_price']) * position['position_size']
                pnl_pct = (pnl / position['margin']) * 100
                
                self.balance += pnl
                total_balance = self.get_total_balance()
                
                # Check for profit locking
                lock_result = self.profit_locker.check_and_lock(total_balance)
                if lock_result['locked']:
                    self.locked_profit = lock_result['locked_balance']
                    self.balance = lock_result['tradeable_balance']
                    print(f"  🔒 PROFIT LOCKED: ${lock_result['lock_amount']:.2f} at ${lock_result['milestone_reached']:.2f} milestone")
                
                # Check for position tier upgrade
                self._check_tier_upgrade(total_balance)
                
                # Get strategy seed from processing manager
                strategy = self.processing_manager.strategies.get(tf)
                strategy_seed = strategy.seed if strategy else 0
                
                self.all_trades.append({
                    'timeframe': tf,
                    'strategy_seed': strategy_seed,
                    'entry_time': position['entry_time'],
                    'exit_time': current_candle['timestamp'],
                    'outcome': 'TP',
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'balance': self.balance,
                    'total_balance': total_balance,
                    'minutes_held': minutes_held,
                    'confidence': position['confidence']
                })
                
                print(f"✅ TP {tf:3s} | ${position['entry_price']:.2f} → ${position['tp_price']:.2f} | "
                      f"+${pnl:.2f} ({pnl_pct:+.1f}%) | {minutes_held}m | "
                      f"Conf: {position['confidence']:.2f} | Bal: ${total_balance:.2f}")
                
                # Record trade result in strategy manager (if ML enabled)
                if self.ml_config.is_ml_enabled(self.symbol):
                    self.strategy_manager.record_trade(tf, {
                        'won': True,
                        'pnl': pnl,
                        'duration_min': minutes_held,
                        'exit_type': 'TP'
                    })
                    
                    # Check if strategy needs adjustment
                    self.check_and_adjust_strategy(tf)
                
                del self.active_positions[key]
                continue
            
            # Check SL
            sl_hit = (current_candle['high'] >= position['sl_price'] if direction == 'SHORT'
                      else current_candle['low'] <= position['sl_price'])
            
            if sl_hit:
                if direction == 'SHORT':
                    pnl = (position['entry_price'] - position['sl_price']) * position['position_size']
                else:  # LONG
                    pnl = (position['sl_price'] - position['entry_price']) * position['position_size']
                pnl_pct = (pnl / position['margin']) * 100
                
                self.balance += pnl
                total_balance = self.get_total_balance()
                
                # Learn from failed prediction (if ML enabled)
                if 'prediction_id' in position and self.ml_config.is_feature_enabled(self.symbol, 'intelligent_learning'):
                    self.intelligent_learner.analyze_failure(
                        prediction={
                            'predicted_win_prob': position.get('predicted_win_prob', 0.5),
                            'predicted_duration_min': position.get('predicted_duration_min', 60),
                            'predicted_pnl': position.get('predicted_pnl', 0)
                        },
                        actual_outcome={
                            'won': False,
                            'duration_min': minutes_held,
                            'pnl': pnl,
                            'exit_type': 'SL'
                        },
                        features=position.get('features', {})
                    )
                
                # Get strategy seed from processing manager
                strategy = self.processing_manager.strategies.get(tf)
                strategy_seed = strategy.seed if strategy else 0
                
                self.all_trades.append({
                    'timeframe': tf,
                    'strategy_seed': strategy_seed,
                    'entry_time': position['entry_time'],
                    'exit_time': current_candle['timestamp'],
                    'outcome': 'SL',
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'balance': self.balance,
                    'total_balance': total_balance,
                    'minutes_held': minutes_held,
                    'confidence': position['confidence']
                })
                
                print(f"❌ SL {tf:3s} | ${position['entry_price']:.2f} → ${position['sl_price']:.2f} | "
                      f"-${abs(pnl):.2f} ({pnl_pct:+.1f}%) | {minutes_held}m | "
                      f"Conf: {position['confidence']:.2f} | Bal: ${total_balance:.2f}")
                
                # Record trade result in strategy manager (if ML enabled)
                if self.ml_config.is_ml_enabled(self.symbol):
                    self.strategy_manager.record_trade(tf, {
                        'won': False,
                        'pnl': pnl,
                        'duration_min': minutes_held,
                        'exit_type': 'SL'
                    })
                    
                    # Check if strategy needs adjustment
                    self.check_and_adjust_strategy(tf)
                
                del self.active_positions[key]
                continue
            
            # Check time limit
            if minutes_held >= config['time_limit_minutes']:
                exit_price = current_candle['close']
                if direction == 'SHORT':
                    pnl = (position['entry_price'] - exit_price) * position['position_size']
                else:  # LONG
                    pnl = (exit_price - position['entry_price']) * position['position_size']
                pnl_pct = (pnl / position['margin']) * 100
                
                self.balance += pnl
                total_balance = self.get_total_balance()
                
                # Get strategy seed from processing manager
                strategy = self.processing_manager.strategies.get(tf)
                strategy_seed = strategy.seed if strategy else 0
                
                self.all_trades.append({
                    'timeframe': tf,
                    'strategy_seed': strategy_seed,
                    'entry_time': position['entry_time'],
                    'exit_time': current_candle['timestamp'],
                    'outcome': 'Time',
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'balance': self.balance,
                    'total_balance': total_balance,
                    'minutes_held': minutes_held,
                    'confidence': position['confidence']
                })
                
                print(f"⏱️  TIME {tf:3s} | ${position['entry_price']:.2f} → ${exit_price:.2f} | "
                      f"{pnl:+.2f} ({pnl_pct:+.1f}%) | {minutes_held}m | "
                      f"Conf: {position['confidence']:.2f} | Bal: ${total_balance:.2f}")
                
                # Record trade result in strategy manager (if ML enabled)
                if self.ml_config.is_ml_enabled(self.symbol):
                    self.strategy_manager.record_trade(tf, {
                        'won': pnl > 0,
                        'pnl': pnl,
                        'duration_min': minutes_held,
                        'exit_type': 'TIME'
                    })
                    
                    # Check if strategy needs adjustment
                    self.check_and_adjust_strategy(tf)
                
                del self.active_positions[key]
    
    def _validate_pnl_calculation(self, position: dict, exit_price: float, pnl: float, pnl_pct: float, outcome: str):
            """Validate PnL calculation accuracy"""
            
            # Manual calculation
            expected_pnl = (position['entry_price'] - exit_price) * position['position_size']
            expected_pnl_pct = (expected_pnl / position['margin']) * 100
            
            # Check if calculations match
            pnl_error = abs(pnl - expected_pnl)
            pnl_pct_error = abs(pnl_pct - expected_pnl_pct)
            
            validation = {
                'timestamp': position['entry_time'],
                'outcome': outcome,
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'position_size': position['position_size'],
                'margin': position['margin'],
                'calculated_pnl': pnl,
                'expected_pnl': expected_pnl,
                'pnl_error': pnl_error,
                'calculated_pnl_pct': pnl_pct,
                'expected_pnl_pct': expected_pnl_pct,
                'pnl_pct_error': pnl_pct_error,
                'valid': pnl_error < 0.01 and pnl_pct_error < 0.1
            }
            
            self.calculation_checks.append(validation)
            
            # Alert if calculation is off
            if not validation['valid']:
                print(f"  ⚠️ CALCULATION WARNING: PnL error ${pnl_error:.4f}, PnL% error {pnl_pct_error:.2f}%")
    
    def _check_tier_upgrade(self, total_balance: float):
        """Check if position tier should be upgraded OR downgraded based on balance"""
        old_tier = self.current_position_tier
        old_limit = self.founder_fee.get_position_limit()
        
        # Track balance milestones
        if total_balance > self.balance_milestones['peak']:
            self.balance_milestones['peak'] = total_balance
        if total_balance < self.balance_milestones['lowest']:
            self.balance_milestones['lowest'] = total_balance
        
        # Track critical balance levels
        if total_balance < 100.0:
            self.balance_milestones['times_below_100'] += 1
        if total_balance < 50.0:
            self.balance_milestones['times_below_50'] += 1
        if total_balance <= 0:
            self.balance_milestones['times_depleted'] += 1
            print(f"\n⚠️  BALANCE DEPLETED: ${total_balance:.2f}")
            print(f"   Trading PAUSED - waiting for funds")
            print(f"   All positions must close before recovery\n")
        
        # Update founder fee manager with current balance (updates tier in backtest mode)
        self.founder_fee.check_and_collect(
            current_balance=total_balance,
            active_timeframes=['1m', '5m', '15m', '1h', '4h'],  # Dummy for backtest
            active_assets=['ETH', 'BTC'],  # Dummy for backtest
            mode='BACKTEST'
        )
        
        # Get updated tier from founder fee manager
        new_limit = self.founder_fee.get_position_limit()
        
        # Map position limits to tier numbers for display
        # 1 pos/TF/asset = tier 1, 2 = tier 2, 3 = tier 3
        self.current_position_tier = new_limit
        
        # Check if tier UPGRADED
        if new_limit > old_limit:
            total_slots = self.founder_fee.get_total_position_limit()
            print(f"\n🎉 POSITION TIER UPGRADED: {old_limit} → {new_limit} positions per TF per asset")
            print(f"   Total Slots: {total_slots} positions (5 TFs × 2 assets × {new_limit})")
            print(f"   Balance: ${total_balance:.2f}")
            print(f"   Peak Balance: ${self.balance_milestones['peak']:.2f}\n")
            self.tier_upgrade_history.append({
                'balance': total_balance,
                'old_limit': old_limit,
                'new_limit': new_limit,
                'total_slots': total_slots,
                'type': 'upgrade'
            })
        
        # Check if tier DOWNGRADED (from losses)
        elif new_limit < old_limit:
            total_slots = self.founder_fee.get_total_position_limit()
            print(f"\n⚠️  POSITION TIER DOWNGRADED: {old_limit} → {new_limit} positions per TF per asset")
            print(f"   Total Slots: {total_slots} positions (5 TFs × 2 assets × {new_limit})")
            print(f"   Balance: ${total_balance:.2f} (down from peak ${self.balance_milestones['peak']:.2f})")
            print(f"   Reason: Balance dropped below tier threshold\n")
            self.tier_downgrade_history.append({
                'balance': total_balance,
                'old_limit': old_limit,
                'new_limit': new_limit,
                'total_slots': total_slots,
                'type': 'downgrade',
                'peak_before_drop': self.balance_milestones['peak']
            })
    
    def check_entry_opportunity(self, minute_index: int, timeframe: str):
            """Check for entry opportunity with HIGH ACCURACY FILTER and PREDICTION TRACKING"""
            
            asset = self.symbol  # ETH or BTC
            if not self.can_open_position(timeframe, asset):
                return
            
            # Check if balance is depleted or critically low
            if self.balance <= 0:
                # Cannot open positions with no funds
                return
            
            # Warn if balance critically low (< $10)
            if self.balance < 10.0 and self.balance > 0:
                total_balance = self.get_total_balance()
                if len(self.active_positions) == 0:  # Only warn once when no positions
                    print(f"  ⚠️  CRITICAL: Balance ${self.balance:.2f} (total: ${total_balance:.2f}) - Limited trading capacity")
            
            config = TIMEFRAME_CONFIGS[timeframe]
            candles_tf = self.candles_by_tf[timeframe]
            
            # Calculate indices
            idx_tf = minute_index // config['aggregation_minutes']
            
            # Use highest available timeframe for regime detection (4h preferred, else highest available)
            higher_tf = '4h' if '4h' in self.candles_by_tf else (
                '1h' if '1h' in self.candles_by_tf else timeframe
            )
            higher_tf_minutes = TIMEFRAME_CONFIGS[higher_tf]['aggregation_minutes']
            idx_higher = minute_index // higher_tf_minutes
            
            # Need sufficient history
            if idx_tf < 50 or idx_higher < 20 or idx_tf >= len(candles_tf):
                return
            
            # Get regime using highest available timeframe
            regime = BacktestIndicators.get_market_regime(
                candles_tf[:idx_tf + 1],
                self.candles_by_tf[higher_tf][:idx_higher + 1]
            )
            
            # Only trade BULL or BEAR regimes (skip RANGE)
            if regime == 'RANGE':
                return
            
            # Check basic trend alignment
            closes = [c['close'] for c in candles_tf[:idx_tf + 1]]
            ema9 = BacktestIndicators.ema(closes, period=9)
            ema21 = BacktestIndicators.ema(closes, period=21)
            
            current_price = self.candles[minute_index]['close']
            
            # Determine trade direction based on regime
            if regime == 'BEAR':
                # SHORT: price < ema9 < ema21
                if not (current_price < ema9 < ema21):
                    return
                trade_direction = 'SHORT'
            elif regime == 'BULL':
                # LONG: price > ema9 > ema21
                if not (current_price > ema9 > ema21):
                    return
                trade_direction = 'LONG'
            else:
                return
            
            # Extract features for confidence
            features = extract_features(
                candles_tf, 
                self.candles_by_tf[higher_tf],
                idx_tf, 
                idx_higher, 
                current_price
            )
            
            if features is None:
                return
            
            confidence = calculate_rule_based_confidence(features)
            
            # Calculate ATR-based TP/SL
            atr = BacktestIndicators.atr(candles_tf[:idx_tf + 1], period=14)
            atr_pct = (atr / current_price) * 100
            
            tp_pct = atr_pct * config['tp_multiplier']
            sl_pct = atr_pct * config['sl_multiplier']
            
            # ===================================================================
            # REVERSAL DETECTION - Filter out trades near reversals
            # ===================================================================
            has_reversal_risk, reversal_reason = self.reversal_detector.check_reversal_risk(
                candles_tf[:idx_tf + 1],
                idx_tf,
                current_price,
                trade_direction,
                timeframe
            )
            
            if has_reversal_risk:
                if self.reversal_detector.stats['total_checked'] <= 10:
                    print(f"  🔄 {timeframe} Reversal Risk: {reversal_reason}")
                return
            
            # ===================================================================
            # HIGH ACCURACY FILTER - 10 CRITERIA
            # ===================================================================
            filter_passed, rejection_reason, adjusted_confidence = self.high_accuracy_filter.evaluate(
                candles_tf,
                self.candles_by_tf[higher_tf],
                idx_tf,
                idx_higher,
                current_price,
                features,
                confidence,
                tp_pct,
                sl_pct,
                regime
            )
            
            if not filter_passed:
                # Show first 10 rejections for debugging
                if self.high_accuracy_filter.filter_stats['total_evaluated'] <= 10:
                    print(f"  ⛔ {timeframe} Rejected: {rejection_reason}")
                return
            
            # ===================================================================
            # PREDICTION GENERATION
            # ===================================================================
            
            # Get tier and leverage
            total_balance = self.get_total_balance()
            tier_info = self.tier_mgr.update_tier(total_balance)
            tier = tier_info['new_tier']
            tier_config = self.tier_mgr.get_config(tier)
            leverage = self.leverage_scaler.get_leverage(total_balance)
            
            # Calculate position size
            risk_amount = self.balance * (tier_config.max_risk_per_trade_pct / 100)
            risk_amount *= config['position_size_multiplier']  # Adjust for timeframe
            
            # Position value needed so that sl_pct loss = risk_amount (unleveraged)
            position_value = risk_amount / (sl_pct / 100)
            max_position_value = self.balance * leverage
            position_value = min(position_value, max_position_value)
            
            margin = position_value / leverage
            
            if margin > self.balance:
                return
            
            position_size = position_value / current_price
            
            # Calculate TP/SL prices based on direction
            if trade_direction == 'SHORT':
                tp_price = current_price * (1 - tp_pct / 100)
                sl_price = current_price * (1 + sl_pct / 100)
            else:  # LONG
                tp_price = current_price * (1 + tp_pct / 100)
                sl_price = current_price * (1 - sl_pct / 100)
            
            # Generate prediction
            prediction = self.prediction_tracker.generate_prediction(
                symbol=self.symbol,
                timeframe=timeframe,
                entry_price=current_price,
                tp_price=tp_price,
                sl_price=sl_price,
                confidence=adjusted_confidence,
                features=features,
                position_size=position_size,
                margin=margin
            )
            
            # Check if trade meets prediction requirements (68%+ win rate)
            allow_trade, reason = self.prediction_tracker.should_trade(
                prediction['predicted_win_prob'],
                prediction['quality_tier'],
                min_win_rate=0.68  # 68% minimum predicted win rate (relaxed for all TFs)
            )
            
            if not allow_trade:
                print(f"  🚫 {timeframe} Prediction Reject: {reason}")
                return
            
            # ===================================================================
            # POSITION SIZE ADJUSTMENT BY QUALITY TIER
            # ===================================================================
            tier_multiplier = get_position_size_multiplier(prediction['quality_tier'])
            if tier_multiplier == 0:
                print(f"  🚫 {timeframe} Quality tier too low: {prediction['quality_tier']}")
                return
            
            # Adjust position size by quality
            position_size *= tier_multiplier
            position_value *= tier_multiplier
            margin *= tier_multiplier
            
            # ===================================================================
            # POSITION SIZE LIMITER - $100 cap for accounts < $5K
            # ===================================================================
            limited_value, was_limited, limit_info = self.position_limiter.limit_position_size(
                position_value, total_balance, timeframe
            )
            
            if was_limited:
                # Recalculate position size and margin based on limited value
                reduction_factor = limited_value / position_value
                position_size *= reduction_factor
                position_value = limited_value
                margin *= reduction_factor
                reason = limit_info.get('reason', 'limit_exceeded')
                print(f"  💰 {timeframe} Position limited: {reason} | ${limit_info['requested']:.2f} → ${position_value:.2f}")
            
            # Final margin check
            if margin > self.balance:
                print(f"  ⚠️ {timeframe} Margin ${margin:.2f} exceeds balance ${self.balance:.2f} after tier adjustment")
                return
            
            # ===================================================================
            # ENTER POSITION
            # ===================================================================
            
            # Get strategy seed from BASE_STRATEGY
            from ml.base_strategy import BASE_STRATEGY
            strategy_seed = BASE_STRATEGY[timeframe].get('seed', 0)
            
            # Find next available slot for this timeframe and asset
            asset = self.symbol
            slot_index = 0
            max_slots = self.founder_fee.get_position_limit()
            while (timeframe, asset, slot_index) in self.active_positions:
                slot_index += 1
                # Safety check - should never exceed position limit
                if slot_index >= max_slots:
                    print(f"  ⚠️ {timeframe} ERROR: No available slots (max={max_slots})")
                    return
            
            position_key = (timeframe, asset, slot_index)
            self.active_positions[position_key] = {
                'entry_time': self.candles[minute_index]['timestamp'],
                'entry_minute': minute_index,
                'entry_price': current_price,
                'tp_price': tp_price,
                'sl_price': sl_price,
                'position_size': position_size,
                'prediction_id': prediction['prediction_id'],
                'features': features,
                'margin': margin,
                'leverage': leverage,
                'confidence': adjusted_confidence,
                'prediction_id': prediction['prediction_id'],
                'quality_tier': prediction['quality_tier'],
                'predicted_win_prob': prediction['predicted_win_prob'],
                'predicted_duration_min': prediction['predicted_duration_min'],
                'predicted_pnl': prediction['predicted_pnl'],
                'direction': trade_direction,
                'strategy_seed': strategy_seed  # Track which strategy was used
            }
            
            print(f"🎯 ENTRY {timeframe:3s} {trade_direction:5s} {asset} slot{slot_index} | ${current_price:.2f} | TP: ${tp_price:.2f} ({tp_pct:.2f}%) | "
                  f"SL: ${sl_price:.2f} ({sl_pct:.2f}%) | Lev: {leverage:.0f}× | "
                  f"Conf: {adjusted_confidence:.2f} | Tier: {prediction['quality_tier']} | "
                  f"PredWin: {prediction['predicted_win_prob']:.1%} ⭐⭐ | Active: {len(self.active_positions)}/{self.founder_fee.get_total_position_limit()}")
    
    def check_and_adjust_strategy(self, timeframe: str):
        """
        Check if strategy needs adjustment and apply if so
        Called after every trade closes
        Only runs if adaptive_thresholds feature is enabled
        """
        # Skip if adaptive thresholds not enabled for this asset
        if not self.ml_config.is_feature_enabled(self.symbol, 'adaptive_thresholds'):
            return
        
        trade_count = self.strategy_manager.get_trade_count(timeframe)
        
        # Need minimum trades
        if trade_count < 5:
            return
        
        # Get current phase config
        phase = self.strategy_manager.get_current_phase(timeframe)
        phase_config = self.strategy_manager.get_phase_config(phase)
        
        # Only adjust at phase-specific frequency
        if trade_count % phase_config['adjustment_frequency'] != 0:
            return
        
        # Calculate current win rate (last 10 trades)
        current_wr = self.strategy_manager.get_win_rate(timeframe, window=10)
        
        # Check if adjustment needed
        if not self.strategy_manager.should_adjust(timeframe, current_wr):
            return
        
        # Calculate severity
        severity = self.threshold_adjuster.calculate_severity(
            current_wr=current_wr,
            target_wr=0.72
        )
        
        # Get intelligent learner insights (if enabled)
        error_insights = None
        if self.ml_config.is_feature_enabled(self.symbol, 'intelligent_learning'):
            error_insights = self.intelligent_learner.get_error_summary()
        
        # Get current thresholds
        current_thresholds = self.strategy_manager.get_thresholds(timeframe)
        
        # Calculate new thresholds
        new_thresholds = self.threshold_adjuster.calculate_adjustments(
            timeframe=timeframe,
            current_thresholds=current_thresholds,
            severity=severity,
            phase_magnitude=phase_config['adjustment_magnitude'],
            error_insights=error_insights,
            current_wr=current_wr
        )
        
        # Apply adjustments
        self.strategy_manager.set_thresholds(
            timeframe,
            new_thresholds,
            reason=f"WR {current_wr:.1%} < 72%, severity {severity:.1%}, phase {phase}"
        )
        
        # Log adjustment
        direction = self.threshold_adjuster.get_adjustment_direction(current_wr)
        print(f"\n🔧 ADJUSTED {timeframe} STRATEGY (Trade #{trade_count})")
        print(f"   Win Rate: {current_wr:.1%} (target: 72%)")
        print(f"   Phase: {phase} | Severity: {severity:.1%} | Direction: {direction}")
        print(f"   Confidence: {current_thresholds['min_confidence']:.2f} → {new_thresholds['min_confidence']:.2f}")
        print(f"   Volume: {current_thresholds['min_volume']:.2f}x → {new_thresholds['min_volume']:.2f}x")
        if error_insights and 'recurring_issues' in error_insights:
            if error_insights['recurring_issues']:
                print(f"   💡 Learning: {', '.join(error_insights['recurring_issues'])}")
        print()
    
    def run(self):
        """Run backtest on all timeframes"""
        
        print(f"\n{'='*80}")
        print(f"MULTI-TIMEFRAME BACKTEST: {self.symbol}")
        if self.seed:
            print(f"Backtest Seed: {self.seed} (for reproducibility)")
        active_tfs = ', '.join(self.processing_manager.get_active_timeframes())
        print(f"Timeframes: {active_tfs}")
        # Show strategy seeds
        strategy_seeds = [f"{tf}={self.processing_manager.strategies[tf].seed}" 
                         for tf in self.processing_manager.get_active_timeframes()]
        print(f"Strategy Seeds: {', '.join(strategy_seeds)}")
        print(f"{'='*80}\n")
        
        # Calculate duration in days
        from datetime import datetime
        start_time = datetime.fromisoformat(self.candles[0]['timestamp'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(self.candles[-1]['timestamp'].replace('Z', '+00:00'))
        duration_days = (end_time - start_time).days
        
        print(f"Starting Balance: ${self.starting_balance:.2f}")
        print(f"Date Range: {self.candles[0]['timestamp']} to {self.candles[-1]['timestamp']}")
        print(f"Duration: {duration_days} days")
        print(f"\n{'='*80}\n")
        
        # Print filter statistics
        self.high_accuracy_filter.print_filter_report()
        
        # Run through all minutes - ProcessingManager handles all timeframes independently
        for i in range(len(self.candles)):
            self.processing_manager.process_minute(i, self)
        
        self.print_results()
    
    def print_results(self):
        """Print comprehensive results"""
        
        print(f"\n{'='*80}")
        print("RESULTS")
        print(f"{'='*80}\n")
        
        if not self.all_trades:
            print("❌ NO TRADES")
            return
        
        total_balance = self.get_total_balance()
        total_return = ((total_balance - self.starting_balance) / self.starting_balance) * 100
        
        wins = [t for t in self.all_trades if t['pnl'] > 0]
        losses = [t for t in self.all_trades if t['pnl'] <= 0]
        win_rate = (len(wins) / len(self.all_trades)) * 100
        
        # Calculate by timeframe
        tf_stats = {}
        for tf in self.processing_manager.get_active_timeframes():
            tf_trades = [t for t in self.all_trades if t['timeframe'] == tf]
            if tf_trades:
                tf_wins = [t for t in tf_trades if t['pnl'] > 0]
                tf_stats[tf] = {
                    'trades': len(tf_trades),
                    'wins': len(tf_wins),
                    'win_rate': (len(tf_wins) / len(tf_trades)) * 100,
                    'total_pnl': sum(t['pnl'] for t in tf_trades)
                }
        
        print(f"Symbol: {self.symbol}")
        if self.seed:
            print(f"Backtest Seed: {self.seed}")
        print(f"Total Trades: {len(self.all_trades)}")
        print(f"Wins: {len(wins)} | Losses: {len(losses)}")
        print(f"Win Rate: {win_rate:.1f}%")
        
        print(f"\n📊 By Timeframe:")
        for tf in self.processing_manager.get_active_timeframes():
            if tf in tf_stats:
                stats = tf_stats[tf]
                # Get strategy seed
                strategy = self.processing_manager.strategies.get(tf)
                seed = strategy.seed if strategy else 'unknown'
                print(f"  {tf} (seed={seed}): {stats['trades']} trades, {stats['win_rate']:.1f}% win rate, "
                      f"${stats['total_pnl']:+.2f} PnL")
        
        # Daily stats
        num_days = len(self.candles) / 1440
        trades_per_day = len(self.all_trades) / num_days
        pnl_per_day = (total_balance - self.starting_balance) / num_days
        
        print(f"\n💰 Performance:")
        print(f"Starting Balance: ${self.starting_balance:.2f}")
        print(f"Ending Balance: ${self.balance:.2f}")
        print(f"Locked Profit: ${self.locked_profit:.2f}")
        print(f"Total Balance: ${total_balance:.2f}")
        print(f"Total Return: {total_return:+.2f}%")
        print(f"\nTrades/Day: {trades_per_day:.2f}")
        print(f"Profit/Day: ${pnl_per_day:+.2f}")
        
        if wins:
            avg_win = sum(t['pnl'] for t in wins) / len(wins)
            avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
            print(f"\nAvg Win: ${avg_win:.2f}")
            print(f"Avg Loss: ${avg_loss:.2f}")
            if avg_loss != 0:
                rr = abs(avg_win / avg_loss)
                print(f"Risk/Reward: {rr:.2f}:1")
        
        # Max drawdown
        balances = [t['total_balance'] for t in self.all_trades]
        peak = self.starting_balance
        max_dd = 0
        for bal in balances:
            if bal > peak:
                peak = bal
            dd = ((peak - bal) / peak) * 100
            if dd > max_dd:
                max_dd = dd
        
        print(f"\nMax Drawdown: {max_dd:.2f}%")
        
        # Position Tier Summary
        print(f"\n🎯 Position Tier System (BACKTEST):")
        print(f"Final Tier: {self.current_position_tier}")
        print(f"Final Position Limit: {self.founder_fee.get_position_limit()} per TF per asset")
        print(f"Final Total Slots: {self.founder_fee.get_total_position_limit()} positions")
        print(f"Max Concurrent Positions Used: {self.max_concurrent_positions}")
        
        # Balance milestone tracking
        print(f"\n📈 Balance Milestones:")
        print(f"Peak Balance: ${self.balance_milestones['peak']:.2f}")
        print(f"Lowest Balance: ${self.balance_milestones['lowest']:.2f}")
        if self.balance_milestones['times_below_100'] > 0:
            print(f"Times Below $100: {self.balance_milestones['times_below_100']}")
        if self.balance_milestones['times_below_50'] > 0:
            print(f"Times Below $50: {self.balance_milestones['times_below_50']}")
        if self.balance_milestones['times_depleted'] > 0:
            print(f"⚠️  Times Depleted ($0): {self.balance_milestones['times_depleted']}")
        
        if self.tier_upgrade_history:
            print(f"\nTier Upgrade History:")
            for upgrade in self.tier_upgrade_history:
                print(f"  👍 {upgrade['old_limit']} → {upgrade['new_limit']} per TF per asset at ${upgrade['balance']:.2f} "
                      f"({upgrade['total_slots']} total slots)")
        
        if self.tier_downgrade_history:
            print(f"\nTier Downgrade History (from losses):")
            for downgrade in self.tier_downgrade_history:
                print(f"  👎 {downgrade['old_limit']} → {downgrade['new_limit']} per TF per asset at ${downgrade['balance']:.2f} "
                      f"(down from peak ${downgrade['peak_before_drop']:.2f})")
        
        # Intelligent Learning Report
        if losses:
            self.intelligent_learner.print_learning_report()
        
        # Strategy Evolution Report
        self.print_strategy_evolution_report()
    
    def print_strategy_evolution_report(self):
        """Print strategy evolution statistics"""
        print(f"\n{'='*80}")
        print("🎯 STRATEGY PERFORMANCE SUMMARY")
        print(f"{'='*80}\n")
        
        # Calculate stats from actual trades
        for tf in self.processing_manager.get_active_timeframes():
            tf_trades = [t for t in self.all_trades if t['timeframe'] == tf]
            
            if not tf_trades:
                print(f"{tf}: No trades")
                continue
            
            # Calculate win rate
            wins = [t for t in tf_trades if t['pnl'] > 0]
            win_rate = len(wins) / len(tf_trades)
            total_pnl = sum(t['pnl'] for t in tf_trades)
            
            # Get strategy from processing manager
            strategy = self.processing_manager.strategies.get(tf)
            strategy_seed = strategy.seed if strategy else 'unknown'
            
            print(f"Timeframe: {tf} (strategy_seed={strategy_seed})")
            print(f"  Total Trades: {len(tf_trades)}")
            print(f"  Wins: {len(wins)} | Losses: {len(tf_trades) - len(wins)}")
            print(f"  Win Rate: {win_rate:.1%}")
            print(f"  Total P&L: ${total_pnl:+.2f}")
            
            if wins:
                avg_win = sum(t['pnl'] for t in wins) / len(wins)
                losses = [t for t in tf_trades if t['pnl'] <= 0]
                avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
                print(f"  Avg Win: ${avg_win:.2f}")
                print(f"  Avg Loss: ${avg_loss:.2f}")
                if avg_loss != 0:
                    rr = abs(avg_win / avg_loss)
                    print(f"  Risk/Reward: {rr:.2f}:1")
            
            # Show status
            if win_rate >= 0.72:
                print(f"  ✅ Exceeds 72% target")
            elif win_rate >= 0.60:
                print(f"  🟡 Good performance (60%+)")
            elif win_rate >= 0.50:
                print(f"  🟠 Acceptable (50%+)")
            else:
                print(f"  🔴 Needs optimization (<50%)")
            
            print()


def run_combined_test(
    eth_file: str, 
    btc_file: str, 
    starting_balance_per_asset: float = 10.0,
    seed: Optional[int] = None,
    balance_aware: bool = False
):
    """Run backtest on both assets and show combined results
    
    Note: If balance_aware mode, checks which assets are active at given balance.
    Below $75, only ETH trades. At $75+, both ETH and BTC trade.
    """
    
    # Check which assets should be active
    if balance_aware:
        from core.balance_aware_strategy import get_balance_aware_strategy, Asset
        strategy = get_balance_aware_strategy()
        active_assets = strategy.get_active_assets(starting_balance_per_asset)
        
        # Determine actual allocation
        eth_active = Asset.ETH in active_assets
        btc_active = Asset.BTC in active_assets
        
        if eth_active and not btc_active:
            # ETH only - give all balance to ETH
            eth_balance = starting_balance_per_asset
            btc_balance = 0.0
            total_starting = starting_balance_per_asset
        elif eth_active and btc_active:
            # Both active - split balance
            eth_balance = starting_balance_per_asset
            btc_balance = starting_balance_per_asset
            total_starting = starting_balance_per_asset * 2
        else:
            print("\n⚠️  No assets active at this balance")
            return
    else:
        # Non-balance-aware: always split
        eth_balance = starting_balance_per_asset
        btc_balance = starting_balance_per_asset
        total_starting = starting_balance_per_asset * 2
        eth_active = True
        btc_active = True
    
    print(f"\n{'#'*80}")
    print("MULTI-TIMEFRAME DAILY PROFIT SYSTEM")
    if seed is not None:
        print(f"Backtest Seed: {seed} (deterministic mode)")
        print(f"Strategy Seeds: Generated dynamically from parameters")
    if balance_aware:
        print(f"Balance-Aware Mode: Enabled (${total_starting:.2f} total)")
        if eth_active and not btc_active:
            print(f"Asset Allocation: ETH only (BTC activates at $75+)")
        elif eth_active and btc_active:
            print(f"Asset Allocation: ETH ${eth_balance:.2f} + BTC ${btc_balance:.2f}")
    print(f"{'#'*80}\n")
    
    # Run ETH (if active)
    if eth_active:
        eth_backtest = MultiTimeframeBacktest(eth_file, eth_balance, seed=seed, balance_aware=balance_aware)
        if hasattr(eth_backtest, 'active_timeframes') and not eth_backtest.active_timeframes:
            print("ETH not active at this balance, skipping...")
            eth_backtest = None
        else:
            eth_backtest.run()
    else:
        eth_backtest = None
    
    print(f"\n{'='*80}\n")
    
    # Run BTC (if active, use same seed for determinism)
    if btc_active:
        btc_backtest = MultiTimeframeBacktest(btc_file, btc_balance, seed=seed, balance_aware=balance_aware)
        if hasattr(btc_backtest, 'active_timeframes') and not btc_backtest.active_timeframes:
            print("BTC not active at this balance, skipping...")
            btc_backtest = None
        else:
            btc_backtest.run()
    else:
        print("BTC not active at this balance (requires $75+ total)")
        btc_backtest = None
    
    # Combined summary
    print(f"\n{'#'*80}")
    print("COMBINED PORTFOLIO RESULTS")
    if seed is not None:
        print(f"Backtest Seed: {seed}")
    print(f"{'#'*80}\n")
    
    # Handle cases where assets weren't active
    if eth_backtest is None and btc_backtest is None:
        print("⚠️  No active assets at this balance")
        return
    
    # Calculate totals based on what actually ran
    eth_final = eth_backtest.get_total_balance() if eth_backtest else 0.0
    btc_final = btc_backtest.get_total_balance() if btc_backtest else 0.0
    total_final = eth_final + btc_final
    total_return = ((total_final - total_starting) / total_starting) * 100
    
    eth_trades = eth_backtest.all_trades if eth_backtest else []
    btc_trades = btc_backtest.all_trades if btc_backtest else []
    total_trades = len(eth_trades) + len(btc_trades)
    total_wins = len([t for t in eth_trades if t['pnl'] > 0]) + \
                 len([t for t in btc_trades if t['pnl'] > 0])
    combined_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    
    num_days = len(eth_backtest.candles if eth_backtest else btc_backtest.candles) / 1440
    trades_per_day = total_trades / num_days
    pnl_per_day = (total_final - total_starting) / num_days
    
    print(f"Starting Capital: ${total_starting:.2f}")
    print(f"ETH Final: ${eth_final:.2f}")
    print(f"BTC Final: ${btc_final:.2f}")
    print(f"Total Final: ${total_final:.2f}")
    print(f"Combined Return: {total_return:+.2f}%")
    print(f"\nTotal Trades: {total_trades}")
    print(f"Combined Win Rate: {combined_win_rate:.1f}%")
    print(f"Trades/Day: {trades_per_day:.2f}")
    print(f"Profit/Day: ${pnl_per_day:+.2f}")
    
    locked = 0.0
    if eth_backtest:
        locked += eth_backtest.locked_profit
    if btc_backtest:
        locked += btc_backtest.locked_profit
    print(f"\nLocked Profit: ${locked:.2f}")
    
    if total_final >= 100:
        print(f"\n🎉 TARGET ACHIEVED! ${total_starting:.2f} → ${total_final:.2f}")
    elif total_final >= 80:
        print(f"\n🚀 EXCELLENT! ${total_starting:.2f} → ${total_final:.2f}")
    elif total_final >= 60:
        print(f"\n✅ GREAT! ${total_starting:.2f} → ${total_final:.2f}")
    else:
        print(f"\n📊 Good progress: ${total_starting:.2f} → ${total_final:.2f}")


def run_batch_seed_test(test_file: str, data_file: str = 'data/eth_90days.json'):
    """Run batch testing of multiple seeds"""
    
    # Load test configuration
    with open(test_file, 'r') as f:
        test_config = json.load(f)
    
    timeframe = test_config['timeframe']
    test_type = test_config['test_type']
    seeds = test_config['seeds']
    
    print(f"\n{'#'*80}")
    print(f"BATCH SEED TESTING - {timeframe}")
    print(f"Test Type: {test_type}")
    print(f"Seeds: {len(seeds)}")
    print(f"{'#'*80}\n")
    
    results = []
    
    for i, seed_info in enumerate(seeds, 1):
        seed = seed_info['seed']
        expected_wr = seed_info.get('expected_wr', 0)
        
        print(f"\n[{i}/{len(seeds)}] Testing Seed {seed} (Expected WR: {expected_wr:.1%})")
        print(f"{'-'*80}")
        
        # Run backtest
        backtest = MultiTimeframeBacktest(data_file, starting_balance=10.0, seed=seed)
        backtest.run()
        
        # Extract results
        final_balance = backtest.get_total_balance()
        
        # Filter trades by timeframe
        tf_trades = [t for t in backtest.all_trades if t['timeframe'] == timeframe]
        
        if len(tf_trades) > 0:
            wins = len([t for t in tf_trades if t['pnl'] > 0])
            win_rate = wins / len(tf_trades)
            total_pnl = sum(t['pnl'] for t in tf_trades)
        else:
            win_rate = 0
            total_pnl = 0
        
        result = {
            'seed': seed,
            'input_seed': seed_info.get('input_seed'),
            'expected_wr': expected_wr,
            'actual_wr': win_rate,
            'trades': len(tf_trades),
            'pnl': total_pnl,
            'final_balance': final_balance
        }
        
        results.append(result)
        
        print(f"Result: {win_rate:.1%} WR | {len(tf_trades)} trades | ${total_pnl:+.2f} P&L")
        print()
    
    # Summary
    print(f"\n{'='*80}")
    print(f"BATCH TEST RESULTS - {timeframe}")
    print(f"{'='*80}\n")
    
    # Sort by win rate
    results.sort(key=lambda x: x['actual_wr'], reverse=True)
    
    print(f"Top 5 Seeds by Win Rate:")
    for i, r in enumerate(results[:5], 1):
        print(f"  {i}. Seed {r['seed']}: {r['actual_wr']:.1%} WR | "
              f"{r['trades']} trades | ${r['pnl']:+.2f}")
    
    print(f"\nBest Overall: Seed {results[0]['seed']} with {results[0]['actual_wr']:.1%} WR")
    
    # Save results
    results_file = f"ml/batch_test_results_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timeframe': timeframe,
            'test_type': test_type,
            'tested_at': datetime.now().isoformat(),
            'results': results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to {results_file}")
    
    return results


if __name__ == "__main__":
    import argparse
    from pre_trading_check import pre_trading_check
    
    parser = argparse.ArgumentParser(description="Multi-timeframe backtest with pre-flight checks")
    parser.add_argument('--skip-check', action='store_true',
                       help='Skip pre-trading validation (NOT RECOMMENDED)')
    parser.add_argument('--non-interactive', action='store_true',
                       help='Auto-update stale data without prompting')
    parser.add_argument('--seed', type=int, default=None,
                       help='Specific seed for deterministic testing')
    parser.add_argument('--test-seeds-file', type=str,
                       help='JSON file with batch of seeds to test')
    parser.add_argument('--data-file', type=str, default='data/eth_90days.json',
                       help='Data file for backtest')
    parser.add_argument('--balance', type=float, default=None,
                       help='Starting balance (activates balance-aware strategy)')
    
    args = parser.parse_args()
    
    # Check if batch testing mode
    if args.test_seeds_file:
        print("\n🔬 BATCH SEED TESTING MODE\n")
        run_batch_seed_test(args.test_seeds_file, args.data_file)
        sys.exit(0)
    
    # PRE-FLIGHT VALIDATION
    if not args.skip_check:
        print("\n" + "#"*80)
        print("🛫 PRE-FLIGHT CHECK")
        print("#"*80)
        print("\nValidating system before backtest...")
        print("This ensures data is fresh and strategies are ready.\n")
        
        result = pre_trading_check(
            interactive=not args.non_interactive,
            force_update=False
        )
        
        if not result['ready']:
            print("\n❌ BACKTEST ABORTED")
            print("System not ready. Fix issues above and try again.\n")
            sys.exit(1)
        
        print("\n✅ Pre-flight check passed\n")
    else:
        print("\n⚠️  WARNING: Skipping pre-flight check (data may be stale)\n")
    
    # Show which strategies are available
    print("\n" + "="*80)
    print("📊 STRATEGY STATUS")
    print("="*80 + "\n")
    
    # Check BASE_STRATEGY
    from ml.base_strategy import BASE_STRATEGY
    print("BASE_STRATEGY (always available):")
    for tf, config in BASE_STRATEGY.items():
        print(f"  {tf:3s}: confidence={config['min_confidence']:.2f}, "
              f"trend={config['min_trend']:.2f}, adx={config['min_adx']}")
    
    # Check fallback strategies
    fallback_file = 'ml/fallback_strategies.json'
    if os.path.exists(fallback_file):
        with open(fallback_file, 'r') as f:
            fallbacks = json.load(f)
        
        print("\nFallback Strategies (high-confidence backups):")
        for key, config in fallbacks.items():
            num_strats = len(config.get('strategies', []))
            updated = config.get('updated_at', 'unknown')[:10]
            print(f"  {key}: {num_strats} strategies (updated: {updated})")
    else:
        print("\n⚠️  No fallback strategies available yet")
        print("   (Will be generated on first data update)")
    
    # Check ML status
    from ml.ml_config import get_ml_config
    ml_config = get_ml_config()
    
    print("\nML Adaptive Learning:")
    eth_enabled = ml_config.is_ml_enabled('ETH')
    btc_enabled = ml_config.is_ml_enabled('BTC')
    print(f"  ETH: {'✅ ENABLED' if eth_enabled else '❌ DISABLED (BASE_STRATEGY locked)'}")
    print(f"  BTC: {'✅ ENABLED' if btc_enabled else '❌ DISABLED (BASE_STRATEGY locked)'}")
    
    # Balance-aware activation
    if args.balance:
        from core.balance_aware_strategy import get_balance_aware_strategy
        
        print("\n" + "="*80)
        print("💰 BALANCE-AWARE STRATEGY ACTIVATION")
        print("="*80 + "\n")
        
        strategy = get_balance_aware_strategy()
        tier_summary = strategy.get_tier_summary(args.balance)
        print(tier_summary)
        
        # Validate requirements
        validation = strategy.validate_trading_requirements(
            balance=args.balance,
            has_btc_wallet=True,  # Assume available for backtest
            connected_metamask=True
        )
        
        if not validation['can_trade']:
            print("\n❌ CANNOT START BACKTEST")
            for issue in validation['issues']:
                print(f"  - {issue}")
            sys.exit(1)
        
        print("\n✅ Requirements validated")
        print(f"Active Timeframes: {', '.join(validation['active_timeframes'])}")
        print(f"Active Assets: {', '.join(validation['active_assets'])}")
        
        # Override starting balance
        starting_balance = args.balance
    else:
        starting_balance = 10.0
    
    print("\n" + "="*80)
    print("🚀 STARTING BACKTEST WITH 90-DAY DATA")
    print("="*80 + "\n")
    
    eth_file = 'data/eth_90days.json'
    btc_file = 'data/btc_90days.json'
    
    run_combined_test(eth_file, btc_file, starting_balance_per_asset=starting_balance, 
                     seed=args.seed, balance_aware=bool(args.balance))
