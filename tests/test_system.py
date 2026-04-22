"""Test script to validate HARVEST system with debug output."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtester import Backtester


def test_with_debug():
    """Run test with detailed debug output."""
    print("=" * 80)
    print("HARVEST SYSTEM TEST - Debug Mode")
    print("=" * 80)
    
    # Test with BTC
    print("\n🔍 Testing with BTCUSDT...")
    btc_backtester = Backtester(symbol="BTCUSDT", initial_equity=10000.0)
    btc_data = btc_backtester.fetch_data(days=30)
    
    if btc_data:
        print(f"\n✅ Data fetched successfully:")
        for tf, candles in btc_data.items():
            if candles:
                print(f"   {tf}: {len(candles)} candles")
                print(f"      First: {candles[0].timestamp}")
                print(f"      Last: {candles[-1].timestamp}")
                print(f"      Price range: ${candles[0].close:.2f} - ${candles[-1].close:.2f}")
        
        # Run backtest with smaller lookback to get more data points
        print(f"\n🚀 Running backtest...")
        results = btc_backtester.run_backtest(btc_data)
        
        print(f"\n📊 Regime history entries: {len(btc_backtester.regime_history)}")
        if btc_backtester.regime_history:
            print(f"   First regime: {btc_backtester.regime_history[0]}")
            print(f"   Last regime: {btc_backtester.regime_history[-1]}")
            
            # Count regimes
            regime_counts = {}
            for entry in btc_backtester.regime_history:
                r = entry['regime']
                regime_counts[r] = regime_counts.get(r, 0) + 1
            
            print(f"\n   Regime breakdown:")
            for regime, count in regime_counts.items():
                print(f"      {regime}: {count}")
        
        btc_backtester.export_results("btc_test_results.json")
    
    # Test with ETH (often more volatile)
    print("\n" + "=" * 80)
    print("\n🔍 Testing with ETHUSDT...")
    eth_backtester = Backtester(symbol="ETHUSDT", initial_equity=10000.0)
    eth_data = eth_backtester.fetch_data(days=30)
    
    if eth_data:
        print(f"\n✅ Data fetched successfully:")
        for tf, candles in eth_data.items():
            if candles:
                print(f"   {tf}: {len(candles)} candles")
                print(f"      First: {candles[0].timestamp}")
                print(f"      Last: {candles[-1].timestamp}")
                print(f"      Price range: ${candles[0].close:.2f} - ${candles[-1].close:.2f}")
        
        print(f"\n🚀 Running backtest...")
        results = eth_backtester.run_backtest(eth_data)
        
        print(f"\n📊 Regime history entries: {len(eth_backtester.regime_history)}")
        if eth_backtester.regime_history:
            print(f"   First regime: {eth_backtester.regime_history[0]}")
            print(f"   Last regime: {eth_backtester.regime_history[-1]}")
            
            regime_counts = {}
            for entry in eth_backtester.regime_history:
                r = entry['regime']
                regime_counts[r] = regime_counts.get(r, 0) + 1
            
            print(f"\n   Regime breakdown:")
            for regime, count in regime_counts.items():
                print(f"      {regime}: {count}")
        
        eth_backtester.export_results("eth_test_results.json")
    
    print("\n" + "=" * 80)
    print("✅ Test complete")
    print("=" * 80)


if __name__ == "__main__":
    test_with_debug()
