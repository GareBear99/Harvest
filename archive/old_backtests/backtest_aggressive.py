#!/usr/bin/env python3
"""
Aggressive Backtester with Leverage & Compounding
Simulates high-frequency scalping with 30-50× leverage to turn $10 into $100+
"""

import json
import sys
from datetime import datetime
from typing import List, Dict
from strategies.micro_scalper import MicroScalper


class AggressiveBacktester:
    """
    Backtest aggressive scalping with leverage and compounding.
    
    Features:
    - 30-50× leverage simulation
    - Aggressive compounding (reinvest after each win)
    - Realistic fees/slippage (0.08% per trade)
    - Max drawdown tracking
    - Circuit breakers (30% loss, 5% daily DD)
    """
    
    def __init__(self, initial_balance: float = 10.0, leverage: int = 30):
        """
        Initialize aggressive backtester.
        
        Args:
            initial_balance: Starting capital
            leverage: Trading leverage
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.peak_balance = initial_balance
        self.leverage = leverage
        
        # Fees & slippage
        self.maker_fee = 0.0002  # 0.02%
        self.taker_fee = 0.0005  # 0.05%
        self.slippage = 0.0003   # 0.03%
        self.total_cost_per_trade = self.taker_fee + self.slippage  # 0.08%
        
        # Risk limits
        self.max_total_loss_pct = 0.30  # 30% total loss → stop
        self.max_daily_drawdown_pct = 0.05  # 5% daily DD → stop
        self.daily_start_balance = initial_balance
        
        # Tracking
        self.trades = []
        self.position = None
        self.stopped = False
        self.stop_reason = None
        
        # Strategy
        self.strategy = MicroScalper(leverage=leverage)
    
    def check_circuit_breakers(self) -> bool:
        """
        Check if circuit breakers triggered.
        
        Returns:
            True if should stop trading
        """
        # Total loss circuit breaker (30%)
        total_loss_pct = (self.initial_balance - self.balance) / self.initial_balance
        if total_loss_pct >= self.max_total_loss_pct:
            self.stopped = True
            self.stop_reason = f'Total loss {total_loss_pct*100:.1f}% (max 30%)'
            return True
        
        # Daily drawdown circuit breaker (5%)
        daily_dd_pct = (self.peak_balance - self.balance) / self.peak_balance
        if daily_dd_pct >= self.max_daily_drawdown_pct:
            self.stopped = True
            self.stop_reason = f'Daily DD {daily_dd_pct*100:.1f}% (max 5%)'
            return True
        
        return False
    
    def open_position(self, signal: Dict, candle_idx: int):
        """Open new position based on signal."""
        if self.position or self.stopped:
            return
        
        entry_price = signal['entry_price']
        direction = signal['direction']
        leverage = signal['leverage']
        
        # Position size = full balance × leverage
        position_size = self.balance * leverage
        
        # Apply entry cost (fees + slippage)
        entry_cost = self.balance * self.total_cost_per_trade
        self.balance -= entry_cost
        
        self.position = {
            'direction': direction,
            'entry_price': entry_price,
            'entry_idx': candle_idx,
            'tp_price': signal['tp_price'],
            'sl_price': signal['sl_price'],
            'tp_pct': signal['tp_pct'],
            'sl_pct': signal['sl_pct'],
            'leverage': leverage,
            'position_size': position_size,
            'balance_at_entry': self.balance,
            'entry_cost': entry_cost,
            'signals': signal['signals']
        }
    
    def check_exit(self, current_price: float, candle_idx: int) -> bool:
        """
        Check if position should be closed.
        
        Returns:
            True if position closed
        """
        if not self.position:
            return False
        
        direction = self.position['direction']
        entry_price = self.position['entry_price']
        tp_price = self.position['tp_price']
        sl_price = self.position['sl_price']
        leverage = self.position['leverage']
        
        # Calculate price move percentage
        if direction == 'LONG':
            price_move_pct = (current_price - entry_price) / entry_price
        else:  # SHORT
            price_move_pct = (entry_price - current_price) / entry_price
        
        # Check TP/SL
        exit_reason = None
        if direction == 'LONG':
            if current_price >= tp_price:
                exit_reason = 'TP'
            elif current_price <= sl_price:
                exit_reason = 'SL'
        else:  # SHORT
            if current_price <= tp_price:
                exit_reason = 'TP'
            elif current_price >= sl_price:
                exit_reason = 'SL'
        
        if exit_reason:
            # Calculate P&L with leverage
            pnl_pct = price_move_pct * leverage
            
            # Apply exit cost
            exit_cost = self.balance * self.total_cost_per_trade
            self.balance -= exit_cost
            
            # Apply P&L to balance
            pnl = self.balance * pnl_pct
            self.balance += pnl
            
            # Update peak balance
            if self.balance > self.peak_balance:
                self.peak_balance = self.balance
            
            # Record trade
            trade_record = {
                'entry_idx': self.position['entry_idx'],
                'exit_idx': candle_idx,
                'direction': direction,
                'entry_price': entry_price,
                'exit_price': current_price,
                'leverage': leverage,
                'price_move_pct': price_move_pct * 100,
                'pnl_pct': pnl_pct * 100,
                'pnl': pnl,
                'balance_after': self.balance,
                'exit_reason': exit_reason,
                'entry_cost': self.position['entry_cost'],
                'exit_cost': exit_cost,
                'signals': self.position['signals']
            }
            self.trades.append(trade_record)
            
            # Update strategy
            won = pnl > 0
            self.strategy.update_after_trade(won)
            
            # Clear position
            self.position = None
            
            # Check circuit breakers
            self.check_circuit_breakers()
            
            return True
        
        return False
    
    def run(self, candles: List[Dict]):
        """
        Run aggressive backtest on 1-minute candles.
        
        Args:
            candles: List of 1-minute candles
        """
        print(f"Starting aggressive backtest...")
        print(f"Initial balance: ${self.initial_balance:.2f}")
        print(f"Leverage: {self.leverage}×")
        print(f"Total cost per trade: {self.total_cost_per_trade*100:.2f}%")
        print()
        
        # Process each candle
        for i in range(len(candles)):
            if self.stopped:
                print(f"\n🛑 STOPPED: {self.stop_reason}")
                break
            
            current_candle = candles[i]
            current_price = current_candle['close']
            
            # Check if position should be closed
            if self.position:
                self.check_exit(current_price, i)
                continue  # Don't open new position while in one
            
            # Need warmup period (at least 30 candles)
            if i < 30:
                continue
            
            # Get recent data
            closes_1m = [c['close'] for c in candles[max(0, i-100):i+1]]
            closes_5m = [c['close'] for c in candles[::5][max(0, (i//5)-20):(i//5)+1]]
            volumes_1m = [c['volume'] for c in candles[max(0, i-100):i+1]]
            
            # Generate signal
            signal = self.strategy.generate_signal(
                closes_1m, closes_5m, volumes_1m, current_price
            )
            
            if signal:
                self.open_position(signal, i)
        
        # Close any remaining position at end
        if self.position:
            final_price = candles[-1]['close']
            self.check_exit(final_price, len(candles)-1)
        
        return self.generate_report(candles)
    
    def generate_report(self, candles: List[Dict]) -> Dict:
        """Generate performance report."""
        total_trades = len(self.trades)
        if total_trades == 0:
            return {
                'total_trades': 0,
                'final_balance': self.balance,
                'total_return_pct': 0,
                'message': 'No trades executed'
            }
        
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100
        
        total_return = self.balance - self.initial_balance
        total_return_pct = (total_return / self.initial_balance) * 100
        
        # Calculate max drawdown
        peak = self.initial_balance
        max_dd = 0
        for trade in self.trades:
            balance = trade['balance_after']
            if balance > peak:
                peak = balance
            dd = (peak - balance) / peak
            if dd > max_dd:
                max_dd = dd
        
        # Average win/loss
        avg_win = sum(t['pnl_pct'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl_pct'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        return {
            'initial_balance': self.initial_balance,
            'final_balance': self.balance,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'max_drawdown_pct': max_dd * 100,
            'leverage_used': self.leverage,
            'stopped': self.stopped,
            'stop_reason': self.stop_reason
        }
    
    def print_report(self, report: Dict, candles: List[Dict]):
        """Print formatted report."""
        print("\n" + "="*70)
        print("AGGRESSIVE BACKTEST RESULTS (WITH LEVERAGE)")
        print("="*70)
        
        print(f"\n💰 PERFORMANCE:")
        print(f"   Starting balance: ${report['initial_balance']:.2f}")
        print(f"   Ending balance: ${report['final_balance']:.2f}")
        print(f"   Total return: ${report['total_return']:.2f} ({report['total_return_pct']:+.2f}%)")
        
        # Calculate daily return
        days = len(candles) / 1440  # 1440 minutes per day
        daily_return_pct = report['total_return_pct'] / days if days > 0 else 0
        print(f"   Daily average: {daily_return_pct:+.2f}%")
        
        print(f"\n📊 TRADES:")
        print(f"   Total trades: {report['total_trades']}")
        print(f"   Winning: {report['winning_trades']} ({report['win_rate']:.1f}%)")
        print(f"   Losing: {report['losing_trades']} ({100 - report['win_rate']:.1f}%)")
        print(f"   Avg win: {report['avg_win_pct']:+.2f}% (per trade)")
        print(f"   Avg loss: {report['avg_loss_pct']:+.2f}% (per trade)")
        
        print(f"\n📈 LEVERAGE:")
        print(f"   Leverage used: {report['leverage_used']}×")
        print(f"   Max drawdown: {report['max_drawdown_pct']:.2f}%")
        
        if report['stopped']:
            print(f"\n🛑 CIRCUIT BREAKER:")
            print(f"   Reason: {report['stop_reason']}")
        
        print(f"\n🎯 TARGET COMPARISON:")
        print(f"   Conservative target: $10 → $38-40 (280-300%)")
        print(f"   Aggressive target: $10 → $100-120 (900-1100%)")
        print(f"   Actual result: ${report['initial_balance']:.2f} → ${report['final_balance']:.2f} ({report['total_return_pct']:+.1f}%)")
        
        if report['total_return_pct'] >= 280:
            print(f"   ✅ CONSERVATIVE TARGET ACHIEVED!")
        if report['total_return_pct'] >= 900:
            print(f"   ✅✅ AGGRESSIVE TARGET ACHIEVED!")
        
        print()


def main():
    """Main execution."""
    # Load data
    data_file = sys.argv[1] if len(sys.argv) > 1 else 'data/eth_minute_data_7days.json'
    leverage = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    print(f"Loading data from: {data_file}")
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    candles = data['candles']
    print(f"Loaded {len(candles)} 1-minute candles")
    
    # Calculate price stats
    start_price = candles[0]['close']
    end_price = candles[-1]['close']
    price_change_pct = ((end_price - start_price) / start_price) * 100
    print(f"Price: ${start_price:.2f} → ${end_price:.2f} ({price_change_pct:+.2f}%)")
    print()
    
    # Run backtest
    backtester = AggressiveBacktester(initial_balance=10.0, leverage=leverage)
    report = backtester.run(candles)
    backtester.print_report(report, candles)


if __name__ == '__main__':
    main()
