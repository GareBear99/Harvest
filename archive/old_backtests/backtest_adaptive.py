#!/usr/bin/env python3
"""
Adaptive backtesting system with market regime detection.
Uses dynamic parameters based on BULL/BEAR/RANGE conditions.
"""
import json
from datetime import datetime
from collections import deque
from core.indicators_backtest import BacktestIndicators


class WinRateTracker:
    """Track rolling win rate and implement circuit breaker."""
    
    def __init__(self, window: int = 20):
        self.window = window
        self.recent_trades = deque(maxlen=window)
        self.paused_until_idx = -1
        
    def add_trade(self, won: bool):
        """Add trade result."""
        self.recent_trades.append(1 if won else 0)
    
    def get_win_rate(self) -> float:
        """Get current win rate (0.0 to 1.0)."""
        if not self.recent_trades:
            return 0.5
        return sum(self.recent_trades) / len(self.recent_trades)
    
    def get_position_multiplier(self) -> float:
        """Get position size multiplier based on win rate."""
        if len(self.recent_trades) < 10:
            return 1.0  # Full size until we have data
        
        win_rate = self.get_win_rate()
        
        if win_rate >= 0.60:
            return 1.0  # Full size
        elif win_rate >= 0.40:
            return 0.5  # Half size
        else:
            return 0.0  # Stop trading (circuit breaker)
    
    def should_pause_trading(self, current_idx: int) -> bool:
        """Check if trading should be paused."""
        # If we hit circuit breaker, pause for 240 minutes (4 hours)
        if self.paused_until_idx >= 0 and current_idx < self.paused_until_idx:
            return True
        
        # Check if we should trigger pause
        if len(self.recent_trades) >= 10 and self.get_win_rate() < 0.30:
            self.paused_until_idx = current_idx + 240  # Pause for 4 hours
            return True
        
        return False


def run_adaptive_backtest(data_file: str = 'data/minute_data_7days.json'):
    """Run adaptive backtest on 7-day minute data."""
    
    # Load data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    candles = data['candles']
    print(f"Loaded {len(candles)} minute candles")
    print(f"Period: {data['start_time']} to {data['end_time']}")
    
    # Calculate price change
    start_price = candles[0]['close']
    end_price = candles[-1]['close']
    price_change_pct = ((end_price - start_price) / start_price) * 100
    print(f"Price: ${start_price:.2f} -> ${end_price:.2f} ({price_change_pct:+.2f}%)")
    print()
    
    # Aggregate to higher timeframes
    candles_5m = BacktestIndicators.aggregate_candles(candles, 5)
    candles_15m = BacktestIndicators.aggregate_candles(candles, 15)
    candles_1h = BacktestIndicators.aggregate_candles(candles, 60)
    candles_4h = BacktestIndicators.aggregate_candles(candles, 240)
    
    # Initialize tracking
    balance = 10.0
    position = None
    trades = []
    win_tracker = WinRateTracker(window=20)
    
    # Regime tracking
    regime_counts = {'BULL': 0, 'BEAR': 0, 'RANGE': 0}
    
    # Strategy trade counts
    strategy_stats = {
        'BEAR_SHORT': {'trades': [], 'wins': 0, 'losses': 0},
        'BULL_LONG': {'trades': [], 'wins': 0, 'losses': 0},
        'RANGE': {'trades': [], 'wins': 0, 'losses': 0}
    }
    
    # Main backtest loop (process every 5 minutes)
    for i in range(len(candles_5m)):
        current_candle = candles_5m[i]
        current_price = current_candle['close']
        timestamp = current_candle['timestamp']
        
        # Get hour for time filtering
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = datetime.fromtimestamp(timestamp / 1000)
        hour = dt.hour
        
        # Skip low-liquidity hours (00:00-04:00 UTC)
        if hour in range(0, 4):
            continue
        
        # Get current regime (need enough data for EMAs)
        idx_1h = i // 12
        idx_4h = i // 48
        
        # Skip if not enough candles for regime detection
        # Need 50 1h candles (2 days) and 20 4h candles (~3.3 days)
        if idx_4h < 20 or idx_1h < 50:
            continue
        
        regime = BacktestIndicators.get_market_regime(
            candles_1h[:idx_1h + 1],
            candles_4h[:idx_4h + 1]
        )
        regime_counts[regime] += 1
        
        # Get ATR-based TP/SL targets
        atr_targets = BacktestIndicators.calculate_atr_targets(candles_1h[:idx_1h + 1])
        
        # Check circuit breaker
        if win_tracker.should_pause_trading(i):
            continue
        
        # Get position multiplier from win rate
        position_multiplier = win_tracker.get_position_multiplier()
        if position_multiplier == 0:
            continue
        
        # Check if we need to close existing position
        if position:
            pnl_pct = ((current_price - position['entry_price']) / position['entry_price'] * 100) * \
                      (1 if position['direction'] == 'LONG' else -1)
            
            should_close = False
            exit_reason = ''
            
            # Check TP/SL
            if pnl_pct >= position['tp_pct']:
                should_close = True
                exit_reason = 'TP'
            elif pnl_pct <= -position['sl_pct']:
                should_close = True
                exit_reason = 'SL'
            
            if should_close:
                pnl = balance * (pnl_pct / 100)
                balance += pnl
                
                trade_record = {
                    'strategy': position['strategy'],
                    'direction': position['direction'],
                    'entry_price': position['entry_price'],
                    'exit_price': current_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'exit_reason': exit_reason,
                    'regime': position['regime']
                }
                trades.append(trade_record)
                
                # Update strategy stats
                strategy = position['strategy']
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {'trades': [], 'wins': 0, 'losses': 0}
                strategy_stats[strategy]['trades'].append(pnl)
                if pnl > 0:
                    strategy_stats[strategy]['wins'] += 1
                else:
                    strategy_stats[strategy]['losses'] += 1
                
                # Update win tracker
                win_tracker.add_trade(pnl > 0)
                
                position = None
        
        # Try to open new position if none exists
        if not position:
            # Get closes for indicators
            closes_5m = [c['close'] for c in candles_5m[max(0, i-100):i+1]]
            closes_1h = [c['close'] for c in candles_1h[:idx_1h + 1]]
            closes_15m = [c['close'] for c in candles_15m[:min(i // 3 + 1, len(candles_15m))]]
            
            # === BEAR MARKET SHORT STRATEGY ===
            if regime == 'BEAR' and i % 3 == 0:  # Check every 15 minutes
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
                        'regime': regime,
                        'size_multiplier': position_multiplier
                    }
            
            # === BULL STRATEGY ONLY ===
            elif not position and regime == 'BULL' and i % 12 == 0:  # Every hour in bull
                rsi = BacktestIndicators.rsi(closes_1h, 14)
                ema20 = BacktestIndicators.ema(closes_1h, 20)
                
                # LONG on dips in bull market
                if rsi < 45 and current_price > ema20:
                    position = {
                        'strategy': 'BULL_LONG',
                        'direction': 'LONG',
                        'entry_price': current_price,
                        'tp_pct': atr_targets['tp_pct'],
                        'sl_pct': atr_targets['sl_pct'],
                        'regime': regime,
                        'size_multiplier': position_multiplier
                    }
            
            # RANGE: Sit out (capital preservation mode)
            
    
    # Close any remaining position
    if position:
        pnl_pct = ((candles_5m[-1]['close'] - position['entry_price']) / position['entry_price'] * 100) * \
                  (1 if position['direction'] == 'LONG' else -1)
        pnl = balance * (pnl_pct / 100)
        balance += pnl
        trades.append({
            'strategy': position['strategy'],
            'direction': position['direction'],
            'entry_price': position['entry_price'],
            'exit_price': candles_5m[-1]['close'],
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'exit_reason': 'END',
            'regime': position['regime']
        })
        strategy = position['strategy']
        if strategy not in strategy_stats:
            strategy_stats[strategy] = {'trades': [], 'wins': 0, 'losses': 0}
        strategy_stats[strategy]['trades'].append(pnl)
        if pnl > 0:
            strategy_stats[strategy]['wins'] += 1
        else:
            strategy_stats[strategy]['losses'] += 1
    
    # Calculate results
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t['pnl'] > 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    total_return = balance - 10.0
    total_return_pct = (total_return / 10.0) * 100
    
    # Print results
    print("=" * 70)
    print("ADAPTIVE BACKTEST RESULTS")
    print("=" * 70)
    print(f"\n💰 PERFORMANCE:")
    print(f"   Starting balance: $10.00")
    print(f"   Ending balance: ${balance:.2f}")
    print(f"   Total return: ${total_return:.2f} ({total_return_pct:+.2f}%)")
    print(f"   Daily average: {total_return_pct / 7:+.2f}%")
    
    print(f"\n📊 TRADES:")
    print(f"   Total trades: {total_trades}")
    print(f"   Winning: {winning_trades} ({win_rate:.1f}%)")
    print(f"   Losing: {total_trades - winning_trades} ({100 - win_rate:.1f}%)")
    
    print(f"\n🌍 REGIME DISTRIBUTION:")
    total_candles = sum(regime_counts.values())
    for regime, count in regime_counts.items():
        pct = (count / total_candles * 100) if total_candles > 0 else 0
        print(f"   {regime}: {pct:.1f}% of time")
    
    print(f"\n📈 STRATEGY BREAKDOWN:")
    for strategy, stats in strategy_stats.items():
        if stats['trades']:
            total_trades = len(stats['trades'])
            win_rate = (stats['wins'] / total_trades * 100) if total_trades > 0 else 0
            total_pnl = sum(stats['trades'])
            print(f"   {strategy}:")
            print(f"      Trades: {total_trades} ({win_rate:.1f}% win rate)")
            print(f"      Total P&L: ${total_pnl:+.2f}")
    
    print(f"\n🎯 COMPARISON TO FIXED PARAMS:")
    print(f"   Fixed baseline: +2.3% (+0.33%/day, 44.1% win rate)")
    print(f"   Fixed optimized: -9.31% (-1.33%/day, 38.5% win rate)")
    print(f"   Adaptive: {total_return_pct:+.2f}% ({total_return_pct / 7:+.2f}%/day, {win_rate:.1f}% win rate)")
    
    if total_return_pct > -9.31:
        improvement = total_return_pct - (-9.31)
        print(f"   ✅ Improvement over optimized: {improvement:+.2f}%")
    else:
        print(f"   ❌ Still underperforming")
    
    print()


if __name__ == '__main__':
    import sys
    
    # Allow passing data file as argument
    data_file = sys.argv[1] if len(sys.argv) > 1 else 'data/minute_data_7days.json'
    run_adaptive_backtest(data_file)
