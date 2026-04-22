#!/usr/bin/env python3
"""
Risk Management Validation (Phase 3) - Working Version
Tests that the risk governor correctly enforces all safety limits
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.models import Config, AccountState, Engine, Regime
from core.risk_governor import RiskGovernor


def test_daily_drawdown_limit():
    """Test that daily drawdown limit is enforced"""
    print("\n=== Test: Daily Drawdown Limit ===")
    
    config = Config()
    config.max_daily_drawdown_pct = 2.0
    governor = RiskGovernor(config)
    
    # Account at drawdown limit
    account = AccountState(
        equity=10000.0,
        daily_pnl=-200.0,
        daily_pnl_pct=-2.0,
        consecutive_losses=1,
        trades_today={},
        losses_today={},
        mode=Engine.IDLE
    )
    
    # Should be blocked
    is_safe = governor.validate_account_state(account)
    
    print(f"Daily PnL: ${account.daily_pnl:.2f} ({account.daily_pnl_pct:.1f}%)")
    print(f"Max allowed: {config.max_daily_drawdown_pct}%")
    print(f"Account safe to trade: {is_safe}")
    
    if not is_safe:
        print("✅ PASS: Daily drawdown limit correctly enforced")
        return True
    else:
        print("❌ FAIL: Should be blocked at drawdown limit")
        return False


def test_consecutive_loss_limit():
    """Test that consecutive loss limit is enforced"""
    print("\n=== Test: Consecutive Loss Limit ===")
    
    config = Config()
    config.max_consecutive_losses = 2
    governor = RiskGovernor(config)
    
    # Account at consecutive loss limit
    account = AccountState(
        equity=10000.0,
        daily_pnl=-100.0,
        daily_pnl_pct=-1.0,
        consecutive_losses=2,
        trades_today={},
        losses_today={},
        mode=Engine.IDLE
    )
    
    # Should be blocked
    is_safe = governor.validate_account_state(account)
    
    print(f"Consecutive losses: {account.consecutive_losses}")
    print(f"Max allowed: {config.max_consecutive_losses}")
    print(f"Account safe to trade: {is_safe}")
    
    if not is_safe:
        print("✅ PASS: Consecutive loss limit correctly enforced")
        return True
    else:
        print("❌ FAIL: Should be blocked at consecutive loss limit")
        return False


def test_healthy_account_allowed():
    """Test that healthy account can trade"""
    print("\n=== Test: Healthy Account Allowed ===")
    
    config = Config()
    governor = RiskGovernor(config)
    
    # Healthy account
    account = AccountState(
        equity=10000.0,
        daily_pnl=50.0,
        daily_pnl_pct=0.5,
        consecutive_losses=0,
        trades_today={},
        losses_today={},
        mode=Engine.IDLE
    )
    
    # Should be allowed
    is_safe = governor.validate_account_state(account)
    
    print(f"Daily PnL: ${account.daily_pnl:.2f} ({account.daily_pnl_pct:.1f}%)")
    print(f"Consecutive losses: {account.consecutive_losses}")
    print(f"Account safe to trade: {is_safe}")
    
    if is_safe:
        print("✅ PASS: Healthy account correctly allowed to trade")
        return True
    else:
        print("❌ FAIL: Healthy account should be allowed")
        return False


def test_regime_based_engine_selection():
    """Test that engine selection is based on regime"""
    print("\n=== Test: Regime-Based Engine Selection ===")
    
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
        (Regime.RANGE, Engine.ER90, "Range -> ER90"),
        (Regime.WEAK_TREND, Engine.ER90, "Weak Trend -> ER90"),
        (Regime.STRONG_TREND, Engine.SIB, "Strong Trend -> SIB"),
        (Regime.DRAWDOWN, Engine.IDLE, "Drawdown -> IDLE"),
    ]
    
    all_passed = True
    
    for regime, expected_engine, description in test_cases:
        active_engine = governor.determine_active_engine(regime, account)
        status = "✅" if active_engine == expected_engine else "❌"
        print(f"  {status} {description}: {active_engine.value}")
        
        if active_engine != expected_engine:
            all_passed = False
    
    if all_passed:
        print("✅ PASS: All regime-based selections correct")
        return True
    else:
        print("❌ FAIL: Some regime selections incorrect")
        return False


def test_position_size_calculation():
    """Test position sizing calculations are reasonable"""
    print("\n=== Test: Position Size Calculations ===")
    
    config = Config()
    
    # Test ER-90 risk parameters
    equity = 10000.0
    er90_risk_pct = config.er90_risk_pct_min  # 0.25%
    er90_risk_amount = equity * (er90_risk_pct / 100)
    
    print(f"ER-90 Risk Calculation:")
    print(f"  Equity: ${equity:,.2f}")
    print(f"  Risk per trade: {er90_risk_pct}%")
    print(f"  Risk amount: ${er90_risk_amount:.2f}")
    
    # Test SIB risk parameters
    sib_risk_pct = config.sib_risk_pct_min  # 0.5%
    sib_risk_amount = equity * (sib_risk_pct / 100)
    
    print(f"\nSIB Risk Calculation:")
    print(f"  Equity: ${equity:,.2f}")
    print(f"  Risk per trade: {sib_risk_pct}%")
    print(f"  Risk amount: ${sib_risk_amount:.2f}")
    
    # Verify reasonable values
    if 0 < er90_risk_amount < equity * 0.01 and 0 < sib_risk_amount < equity * 0.02:
        print("\n✅ PASS: Risk amounts are reasonable (<1% and <2% respectively)")
        return True
    else:
        print("\n❌ FAIL: Risk amounts out of reasonable range")
        return False


def test_leverage_limits():
    """Test that leverage limits are configured properly"""
    print("\n=== Test: Leverage Limits ===")
    
    config = Config()
    
    print(f"ER-90 Leverage Range:")
    print(f"  Min: {config.er90_leverage_min}x")
    print(f"  Max: {config.er90_leverage_max}x")
    
    print(f"\nSIB Leverage Range:")
    print(f"  Min: {config.sib_leverage_min}x")
    print(f"  Max: {config.sib_leverage_max}x")
    
    # Verify reasonable ranges
    er90_valid = 5 <= config.er90_leverage_min <= 15 and 15 <= config.er90_leverage_max <= 25
    sib_valid = 15 <= config.sib_leverage_min <= 25 and 25 <= config.sib_leverage_max <= 50
    
    if er90_valid and sib_valid:
        print("\n✅ PASS: Leverage limits are within safe ranges")
        return True
    else:
        print("\n❌ FAIL: Leverage limits outside safe ranges")
        return False


def test_liquidation_buffer():
    """Test liquidation buffer calculation"""
    print("\n=== Test: Liquidation Buffer ===")
    
    config = Config()
    
    print(f"Liquidation buffer: {config.liquidation_buffer_pct}%")
    
    # Example calculation
    leverage = 15.0
    entry_price = 50000.0
    
    # Liquidation distance is roughly 1/leverage
    liq_distance_pct = (100 / leverage)
    
    # Stop loss should be before liquidation with buffer
    safe_stop_distance = liq_distance_pct * (1 - config.liquidation_buffer_pct / 100)
    safe_stop_price = entry_price * (1 - safe_stop_distance / 100)
    
    print(f"\nExample (15x leverage, $50,000 entry):")
    print(f"  Liquidation distance: ~{liq_distance_pct:.2f}%")
    print(f"  Safe stop distance: ~{safe_stop_distance:.2f}%")
    print(f"  Safe stop price: ${safe_stop_price:,.2f}")
    
    if config.liquidation_buffer_pct >= 10:
        print("\n✅ PASS: Liquidation buffer is adequate (≥10%)")
        return True
    else:
        print("\n❌ FAIL: Liquidation buffer too small")
        return False


def test_risk_recording():
    """Test that risk governor can record trade outcomes"""
    print("\n=== Test: Trade Outcome Recording ===")
    
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
    
    # Record a loss
    account = governor.record_trade_outcome(account, Engine.ER90, is_loss=True)
    
    print(f"After recording one loss:")
    print(f"  Consecutive losses: {account.consecutive_losses}")
    print(f"  ER90 trades today: {account.trades_today.get(Engine.ER90, 0)}")
    print(f"  ER90 losses today: {account.losses_today.get(Engine.ER90, 0)}")
    
    # Record a win
    account = governor.record_trade_outcome(account, Engine.ER90, is_loss=False)
    
    print(f"\nAfter recording one win:")
    print(f"  Consecutive losses: {account.consecutive_losses}")
    print(f"  ER90 trades today: {account.trades_today.get(Engine.ER90, 0)}")
    
    if account.consecutive_losses == 0 and account.trades_today[Engine.ER90] == 2:
        print("\n✅ PASS: Trade outcomes recorded correctly")
        return True
    else:
        print("\n❌ FAIL: Trade recording incorrect")
        return False


if __name__ == '__main__':
    print("="*70)
    print("HARVEST RISK MANAGEMENT VALIDATION (PHASE 3)")
    print("="*70)
    
    results = []
    
    # Run all tests
    results.append(("Daily Drawdown Limit", test_daily_drawdown_limit()))
    results.append(("Consecutive Loss Limit", test_consecutive_loss_limit()))
    results.append(("Healthy Account Allowed", test_healthy_account_allowed()))
    results.append(("Regime-Based Selection", test_regime_based_engine_selection()))
    results.append(("Position Size Calculation", test_position_size_calculation()))
    results.append(("Leverage Limits", test_leverage_limits()))
    results.append(("Liquidation Buffer", test_liquidation_buffer()))
    results.append(("Trade Outcome Recording", test_risk_recording()))
    
    # Summary
    print("\n" + "="*70)
    print("PHASE 3 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({100*passed//total}%)")
    
    if passed == total:
        print("\n🎉 All Phase 3 risk management tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)
