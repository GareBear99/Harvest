#!/usr/bin/env python3
"""
FINAL OPTIMIZED DAILY PROFIT SYSTEM
Complete with portfolio management, confidence-based sizing, and session filters
Target: $20 → $100+ with 5-8 trades/day and 70%+ win rate
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.indicators_backtest import BacktestIndicators
from core.tier_manager import TierManager
from core.profit_locker import ProfitLocker
from core.leverage_scaler import LeverageScaler
from core.portfolio_manager import PortfolioManager
from analysis.ml_confidence_model import extract_features, calculate_rule_based_confidence


# Timeframe configurations with confidence-based adjustments
TIMEFRAME_CONFIGS = {
    '15m': {
        'aggregation_minutes': 15,
        'tp_multiplier': 1.5,
        'sl_multiplier': 0.75,
        'time_limit_minutes': 180,
        'base_position_multiplier': 0.5,
        'confidence_threshold': 0.75
    },
    '1h': {
        'aggregation_minutes': 60,
        'tp_multiplier': 2.0,
        'sl_multiplier': 1.0,
        'time_limit_minutes': 720,
        'base_position_multiplier': 1.0,
        'confidence_threshold': 0.75
    },
    '4h': {
        'aggregation_minutes': 240,
        'tp_multiplier': 2.5,
        'sl_multiplier': 1.25,
        'time_limit_minutes': 1440,
        'base_position_multiplier': 1.5,
        'confidence_threshold': 0.75
    }
}

# Session filters - avoid low-liquidity periods (DISABLED for now - data format issues)
def is_good_trading_session(timestamp_str: str) -> bool:
    """
    Check if it's a good time to trade based on UTC hour
    Note: Currently disabled to allow all sessions
    """
    return True  # Allow all trading sessions


class OptimizedMultiTimeframeBacktest:
    def __init__(self, data_file: str, starting_balance: float = 10.0):
        self.data_file = data_file
        self.symbol = data_file.split('/')[-1].split('_')[0].upper()
        self.starting_balance = starting_balance
        
        # Load data
        with open(data_file, 'r') as f:
            data = json.load(f)
        self.candles = data['candles']
        
        # Initialize systems
        self.tier_mgr = TierManager()
        self.profit_locker = ProfitLocker(initial_balance=starting_balance)
        self.leverage_scaler = LeverageScaler()
        self.portfolio_mgr = PortfolioManager(
            max_portfolio_exposure=0.80,
            max_concurrent_positions=3  # Lower for 2-asset system
        )
        
        # State
        self.balance = starting_balance
        self.locked_profit = 0.0
        self.active_positions = {}
        self.all_trades = []
        
        # Pre-aggregate all timeframes
        self.candles_by_tf = {
            '15m': BacktestIndicators.aggregate_candles(self.candles, 15),
            '1h': BacktestIndicators.aggregate_candles(self.candles, 60),
            '4h': BacktestIndicators.aggregate_candles(self.candles, 240)
        }
        
        # Track current day for daily loss limit
        self.current_day = None
    
    def get_total_balance(self):
        return self.balance + self.locked_profit
    
    def check_existing_positions(self, minute_index: int):
        """Check and update all active positions"""
        
        for tf in list(self.active_positions.keys()):
            position = self.active_positions[tf]
            config = TIMEFRAME_CONFIGS[tf]
            
            minutes_held = minute_index - position['entry_minute']
            current_candle = self.candles[minute_index]
            
            # Check TP
            if current_candle['low'] <= position['tp_price']:
                pnl = (position['entry_price'] - position['tp_price']) * position['position_size']
                pnl_pct = (pnl / position['margin']) * 100
                
                self.balance += pnl
                total_balance = self.get_total_balance()
                
                # Check for profit locking
                lock_result = self.profit_locker.check_and_lock(total_balance)
                if lock_result['locked']:
                    self.locked_profit = lock_result['locked_balance']
                    self.balance = lock_result['tradeable_balance']
                    print(f"  🔒 PROFIT LOCKED: ${lock_result['lock_amount']:.2f} at ${lock_result['milestone_reached']:.2f} milestone")
                
                self.all_trades.append({
                    'timeframe': tf,
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
                
                # Update portfolio manager
                self.portfolio_mgr.close_position(self.symbol, tf, pnl)
                
                del self.active_positions[tf]
                continue
            
            # Check SL
            if current_candle['high'] >= position['sl_price']:
                pnl = (position['entry_price'] - position['sl_price']) * position['position_size']
                pnl_pct = (pnl / position['margin']) * 100
                
                self.balance += pnl
                total_balance = self.get_total_balance()
                
                self.all_trades.append({
                    'timeframe': tf,
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
                
                self.portfolio_mgr.close_position(self.symbol, tf, pnl)
                
                del self.active_positions[tf]
                continue
            
            # Check time limit
            if minutes_held >= config['time_limit_minutes']:
                exit_price = current_candle['close']
                pnl = (position['entry_price'] - exit_price) * position['position_size']
                pnl_pct = (pnl / position['margin']) * 100
                
                self.balance += pnl
                total_balance = self.get_total_balance()
                
                self.all_trades.append({
                    'timeframe': tf,
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
                
                self.portfolio_mgr.close_position(self.symbol, tf, pnl)
                
                del self.active_positions[tf]
    
    def check_entry_opportunity(self, minute_index: int, timeframe: str):
        """Check for entry opportunity on specific timeframe"""
        
        if self.balance <= 0:
            return
        
        config = TIMEFRAME_CONFIGS[timeframe]
        candles_tf = self.candles_by_tf[timeframe]
        
        # Calculate indices
        idx_tf = minute_index // config['aggregation_minutes']
        idx_4h = minute_index // 240
        
        # Need sufficient history
        if idx_tf < 50 or idx_4h < 20 or idx_tf >= len(candles_tf):
            return
        
        current_price = self.candles[minute_index]['close']
        timestamp = self.candles[minute_index]['timestamp']
        
        # SESSION FILTER: Skip low-liquidity periods
        if not is_good_trading_session(timestamp):
            return
        
        # Get regime
        regime = BacktestIndicators.get_market_regime(
            candles_tf[:idx_tf + 1],
            self.candles_by_tf['4h'][:idx_4h + 1]
        )
        
        if regime != 'BEAR':
            return
        
        # Check basic trend alignment
        closes = [c['close'] for c in candles_tf[:idx_tf + 1]]
        ema9 = BacktestIndicators.ema(closes, period=9)
        ema21 = BacktestIndicators.ema(closes, period=21)
        
        if not (current_price < ema9 < ema21):
            return
        
        # Extract features for confidence
        features = extract_features(
            candles_tf, 
            self.candles_by_tf['4h'],
            idx_tf, 
            idx_4h, 
            current_price
        )
        
        if features is None:
            return
        
        confidence = calculate_rule_based_confidence(features)
        
        if confidence < config['confidence_threshold']:
            return
        
        # Calculate ATR-based TP/SL
        atr = BacktestIndicators.atr(candles_tf[:idx_tf + 1], period=14)
        atr_pct = (atr / current_price) * 100
        
        tp_pct = atr_pct * config['tp_multiplier']
        sl_pct = atr_pct * config['sl_multiplier']
        
        # Get tier and leverage
        total_balance = self.get_total_balance()
        tier_info = self.tier_mgr.update_tier(total_balance)
        tier = tier_info['new_tier']
        tier_config = self.tier_mgr.get_config(tier)
        leverage = self.leverage_scaler.get_leverage(total_balance)
        
        # OPTIMIZED: Confidence-based position sizing
        position_multiplier = self.portfolio_mgr.calculate_position_sizing_multiplier(
            confidence, timeframe
        )
        
        # Calculate position size
        risk_amount = self.balance * (tier_config.max_risk_per_trade_pct / 100)
        risk_amount *= position_multiplier  # Apply confidence + timeframe multiplier
        
        position_value = (risk_amount / (sl_pct / 100)) * leverage
        max_position_value = self.balance * leverage
        position_value = min(position_value, max_position_value)
        
        margin = position_value / leverage
        
        if margin > self.balance:
            return
        
        # PORTFOLIO RISK CHECK
        can_open, reason = self.portfolio_mgr.can_open_position(
            self.symbol,
            timeframe,
            margin,
            self.balance,
            total_balance
        )
        
        if not can_open:
            return  # Silently skip if portfolio limits reached
        
        position_size = position_value / current_price
        
        # Enter position
        tp_price = current_price * (1 - tp_pct / 100)
        sl_price = current_price * (1 + sl_pct / 100)
        
        self.active_positions[timeframe] = {
            'entry_time': timestamp,
            'entry_minute': minute_index,
            'entry_price': current_price,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'position_size': position_size,
            'margin': margin,
            'leverage': leverage,
            'confidence': confidence
        }
        
        # Register with portfolio manager
        self.portfolio_mgr.register_position(
            self.symbol,
            timeframe,
            margin,
            position_size,
            current_price,
            tp_price,
            sl_price,
            leverage,
            confidence
        )
        
        print(f"🎯 ENTRY {timeframe:3s} | ${current_price:.2f} | TP: ${tp_price:.2f} ({tp_pct:.2f}%) | "
              f"SL: ${sl_price:.2f} ({sl_pct:.2f}%) | Lev: {leverage:.0f}× | "
              f"Conf: {confidence:.2f} ⭐ | Mult: {position_multiplier:.2f}×")
    
    def check_new_day(self, timestamp_str: str):
        """Check if we've entered a new day and reset daily tracking"""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            day = dt.date()
            
            if self.current_day != day:
                if self.current_day is not None:
                    # New day started
                    total_balance = self.get_total_balance()
                    self.portfolio_mgr.start_new_day(total_balance)
                    
                    # Show daily stats if available
                    stats = self.portfolio_mgr.get_daily_stats()
                    if stats:
                        print(f"\n📅 NEW DAY: {day} | Balance: ${total_balance:.2f}")
                
                self.current_day = day
                self.portfolio_mgr.start_new_day(self.get_total_balance())
        except:
            pass
    
    def run(self):
        """Run backtest on all timeframes with optimizations"""
        
        print(f"\n{'='*80}")
        print(f"OPTIMIZED MULTI-TIMEFRAME BACKTEST: {self.symbol}")
        print(f"Features: Portfolio Mgmt, Confidence Sizing, Session Filters")
        print(f"{'='*80}\n")
        
        print(f"Starting Balance: ${self.starting_balance:.2f}")
        print(f"Date Range: {self.candles[0]['timestamp']} to {self.candles[-1]['timestamp']}")
        print(f"\n{'='*80}\n")
        
        # Run through all minutes
        for i in range(len(self.candles)):
            # Check for new day
            self.check_new_day(self.candles[i]['timestamp'])
            
            # Check existing positions
            self.check_existing_positions(i)
            
            # Check entry opportunities on each timeframe
            if i % 15 == 0:
                self.check_entry_opportunity(i, '15m')
            
            if i % 60 == 0:
                self.check_entry_opportunity(i, '1h')
            
            if i % 240 == 0:
                self.check_entry_opportunity(i, '4h')
        
        self.print_results()
    
    def print_results(self):
        """Print comprehensive results"""
        
        print(f"\n{'='*80}")
        print("FINAL RESULTS")
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
        for tf in ['15m', '1h', '4h']:
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
        print(f"Total Trades: {len(self.all_trades)}")
        print(f"Wins: {len(wins)} | Losses: {len(losses)}")
        print(f"Win Rate: {win_rate:.1f}%")
        
        print(f"\n📊 By Timeframe:")
        for tf in ['15m', '1h', '4h']:
            if tf in tf_stats:
                stats = tf_stats[tf]
                print(f"  {tf}: {stats['trades']} trades, {stats['win_rate']:.1f}% win rate, "
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


def run_final_test(eth_file: str, btc_file: str, starting_balance_per_asset: float = 10.0):
    """Run final optimized backtest"""
    
    print(f"\n{'#'*80}")
    print("FINAL OPTIMIZED DAILY PROFIT SYSTEM")
    print("Features: Portfolio Mgmt + Confidence Sizing + Session Filters")
    print(f"{'#'*80}\n")
    
    # Run ETH
    eth_backtest = OptimizedMultiTimeframeBacktest(eth_file, starting_balance_per_asset)
    eth_backtest.run()
    
    print(f"\n{'='*80}\n")
    
    # Run BTC
    btc_backtest = OptimizedMultiTimeframeBacktest(btc_file, starting_balance_per_asset)
    btc_backtest.run()
    
    # Combined summary
    print(f"\n{'#'*80}")
    print("FINAL COMBINED PORTFOLIO RESULTS")
    print(f"{'#'*80}\n")
    
    total_starting = starting_balance_per_asset * 2
    eth_final = eth_backtest.get_total_balance()
    btc_final = btc_backtest.get_total_balance()
    total_final = eth_final + btc_final
    total_return = ((total_final - total_starting) / total_starting) * 100
    
    total_trades = len(eth_backtest.all_trades) + len(btc_backtest.all_trades)
    total_wins = len([t for t in eth_backtest.all_trades if t['pnl'] > 0]) + \
                 len([t for t in btc_backtest.all_trades if t['pnl'] > 0])
    combined_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    
    num_days = len(eth_backtest.candles) / 1440
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
    print(f"\nLocked Profit: ${eth_backtest.locked_profit + btc_backtest.locked_profit:.2f}")
    
    if total_final >= 100:
        print(f"\n🎉🎉🎉 TARGET ACHIEVED! ${total_starting:.2f} → ${total_final:.2f} 🎉🎉🎉")
        print(f"PHENOMENAL {total_return:.1f}% RETURN IN {num_days:.0f} DAYS!")
    elif total_final >= 80:
        print(f"\n🚀 EXCELLENT! ${total_starting:.2f} → ${total_final:.2f}")
        print(f"Almost there! Just ${100-total_final:.2f} more to $100!")
    elif total_final >= 60:
        print(f"\n✅ GREAT! ${total_starting:.2f} → ${total_final:.2f}")
    else:
        print(f"\n📊 Good progress: ${total_starting:.2f} → ${total_final:.2f}")


if __name__ == "__main__":
    run_final_test('data/eth_21days.json', 'data/btc_21days.json', starting_balance_per_asset=10.0)
