#!/usr/bin/env python3
"""
Tiered Risk System Backtest
Implements progressive de-risking with Kelly Criterion position sizing,
milestone-based profit locking, and adaptive leverage scaling.
"""

import json
import sys
from datetime import datetime, timedelta
from collections import deque
from core.indicators_backtest import BacktestIndicators
from core.tier_manager import TierManager
from core.position_sizer import PositionSizer
from core.profit_locker import ProfitLocker
from core.leverage_scaler import LeverageScaler


class ConsecutiveLossTracker:
    """Track consecutive losses for circuit breakers"""
    
    def __init__(self):
        self.consecutive_losses = 0
        self.total_losses = 0
        self.max_consecutive = 0
        
    def add_trade(self, won: bool):
        if won:
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
            self.total_losses += 1
            self.max_consecutive = max(self.max_consecutive, self.consecutive_losses)
    
    def should_reduce_leverage(self) -> bool:
        """Reduce leverage by 50% after 3 consecutive losses"""
        return self.consecutive_losses >= 3
    
    def should_pause(self) -> bool:
        """Pause trading for 4 hours after 5 consecutive losses"""
        return self.consecutive_losses >= 5
    
    def should_stop_day(self) -> bool:
        """Stop trading for the day after 7 consecutive losses"""
        return self.consecutive_losses >= 7


class DailyLossLimiter:
    """Track daily losses and enforce limits"""
    
    def __init__(self):
        self.daily_start_balance = None
        self.current_day = None
        self.days_stopped = []
        
    def update(self, current_timestamp: int, balance: float, tier_config: any) -> bool:
        """
        Update daily tracking and check if we should stop
        Returns True if trading should continue, False if limit hit
        """
        current_day = current_timestamp // (24 * 60)  # Day number
        
        # New day
        if current_day != self.current_day:
            self.current_day = current_day
            self.daily_start_balance = balance
            return True
        
        # Check daily loss limit
        if self.daily_start_balance:
            loss_pct = (self.daily_start_balance - balance) / self.daily_start_balance
            limit = tier_config.max_risk_per_trade_pct * 3  # 3x single trade risk as daily limit
            
            if loss_pct > limit / 100:
                self.days_stopped.append(current_day)
                return False
        
        return True


def run_tiered_backtest(data_file: str = 'data/eth_21days.json', initial_balance: float = 10.0):
    """Run tiered risk system backtest"""
    
    # Load data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    candles = data['candles']
    symbol = data_file.split('/')[-1].split('_')[0].upper()
    
    print("=" * 80)
    print(f"TIERED RISK SYSTEM BACKTEST - {symbol}")
    print("=" * 80)
    print(f"Data: {len(candles)} minute candles")
    print(f"Initial Balance: ${initial_balance:.2f}")
    print()
    
    # Calculate price stats
    start_price = candles[0]['close']
    end_price = candles[-1]['close']
    price_change_pct = ((end_price - start_price) / start_price) * 100
    
    start_time = datetime.fromisoformat(candles[0]['timestamp'])
    end_time = datetime.fromisoformat(candles[-1]['timestamp'])
    duration_days = (end_time - start_time).days
    
    print(f"Period: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')} ({duration_days} days)")
    print(f"Price: ${start_price:.2f} → ${end_price:.2f} ({price_change_pct:+.2f}%)")
    print()
    
    # Aggregate to higher timeframes
    candles_5m = BacktestIndicators.aggregate_candles(candles, 5)
    candles_1h = BacktestIndicators.aggregate_candles(candles, 60)
    candles_4h = BacktestIndicators.aggregate_candles(candles, 240)
    
    # Initialize tiered risk system
    tier_manager = TierManager()
    position_sizer = PositionSizer(min_position=5.0)
    profit_locker = ProfitLocker(initial_balance=initial_balance)
    leverage_scaler = LeverageScaler()
    
    # Initialize tracking
    balance = initial_balance
    peak_balance = initial_balance
    position = None
    trades = []
    
    # Risk management
    loss_tracker = ConsecutiveLossTracker()
    daily_limiter = DailyLossLimiter()
    paused_until = 0  # Minute index
    
    # Circuit breakers
    max_drawdown_from_peak = 0.30  # 30% circuit breaker
    stopped = False
    stop_reason = None
    
    # Fees & slippage
    fee_per_trade = 0.0008  # 0.08%
    
    # Stats
    regime_counts = {'BULL': 0, 'BEAR': 0, 'RANGE': 0}
    tier_stats = {0: [], 1: [], 2: [], 3: []}
    
    # Last check time for adaptive frequency
    last_check_minute = 0
    
    print("Starting backtest...")
    print()
    
    # Main backtest loop (1-minute resolution)
    for i in range(len(candles)):
        if stopped:
            break
        
        current_candle = candles[i]
        current_price = current_candle['close']
        current_timestamp = current_candle['timestamp']
        
        # Update tier based on current balance
        tier_info = tier_manager.update_tier(balance)
        tier_config = tier_manager.get_config()
        
        if tier_info['tier_changed']:
            print(f"\n💫 TIER TRANSITION at minute {i} (${balance:.2f})")
            print(f"   {tier_info['old_tier']} → {tier_info['new_tier']} ({tier_config.name})")
            print(f"   Leverage: {tier_config.leverage}×")
            print(f"   Position Size: {tier_config.position_size_pct*100:.0f}%")
            print(f"   Locked: ${tier_info['locked_balance']:.2f}")
            print(f"   Tradeable: ${tier_info['tradeable_balance']:.2f}")
        
        # Update profit locker
        lock_result = profit_locker.check_and_lock(balance)
        if lock_result['locked']:
            print(f"\n🔒 PROFIT LOCKED at minute {i} (${balance:.2f})")
            print(f"   Milestone: ${lock_result['milestone_reached']:.2f}")
            print(f"   Locked: ${lock_result['locked_balance']:.2f}")
            print(f"   Tradeable: ${lock_result['tradeable_balance']:.2f}")
        
        # Update leverage
        leverage_info = leverage_scaler.update_leverage(balance)
        current_leverage = leverage_info['leverage']
        
        # Apply consecutive loss leverage reduction
        if loss_tracker.should_reduce_leverage():
            current_leverage = max(current_leverage // 2, 5)
        
        # Check if paused
        if i < paused_until:
            continue
        
        # Check daily loss limit
        if not daily_limiter.update(i, balance, tier_config):
            continue  # Skip rest of day
        
        # Check circuit breaker
        if balance < peak_balance * (1 - max_drawdown_from_peak):
            stopped = True
            stop_reason = f'30% drawdown from peak (${peak_balance:.2f} → ${balance:.2f})'
            break
        
        # Check consecutive loss circuit breaker
        if loss_tracker.should_stop_day():
            stopped = True
            stop_reason = '7 consecutive losses'
            break
        
        # Pause if needed
        if loss_tracker.should_pause():
            paused_until = i + 240  # Pause for 4 hours
            print(f"\n⏸️  PAUSED at minute {i} (5 consecutive losses)")
            print(f"   Resuming at minute {paused_until}")
            continue
        
        # Get market regime (need enough data)
        idx_1h = i // 60
        idx_4h = i // 240
        
        if idx_4h < 20 or idx_1h < 50:
            continue
        
        regime = BacktestIndicators.get_market_regime(
            candles_1h[:idx_1h + 1],
            candles_4h[:idx_4h + 1]
        )
        regime_counts[regime] += 1
        
        # Get ATR for TP/SL and volatility adjustment
        atr = BacktestIndicators.atr(candles_1h[:idx_1h + 1], period=14)
        
        # Calculate average ATR for volatility adjustment
        if idx_1h >= 20:
            recent_atrs = [BacktestIndicators.atr(candles_1h[:j+1], period=14)
                          for j in range(max(0, idx_1h-20), idx_1h+1)]
            avg_atr = sum(recent_atrs) / len(recent_atrs) if recent_atrs else atr
        else:
            avg_atr = atr
        
        # Check if position should be closed
        if position:
            direction = position['direction']
            entry_price = position['entry_price']
            entry_time = position['entry_minute']
            
            # Calculate price move
            if direction == 'LONG':
                price_move_pct = (current_price - entry_price) / entry_price
            else:  # SHORT
                price_move_pct = (entry_price - current_price) / entry_price
            
            # Check for trailing stop (if position is in profit)
            tp_threshold = position['tp_pct'] / 100
            sl_threshold = -position['sl_pct'] / 100
            
            trailing_sl = sl_threshold
            if price_move_pct >= tp_threshold * 0.5:
                # Move to breakeven when 50% to TP
                trailing_sl = max(trailing_sl, -0.001)  # Small buffer for fees
            
            # Check exit conditions
            should_close = False
            exit_reason = None
            
            if price_move_pct >= tp_threshold:
                should_close = True
                exit_reason = 'TP'
            elif price_move_pct <= trailing_sl:
                should_close = True
                exit_reason = 'SL' if trailing_sl == sl_threshold else 'Trailing_SL'
            elif i - entry_time >= 360:  # 6 hours
                should_close = True
                exit_reason = 'Time_Limit'
            
            if should_close:
                # Calculate P&L
                pnl_pct_unleveraged = price_move_pct
                pnl_pct_leveraged = pnl_pct_unleveraged * position['leverage']
                pnl_pct_after_fees = pnl_pct_leveraged - (fee_per_trade * 2)
                
                # Calculate dollar P&L based on position size
                pnl = position['position_size'] * pnl_pct_after_fees
                balance += pnl
                
                # Update peak
                if balance > peak_balance:
                    peak_balance = balance
                
                # Record trade
                trade_record = {
                    'trade_num': len(trades) + 1,
                    'minute': i,
                    'tier': tier_config.tier_id,
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'leverage': position['leverage'],
                    'position_size': position['position_size'],
                    'position_pct': position['position_size'] / (balance - pnl) * 100,
                    'price_move_pct': pnl_pct_unleveraged * 100,
                    'pnl_pct_leveraged': pnl_pct_leveraged * 100,
                    'pnl_pct_after_fees': pnl_pct_after_fees * 100,
                    'pnl': pnl,
                    'balance_after': balance,
                    'exit_reason': exit_reason,
                    'regime': regime,
                    'hold_minutes': i - entry_time
                }
                trades.append(trade_record)
                tier_stats[tier_config.tier_id].append(trade_record)
                
                # Update position sizer performance
                position_sizer.update_performance(pnl_pct_after_fees)
                
                # Update loss tracker
                loss_tracker.add_trade(pnl > 0)
                
                # Print trade result
                result_emoji = "✅" if pnl > 0 else "❌"
                print(f"{result_emoji} Trade #{trade_record['trade_num']} | "
                      f"Tier {tier_config.tier_id} | "
                      f"{exit_reason} | "
                      f"P&L: {pnl_pct_after_fees*100:+.2f}% "
                      f"(${pnl:+.2f}) | "
                      f"Balance: ${balance:.2f}")
                
                position = None
        
        # Try to open new position
        if not position and regime in ['BEAR']:  # Only trade in BEAR for now
            # Check if enough time passed since last check
            minutes_since_last = i - last_check_minute
            
            if not tier_manager.should_check_entry(minutes_since_last, regime):
                continue
            
            last_check_minute = i
            
            # Get tradeable balance
            tradeable_balance = profit_locker.get_tradeable_balance(balance)
            
            if tradeable_balance < 5:
                continue
            
            # Calculate position size
            size_result = position_sizer.calculate_position_size(
                tradeable_balance,
                tier_config,
                atr,
                avg_atr
            )
            
            position_size = size_result['position_size']
            
            # Check if we can trade this size
            if not profit_locker.should_allow_trade(balance, position_size):
                continue
            
            # Check BEAR_SHORT entry conditions
            idx_5m = i // 5
            if idx_5m < 50:
                continue
            
            recent_5m = candles_5m[max(0, idx_5m-50):idx_5m+1]
            
            # Calculate indicators
            closes_5m = [c['close'] for c in recent_5m]
            rsi_14 = BacktestIndicators.rsi(closes_5m, period=14)
            ema_9 = BacktestIndicators.ema(closes_5m, period=9)
            ema_21 = BacktestIndicators.ema(closes_5m, period=21)
            adx = BacktestIndicators.adx(candles_1h[:idx_1h+1], period=14)
            
            # Calculate volume
            volumes = [c['volume'] for c in recent_5m[-20:]]
            avg_volume = sum(volumes) / len(volumes)
            current_volume = current_candle['volume']
            
            # Entry filters
            entry_valid = False
            
            # Primary conditions (any of)
            cond1 = 55 <= rsi_14 <= 70  # Overbought rally
            cond2 = abs(current_price - ema_9) / ema_9 < 0.002 and current_price < ema_9  # Near EMA9 resistance
            cond3 = current_price < ema_9 and recent_5m[-2]['close'] > ema_9  # Just crossed below
            
            # Additional filters (all required)
            filter1 = adx > tier_config.min_adx  # Strong trend
            filter2 = ema_9 < ema_21  # Downtrend confirmed
            filter3 = current_volume > avg_volume * 0.8  # Sufficient volume
            filter4 = i > paused_until + 120  # No entry within 2h after pause
            
            if (cond1 or cond2 or cond3) and filter1 and filter2 and filter3 and filter4:
                entry_valid = True
            
            if entry_valid:
                # Open SHORT position
                position = {
                    'direction': 'SHORT',
                    'entry_price': current_price,
                    'entry_minute': i,
                    'leverage': current_leverage,
                    'position_size': position_size,
                    'tp_pct': tier_config.tp_pct * 100,  # Convert to percentage
                    'sl_pct': tier_config.sl_pct * 100,
                    'regime': regime,
                    'tier': tier_config.tier_id
                }
    
    # Final results
    print("\n" + "=" * 80)
    print("BACKTEST COMPLETE")
    print("=" * 80)
    
    if stopped:
        print(f"⚠️  Stopped: {stop_reason}")
        print()
    
    # Calculate metrics
    total_return = ((balance - initial_balance) / initial_balance) * 100
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t['pnl'] > 0)
    losing_trades = total_trades - winning_trades
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    # Calculate max drawdown
    equity_curve = [initial_balance]
    for trade in trades:
        equity_curve.append(trade['balance_after'])
    
    max_dd = 0
    peak = initial_balance
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100
        if dd > max_dd:
            max_dd = dd
    
    # Print results
    print(f"Final Balance: ${balance:.2f} ({total_return:+.2f}%)")
    print(f"Peak Balance: ${peak_balance:.2f}")
    print(f"Locked Balance: ${profit_locker.locked_balance:.2f}")
    print(f"Tradeable Balance: ${profit_locker.get_tradeable_balance(balance):.2f}")
    print()
    
    print(f"Total Trades: {total_trades}")
    print(f"Wins: {winning_trades} | Losses: {losing_trades}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Max Drawdown: {max_dd:.2f}%")
    print(f"Max Consecutive Losses: {loss_tracker.max_consecutive}")
    print()
    
    # Tier statistics
    print("TIER STATISTICS:")
    print("-" * 80)
    for tier_id in sorted(tier_stats.keys()):
        tier_trades = tier_stats[tier_id]
        if not tier_trades:
            continue
        
        tier_wins = sum(1 for t in tier_trades if t['pnl'] > 0)
        tier_wr = (tier_wins / len(tier_trades) * 100) if tier_trades else 0
        tier_pnl = sum(t['pnl'] for t in tier_trades)
        
        print(f"Tier {tier_id} ({tier_manager.tiers[tier_id].name}):")
        print(f"  Trades: {len(tier_trades)} | Win Rate: {tier_wr:.1f}% | P&L: ${tier_pnl:+.2f}")
    
    print()
    
    # Regime statistics
    print("REGIME DISTRIBUTION:")
    print("-" * 80)
    total_regime_checks = sum(regime_counts.values())
    for regime, count in regime_counts.items():
        pct = (count / total_regime_checks * 100) if total_regime_checks > 0 else 0
        print(f"{regime}: {count} checks ({pct:.1f}%)")
    
    print()
    
    # Profit locker stats
    print("PROFIT LOCKER:")
    print("-" * 80)
    locker_stats = profit_locker.get_stats()
    print(f"Milestones Reached: {locker_stats['milestones_reached']}/{locker_stats['total_milestones']}")
    print(f"Locked: ${locker_stats['locked_balance']:.2f}")
    if locker_stats['lock_events']:
        print(f"Lock Events:")
        for event in locker_stats['lock_events']:
            print(f"  ${event['milestone']:.0f} milestone → Locked ${event['locked_amount']:.2f} ({event['multiple']:.1f}x)")
    
    print()
    print("=" * 80)
    
    return {
        'balance': balance,
        'return_pct': total_return,
        'trades': total_trades,
        'win_rate': win_rate,
        'max_drawdown': max_dd,
        'locked_balance': profit_locker.locked_balance,
        'tier_stats': tier_stats,
        'trades_data': trades
    }


if __name__ == "__main__":
    data_file = sys.argv[1] if len(sys.argv) > 1 else 'data/eth_21days.json'
    initial_balance = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
    
    results = run_tiered_backtest(data_file, initial_balance)
