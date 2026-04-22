#!/usr/bin/env python3
"""
Strategy Signal Generation Tests (Phase 2) - Simplified Version
Tests integration of strategies with risk governor and regime classifier
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from core.models import Config, AccountState, Engine, Regime
from core.risk_governor import RiskGovernor
from core.regime_classifier import RegimeClassifier


def create_test_candles(prices, start_time=None):
    """Helper to create OHLCV test data"""
    from core.models import OHLCV
    
    if start_time is None:
        start_time = datetime.now() - timedelta(hours=len(prices))
    
    candles = []
    for i, price in enumerate(prices):
        candles.append(OHLCV(
            timestamp=start_time + timedelta(hours=i),
            open=price,
            high=price * 1.01,
            low=price * 0.99,
            close=price,
            volume=1000.0
        ))
    return candles


def test_risk_governor_blocking_consecutive_losses():
    """Test that risk governor blocks after consecutive losses"""
    print("\n=== Test: Risk Governor Blocks After Consecutive Losses ===")
    
    config = Config()
    config.max_consecutive_losses = 2
    
    governor = RiskGovernor(config)
    
    # Account with 2 consecutive losses
    account = AccountState(
        equity=10000.0,
        daily_pnl=-150.0,
        daily_pnl_pct=-1.5,
        consecutive_losses=2,
        trades_today={},
        losses_today={},
        mode=Engine.IDLE
    )
    
    # Try to determine active engine - should return IDLE
    regime = Regime.RANGE
    active_engine = governor.determine_active_engine(regime, account)
    
    print(f"Consecutive losses: {account.consecutive_losses}")
    print(f"Active engine: {active_engine.value}")
    
    if active_engine == Engine.IDLE:
        print("✅ PASS: Risk governor correctly blocks trading after max consecutive losses")
        return True
    else:
        print(f"❌ FAIL: Expected IDLE, got {active_engine.value}")
        return False


def test_risk_governor_blocking_daily_drawdown():
    """Test that risk governor blocks after hitting daily drawdown limit"""
    print("\n=== Test: Risk Governor Blocks After Daily Drawdown ===")
    
    config = Config()
    config.max_daily_drawdown_pct = 2.0
    
    governor = RiskGovernor(config)
    
    # Account with -2% daily PnL (at limit)
    account = AccountState(
        equity=10000.0,
        daily_pnl=-200.0,
        daily_pnl_pct=-2.0,
        consecutive_losses=1,
        trades_today={},
        losses_today={},
        mode=Engine.IDLE
    )
    
    # Try to determine active engine - should return IDLE
    regime = Regime.RANGE
    active_engine = governor.determine_active_engine(regime, account)
    
    print(f"Daily PnL: ${account.daily_pnl:.2f} ({account.daily_pnl_pct:.1f}%)")
    print(f"Max drawdown: {config.max_daily_drawdown_pct}%")
    print(f"Active engine: {active_engine.value}")
    
    if active_engine == Engine.IDLE:
        print("✅ PASS: Risk governor correctly blocks trading after hitting daily drawdown")
        return True
    else:
        print(f"❌ FAIL: Expected IDLE, got {active_engine.value}")
        return False


def test_regime_determines_strategy_selection():
    """Test that regime determines which strategy is active"""
    print("\n=== Test: Regime Determines Strategy Selection ===")
    
    config = Config()
    governor = RiskGovernor(config)
    
    # Healthy account
    account = AccountState(
        equity=10000.0,
        daily_pnl=0.0,
        daily_pnl_pct=0.0,
        consecutive_losses=0,
        trades_today={},
        losses_today={},
        mode=Engine.IDLE
    )
    
    test_cases = [
        (Regime.RANGE, Engine.ER90),
        (Regime.WEAK_TREND, Engine.ER90),
        (Regime.STRONG_TREND, Engine.SIB),
    ]
    
    all_passed = True
    
    for regime, expected_engine in test_cases:
        active_engine = governor.determine_active_engine(regime, account)
        print(f"  Regime: {regime.value:15} -> Engine: {active_engine.value:6} (expected: {expected_engine.value})")
        
        if active_engine != expected_engine:
            print(f"    ❌ FAIL: Expected {expected_engine.value}, got {active_engine.value}")
            all_passed = False
    
    if all_passed:
        print("✅ PASS: Regime correctly determines strategy selection")
        return True
    else:
        print("❌ FAIL: Some regime-to-strategy mappings incorrect")
        return False


def test_er90_max_trades_limit():
    """Test that ER-90 respects max trades per day limit"""
    print("\n=== Test: ER-90 Max Trades Per Day Limit ===")
    
    config = Config()
    config.er90_max_losses_per_day = 1
    
    governor = RiskGovernor(config)
    
    # Account that has already taken 1 ER-90 loss today
    account = AccountState(
        equity=10000.0,
        daily_pnl=-50.0,
        daily_pnl_pct=-0.5,
        consecutive_losses=0,
        trades_today={Engine.ER90: 1},
        losses_today={Engine.ER90: 1},
        mode=Engine.IDLE
    )
    
    regime = Regime.RANGE
    active_engine = governor.determine_active_engine(regime, account)
    
    print(f"ER-90 losses today: {account.losses_today.get(Engine.ER90, 0)}")
    print(f"Max ER-90 losses per day: {config.er90_max_losses_per_day}")
    print(f"Active engine: {active_engine.value}")
    
    # Should be IDLE because ER-90 hit its limit
    if active_engine == Engine.IDLE:
        print("✅ PASS: ER-90 correctly blocked after reaching daily loss limit")
        return True
    else:
        print(f"❌ FAIL: Expected IDLE, got {active_engine.value}")
        return False


def test_sib_max_trades_limit():
    """Test that SIB respects max trades per day limit"""
    print("\n=== Test: SIB Max Trades Per Day Limit ===")
    
    config = Config()
    config.sib_max_trades_per_day = 1
    
    governor = RiskGovernor(config)
    
    # Account that has already taken 1 SIB trade today
    account = AccountState(
        equity=10000.0,
        daily_pnl=100.0,
        daily_pnl_pct=1.0,
        consecutive_losses=0,
        trades_today={Engine.SIB: 1},
        losses_today={},
        mode=Engine.IDLE
    )
    
    regime = Regime.STRONG_TREND
    active_engine = governor.determine_active_engine(regime, account)
    
    print(f"SIB trades today: {account.trades_today.get(Engine.SIB, 0)}")
    print(f"Max SIB trades per day: {config.sib_max_trades_per_day}")
    print(f"Active engine: {active_engine.value}")
    
    # Should be IDLE because SIB hit its limit
    if active_engine == Engine.IDLE:
        print("✅ PASS: SIB correctly blocked after reaching daily trade limit")
        return True
    else:
        print(f"❌ FAIL: Expected IDLE, got {active_engine.value}")
        return False


def test_regime_classifier_range_detection():
    """Test that regime classifier detects range-bound markets"""
    print("\n=== Test: Regime Classifier Detects Range ===")
    
    config = Config()
    classifier = RegimeClassifier(config)
    
    # Create flat, range-bound price data
    prices = [100.0] * 100 + np.random.normal(0, 0.5, 100)  # Flat with small noise
    candles = create_test_candles(prices)
    
    account = AccountState(
        equity=10000.0,
        daily_pnl=0.0,
        daily_pnl_pct=0.0,
        consecutive_losses=0,
        trades_today={},
        losses_today={},
        mode=Engine.IDLE
    )
    
    regime = classifier.classify(candles, account)
    
    print(f"Detected regime: {regime.value}")
    
    # Should detect RANGE
    if regime == Regime.RANGE:
        print("✅ PASS: Correctly classified flat market as RANGE")
        return True
    else:
        print(f"❌ FAIL: Expected RANGE, got {regime.value}")
        return False


def test_regime_classifier_trend_detection():
    """Test that regime classifier detects trending markets"""
    print("\n=== Test: Regime Classifier Detects Trend ===")
    
    config = Config()
    classifier = RegimeClassifier(config)
    
    # Create strong uptrend
    prices = np.linspace(100, 150, 200)  # +50% uptrend
    candles = create_test_candles(prices)
    
    account = AccountState(
        equity=10000.0,
        daily_pnl=0.0,
        daily_pnl_pct=0.0,
        consecutive_losses=0,
        trades_today={},
        losses_today={},
        mode=Engine.IDLE
    )
    
    regime = classifier.classify(candles, account)
    
    print(f"Detected regime: {regime.value}")
    
    # Should detect STRONG_TREND or WEAK_TREND
    if regime in [Regime.STRONG_TREND, Regime.WEAK_TREND]:
        print(f"✅ PASS: Correctly classified uptrend as {regime.value}")
        return True
    else:
        print(f"❌ FAIL: Expected TREND, got {regime.value}")
        return False


def test_mutual_exclusivity_via_regime():
    """Test that ER-90 and SIB are mutually exclusive via regime"""
    print("\n=== Test: ER-90 and SIB Mutual Exclusivity ===")
    
    config = Config()
    governor = RiskGovernor(config)
    
    account = AccountState(
        equity=10000.0,
        daily_pnl=0.0,
        daily_pnl_pct=0.0,
        consecutive_losses=0,
        trades_today={},
        losses_today={},
        mode=Engine.IDLE
    )
    
    # In RANGE regime, should only get ER-90
    engine_range = governor.determine_active_engine(Regime.RANGE, account)
    
    # In STRONG_TREND regime, should only get SIB
    engine_trend = governor.determine_active_engine(Regime.STRONG_TREND, account)
    
    print(f"RANGE regime -> {engine_range.value}")
    print(f"STRONG_TREND regime -> {engine_trend.value}")
    
    if engine_range == Engine.ER90 and engine_trend == Engine.SIB:
        print("✅ PASS: Strategies are mutually exclusive based on regime")
        return True
    else:
        print(f"❌ FAIL: Expected ER90 for RANGE and SIB for STRONG_TREND")
        return False


if __name__ == '__main__':
    print("="*60)
    print("HARVEST STRATEGY INTEGRATION TESTS (PHASE 2)")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(("Risk Governor: Consecutive Losses", test_risk_governor_blocking_consecutive_losses()))
    results.append(("Risk Governor: Daily Drawdown", test_risk_governor_blocking_daily_drawdown()))
    results.append(("Regime -> Strategy Selection", test_regime_determines_strategy_selection()))
    results.append(("ER-90 Max Trades Limit", test_er90_max_trades_limit()))
    results.append(("SIB Max Trades Limit", test_sib_max_trades_limit()))
    results.append(("Regime: Range Detection", test_regime_classifier_range_detection()))
    results.append(("Regime: Trend Detection", test_regime_classifier_trend_detection()))
    results.append(("Mutual Exclusivity", test_mutual_exclusivity_via_regime()))
    
    # Summary
    print("\n" + "="*60)
    print("PHASE 2 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({100*passed//total}%)")
    
    if passed == total:
        print("\n🎉 All Phase 2 tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
