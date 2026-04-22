"""
System Health Monitor
Comprehensive checks for production readiness across all trading system components.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from .expected_values import DATA_EXPECTATIONS, STRATEGY_BOUNDS, PERFORMANCE_EXPECTATIONS
from .audit_logger import log_system_check


class SystemHealth:
    """Monitor overall system health and readiness"""
    
    def __init__(self):
        self.checks = {}
        self.overall_passed = True
    
    def check_data_freshness(self) -> Tuple[bool, Dict[str, Any]]:
        """Check if all required data files exist and are recent"""
        
        details = {'files': []}
        all_passed = True
        
        required_files = [
            ('BTCUSDT', 'data/BTCUSDT_1m_90d.json'),
            ('ETHUSDT', 'data/ETHUSDT_1m_90d.json')
        ]
        
        for symbol, filepath in required_files:
            if not os.path.exists(filepath):
                details['files'].append({
                    'symbol': symbol,
                    'status': 'MISSING',
                    'filepath': filepath
                })
                all_passed = False
            else:
                # Check file age
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                age_days = (datetime.now() - file_time).days
                
                # Check if stale (>30 days)
                is_fresh = age_days < 30
                
                details['files'].append({
                    'symbol': symbol,
                    'status': 'FRESH' if is_fresh else 'STALE',
                    'filepath': filepath,
                    'age_days': age_days,
                    'last_modified': file_time.isoformat()
                })
                
                if not is_fresh:
                    all_passed = False
        
        log_system_check('data_freshness', all_passed, details)
        return all_passed, details
    
    def check_fallback_strategies(self) -> Tuple[bool, Dict[str, Any]]:
        """Check if fallback strategies exist and are valid"""
        
        details = {'strategies': []}
        all_passed = True
        
        fallback_file = 'ml/fallback_strategies.json'
        
        if not os.path.exists(fallback_file):
            details['error'] = 'Fallback file missing'
            log_system_check('fallback_strategies', False, details)
            return False, details
        
        try:
            with open(fallback_file, 'r') as f:
                fallbacks = json.load(f)
            
            required_keys = ['BTCUSDT_1m', 'BTCUSDT_5m', 'ETHUSDT_1m', 'ETHUSDT_5m']
            
            for key in required_keys:
                if key not in fallbacks:
                    details['strategies'].append({
                        'key': key,
                        'status': 'MISSING'
                    })
                    all_passed = False
                else:
                    # Check strategy count
                    strategy_count = len(fallbacks[key].get('strategies', []))
                    has_validation = fallbacks[key].get('validation_passed', False)
                    
                    if strategy_count < 2:
                        status = 'INSUFFICIENT'
                        all_passed = False
                    elif not has_validation:
                        status = 'UNVALIDATED'
                        all_passed = False
                    else:
                        status = 'OK'
                    
                    details['strategies'].append({
                        'key': key,
                        'status': status,
                        'count': strategy_count,
                        'validated': has_validation
                    })
        
        except Exception as e:
            details['error'] = str(e)
            all_passed = False
        
        log_system_check('fallback_strategies', all_passed, details)
        return all_passed, details
    
    def check_model_files(self) -> Tuple[bool, Dict[str, Any]]:
        """Check if ML model files exist"""
        
        details = {'models': []}
        all_passed = True
        
        model_patterns = [
            ('BTCUSDT_1m', 'ml/models/BTCUSDT_1m_*.pkl'),
            ('BTCUSDT_5m', 'ml/models/BTCUSDT_5m_*.pkl'),
            ('ETHUSDT_1m', 'ml/models/ETHUSDT_1m_*.pkl'),
            ('ETHUSDT_5m', 'ml/models/ETHUSDT_5m_*.pkl')
        ]
        
        import glob
        
        for key, pattern in model_patterns:
            matches = glob.glob(pattern)
            
            if not matches:
                details['models'].append({
                    'key': key,
                    'status': 'MISSING'
                })
                all_passed = False
            else:
                # Get most recent
                latest = max(matches, key=os.path.getmtime)
                file_time = datetime.fromtimestamp(os.path.getmtime(latest))
                age_days = (datetime.now() - file_time).days
                
                details['models'].append({
                    'key': key,
                    'status': 'EXISTS',
                    'file': latest,
                    'age_days': age_days
                })
        
        log_system_check('model_files', all_passed, details)
        return all_passed, details
    
    def check_directories(self) -> Tuple[bool, Dict[str, Any]]:
        """Check if all required directories exist"""
        
        details = {'directories': []}
        all_passed = True
        
        required_dirs = [
            'data',
            'ml',
            'ml/models',
            'ml/metadata',
            'logs',
            'logs/audit',
            'validation'
        ]
        
        for dir_path in required_dirs:
            exists = os.path.exists(dir_path)
            
            details['directories'].append({
                'path': dir_path,
                'exists': exists
            })
            
            if not exists:
                all_passed = False
        
        log_system_check('directories', all_passed, details)
        return all_passed, details
    
    def check_dependencies(self) -> Tuple[bool, Dict[str, Any]]:
        """Check if all required Python dependencies are available"""
        
        details = {'packages': []}
        all_passed = True
        
        required_packages = [
            'numpy',
            'pandas',
            'sklearn',
            'binance',
            'requests'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                details['packages'].append({
                    'package': package,
                    'status': 'INSTALLED'
                })
            except ImportError:
                details['packages'].append({
                    'package': package,
                    'status': 'MISSING'
                })
                all_passed = False
        
        log_system_check('dependencies', all_passed, details)
        return all_passed, details
    
    def run_all_checks(self) -> Dict[str, Tuple[bool, Dict[str, Any]]]:
        """Run all system health checks"""
        
        checks = {
            'data_freshness': self.check_data_freshness(),
            'fallback_strategies': self.check_fallback_strategies(),
            'model_files': self.check_model_files(),
            'directories': self.check_directories(),
            'dependencies': self.check_dependencies()
        }
        
        self.checks = checks
        self.overall_passed = all(passed for passed, _ in checks.values())
        
        return checks
    
    def print_report(self):
        """Print comprehensive health report"""
        
        print(f"\n{'='*80}")
        print(f"🏥 SYSTEM HEALTH REPORT")
        print(f"{'='*80}\n")
        
        if not self.checks:
            print("⚠️  No checks run yet. Call run_all_checks() first.")
            return
        
        # Overall status
        if self.overall_passed:
            print(f"✅ Overall Status: HEALTHY\n")
        else:
            print(f"❌ Overall Status: ISSUES DETECTED\n")
        
        # Individual checks
        for check_name, (passed, details) in self.checks.items():
            icon = "✅" if passed else "❌"
            status = "PASSED" if passed else "FAILED"
            
            print(f"{icon} {check_name.replace('_', ' ').title()}: {status}")
            
            # Show details for failures
            if not passed:
                if 'error' in details:
                    print(f"    Error: {details['error']}")
                
                if 'files' in details:
                    for file_info in details['files']:
                        if file_info['status'] != 'FRESH':
                            print(f"    - {file_info['symbol']}: {file_info['status']}")
                
                if 'strategies' in details:
                    for strat_info in details['strategies']:
                        if strat_info['status'] != 'OK':
                            print(f"    - {strat_info['key']}: {strat_info['status']}")
                
                if 'models' in details:
                    for model_info in details['models']:
                        if model_info['status'] != 'EXISTS':
                            print(f"    - {model_info['key']}: {model_info['status']}")
                
                if 'directories' in details:
                    for dir_info in details['directories']:
                        if not dir_info['exists']:
                            print(f"    - {dir_info['path']}: MISSING")
                
                if 'packages' in details:
                    for pkg_info in details['packages']:
                        if pkg_info['status'] != 'INSTALLED':
                            print(f"    - {pkg_info['package']}: {pkg_info['status']}")
        
        print(f"\n{'='*80}")
        
        # Recommendations
        if not self.overall_passed:
            print(f"\n📋 RECOMMENDATIONS:\n")
            
            for check_name, (passed, details) in self.checks.items():
                if not passed:
                    if check_name == 'data_freshness':
                        print("  - Run: python pre_trading_check.py --non-interactive")
                    elif check_name == 'fallback_strategies':
                        print("  - Run: python auto_strategy_updater.py")
                    elif check_name == 'model_files':
                        print("  - Run: python training_manager.py train_all")
                    elif check_name == 'directories':
                        print("  - Create missing directories")
                    elif check_name == 'dependencies':
                        print("  - Run: pip install -r requirements.txt")
            
            print()
        
        print(f"{'='*80}\n")


def run_health_check() -> bool:
    """
    Run complete system health check and print report.
    
    Returns:
        True if all checks passed, False otherwise
    """
    
    health = SystemHealth()
    health.run_all_checks()
    health.print_report()
    
    return health.overall_passed


if __name__ == "__main__":
    """Run system health check"""
    
    passed = run_health_check()
    
    exit(0 if passed else 1)
