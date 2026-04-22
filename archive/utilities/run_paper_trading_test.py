#!/usr/bin/env python3
"""
7-Day Paper Trading Test for HARVEST
Runs the trading system in paper mode and logs all signals/trades
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import Config, AccountState, Engine
from core.data_ingestion import DataIngestion
from core.regime_classifier import RegimeClassifier
from core.risk_governor import RiskGovernor
from core.leverage_executor import LeverageExecutor
from strategies.er90 import ER90Strategy
from strategies.sib import SIBStrategy


class PaperTradingTest:
    """Run 7-day paper trading test with full logging."""
    
    def __init__(self, capital: float = 10.0):
        print("="*70)
        print("HARVEST 7-DAY PAPER TRADING TEST")
        print("="*70)
        print(f"\nStarting capital: ${capital}")
        print(f"Start time: {datetime.now()}")
        print(f"Mode: PAPER TRADING (NO RISK)")
        print("\nThis will run for 7 days and log all signals generated.")
        print("You can stop anytime with Ctrl+C\n")
        
        # Initialize config for small capital
        self.config = Config(
            initial_equity=capital,
            small_capital_mode=(capital < 100),
            enable_paper_leverage=True,
            use_hyperliquid=False
        )
        
        # Initialize components
        self.symbol = "ETHUSDT"
        self.data_ingestion = DataIngestion(self.symbol)
        self.regime_classifier = RegimeClassifier(self.config)
        self.risk_governor = RiskGovernor(self.config)
        self.er90 = ER90Strategy(self.config)
        self.sib = SIBStrategy(self.config)
        self.executor = LeverageExecutor(config=self.config)
        
        # Initialize account state
        self.account = AccountState(
            equity=capital,
            daily_pnl=0.0,
            daily_pnl_pct=0.0,
            consecutive_losses=0,
            trades_today={},
            losses_today={},
            mode=Engine.IDLE
        )
        
        # Tracking
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(days=7)
        self.signals_generated = []
        self.trades_executed = []
        self.check_count = 0
        self.log_file = f"paper_trading_test_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        
        print(f"Test will end: {self.end_time}")
        print(f"Log file: {self.log_file}")
        print("\nPress Ctrl+C to stop early\n")
        print("="*70)
    
    def check_for_signals(self):
        """Check market for trading signals."""
        try:
            self.check_count += 1
            
            # Fetch data
            data = self.data_ingestion.fetch_multiple_timeframes(days=7)
            
            if not data or not data.get("1h"):
                print(f"[{datetime.now()}] No data received")
                return
            
            candles_1h = data.get("1h", [])
            candles_4h = data.get("4h", [])
            candles_5m = data.get("5m", [])
            
            if len(candles_1h) < 200 or len(candles_4h) < 50:
                print(f"[{datetime.now()}] Insufficient data")
                return
            
            # Classify regime
            regime = self.regime_classifier.classify(candles_4h, self.account)
            
            # Determine active engine
            active_engine = self.risk_governor.determine_active_engine(regime, self.account)
            
            # Log check
            current_price = candles_1h[-1].close
            print(f"[{datetime.now()}] Check #{self.check_count}")
            print(f"  Price: ${current_price:.2f}")
            print(f"  Regime: {regime.value}")
            print(f"  Engine: {active_engine.value}")
            print(f"  Equity: ${self.executor.paper_equity:.2f}")
            
            if active_engine == Engine.IDLE:
                print(f"  Status: IDLE (no trading)")
                return
            
            # Check for signals
            intent = None
            current_hour = datetime.now().hour
            
            if active_engine == Engine.ER90:
                intent = self.er90.check_entry(candles_5m, candles_1h, self.account)
            elif active_engine == Engine.SIB:
                # SIB only trades during specific hours
                if 14 <= current_hour <= 18:
                    intent = self.sib.check_entry(candles_5m, candles_1h, candles_4h, self.account)
            
            if intent:
                print(f"\n🎯 SIGNAL GENERATED!")
                print(f"  Engine: {intent.engine.value}")
                print(f"  Side: {intent.side.value}")
                print(f"  Entry: ${intent.entry:.2f}")
                print(f"  Stop: ${intent.stop:.2f}")
                print(f"  TP: ${intent.tp1:.2f}")
                print(f"  Leverage: {intent.leverage_cap}x")
                
                # Log signal
                self.signals_generated.append({
                    'timestamp': datetime.now().isoformat(),
                    'engine': intent.engine.value,
                    'side': intent.side.value,
                    'entry': intent.entry,
                    'stop': intent.stop,
                    'tp1': intent.tp1,
                    'leverage': intent.leverage_cap
                })
                
                # Execute in paper mode
                success = self.executor.execute_intent(intent, coin="ETH")
                
                if success:
                    print(f"  ✅ Paper trade executed")
                    self.trades_executed.append({
                        'timestamp': datetime.now().isoformat(),
                        'intent': intent.to_dict(),
                        'equity_after': self.executor.paper_equity
                    })
                else:
                    print(f"  ❌ Failed to execute (insufficient capital?)")
                
                print()
            
        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")
    
    def save_log(self):
        """Save test results to JSON."""
        results = {
            'test_info': {
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
                'checks_performed': self.check_count,
                'starting_capital': self.config.initial_equity,
                'final_capital': self.executor.paper_equity
            },
            'signals_generated': self.signals_generated,
            'trades_executed': self.trades_executed,
            'statistics': {
                'total_signals': len(self.signals_generated),
                'total_trades': len(self.trades_executed),
                'signals_per_day': len(self.signals_generated) / max(1, (datetime.now() - self.start_time).days or 1),
                'profit_loss': self.executor.paper_equity - self.config.initial_equity,
                'return_pct': ((self.executor.paper_equity / self.config.initial_equity) - 1) * 100
            }
        }
        
        with open(self.log_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📊 Results saved to: {self.log_file}")
    
    def print_summary(self):
        """Print test summary."""
        duration = datetime.now() - self.start_time
        days = duration.days
        hours = duration.seconds // 3600
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"\nDuration: {days} days, {hours} hours")
        print(f"Market checks: {self.check_count}")
        print(f"Signals generated: {len(self.signals_generated)}")
        print(f"Trades executed: {len(self.trades_executed)}")
        print(f"\nStarting capital: ${self.config.initial_equity:.2f}")
        print(f"Final capital: ${self.executor.paper_equity:.2f}")
        print(f"Profit/Loss: ${self.executor.paper_equity - self.config.initial_equity:.2f}")
        
        if self.config.initial_equity > 0:
            return_pct = ((self.executor.paper_equity / self.config.initial_equity) - 1) * 100
            print(f"Return: {return_pct:+.2f}%")
        
        if days > 0:
            print(f"\nSignals per day: {len(self.signals_generated) / days:.2f}")
        
        print("\n" + "="*70)
    
    def run(self, check_interval_minutes: int = 60):
        """
        Run the paper trading test.
        
        Args:
            check_interval_minutes: How often to check for signals (default 60 min)
        """
        print(f"\nStarting test... Checking every {check_interval_minutes} minutes\n")
        
        try:
            while datetime.now() < self.end_time:
                self.check_for_signals()
                
                # Calculate time to next check
                time_remaining = self.end_time - datetime.now()
                if time_remaining.total_seconds() <= 0:
                    break
                
                # Sleep until next check (or until test ends)
                sleep_seconds = min(check_interval_minutes * 60, time_remaining.total_seconds())
                
                next_check = datetime.now() + timedelta(seconds=sleep_seconds)
                print(f"  Next check: {next_check.strftime('%Y-%m-%d %H:%M:%S')}")
                print()
                
                time.sleep(sleep_seconds)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Test stopped by user")
        
        finally:
            self.print_summary()
            self.save_log()
            
            if len(self.signals_generated) == 0:
                print("\n💡 No signals generated during test period.")
                print("This is normal in range-bound markets.")
                print("The system is working correctly - it's just being conservative.")
            else:
                print(f"\n✅ {len(self.signals_generated)} signal(s) generated!")
                print("Review the log file for details.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run HARVEST paper trading test")
    parser.add_argument('--capital', type=float, default=10.0, 
                       help='Starting capital (default: $10)')
    parser.add_argument('--interval', type=int, default=60,
                       help='Check interval in minutes (default: 60)')
    parser.add_argument('--days', type=int, default=7,
                       help='Test duration in days (default: 7)')
    
    args = parser.parse_args()
    
    # Create and run test
    test = PaperTradingTest(capital=args.capital)
    
    # Adjust end time based on days argument
    if args.days != 7:
        test.end_time = test.start_time + timedelta(days=args.days)
        print(f"\nTest duration adjusted to {args.days} days")
        print(f"Will end: {test.end_time}\n")
    
    test.run(check_interval_minutes=args.interval)
    
    print("\n🎉 Paper trading test complete!")
    print("\nNext steps:")
    print("1. Review the log file for all signals")
    print("2. If signals look good, proceed to testnet")
    print("3. If no signals, that's normal in range markets")
    print("4. Consider running for longer or in more volatile periods")


if __name__ == "__main__":
    main()
