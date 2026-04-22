#!/usr/bin/env python3
"""
Test Paper Trading with Live Updates
Simulates paper trading session with trades every 5 seconds
"""

import time
import random
from core.paper_trading_tracker import get_paper_trading_tracker

def main():
    print("="*70)
    print("PAPER TRADING LIVE TEST")
    print("="*70)
    print()
    
    # Reset and start
    tracker = get_paper_trading_tracker()
    tracker.reset()
    
    result = tracker.start_paper_trading(100)
    print(result['message'])
    print()
    print("Starting live trading simulation...")
    print("Dashboard should now show paper trading status")
    print("Press Ctrl+C to stop")
    print()
    
    trade_num = 0
    
    try:
        while True:
            # Wait 5 seconds
            time.sleep(5)
            
            # Random trade outcome
            trade_num += 1
            outcome = 'win' if random.random() > 0.3 else 'loss'
            pnl = random.uniform(0.50, 2.00) if outcome == 'win' else -random.uniform(0.20, 1.00)
            
            trade = {
                'timeframe': random.choice(['1m', '5m', '15m']),
                'asset': random.choice(['ETH', 'BTC']),
                'pnl': pnl,
                'outcome': outcome
            }
            
            result = tracker.record_trade(trade)
            
            # Show trade
            status = tracker.get_status()
            print(f"Trade {trade_num}: {result['message']}")
            print(f"  Balance: ${status['current_balance']:.2f} | P&L: ${status['total_pnl']:.2f} | Trades: {status['total_trades']}")
            
            # Check requirements
            reqs = tracker.check_requirements()
            if reqs['all_met']:
                print()
                print("🎉 ALL REQUIREMENTS MET!")
                print("Paper trading session can be completed")
                print("Check dashboard - should show 'READY'")
                break
                
    except KeyboardInterrupt:
        print()
        print("Stopped by user")
    
    print()
    print("="*70)
    print("Session continues in background")
    print("Dashboard will keep showing status")
    print("="*70)

if __name__ == '__main__':
    main()
