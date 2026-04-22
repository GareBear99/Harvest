#!/usr/bin/env python3
"""
Adaptive Backtest with Leverage & Compounding
Uses proven BEAR_SHORT strategy with 20-50× leverage to amplify returns.
"""

import json
import sys
from datetime import datetime
from collections import deque
from core.indicators_backtest import BacktestIndicators


class WinRateTracker:
    """Track rolling win rate and implement circuit breaker."""
    
    def __init__(self, window: int = 20):
        self.window = window
        self.recent_trades = deque(maxlen=window)
        self.consecutive_losses = 0
        
    def add_trade(self, won: bool):
        self.recent_trades.append(1 if won else 0)
        if won:
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
    
    def get_win_rate(self) -> float:
        if not self.recent_trades:
            return 0.5
        return sum(self.recent_trades) / len(self.recent_trades)
    
    def should_reduce_leverage(self) -> bool:
        """Reduce leverage after 3 consecutive losses."""
        return self.consecutive_losses >= 3
    
    def should_stop(self) -> bool:
        """Stop after 5 consecutive losses."""
        return self.consecutive_losses >= 5


def run_leveraged_backtest(data_file: str = 'data/eth_21days.json', leverage: int = 30):
    """Run leveraged adaptive backtest."""
    
    # Load data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    candles = data['candles']
    print(f"Loaded {len(candles)} minute candles")
    
    # Calculate price stats
    start_price = candles[0]['close']
    end_price = candles[-1]['close']
    price_change_pct = ((end_price - start_price) / start_price) * 100
    print(f"Price: ${start_price:.2f} → ${end_price:.2f} ({price_change_pct:+.2f}%)")
    print(f"Leverage: {leverage}×")
    print()
    
    # Aggregate to higher timeframes
    candles_5m = BacktestIndicators.aggregate_candles(candles, 5)
    candles_1h = BacktestIndicators.aggregate_candles(candles, 60)
    candles_4h = BacktestIndicators.aggregate_candles(candles, 240)
    
    # Initialize tracking
    balance = 10.0
    initial_balance = 10.0
    peak_balance = 10.0
    position = None
    trades = []
    win_tracker = WinRateTracker(window=20)
    
    # Regime tracking
    regime_counts = {'BULL': 0, 'BEAR': 0, 'RANGE': 0}
    
    # Strategy stats
    strategy_stats = {'BEAR_SHORT': {'trades': [], 'wins': 0, 'losses': 0}}
    
    # Fees & slippage
    fee_per_trade = 0.0008  # 0.08% (0.05% taker + 0.03% slippage)
    
    # Risk limits
    max_drawdown_from_peak = 0.30  # 30% max loss from peak
    stopped = False
    stop_reason = None
    
    # Main backtest loop (process every 5 minutes)
    for i in range(len(candles_5m)):
        if stopped:
            break
        
        current_candle = candles_5m[i]
        current_price = current_candle['close']
        
        # Get current regime
        idx_1h = i // 12
        idx_4h = i // 48
        
        # Skip if not enough 4h candles
        if idx_4h < 20 or idx_1h < 50:
            continue
        
        regime = BacktestIndicators.get_market_regime(
            candles_1h[:idx_1h + 1],
            candles_4h[:idx_4h + 1]
        )
        regime_counts[regime] += 1
        
        # Get ATR-based TP/SL
        atr_targets = BacktestIndicators.calculate_atr_targets(candles_1h[:idx_1h + 1])
        
        # Check if win tracker says stop
        if win_tracker.should_stop():
            stopped = True
            stop_reason = '5 consecutive losses'
            break
        
        # Adjust leverage based on performance
        current_leverage = leverage
        if win_tracker.should_reduce_leverage():
            current_leverage = 10  # Reduce to 10× after 3 losses
        
        # Check circuit breaker (30% loss from peak)
        if balance < peak_balance * (1 - max_drawdown_from_peak):
            stopped = True
            stop_reason = f'30% drawdown from peak (${peak_balance:.2f} → ${balance:.2f})'
            break
        
        # Check if position should be closed
        if position:
            direction = position['direction']
            entry_price = position['entry_price']
            
            # Calculate price move
            if direction == 'LONG':
                price_move_pct = (current_price - entry_price) / entry_price
            else:  # SHORT
                price_move_pct = (entry_price - current_price) / entry_price
            
            # Check TP/SL
            should_close = False
            exit_reason = None
            
            if price_move_pct >= position['tp_pct'] / 100:
                should_close = True
                exit_reason = 'TP'
            elif price_move_pct <= -position['sl_pct'] / 100:
                should_close = True
                exit_reason = 'SL'
            
            if should_close:
                # Calculate P&L with leverage
                pnl_pct_unleveraged = price_move_pct
                pnl_pct_leveraged = pnl_pct_unleveraged * position['leverage']
                
                # Apply fees (entry + exit)
                pnl_pct_after_fees = pnl_pct_leveraged - (fee_per_trade * 2)
                
                # Calculate dollar P&L
                pnl = balance * pnl_pct_after_fees
                balance += pnl
                
                # Update peak
                if balance > peak_balance:
                    peak_balance = balance
                
                # Record trade
                trade_record = {
                    'strategy': 'BEAR_SHORT',
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'leverage': position['leverage'],
                    'price_move_pct': pnl_pct_unleveraged * 100,
                    'pnl_pct_leveraged': pnl_pct_leveraged * 100,
                    'pnl_pct_after_fees': pnl_pct_after_fees * 100,
                    'pnl': pnl,
                    'balance_after': balance,
                    'exit_reason': exit_reason,
                    'regime': position['regime']
                }
                trades.append(trade_record)
                
                # Update stats
                strategy_stats['BEAR_SHORT']['trades'].append(pnl)
                if pnl > 0:
                    strategy_stats['BEAR_SHORT']['wins'] += 1
                else:
                    strategy_stats['BEAR_SHORT']['losses'] += 1
                
                # Update win tracker
                win_tracker.add_trade(pnl > 0)
                
                position = None
        
        # Try to open new position if none exists
        if not position and regime == 'BEAR':
            # Check every 3 candles (15 minutes) in BEAR regime
            if i % 3 != 0:
                continue
            
            # Get closes for indicators
            closes_5m = [c['close'] for c in candles_5m[max(0, i-100):i+1]]
            
            # BEAR_SHORT strategy
            rsi_5m = BacktestIndicators.rsi(closes_5m, 14)
            ema9_5m = BacktestIndicators.ema(closes_5m, 9)
            ema21_5m = BacktestIndicators.ema(closes_5m, 21)
            
            should_short = False
            
            # Condition 1: Overbought rally in downtrend
            if rsi_5m > 55 and rsi_5m < 70:
                should_short = True
            
            # Condition 2: Riding the downtrend
            if ema9_5m < ema21_5m and current_price > ema9_5m * 0.998:
                should_short = True
            
            # Condition 3: Fresh breakdown
            if len(closes_5m) > 1:
                prev_price = closes_5m[-2]
                if prev_price >= ema9_5m and current_price < ema9_5m:
                    should_short = True
            
            if should_short:
                position = {
                    'strategy': 'BEAR_SHORT',
                    'direction': 'SHORT',
                    'entry_price': current_price,
                    'tp_pct': atr_targets['tp_pct'] * 0.8,
                    'sl_pct': atr_targets['sl_pct'] * 0.6,
                    'leverage': current_leverage,
                    'regime': regime
                }
    
    # Close any remaining position
    if position:
        current_price = candles_5m[-1]['close']
        entry_price = position['entry_price']
        direction = position['direction']
        
        if direction == 'SHORT':
            price_move_pct = (entry_price - current_price) / entry_price
        else:
            price_move_pct = (current_price - entry_price) / entry_price
        
        pnl_pct_leveraged = price_move_pct * position['leverage'] - (fee_per_trade * 2)
        pnl = balance * pnl_pct_leveraged
        balance += pnl
        
        trades.append({
            'strategy': 'BEAR_SHORT',
            'direction': direction,
            'entry_price': entry_price,
            'exit_price': current_price,
            'leverage': position['leverage'],
            'price_move_pct': price_move_pct * 100,
            'pnl_pct_leveraged': pnl_pct_leveraged * 100,
            'pnl': pnl,
            'balance_after': balance,
            'exit_reason': 'END',
            'regime': position['regime']
        })
        
        if pnl > 0:
            strategy_stats['BEAR_SHORT']['wins'] += 1
        else:
            strategy_stats['BEAR_SHORT']['losses'] += 1
    
    # Calculate results
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t['pnl'] > 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    total_return = balance - initial_balance
    total_return_pct = (total_return / initial_balance) * 100
    
    # Calculate max drawdown
    peak = initial_balance
    max_dd = 0
    for trade in trades:
        b = trade['balance_after']
        if b > peak:
            peak = b
        dd = (peak - b) / peak
        if dd > max_dd:
            max_dd = dd
    
    # Print results
    print("="*70)
    print("LEVERAGED ADAPTIVE BACKTEST RESULTS")
    print("="*70)
    
    print(f"\n💰 PERFORMANCE:")
    print(f"   Starting balance: ${initial_balance:.2f}")
    print(f"   Ending balance: ${balance:.2f}")
    print(f"   Peak balance: ${peak_balance:.2f}")
    print(f"   Total return: ${total_return:.2f} ({total_return_pct:+.2f}%)")
    
    days = len(candles) / 1440
    daily_return_pct = total_return_pct / days if days > 0 else 0
    print(f"   Daily average: {daily_return_pct:+.2f}%")
    
    print(f"\n📊 TRADES:")
    print(f"   Total trades: {total_trades}")
    print(f"   Winning: {winning_trades} ({win_rate:.1f}%)")
    print(f"   Losing: {total_trades - winning_trades} ({100 - win_rate:.1f}%)")
    
    print(f"\n📈 LEVERAGE:")
    print(f"   Base leverage: {leverage}×")
    print(f"   Max drawdown: {max_dd * 100:.2f}%")
    
    if stopped:
        print(f"\n🛑 STOPPED:")
        print(f"   Reason: {stop_reason}")
    
    print(f"\n🌍 REGIME DISTRIBUTION:")
    total_candles = sum(regime_counts.values())
    for regime, count in regime_counts.items():
        pct = (count / total_candles * 100) if total_candles > 0 else 0
        print(f"   {regime}: {pct:.1f}% of time")
    
    print(f"\n🎯 TARGET COMPARISON:")
    print(f"   Conservative target: $10 → $38-40 (280-300%)")
    print(f"   Aggressive target: $10 → $100-120 (900-1100%)")
    print(f"   Actual result: ${initial_balance:.2f} → ${balance:.2f} ({total_return_pct:+.1f}%)")
    
    if total_return_pct >= 280:
        print(f"   ✅ CONSERVATIVE TARGET ACHIEVED!")
    if total_return_pct >= 900:
        print(f"   ✅✅ AGGRESSIVE TARGET ACHIEVED!")
    
    print()


if __name__ == '__main__':
    data_file = sys.argv[1] if len(sys.argv) > 1 else 'data/eth_21days.json'
    leverage = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    run_leveraged_backtest(data_file, leverage)
