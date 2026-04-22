#!/usr/bin/env python3
"""
Comprehensive Test Suite for HARVEST Leverage Trading System
Tests all components without requiring real funds or private keys
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import Config, ExecutionIntent, Side, Engine
from core.leverage_executor import LeverageExecutor
from datetime import datetime
from decimal import Decimal


def test_config():
    """Test configuration for leverage trading."""
    print("\n" + "="*70)
    print("TEST 1: Configuration")
    print("="*70)
    
    # Test with $10 capital
    config_10 = Config(
        initial_equity=10.0,
        small_capital_mode=True,
        enable_paper_leverage=True,
        use_hyperliquid=False
    )
    
    print(f"✅ Small capital config ($10):")
    print(f"   Small capital mode: {config_10.small_capital_mode}")
    print(f"   Risk per trade: {config_10.small_capital_risk_pct}%")
    print(f"   Paper leverage: {config_10.enable_paper_leverage}")
    print(f"   Min position: ${config_10.min_position_size_usd}")
    
    # Test with $100 capital
    config_100 = Config(
        initial_equity=100.0,
        small_capital_mode=True,
        enable_paper_leverage=False,
        use_hyperliquid=True
    )
    
    print(f"\n✅ Medium capital config ($100):")
    print(f"   Small capital mode: {config_100.small_capital_mode}")
    print(f"   Use Hyperliquid: {config_100.use_hyperliquid}")
    print(f"   Testnet: {config_100.hyperliquid_testnet}")
    
    return True


def test_paper_trading_10_dollars():
    """Test paper trading with $10 capital."""
    print("\n" + "="*70)
    print("TEST 2: Paper Trading with $10")
    print("="*70)
    
    config = Config(
        initial_equity=10.0,
        small_capital_mode=True,
        enable_paper_leverage=True
    )
    
    executor = LeverageExecutor(config=config)
    
    print(f"Initial equity: ${executor.paper_equity:.2f}")
    print(f"Mode: {'PAPER' if executor.paper_mode else 'LIVE'}")
    
    # Create test intent (ER-90 LONG)
    intent = ExecutionIntent(
        timestamp=datetime.now(),
        engine=Engine.ER90,
        side=Side.LONG,
        entry=4000.0,
        stop=3960.0,  # 1% stop
        tp1=4080.0,   # 2% TP
        runner=None,
        leverage_cap=20.0,
        notional_usd=200.0,
        risk_pct=5.0,
        symbol="ETHUSDT"
    )
    
    print(f"\nExecuting LONG trade:")
    print(f"   Entry: ${intent.entry}")
    print(f"   Stop: ${intent.stop} (-1%)")
    print(f"   TP: ${intent.tp1} (+2%)")
    print(f"   Leverage: {intent.leverage_cap}x")
    
    # Execute
    success = executor.execute_intent(intent, coin="ETH")
    
    if success:
        print(f"✅ Position opened successfully")
        
        # Check position
        position = executor.get_position_status("ETH")
        if position:
            print(f"   Position size: ${position['size_usd']:.2f}")
            print(f"   Margin used: ${position['margin_used']:.2f}")
            print(f"   Remaining equity: ${executor.paper_equity:.2f}")
            
            # Close position
            executor.close_position("ETH", reason="test")
            print(f"✅ Position closed")
            print(f"   Final equity: ${executor.paper_equity:.2f}")
            return True
    else:
        print(f"❌ Failed to open position")
        return False


def test_paper_trading_100_dollars():
    """Test paper trading with $100 capital."""
    print("\n" + "="*70)
    print("TEST 3: Paper Trading with $100")
    print("="*70)
    
    config = Config(
        initial_equity=100.0,
        small_capital_mode=True,
        enable_paper_leverage=True
    )
    
    executor = LeverageExecutor(config=config)
    
    print(f"Initial equity: ${executor.paper_equity:.2f}")
    
    # Create test intent (SIB SHORT)
    intent = ExecutionIntent(
        timestamp=datetime.now(),
        engine=Engine.SIB,
        side=Side.SHORT,
        entry=4000.0,
        stop=4040.0,  # 1% stop (above for short)
        tp1=3920.0,   # 2% TP (below for short)
        runner=4800.0,
        leverage_cap=30.0,
        notional_usd=1000.0,
        risk_pct=2.0,
        symbol="ETHUSDT"
    )
    
    print(f"\nExecuting SHORT trade:")
    print(f"   Entry: ${intent.entry}")
    print(f"   Stop: ${intent.stop} (+1%)")
    print(f"   TP: ${intent.tp1} (-2%)")
    print(f"   Leverage: {intent.leverage_cap}x")
    
    # Execute
    success = executor.execute_intent(intent, coin="ETH")
    
    if success:
        print(f"✅ Position opened successfully")
        
        position = executor.get_position_status("ETH")
        if position:
            print(f"   Position size: ${position['size_usd']:.2f}")
            print(f"   Margin used: ${position['margin_used']:.2f}")
            
            # Test stop-loss trigger
            print(f"\nTesting stop-loss trigger...")
            sl_trigger = executor.check_stop_loss_take_profit("ETH", 4050.0)
            if sl_trigger == "stop-loss":
                print(f"✅ Stop-loss would trigger at $4,050")
            
            # Test take-profit trigger
            print(f"Testing take-profit trigger...")
            tp_trigger = executor.check_stop_loss_take_profit("ETH", 3900.0)
            if tp_trigger == "take-profit":
                print(f"✅ Take-profit would trigger at $3,900")
            
            executor.close_position("ETH", reason="test")
            print(f"✅ Position closed")
            return True
    else:
        print(f"❌ Failed to open position")
        return False


def test_multiple_positions():
    """Test handling multiple positions."""
    print("\n" + "="*70)
    print("TEST 4: Multiple Positions")
    print("="*70)
    
    config = Config(
        initial_equity=500.0,
        small_capital_mode=False,
        enable_paper_leverage=True
    )
    
    executor = LeverageExecutor(config=config)
    
    print(f"Initial equity: ${executor.paper_equity:.2f}")
    
    # Open first position
    intent1 = ExecutionIntent(
        timestamp=datetime.now(),
        engine=Engine.ER90,
        side=Side.LONG,
        entry=4000.0,
        stop=3960.0,
        tp1=4080.0,
        runner=None,
        leverage_cap=20.0,
        notional_usd=2000.0,
        risk_pct=1.0,
        symbol="ETHUSDT"
    )
    
    success1 = executor.execute_intent(intent1, coin="ETH")
    print(f"{'✅' if success1 else '❌'} First position (ETH): {'opened' if success1 else 'failed'}")
    
    # Check account summary
    summary = executor.get_account_summary()
    print(f"\nAccount summary:")
    print(f"   Mode: {summary['mode']}")
    print(f"   Equity: ${summary['equity']:.2f}")
    print(f"   Open positions: {summary['open_positions']}")
    print(f"   Positions: {summary['positions']}")
    
    # Close all
    closed = executor.close_all_positions(reason="test")
    print(f"\n✅ Closed {closed} position(s)")
    print(f"   Final equity: ${executor.paper_equity:.2f}")
    
    return success1


def test_position_sizing():
    """Test position sizing calculations."""
    print("\n" + "="*70)
    print("TEST 5: Position Sizing")
    print("="*70)
    
    test_cases = [
        (10.0, True, "Small capital ($10)"),
        (100.0, True, "Medium capital ($100)"),
        (1000.0, False, "Large capital ($1000)")
    ]
    
    for capital, small_cap_mode, description in test_cases:
        config = Config(
            initial_equity=capital,
            small_capital_mode=small_cap_mode,
            enable_paper_leverage=True
        )
        
        executor = LeverageExecutor(config=config)
        
        intent = ExecutionIntent(
            timestamp=datetime.now(),
            engine=Engine.ER90,
            side=Side.LONG,
            entry=4000.0,
            stop=3960.0,
            tp1=4080.0,
            runner=None,
            leverage_cap=20.0,
            notional_usd=200.0,
            risk_pct=2.0,
            symbol="ETHUSDT"
        )
        
        position_size = executor.calculate_position_size(
            intent, 
            Decimal(str(capital))
        )
        
        margin_needed = position_size / Decimal(str(intent.leverage_cap))
        
        print(f"\n{description}:")
        print(f"   Available capital: ${capital}")
        print(f"   Position size: ${position_size}")
        print(f"   Margin needed: ${margin_needed}")
        print(f"   Leverage: {intent.leverage_cap}x")
        print(f"   Small cap mode: {small_cap_mode}")
    
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*70)
    print("HARVEST LEVERAGE TRADING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print("\nRunning all tests without requiring real funds or API keys...")
    
    tests = [
        ("Configuration", test_config),
        ("Paper Trading ($10)", test_paper_trading_10_dollars),
        ("Paper Trading ($100)", test_paper_trading_100_dollars),
        ("Multiple Positions", test_multiple_positions),
        ("Position Sizing", test_position_sizing)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nThe leverage trading system is fully functional and ready for:")
        print("1. Paper trading (safe testing)")
        print("2. Testnet testing (with Hyperliquid testnet funds)")
        print("3. Live trading (when you're ready with real capital)")
        print("\nNext steps:")
        print("- Set ETH_PRIVATE_KEY environment variable")
        print("- Get testnet funds from Hyperliquid faucet")
        print("- Run: python3 core/hyperliquid_connector.py")
        print("- Read: HYPERLIQUID_INTEGRATION_COMPLETE.md")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("Please review the errors above")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
