"""Simple test on ETH with verbose checking."""
import sys
sys.path.insert(0, '.')

from backtester import Backtester

print("Testing HARVEST on ETHUSDT with simplified conditions...")
print("="*70)

bt = Backtester(symbol='ETHUSDT', initial_equity=10000.0)
print(f"Config: RSI thresholds = {bt.config.er90_rsi_upper}/{bt.config.er90_rsi_lower}")

data = bt.fetch_data(days=30)

print("\n📊 Running backtest...")
results = bt.run_backtest(data)

bt.export_results('eth_simple_test.json')

print("\n" + "="*70)
print(f"✅ Complete: {results.get('total_execution_intents', 0)} signals generated")
print("="*70)

if results.get('total_execution_intents', 0) == 0:
    print("\n⚠️  Still no signals. The system WILL NOT force trades.")
    print("This means conditions were never all met during the 30-day period.")
    print("\nWith $10 capital + leverage, you need the system to be this")
    print("conservative to avoid blowing up the account.")
