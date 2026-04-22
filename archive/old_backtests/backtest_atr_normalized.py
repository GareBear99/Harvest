#!/usr/bin/env python3
"""
ATR-Normalized Backtest
Uses ATR-based TP/SL instead of fixed percentages to adapt to each asset's volatility
"""

import json
import sys
from datetime import datetime
from core.indicators_backtest import BacktestIndicators
from core.tier_manager import TierManager
from core.position_sizer import PositionSizer
from core.profit_locker import ProfitLocker


def run_atr_backtest(data_file: str, initial_balance: float = 10.0):
    """Run backtest with ATR-normalized TP/SL"""
    
    # Load data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    candles = data['candles']
    symbol = data_file.split('/')[-1].split('_')[0].upper()
    
    print("=" * 80)
    print(f"ATR-NORMALIZED BACKTEST - {symbol}")
    print("=" * 80)
    print(f"Data: {len(candles)} minute candles")
    print(f"Initial Balance: ${initial_balance:.2f}")
    print(f"TP/SL: 2× ATR / 1× ATR (volatility-adjusted)")
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
    
    # Aggregate timeframes
    candles_5m = BacktestIndicators.aggregate_candles(candles, 5)
    candles_1h = BacktestIndicators.aggregate_candles(candles, 60)
    candles_4h = BacktestIndicators.aggregate_candles(candles, 240)
    
    # Initialize system
    tier_manager = TierManager()
    position_sizer = PositionSizer(min_position=5.0)
    profit_locker = ProfitLocker(initial_balance=initial_balance)
    
    # Tracking
    balance = initial_balance
    peak_balance = initial_balance
    position = None
    trades = []
    
    # Risk management
    from collections import deque
    consecutive_losses = 0
    max_consecutive = 0
    
    # Fees
    fee_per_trade = 0.0008
    
    # Circuit breakers
    max_drawdown_from_peak = 0.30
    stopped = False
    stop_reason = None
    
    # Stats
    regime_counts = {'BULL': 0, 'BEAR': 0, 'RANGE': 0}
    
    # Last check
    last_check_minute = 0
    
    print("Starting backtest...")
    print()
    
    # Main loop
    for i in range(len(candles)):
        if stopped:
            break
        
        current_candle = candles[i]
        current_price = current_candle['close']
        
        # Update tier
        tier_info = tier_manager.update_tier(balance)
        tier_config = tier_manager.get_config()
        
        if tier_info['tier_changed']:
            print(f"\n💫 TIER TRANSITION at minute {i} (${balance:.2f})")
            print(f"   {tier_info['old_tier']} → {tier_info['new_tier']} ({tier_config.name})")
            print(f"   Leverage: {tier_config.leverage}×")
        
        # Update profit locker
        lock_result = profit_locker.check_and_lock(balance)
        if lock_result['locked']:
            print(f"\n🔒 PROFIT LOCKED at minute {i} (${balance:.2f})")
            print(f"   Milestone: ${lock_result['milestone_reached']:.2f}")
            print(f"   Locked: ${lock_result['locked_balance']:.2f}")
        
        # Get regime
        idx_1h = i // 60
        idx_4h = i // 240
        
        if idx_4h < 20 or idx_1h < 50:
            continue
        
        regime = BacktestIndicators.get_market_regime(
            candles_1h[:idx_1h + 1],
            candles_4h[:idx_4h + 1]
        )
        regime_counts[regime] += 1
        
        # Get ATR (use 1h timeframe)
        atr = BacktestIndicators.atr(candles_1h[:idx_1h + 1], period=14)
        avg_price = current_price
        atr_pct = (atr / avg_price) * 100
        
        # ATR-based TP/SL
        tp_pct_atr = atr_pct * 2.0  # 2× ATR for TP
        sl_pct_atr = atr_pct * 1.0  # 1× ATR for SL
        
        # Check circuit breaker
        if balance < peak_balance * (1 - max_drawdown_from_peak):
            stopped = True
            stop_reason = f'30% drawdown from peak'
            break
        
        # Close position if exists
        if position:
            direction = position['direction']
            entry_price = position['entry_price']
            entry_time = position['entry_minute']
            
            # Calculate price move
            if direction == 'LONG':
                price_move_pct = (current_price - entry_price) / entry_price
            else:  # SHORT
                price_move_pct = (entry_price - current_price) / entry_price
            
            # Check TP/SL
            tp_threshold = position['tp_pct'] / 100
            sl_threshold = -position['sl_pct'] / 100
            
            should_close = False
            exit_reason = None
            
            if price_move_pct >= tp_threshold:
                should_close = True
                exit_reason = 'TP'
            elif price_move_pct <= sl_threshold:
                should_close = True
                exit_reason = 'SL'
            elif i - entry_time >= 720:  # 12 hours (increased from 6)
                should_close = True
                exit_reason = 'Time_Limit'
            
            if should_close:
                # Calculate P&L
                pnl_pct_unleveraged = price_move_pct
                pnl_pct_leveraged = pnl_pct_unleveraged * position['leverage']
                pnl_pct_after_fees = pnl_pct_leveraged - (fee_per_trade * 2)
                
                pnl = position['position_size'] * pnl_pct_after_fees
                balance += pnl
                
                if balance > peak_balance:
                    peak_balance = balance
                
                # Track consecutive losses
                if pnl > 0:
                    consecutive_losses = 0
                else:
                    consecutive_losses += 1
                    max_consecutive = max(max_consecutive, consecutive_losses)
                
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
                    'tp_pct': position['tp_pct'],
                    'sl_pct': position['sl_pct'],
                    'atr_at_entry': position['atr'],
                    'price_move_pct': pnl_pct_unleveraged * 100,
                    'pnl_pct_after_fees': pnl_pct_after_fees * 100,
                    'pnl': pnl,
                    'balance_after': balance,
                    'exit_reason': exit_reason,
                    'hold_minutes': i - entry_time
                }
                trades.append(trade_record)
                
                position_sizer.update_performance(pnl_pct_after_fees)
                
                result_emoji = "✅" if pnl > 0 else "❌"
                print(f"{result_emoji} Trade #{trade_record['trade_num']} | "
                      f"Tier {tier_config.tier_id} | "
                      f"{exit_reason} | "
                      f"TP/SL: {trade_record['tp_pct']:.2f}%/{trade_record['sl_pct']:.2f}% | "
                      f"P&L: {pnl_pct_after_fees*100:+.2f}% "
                      f"(${pnl:+.2f}) | "
                      f"Balance: ${balance:.2f}")
                
                position = None
        
        # Try to open position
        if not position and regime in ['BEAR']:
            minutes_since_last = i - last_check_minute
            
            if not tier_manager.should_check_entry(minutes_since_last, regime):
                continue
            
            last_check_minute = i
            
            tradeable_balance = profit_locker.get_tradeable_balance(balance)
            
            if tradeable_balance < 5:
                continue
            
            # Calculate position size
            size_result = position_sizer.calculate_position_size(
                tradeable_balance,
                tier_config,
                atr,
                atr  # Use same ATR for both
            )
            
            position_size = size_result['position_size']
            
            if not profit_locker.should_allow_trade(balance, position_size):
                continue
            
            # Check entry conditions
            idx_5m = i // 5
            if idx_5m < 50:
                continue
            
            recent_5m = candles_5m[max(0, idx_5m-50):idx_5m+1]
            
            closes_5m = [c['close'] for c in recent_5m]
            rsi_14 = BacktestIndicators.rsi(closes_5m, period=14)
            ema_9 = BacktestIndicators.ema(closes_5m, period=9)
            ema_21 = BacktestIndicators.ema(closes_5m, period=21)
            adx = BacktestIndicators.adx(candles_1h[:idx_1h+1], period=14)
            
            volumes = [c['volume'] for c in recent_5m[-20:]]
            avg_volume = sum(volumes) / len(volumes)
            current_volume = current_candle['volume']
            
            # Entry conditions
            entry_valid = False
            
            # Relaxed conditions for more entries
            cond1 = 55 <= rsi_14 <= 70
            cond2 = abs(current_price - ema_9) / ema_9 < 0.003  # Relaxed from 0.002
            cond3 = current_price < ema_9 and recent_5m[-2]['close'] > ema_9
            
            filter1 = adx > 15  # Lowered from 20
            filter2 = ema_9 < ema_21
            filter3 = current_volume > avg_volume * 0.7  # Lowered from 0.8
            
            if (cond1 or cond2 or cond3) and filter1 and filter2 and filter3:
                entry_valid = True
            
            if entry_valid:
                # Open SHORT position with ATR-based TP/SL
                position = {
                    'direction': 'SHORT',
                    'entry_price': current_price,
                    'entry_minute': i,
                    'leverage': tier_config.leverage,
                    'position_size': position_size,
                    'tp_pct': tp_pct_atr,  # ATR-based
                    'sl_pct': sl_pct_atr,  # ATR-based
                    'atr': atr_pct,
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
    
    print(f"Final Balance: ${balance:.2f} ({total_return:+.2f}%)")
    print(f"Peak Balance: ${peak_balance:.2f}")
    print(f"Locked Balance: ${profit_locker.locked_balance:.2f}")
    print()
    
    print(f"Total Trades: {total_trades}")
    print(f"Wins: {winning_trades} | Losses: {losing_trades}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Max Drawdown: {max_dd:.2f}%")
    print(f"Max Consecutive Losses: {max_consecutive}")
    print()
    
    if trades:
        avg_tp = sum(t['tp_pct'] for t in trades) / len(trades)
        avg_sl = sum(t['sl_pct'] for t in trades) / len(trades)
        print(f"Average TP/SL: {avg_tp:.2f}% / {avg_sl:.2f}%")
        print(f"(Automatically adjusted based on ATR)")
    
    print("=" * 80)
    
    return {
        'balance': balance,
        'return_pct': total_return,
        'trades': total_trades,
        'win_rate': win_rate,
        'max_drawdown': max_dd,
        'trades_data': trades
    }


if __name__ == "__main__":
    data_file = sys.argv[1] if len(sys.argv) > 1 else 'data/eth_21days.json'
    initial_balance = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
    
    results = run_atr_backtest(data_file, initial_balance)
