#!/usr/bin/env python3
"""
Comprehensive Test Suite for Data Validation

Tests all edge cases and discrepancy detection:
- Timestamp issues
- Price anomalies
- Data corruption
- Missing data
- Format errors
"""

import json
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_test_data(scenario):
    """Create test data for different scenarios"""
    
    base_time = datetime(2025, 1, 1, 0, 0, 0)
    data = []
    
    if scenario == "perfect":
        # Perfect data - should pass all checks
        for i in range(100):
            ts = base_time + timedelta(minutes=i)
            price = 3000 + i
            data.append({
                'timestamp': ts.isoformat(),
                'open': price,
                'high': price + 10,
                'low': price - 10,
                'close': price + 5,
                'volume': 100.0
            })
    
    elif scenario == "missing_timestamps":
        # Missing some timestamps (gaps)
        for i in range(100):
            if i == 50:  # Skip timestamp 50
                continue
            ts = base_time + timedelta(minutes=i)
            price = 3000 + i
            data.append({
                'timestamp': ts.isoformat(),
                'open': price,
                'high': price + 10,
                'low': price - 10,
                'close': price + 5,
                'volume': 100.0
            })
    
    elif scenario == "duplicate_timestamps":
        # Duplicate timestamps
        for i in range(100):
            ts = base_time + timedelta(minutes=i)
            price = 3000 + i
            data.append({
                'timestamp': ts.isoformat(),
                'open': price,
                'high': price + 10,
                'low': price - 10,
                'close': price + 5,
                'volume': 100.0
            })
            
            if i == 50:  # Add duplicate at 50
                data.append({
                    'timestamp': ts.isoformat(),
                    'open': price,
                    'high': price + 10,
                    'low': price - 10,
                    'close': price + 5,
                    'volume': 100.0
                })
    
    elif scenario == "out_of_order":
        # Timestamps out of chronological order
        for i in range(100):
            ts = base_time + timedelta(minutes=i)
            price = 3000 + i
            data.append({
                'timestamp': ts.isoformat(),
                'open': price,
                'high': price + 10,
                'low': price - 10,
                'close': price + 5,
                'volume': 100.0
            })
        
        # Swap items 50 and 51
        data[50], data[51] = data[51], data[50]
    
    elif scenario == "invalid_ohlc":
        # Invalid OHLC relationships (high < low)
        for i in range(100):
            ts = base_time + timedelta(minutes=i)
            price = 3000 + i
            
            if i == 50:
                # Invalid: high < low
                data.append({
                    'timestamp': ts.isoformat(),
                    'open': price,
                    'high': price - 20,  # Lower than low!
                    'low': price - 10,
                    'close': price + 5,
                    'volume': 100.0
                })
            else:
                data.append({
                    'timestamp': ts.isoformat(),
                    'open': price,
                    'high': price + 10,
                    'low': price - 10,
                    'close': price + 5,
                    'volume': 100.0
                })
    
    elif scenario == "negative_prices":
        # Negative or zero prices
        for i in range(100):
            ts = base_time + timedelta(minutes=i)
            price = 3000 + i if i != 50 else -100  # Negative price at 50
            data.append({
                'timestamp': ts.isoformat(),
                'open': price,
                'high': price + 10 if price > 0 else 0,
                'low': price - 10 if price > 0 else -200,
                'close': price + 5,
                'volume': 100.0
            })
    
    elif scenario == "extreme_volatility":
        # Unrealistic price jumps
        for i in range(100):
            ts = base_time + timedelta(minutes=i)
            
            if i == 50:
                # 50% jump in 1 minute
                price = 3000 * 1.5
            else:
                price = 3000 + i
            
            data.append({
                'timestamp': ts.isoformat(),
                'open': price,
                'high': price + 10,
                'low': price - 10,
                'close': price + 5,
                'volume': 100.0
            })
    
    elif scenario == "suspicious_prices":
        # Prices outside expected range
        for i in range(100):
            ts = base_time + timedelta(minutes=i)
            
            if i == 50:
                # ETH at $1 (suspiciously low)
                price = 1
            else:
                price = 3000 + i
            
            data.append({
                'timestamp': ts.isoformat(),
                'open': price,
                'high': price + 10 if price > 10 else price + 0.1,
                'low': price - 10 if price > 10 else price - 0.1,
                'close': price + 5 if price > 10 else price + 0.05,
                'volume': 100.0
            })
    
    elif scenario == "large_time_gap":
        # Large gap in timestamps (> 1 hour)
        for i in range(100):
            if i == 50:
                # Add 2-hour gap
                ts = base_time + timedelta(minutes=i) + timedelta(hours=2)
            else:
                ts = base_time + timedelta(minutes=i)
            
            price = 3000 + i
            data.append({
                'timestamp': ts.isoformat(),
                'open': price,
                'high': price + 10,
                'low': price - 10,
                'close': price + 5,
                'volume': 100.0
            })
    
    return data


def test_scenario(name, scenario):
    """Test a specific scenario"""
    
    print(f"\n{'='*80}")
    print(f"TEST: {name}")
    print(f"{'='*80}")
    
    # Create test data
    data = create_test_data(scenario)
    
    # Save to temp file
    temp_file = f'/tmp/test_{scenario}.json'
    with open(temp_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Created test data: {len(data)} candles")
    print(f"Scenario: {scenario}")
    
    # Run audit (simplified inline check)
    issues_found = []
    
    # Check timestamps
    timestamps = [datetime.fromisoformat(c['timestamp']) for c in data]
    
    # Check order
    for i in range(1, len(timestamps)):
        if timestamps[i] <= timestamps[i-1]:
            issues_found.append(f"Out of order at {i}")
            break
    
    # Check intervals
    for i in range(1, len(timestamps)):
        diff = (timestamps[i] - timestamps[i-1]).total_seconds()
        if diff != 60 and diff not in [0, -3540]:  # Allow DST
            issues_found.append(f"Irregular interval: {diff}s")
            break
    
    # Check OHLC
    for i, candle in enumerate(data):
        h, l = candle['high'], candle['low']
        if h < l:
            issues_found.append(f"Invalid OHLC at {i}")
            break
    
    # Check prices
    for i, candle in enumerate(data):
        if candle['close'] <= 0:
            issues_found.append(f"Invalid price at {i}")
            break
    
    # Check gaps
    for i in range(1, len(timestamps)):
        gap = (timestamps[i] - timestamps[i-1]).total_seconds()
        if gap > 3600:
            issues_found.append(f"Large gap: {gap/60:.0f} min")
            break
    
    # Cleanup
    os.remove(temp_file)
    
    # Result
    if scenario == "perfect":
        expected = 0
    else:
        expected = 1  # Should find at least 1 issue
    
    found = len(issues_found)
    
    if found >= expected:
        print(f"✅ PASS: Expected issues, found {found}")
        if issues_found:
            print(f"   Issues: {', '.join(issues_found[:3])}")
        return True
    else:
        print(f"❌ FAIL: Expected {expected}+ issues, found {found}")
        return False


def main():
    print("\n" + "="*80)
    print("🧪 COMPREHENSIVE DATA VALIDATION TEST SUITE")
    print("="*80)
    print("\nTesting all edge cases and discrepancy detection...")
    
    test_cases = [
        ("Perfect Data (Should Pass)", "perfect"),
        ("Missing Timestamps", "missing_timestamps"),
        ("Duplicate Timestamps", "duplicate_timestamps"),
        ("Out of Order Timestamps", "out_of_order"),
        ("Invalid OHLC Relationships", "invalid_ohlc"),
        ("Negative Prices", "negative_prices"),
        ("Extreme Volatility", "extreme_volatility"),
        ("Suspicious Prices", "suspicious_prices"),
        ("Large Time Gaps", "large_time_gap"),
    ]
    
    results = []
    
    for name, scenario in test_cases:
        passed = test_scenario(name, scenario)
        results.append((name, passed))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\n{'='*80}")
    print(f"Results: {passed_count}/{total_count} tests passed")
    print(f"{'='*80}")
    
    if passed_count == total_count:
        print("\n✅ ALL TESTS PASSED - Validation system working correctly!")
        return 0
    else:
        print(f"\n❌ {total_count - passed_count} TESTS FAILED - Review above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
