"""
Data validation checkpoints for verifying downloaded data integrity.
Validates candle counts, date ranges, price/volume data against expected bounds.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from .expected_values import DATA_EXPECTATIONS, is_within_expected_range
from .audit_logger import log_data_validation


def validate_candle_data(filename: str, symbol: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate downloaded candle data against expected bounds.
    
    Returns:
        (passed, checks) where checks contains all validation results
    """
    
    checks = {
        'candle_count': {'passed': False, 'value': 0, 'expected': None},
        'date_range': {'passed': False, 'value': None, 'expected': None},
        'price_valid': {'passed': False, 'issues': []},
        'volume_valid': {'passed': False, 'issues': []},
        'gaps_detected': {'passed': True, 'count': 0},
        'duplicates_detected': {'passed': True, 'count': 0}
    }
    
    if not os.path.exists(filename):
        checks['error'] = f"File not found: {filename}"
        log_data_validation(symbol, False, checks)
        return False, checks
    
    try:
        # Load data
        with open(filename, 'r') as f:
            data = json.load(f)
        
        if not data:
            checks['error'] = "Empty data file"
            log_data_validation(symbol, False, checks)
            return False, checks
        
        # 1. Validate candle count
        candle_count = len(data)
        checks['candle_count']['value'] = candle_count
        checks['candle_count']['expected'] = f"{DATA_EXPECTATIONS['candle_count_min']}-{DATA_EXPECTATIONS['candle_count_max']}"
        
        if is_within_expected_range(
            candle_count,
            DATA_EXPECTATIONS['candle_count_min'],
            DATA_EXPECTATIONS['candle_count_max']
        ):
            checks['candle_count']['passed'] = True
        
        # 2. Validate date range
        # Handle both numeric timestamps (ms) and ISO string timestamps
        def parse_timestamp(ts):
            if isinstance(ts, str):
                return datetime.fromisoformat(ts.replace('Z', ''))
            else:
                return datetime.fromtimestamp(ts / 1000)
        
        first_date = parse_timestamp(data[0]['timestamp'])
        last_date = parse_timestamp(data[-1]['timestamp'])
        date_span_days = (last_date - first_date).days
        
        checks['date_range']['value'] = f"{date_span_days} days ({first_date.date()} to {last_date.date()})"
        checks['date_range']['expected'] = f"{DATA_EXPECTATIONS['date_span_days_min']}-{DATA_EXPECTATIONS['date_span_days_max']} days"
        
        if is_within_expected_range(
            date_span_days,
            DATA_EXPECTATIONS['date_span_days_min'],
            DATA_EXPECTATIONS['date_span_days_max']
        ):
            checks['date_range']['passed'] = True
        
        # 3. Validate price data
        price_issues = []
        for i, candle in enumerate(data):
            # Check for valid OHLC
            if candle['open'] <= 0 or candle['high'] <= 0 or candle['low'] <= 0 or candle['close'] <= 0:
                price_issues.append(f"Index {i}: Invalid price (<=0)")
            
            # Check high >= low
            if candle['high'] < candle['low']:
                price_issues.append(f"Index {i}: High < Low")
            
            # Check OHLC within high/low
            if not (candle['low'] <= candle['open'] <= candle['high']):
                price_issues.append(f"Index {i}: Open outside High/Low range")
            
            if not (candle['low'] <= candle['close'] <= candle['high']):
                price_issues.append(f"Index {i}: Close outside High/Low range")
        
        checks['price_valid']['issues'] = price_issues
        checks['price_valid']['passed'] = len(price_issues) == 0
        
        # 4. Validate volume data
        volume_issues = []
        for i, candle in enumerate(data):
            if candle['volume'] < 0:
                volume_issues.append(f"Index {i}: Negative volume")
            
            # Check minimum volume threshold for major pairs
            if symbol in ['BTCUSDT', 'ETHUSDT']:
                if candle['volume'] < DATA_EXPECTATIONS['volume_min_btc_eth']:
                    volume_issues.append(f"Index {i}: Volume below minimum ({candle['volume']})")
        
        checks['volume_valid']['issues'] = volume_issues
        checks['volume_valid']['passed'] = len(volume_issues) == 0
        
        # 5. Check for time gaps (missing candles)
        gaps = []
        for i in range(1, len(data)):
            # Parse timestamps properly
            ts_curr = parse_timestamp(data[i]['timestamp'])
            ts_prev = parse_timestamp(data[i-1]['timestamp'])
            time_diff = (ts_curr - ts_prev).total_seconds() / 60  # minutes
            if time_diff > 5:  # More than 5 minutes for 1m candles
                gaps.append(f"Gap at index {i}: {time_diff} minutes")
        
        checks['gaps_detected']['count'] = len(gaps)
        checks['gaps_detected']['passed'] = len(gaps) == 0
        if gaps:
            checks['gaps_detected']['details'] = gaps[:10]  # First 10
        
        # 6. Check for duplicate timestamps
        timestamps = [candle['timestamp'] for candle in data]
        unique_timestamps = set(timestamps)
        duplicate_count = len(timestamps) - len(unique_timestamps)
        
        checks['duplicates_detected']['count'] = duplicate_count
        checks['duplicates_detected']['passed'] = duplicate_count == 0
        
        # Overall pass/fail
        passed = all([
            checks['candle_count']['passed'],
            checks['date_range']['passed'],
            checks['price_valid']['passed'],
            checks['volume_valid']['passed'],
            checks['gaps_detected']['passed'],
            checks['duplicates_detected']['passed']
        ])
        
        # Log validation
        log_data_validation(symbol, passed, checks)
        
        return passed, checks
    
    except Exception as e:
        checks['error'] = str(e)
        log_data_validation(symbol, False, checks)
        return False, checks


def print_validation_report(symbol: str, passed: bool, checks: Dict[str, Any]):
    """Print detailed validation report"""
    
    print(f"\n{'='*80}")
    print(f"📊 DATA VALIDATION REPORT: {symbol}")
    print(f"{'='*80}\n")
    
    # Overall status
    status_icon = "✅" if passed else "❌"
    status_text = "PASSED" if passed else "FAILED"
    print(f"{status_icon} Overall Status: {status_text}\n")
    
    # Candle count
    cc = checks['candle_count']
    icon = "✅" if cc['passed'] else "❌"
    print(f"{icon} Candle Count: {cc['value']} (expected: {cc['expected']})")
    
    # Date range
    dr = checks['date_range']
    icon = "✅" if dr['passed'] else "❌"
    print(f"{icon} Date Range: {dr['value']} (expected: {dr['expected']})")
    
    # Price validation
    pv = checks['price_valid']
    icon = "✅" if pv['passed'] else "❌"
    if pv['passed']:
        print(f"{icon} Price Data: Valid")
    else:
        print(f"{icon} Price Data: {len(pv['issues'])} issues found")
        for issue in pv['issues'][:5]:  # Show first 5
            print(f"    - {issue}")
        if len(pv['issues']) > 5:
            print(f"    ... and {len(pv['issues']) - 5} more")
    
    # Volume validation
    vv = checks['volume_valid']
    icon = "✅" if vv['passed'] else "❌"
    if vv['passed']:
        print(f"{icon} Volume Data: Valid")
    else:
        print(f"{icon} Volume Data: {len(vv['issues'])} issues found")
        for issue in vv['issues'][:5]:
            print(f"    - {issue}")
        if len(vv['issues']) > 5:
            print(f"    ... and {len(vv['issues']) - 5} more")
    
    # Gaps
    gd = checks['gaps_detected']
    icon = "✅" if gd['passed'] else "⚠️"
    if gd['passed']:
        print(f"{icon} Time Gaps: None detected")
    else:
        print(f"{icon} Time Gaps: {gd['count']} gaps detected")
        if 'details' in gd:
            for gap in gd['details']:
                print(f"    - {gap}")
    
    # Duplicates
    dd = checks['duplicates_detected']
    icon = "✅" if dd['passed'] else "⚠️"
    if dd['passed']:
        print(f"{icon} Duplicates: None detected")
    else:
        print(f"{icon} Duplicates: {dd['count']} duplicate timestamps")
    
    # Error if any
    if 'error' in checks:
        print(f"\n❌ Error: {checks['error']}")
    
    print(f"\n{'='*80}\n")


def validate_all_active_pairs() -> Dict[str, Tuple[bool, Dict[str, Any]]]:
    """
    Validate all active trading pairs.
    
    Returns:
        Dict of {symbol: (passed, checks)}
    """
    
    results = {}
    
    # Active pairs from config
    active_pairs = [
        ('BTCUSDT', 'data/BTCUSDT_1m_90d.json'),
        ('ETHUSDT', 'data/ETHUSDT_1m_90d.json')
    ]
    
    print(f"\n{'='*80}")
    print(f"🔍 VALIDATING ALL ACTIVE PAIRS")
    print(f"{'='*80}\n")
    
    for symbol, filename in active_pairs:
        passed, checks = validate_candle_data(filename, symbol)
        results[symbol] = (passed, checks)
        
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{symbol}: {status}")
    
    # Summary
    total = len(results)
    passed_count = sum(1 for p, _ in results.values() if p)
    
    print(f"\n{'='*80}")
    print(f"Summary: {passed_count}/{total} pairs passed validation")
    print(f"{'='*80}\n")
    
    return results


if __name__ == "__main__":
    """Run validation on all active pairs"""
    
    results = validate_all_active_pairs()
    
    # Print detailed reports for any failures
    for symbol, (passed, checks) in results.items():
        if not passed:
            print_validation_report(symbol, passed, checks)
