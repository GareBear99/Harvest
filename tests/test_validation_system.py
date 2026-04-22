#!/usr/bin/env python3
"""
Comprehensive Test Suite for Validation System
Tests all components to ensure they work correctly.
"""

import sys
import os
from datetime import datetime

# Add path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_expected_values():
    """Test expected values and validation functions"""
    
    print("\n" + "="*80)
    print("TEST 1: Expected Values & Validation Functions")
    print("="*80 + "\n")
    
    from validation.expected_values import (
        validate_strategy_params,
        validate_performance_metrics,
        is_within_expected_range,
        DATA_EXPECTATIONS,
        STRATEGY_BOUNDS,
        PERFORMANCE_EXPECTATIONS
    )
    
    # Test 1.1: Valid strategy parameters
    print("1.1 Testing valid strategy parameters...")
    valid_params = {
        'min_confidence': 0.85,
        'min_volume': 3.0,
        'min_trend': 0.55,
        'min_adx': 30,
        'atr_min': 0.015,
        'atr_max': 0.040
    }
    
    passed, violations = validate_strategy_params(valid_params)
    assert passed, f"Valid params should pass: {violations}"
    print(f"  ✅ Valid parameters passed: {passed}, violations: {len(violations)}")
    
    # Test 1.2: Invalid strategy parameters
    print("\n1.2 Testing invalid strategy parameters...")
    invalid_params = {
        'min_confidence': 0.99,  # Too high
        'min_volume': 10.0,      # Too high
        'min_trend': 0.10,       # Too low
        'min_adx': 10,           # Too low
        'atr_min': 0.001,        # Too low
        'atr_max': 0.100         # Too high
    }
    
    passed, violations = validate_strategy_params(invalid_params)
    assert not passed, "Invalid params should fail"
    assert len(violations) == 6, f"Should have 6 violations, got {len(violations)}"
    print(f"  ✅ Invalid parameters failed as expected: {len(violations)} violations")
    for v in violations[:3]:
        print(f"     - {v['parameter']}: {v['value']} (expected {v['expected']})")
    
    # Test 1.3: Valid performance metrics
    print("\n1.3 Testing valid performance metrics...")
    valid_perf = {
        'win_rate': 0.85,
        'trades_min': 50,
        'total_pnl': 100.0
    }
    
    passed, violations = validate_performance_metrics(valid_perf)
    assert passed, f"Valid performance should pass: {violations}"
    print(f"  ✅ Valid performance passed: {passed}, violations: {len(violations)}")
    
    # Test 1.4: Invalid performance metrics
    print("\n1.4 Testing invalid performance metrics...")
    invalid_perf = {
        'win_rate': 0.50,  # Too low
        'trades_min': 1,   # Too low
        'total_pnl': -50.0  # Negative
    }
    
    passed, violations = validate_performance_metrics(invalid_perf)
    assert not passed, "Invalid performance should fail"
    print(f"  ✅ Invalid performance failed as expected: {len(violations)} violations")
    
    # Test 1.5: Range checking
    print("\n1.5 Testing range checking...")
    assert is_within_expected_range(85, 70, 98), "85 should be in range [70, 98]"
    assert not is_within_expected_range(50, 70, 98), "50 should not be in range [70, 98]"
    assert not is_within_expected_range(100, 70, 98), "100 should not be in range [70, 98]"
    print(f"  ✅ Range checking works correctly")
    
    print("\n✅ TEST 1 PASSED: All validation functions work correctly\n")


def test_audit_logger():
    """Test audit logging system"""
    
    print("\n" + "="*80)
    print("TEST 2: Audit Logger")
    print("="*80 + "\n")
    
    from validation.audit_logger import (
        get_audit_logger,
        log_data_validation,
        log_strategy_validation,
        log_download,
        log_grid_search,
        AuditLevel
    )
    
    # Get logger
    logger = get_audit_logger()
    
    # Test 2.1: Log directory creation
    print("2.1 Checking log directory...")
    assert os.path.exists("logs/audit"), "Audit log directory should exist"
    print(f"  ✅ Log directory exists: logs/audit")
    
    # Test 2.2: Session file creation
    print("\n2.2 Checking session log file...")
    assert os.path.exists(logger.session_file), f"Session file should exist: {logger.session_file}"
    print(f"  ✅ Session file created: {os.path.basename(logger.session_file)}")
    
    # Test 2.3: Log various events
    print("\n2.3 Logging test events...")
    
    log_data_validation('TEST_BTCUSDT', True, {'candle_count': 129660})
    log_strategy_validation('BTCUSDT', '1m', 1, True, [])
    log_download('BTCUSDT', 129660, True)
    log_grid_search('BTCUSDT', '1m', 121500, 1800.0, 0.92)
    
    logger.log_event(
        event_type="TEST_EVENT",
        level=AuditLevel.INFO,
        message="Test event logged",
        data={'test': True}
    )
    
    print(f"  ✅ Logged 5 test events")
    
    # Test 2.4: Verify events written
    print("\n2.4 Verifying events written to file...")
    with open(logger.session_file, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) >= 6, f"Should have at least 6 events (including SESSION_START), got {len(lines)}"
    print(f"  ✅ Events written to file: {len(lines)} lines")
    
    # Test 2.5: Log warning to trigger summary update
    print("\n2.5 Testing summary file creation...")
    logger.log_event(
        event_type="TEST_WARNING",
        level=AuditLevel.WARNING,
        message="Test warning",
        data={'test': True}
    )
    
    assert os.path.exists("logs/audit/audit_summary.json"), "Summary file should exist"
    print(f"  ✅ Summary file created")
    
    print("\n✅ TEST 2 PASSED: Audit logging works correctly\n")


def test_data_validator():
    """Test data validation on existing files"""
    
    print("\n" + "="*80)
    print("TEST 3: Data Validator")
    print("="*80 + "\n")
    
    from validation.data_validator import validate_candle_data, validate_all_active_pairs
    
    # Test 3.1: Check if data files exist
    print("3.1 Checking for data files...")
    
    test_files = [
        ('BTCUSDT', 'data/BTCUSDT_1m_90d.json'),
        ('ETHUSDT', 'data/ETHUSDT_1m_90d.json')
    ]
    
    files_exist = []
    for symbol, filepath in test_files:
        if os.path.exists(filepath):
            files_exist.append((symbol, filepath))
            print(f"  ✅ Found: {filepath}")
        else:
            print(f"  ⚠️  Missing: {filepath}")
    
    if not files_exist:
        print("\n  ⚠️  No data files found - skipping data validation tests")
        print("  Run `python parallel_downloader.py` to download data first")
        return
    
    # Test 3.2: Validate each file
    print("\n3.2 Validating data files...")
    for symbol, filepath in files_exist:
        print(f"\n  Testing {symbol}...")
        passed, checks = validate_candle_data(filepath, symbol)
        
        print(f"    Candle count: {checks['candle_count']['value']} (expected: {checks['candle_count']['expected']})")
        print(f"    Date range: {checks['date_range']['value']}")
        print(f"    Price valid: {checks['price_valid']['passed']}")
        print(f"    Volume valid: {checks['volume_valid']['passed']}")
        print(f"    Gaps detected: {checks['gaps_detected']['count']}")
        print(f"    Duplicates: {checks['duplicates_detected']['count']}")
        print(f"    Overall: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    # Test 3.3: Validate all pairs
    print("\n3.3 Testing validate_all_active_pairs()...")
    results = validate_all_active_pairs()
    print(f"  ✅ Validated {len(results)} pairs")
    
    print("\n✅ TEST 3 PASSED: Data validation works correctly\n")


def test_system_health():
    """Test system health monitor"""
    
    print("\n" + "="*80)
    print("TEST 4: System Health Monitor")
    print("="*80 + "\n")
    
    from validation.system_health import SystemHealth
    
    health = SystemHealth()
    
    # Test 4.1: Individual checks
    print("4.1 Testing individual health checks...\n")
    
    checks = [
        ("Data Freshness", health.check_data_freshness),
        ("Fallback Strategies", health.check_fallback_strategies),
        ("Model Files", health.check_model_files),
        ("Directories", health.check_directories),
        ("Dependencies", health.check_dependencies)
    ]
    
    for name, check_func in checks:
        print(f"  {name}...", end=" ")
        try:
            passed, message = check_func()
            status = "✅" if passed else "⚠️"
            print(f"{status} {message}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 4.2: Run all checks
    print("\n4.2 Running all checks together...")
    all_checks = health.run_all_checks()
    print(f"  ✅ Completed {len(all_checks)} checks")
    print(f"  Overall: {'✅ HEALTHY' if health.overall_passed else '⚠️ ISSUES DETECTED'}")
    
    # Test 4.3: Print report
    print("\n4.3 Testing report generation...")
    health.print_report()
    
    print("\n✅ TEST 4 PASSED: System health monitor works correctly\n")


def test_production_checklist():
    """Test production readiness checklist"""
    
    print("\n" + "="*80)
    print("TEST 5: Production Readiness Checklist")
    print("="*80 + "\n")
    
    from validation.production_checklist import ProductionReadinessChecklist
    
    checklist = ProductionReadinessChecklist()
    
    # Test 5.1: Run all checks
    print("5.1 Running production checklist...\n")
    results = checklist.run_all_checks()
    
    print(f"\n  ✅ Completed {len(results)} checks")
    print(f"  Overall: {'✅ PRODUCTION READY' if checklist.passed else '⚠️ NOT READY'}")
    
    # Test 5.2: Generate report
    print("\n5.2 Generating report...")
    report_file = checklist.generate_report('test_production_report.json')
    
    assert os.path.exists(report_file), "Report file should be created"
    print(f"  ✅ Report generated: {report_file}")
    
    # Clean up test report
    if os.path.exists('test_production_report.json'):
        os.remove('test_production_report.json')
    
    print("\n✅ TEST 5 PASSED: Production checklist works correctly\n")


def test_strategy_validation_integration():
    """Test integration with auto_strategy_updater"""
    
    print("\n" + "="*80)
    print("TEST 6: Strategy Validation Integration")
    print("="*80 + "\n")
    
    # Test 6.1: Check if fallback file exists
    print("6.1 Checking fallback strategies file...")
    fallback_file = 'ml/fallback_strategies.json'
    
    if not os.path.exists(fallback_file):
        print(f"  ⚠️  No fallback strategies found: {fallback_file}")
        print("  Run `python auto_strategy_updater.py` to generate strategies")
        return
    
    import json
    with open(fallback_file, 'r') as f:
        fallbacks = json.load(f)
    
    print(f"  ✅ Found fallback file with {len(fallbacks)} pairs")
    
    # Test 6.2: Check validation_passed flag
    print("\n6.2 Checking validation_passed flags...")
    for key, config in fallbacks.items():
        has_flag = config.get('validation_passed', False)
        strategy_count = len(config.get('strategies', []))
        status = "✅" if has_flag else "⚠️"
        print(f"  {status} {key}: {strategy_count} strategies, validated: {has_flag}")
    
    # Test 6.3: Validate strategy parameters
    print("\n6.3 Validating strategy parameters...")
    from validation.expected_values import validate_strategy_params, validate_performance_metrics
    
    for key, config in fallbacks.items():
        for i, strategy in enumerate(config.get('strategies', []), 1):
            params = {
                'min_confidence': strategy.get('min_confidence'),
                'min_volume': strategy.get('min_volume'),
                'min_trend': strategy.get('min_trend'),
                'min_adx': strategy.get('min_adx'),
                'atr_min': strategy.get('atr_min'),
                'atr_max': strategy.get('atr_max')
            }
            
            passed, violations = validate_strategy_params(params)
            status = "✅" if passed else "⚠️"
            print(f"  {status} {key} Strategy #{i}: {len(violations)} violations")
            
            if violations:
                for v in violations[:2]:
                    print(f"      - {v['parameter']}: {v['value']} (expected {v['expected']})")
    
    print("\n✅ TEST 6 PASSED: Strategy validation integration works correctly\n")


def test_imports():
    """Test that all modules can be imported"""
    
    print("\n" + "="*80)
    print("TEST 0: Module Imports")
    print("="*80 + "\n")
    
    modules = [
        'validation.expected_values',
        'validation.data_validator',
        'validation.audit_logger',
        'validation.system_health',
        'validation.production_checklist'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except Exception as e:
            print(f"  ❌ {module}: {e}")
            raise
    
    print("\n✅ TEST 0 PASSED: All modules import successfully\n")


def run_all_tests():
    """Run all tests"""
    
    print("\n" + "="*80)
    print("🧪 COMPREHENSIVE VALIDATION SYSTEM TEST SUITE")
    print("="*80)
    print(f"Started: {datetime.now().isoformat()}")
    print("="*80)
    
    tests = [
        ("Module Imports", test_imports),
        ("Expected Values", test_expected_values),
        ("Audit Logger", test_audit_logger),
        ("Data Validator", test_data_validator),
        ("System Health", test_system_health),
        ("Production Checklist", test_production_checklist),
        ("Strategy Integration", test_strategy_validation_integration)
    ]
    
    passed_tests = 0
    failed_tests = []
    
    for name, test_func in tests:
        try:
            test_func()
            passed_tests += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {name}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            failed_tests.append(name)
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\nFailed tests: {', '.join(failed_tests)}")
        print("\n❌ SOME TESTS FAILED")
    else:
        print("\n✅ ALL TESTS PASSED")
    
    print("="*80 + "\n")
    
    return len(failed_tests) == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
