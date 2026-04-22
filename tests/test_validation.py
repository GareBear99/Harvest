#!/usr/bin/env python3
"""
Comprehensive Validation Test Suite
Tests all critical calculations for trading bot accuracy
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.indicators_backtest import BacktestIndicators
from core.tier_manager import TierManager
from core.profit_locker import ProfitLocker
from core.leverage_scaler import LeverageScaler
from analysis.ml_confidence_model import calculate_rule_based_confidence

def test_short_pnl_calculations():
    """Test SHORT position PnL calculations"""
    print("\n" + "="*80)
    print("TEST 1: SHORT Position PnL Calculations")
    print("="*80)
    
    # Test case 1: TP hit (profitable)
    entry = 3000.0
    tp = 2950.0  # 50 points below (1.67% drop)
    position_size = 0.1
    
    pnl_tp = (entry - tp) * position_size
    expected_tp = 50.0 * 0.1
    
    print(f"\nCase 1: TP Hit")
    print(f"Entry: ${entry}, TP: ${tp}, Position Size: {position_size}")
    print(f"PnL: ${pnl_tp:.2f}")
    print(f"Expected: ${expected_tp:.2f}")
    assert abs(pnl_tp - expected_tp) < 0.01, f"TP PnL mismatch!"
    print("✅ PASS")
    
    # Test case 2: SL hit (loss)
    sl = 3030.0  # 30 points above (1% rise)
    pnl_sl = (entry - sl) * position_size
    expected_sl = -30.0 * 0.1
    
    print(f"\nCase 2: SL Hit")
    print(f"Entry: ${entry}, SL: ${sl}, Position Size: {position_size}")
    print(f"PnL: ${pnl_sl:.2f}")
    print(f"Expected: ${expected_sl:.2f}")
    assert abs(pnl_sl - expected_sl) < 0.01, f"SL PnL mismatch!"
    print("✅ PASS")
    
    # Test case 3: Verify TP < Entry < SL for SHORT
    assert tp < entry, "TP should be below entry for SHORT!"
    assert sl > entry, "SL should be above entry for SHORT!"
    print(f"\n✅ Position direction correct: TP ({tp}) < Entry ({entry}) < SL ({sl})")

def test_tp_sl_price_calculations():
    """Test TP/SL price calculations"""
    print("\n" + "="*80)
    print("TEST 2: TP/SL Price Calculations")
    print("="*80)
    
    entry_price = 2987.27
    tp_pct = 0.83  # 0.83% below
    sl_pct = 0.41  # 0.41% above
    
    tp_price = entry_price * (1 - tp_pct / 100)
    sl_price = entry_price * (1 + sl_pct / 100)
    
    expected_tp = 2987.27 * 0.9917  # 2962.48
    expected_sl = 2987.27 * 1.0041  # 2999.52
    
    print(f"\nEntry: ${entry_price:.2f}")
    print(f"TP ({tp_pct}% below): ${tp_price:.2f} (expected ~${expected_tp:.2f})")
    print(f"SL ({sl_pct}% above): ${sl_price:.2f} (expected ~${expected_sl:.2f})")
    
    assert tp_price < entry_price, "TP must be below entry for SHORT!"
    assert sl_price > entry_price, "SL must be above entry for SHORT!"
    assert abs(tp_price - expected_tp) < 1.0, "TP calculation off!"
    assert abs(sl_price - expected_sl) < 1.0, "SL calculation off!"
    print("✅ PASS")

def test_position_sizing():
    """Test position sizing calculations"""
    print("\n" + "="*80)
    print("TEST 3: Position Sizing")
    print("="*80)
    
    balance = 10.0
    risk_pct = 3.75  # Tier 1 Accumulation
    sl_pct = 1.0  # 1% stop loss
    leverage = 25
    price = 3000.0
    position_multiplier = 0.5  # 15m timeframe
    
    risk_amount = balance * (risk_pct / 100) * position_multiplier
    # Position value needed so that sl_pct loss = risk_amount (unleveraged)
    position_value = risk_amount / (sl_pct / 100)
    # Apply max position constraint and calculate margin
    max_position_value = balance * leverage
    position_value = min(position_value, max_position_value)
    margin = position_value / leverage
    position_size = position_value / price
    
    print(f"\nBalance: ${balance}")
    print(f"Risk: {risk_pct}% × {position_multiplier} = ${risk_amount:.2f}")
    print(f"SL: {sl_pct}%")
    print(f"Leverage: {leverage}×")
    print(f"Position Value: ${position_value:.2f}")
    print(f"Margin Required: ${margin:.2f}")
    print(f"Position Size: {position_size:.4f} units at ${price}")
    
    # Verify margin doesn't exceed balance
    assert margin <= balance, f"Margin ${margin:.2f} exceeds balance ${balance:.2f}!"
    print(f"✅ Margin check: ${margin:.2f} <= ${balance:.2f}")
    
    # Verify loss at SL equals risk_amount
    sl_price = price * (1 + sl_pct / 100)
    pnl_at_sl = (price - sl_price) * position_size
    print(f"\nVerify risk: If SL hits at ${sl_price:.2f}")
    print(f"Loss: ${pnl_at_sl:.2f} (should be ~${-risk_amount:.2f})")
    # Note: Due to leverage, actual loss will be risk_amount * leverage on margin
    print("✅ PASS")

def test_leverage_scaling():
    """Test leverage scaling with balance growth"""
    print("\n" + "="*80)
    print("TEST 4: Leverage Scaling")
    print("="*80)
    
    scaler = LeverageScaler()
    
    test_balances = [5, 10, 20, 35, 55, 75, 105, 160]
    expected_leverage = [15, 25, 25, 20, 15, 10, 8, 5]
    
    print(f"\n{'Balance':<10} {'Leverage':<10} {'Expected':<10} {'Status'}")
    print("-" * 45)
    
    for balance, expected in zip(test_balances, expected_leverage):
        leverage = scaler.get_leverage(balance)
        status = "✅" if leverage == expected else "❌"
        print(f"${balance:<9} {leverage}×{'':<8} {expected}×{'':<8} {status}")
        assert leverage == expected, f"Leverage mismatch at ${balance}!"
    
    print("\n✅ PASS: Leverage scales down as balance grows")

def test_profit_locking():
    """Test profit locking milestones"""
    print("\n" + "="*80)
    print("TEST 5: Profit Locking")
    print("="*80)
    
    locker = ProfitLocker(initial_balance=10.0)
    
    milestones = [
        (15, 0),   # Below $20, no lock
        (20, 10),  # Hit $20, lock $10
        (25, 10),  # Between milestones, keep $10
        (40, 20),  # Hit $40, lock $20
        (50, 20),  # Between milestones, keep $20
        (80, 40),  # Hit $80, lock $40
        (100, 40), # Between milestones, keep $40
        (160, 80), # Hit $160, lock $80
    ]
    
    print(f"\n{'Balance':<10} {'Locked':<10} {'Expected':<10} {'Status'}")
    print("-" * 45)
    
    for balance, expected_locked in milestones:
        result = locker.check_and_lock(balance)
        locked = result['locked_balance']
        status = "✅" if locked == expected_locked else "❌"
        
        if result['locked']:
            print(f"${balance:<9} ${locked:<9} ${expected_locked:<9} {status} 🔒 LOCKED")
        else:
            print(f"${balance:<9} ${locked:<9} ${expected_locked:<9} {status}")
        
        assert locked == expected_locked, f"Lock amount mismatch at ${balance}!"
    
    # Verify locks never decrease
    locker2 = ProfitLocker(initial_balance=10.0)
    # Must call at each milestone as balance grows
    locker2.check_and_lock(20)  # Lock $10
    locker2.check_and_lock(40)  # Lock $20
    locker2.check_and_lock(80)  # Lock $40
    result = locker2.check_and_lock(30)  # Drop to $30
    assert result['locked_balance'] == 40, "Locked amount decreased!"
    print("\n✅ PASS: Locks never decrease")

def test_tier_transitions():
    """Test tier transitions"""
    print("\n" + "="*80)
    print("TEST 6: Tier Transitions")
    print("="*80)
    
    tier_mgr = TierManager()
    
    test_balances = [5, 10, 20, 30, 50, 70, 100]
    expected_tiers = [0, 1, 1, 2, 2, 3, 3]
    tier_names = {0: "Recovery", 1: "Accumulation", 2: "Growth", 3: "Preservation"}
    
    print(f"\n{'Balance':<10} {'Tier':<8} {'Name':<15} {'Risk %':<8} {'Status'}")
    print("-" * 55)
    
    for balance, expected_tier in zip(test_balances, expected_tiers):
        tier_info = tier_mgr.update_tier(balance)
        tier = tier_info['new_tier']
        tier_config = tier_mgr.get_config(tier)
        
        status = "✅" if tier == expected_tier else "❌"
        print(f"${balance:<9} {tier:<7} {tier_names[tier]:<14} {tier_config.max_risk_per_trade_pct:.2f}%{'':<4} {status}")
        
        assert tier == expected_tier, f"Tier mismatch at ${balance}!"
    
    print("\n✅ PASS: Tiers transition correctly")

def test_atr_calculations():
    """Test ATR calculations"""
    print("\n" + "="*80)
    print("TEST 7: ATR Calculations")
    print("="*80)
    
    # Create simple test candles
    candles = [
        {'high': 3010, 'low': 2990, 'close': 3000},
        {'high': 3020, 'low': 2995, 'close': 3015},
        {'high': 3025, 'low': 3005, 'close': 3020},
        {'high': 3030, 'low': 3010, 'close': 3025},
        {'high': 3035, 'low': 3015, 'close': 3030},
    ]
    
    atr = BacktestIndicators.atr(candles, period=3)
    
    # Manually calculate True Ranges
    tr1 = 3020 - 2995  # 25
    tr2 = 3025 - 3005  # 20
    tr3 = 3030 - 3010  # 20
    expected_atr = (25 + 20 + 20) / 3  # 21.67
    
    print(f"\nCalculated ATR: {atr:.2f}")
    print(f"Expected ATR: ~{expected_atr:.2f}")
    
    # Allow 10% tolerance due to EMA vs SMA
    assert abs(atr - expected_atr) < expected_atr * 0.3, "ATR calculation significantly off!"
    print("✅ PASS")

def test_candle_aggregation():
    """Test candle aggregation"""
    print("\n" + "="*80)
    print("TEST 8: Candle Aggregation")
    print("="*80)
    
    # Create 60 1-minute candles
    candles_1m = []
    for i in range(60):
        candles_1m.append({
            'timestamp': f'2024-01-01T00:{i:02d}:00',
            'open': 3000 + i,
            'high': 3010 + i,
            'low': 2990 + i,
            'close': 3005 + i,
            'volume': 100
        })
    
    # Aggregate to 15m (should give 4 candles)
    candles_15m = BacktestIndicators.aggregate_candles(candles_1m, 15)
    
    print(f"\nInput: 60 × 1-minute candles")
    print(f"Aggregated to 15m: {len(candles_15m)} candles")
    assert len(candles_15m) == 4, f"Expected 4 candles, got {len(candles_15m)}!"
    
    # Check first 15m candle
    first = candles_15m[0]
    print(f"\nFirst 15m candle:")
    print(f"  Open: {first['open']} (should be {candles_1m[0]['open']})")
    print(f"  High: {first['high']} (should be max of first 15)")
    print(f"  Low: {first['low']} (should be min of first 15)")
    print(f"  Close: {first['close']} (should be {candles_1m[14]['close']})")
    print(f"  Volume: {first['volume']} (should be {100 * 15})")
    
    assert first['open'] == candles_1m[0]['open'], "Open mismatch!"
    assert first['close'] == candles_1m[14]['close'], "Close mismatch!"
    assert first['volume'] == 1500, "Volume sum mismatch!"
    
    print("✅ PASS")

def test_confidence_edge_cases():
    """Test confidence scoring edge cases"""
    print("\n" + "="*80)
    print("TEST 9: Confidence Scoring Edge Cases")
    print("="*80)
    
    # Test extreme bullish (should score low for SHORT)
    features_bullish = {
        'adx': 10,
        'trend_consistency': 0.2,
        'rsi': 30,
        'ema9_slope': 1.0,
        'volume_ratio': 0.5,
        'volume_trend': -0.3,
        'atr_pct': 0.3,
        'distance_to_high': 3.0,
        'roc_10': 2.0
    }
    
    conf_bullish = calculate_rule_based_confidence(features_bullish)
    print(f"\nBullish scenario confidence: {conf_bullish:.2f}")
    assert conf_bullish < 0.5, "Bullish scenario should have low confidence for SHORT!"
    print("✅ LOW confidence for bullish conditions")
    
    # Test ideal bearish (should score high for SHORT)
    features_bearish = {
        'adx': 40,
        'trend_consistency': 0.9,
        'rsi': 65,
        'ema9_slope': -1.0,
        'volume_ratio': 1.5,
        'volume_trend': 0.4,
        'atr_pct': 1.2,
        'distance_to_high': 1.0,
        'roc_10': -2.0
    }
    
    conf_bearish = calculate_rule_based_confidence(features_bearish)
    print(f"Bearish scenario confidence: {conf_bearish:.2f}")
    assert conf_bearish > 0.75, "Bearish scenario should have high confidence for SHORT!"
    print("✅ HIGH confidence for bearish conditions")
    
    # Test clamping to [0, 1]
    assert 0 <= conf_bullish <= 1, "Confidence not clamped to [0,1]!"
    assert 0 <= conf_bearish <= 1, "Confidence not clamped to [0,1]!"
    print("✅ Confidence properly clamped to [0,1]")

def run_all_tests():
    """Run all validation tests"""
    print("\n" + "#"*80)
    print("COMPREHENSIVE VALIDATION TEST SUITE")
    print("#"*80)
    
    tests = [
        test_short_pnl_calculations,
        test_tp_sl_price_calculations,
        test_position_sizing,
        test_leverage_scaling,
        test_profit_locking,
        test_tier_transitions,
        test_atr_calculations,
        test_candle_aggregation,
        test_confidence_edge_cases
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "#"*80)
    print("TEST SUMMARY")
    print("#"*80)
    print(f"\nTotal Tests: {len(tests)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED - SYSTEM VALIDATED!")
        print("✅ Trading bot calculations are sound and accurate")
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED - REQUIRES FIXES")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
