"""
Production Readiness Checklist
Comprehensive validation before enabling live trading.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Tuple
from .system_health import SystemHealth
from .data_validator import validate_all_active_pairs
from .audit_logger import get_audit_logger, AuditLevel


class ProductionReadinessChecklist:
    """Comprehensive checklist for production readiness"""
    
    def __init__(self):
        self.results = {}
        self.passed = False
        self.logger = get_audit_logger()
    
    def check_all_data_validated(self) -> Tuple[bool, str]:
        """Ensure all data files have been validated"""
        
        results = validate_all_active_pairs()
        all_passed = all(passed for passed, _ in results.values())
        
        if all_passed:
            return True, f"All {len(results)} active pairs validated successfully"
        else:
            failed = [symbol for symbol, (p, _) in results.items() if not p]
            return False, f"Data validation failed for: {', '.join(failed)}"
    
    def check_audit_logs_exist(self) -> Tuple[bool, str]:
        """Verify audit logging is operational"""
        
        log_dir = "logs/audit"
        
        if not os.path.exists(log_dir):
            return False, f"Audit log directory missing: {log_dir}"
        
        # Check for recent logs
        log_files = [f for f in os.listdir(log_dir) if f.startswith('audit_') and f.endswith('.jsonl')]
        
        if not log_files:
            return False, "No audit logs found - system may not be logging properly"
        
        return True, f"Audit logging operational ({len(log_files)} log files)"
    
    def check_strategies_recent(self) -> Tuple[bool, str]:
        """Ensure fallback strategies are recently generated"""
        
        fallback_file = 'ml/fallback_strategies.json'
        
        if not os.path.exists(fallback_file):
            return False, "Fallback strategies file missing"
        
        try:
            with open(fallback_file, 'r') as f:
                fallbacks = json.load(f)
            
            # Check each strategy's age
            old_strategies = []
            for key, config in fallbacks.items():
                updated_at = config.get('updated_at')
                if not updated_at:
                    old_strategies.append(f"{key} (no timestamp)")
                    continue
                
                updated_time = datetime.fromisoformat(updated_at)
                age_days = (datetime.now() - updated_time).days
                
                if age_days > 30:
                    old_strategies.append(f"{key} ({age_days} days old)")
            
            if old_strategies:
                return False, f"Stale strategies found: {', '.join(old_strategies)}"
            
            return True, "All strategies are recent (<30 days)"
        
        except Exception as e:
            return False, f"Error checking strategies: {e}"
    
    def check_validation_passed_flag(self) -> Tuple[bool, str]:
        """Verify all strategies have validation_passed flag"""
        
        fallback_file = 'ml/fallback_strategies.json'
        
        if not os.path.exists(fallback_file):
            return False, "Fallback strategies file missing"
        
        try:
            with open(fallback_file, 'r') as f:
                fallbacks = json.load(f)
            
            unvalidated = []
            for key, config in fallbacks.items():
                if not config.get('validation_passed', False):
                    unvalidated.append(key)
            
            if unvalidated:
                return False, f"Unvalidated strategies: {', '.join(unvalidated)}"
            
            return True, "All strategies have passed validation"
        
        except Exception as e:
            return False, f"Error checking validation flags: {e}"
    
    def check_no_critical_audit_events(self) -> Tuple[bool, str]:
        """Ensure no critical issues in recent audit logs"""
        
        summary_file = "logs/audit/audit_summary.json"
        
        if not os.path.exists(summary_file):
            return True, "No critical events recorded"
        
        try:
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            critical_count = len(summary.get('critical', []))
            error_count = len(summary.get('errors', []))
            
            if critical_count > 0:
                return False, f"{critical_count} critical events in audit log"
            
            if error_count > 10:  # Allow some errors, but not too many
                return False, f"{error_count} errors in audit log (>10 threshold)"
            
            return True, "No critical audit events"
        
        except Exception as e:
            return False, f"Error reading audit summary: {e}"
    
    def check_system_health_passed(self) -> Tuple[bool, str]:
        """Run full system health check"""
        
        health = SystemHealth()
        health.run_all_checks()
        
        if health.overall_passed:
            return True, "System health check passed"
        else:
            failed_checks = [name for name, (passed, _) in health.checks.items() if not passed]
            return False, f"System health check failed: {', '.join(failed_checks)}"
    
    def check_grid_search_completed(self) -> Tuple[bool, str]:
        """Verify grid searches have been completed for all pairs"""
        
        required_pairs = [
            ('BTCUSDT', '1m'),
            ('BTCUSDT', '5m'),
            ('ETHUSDT', '1m'),
            ('ETHUSDT', '5m')
        ]
        
        fallback_file = 'ml/fallback_strategies.json'
        
        if not os.path.exists(fallback_file):
            return False, "No fallback strategies found"
        
        try:
            with open(fallback_file, 'r') as f:
                fallbacks = json.load(f)
            
            missing = []
            for asset, tf in required_pairs:
                key = f"{asset}_{tf}"
                if key not in fallbacks:
                    missing.append(key)
                elif len(fallbacks[key].get('strategies', [])) < 2:
                    missing.append(f"{key} (insufficient strategies)")
            
            if missing:
                return False, f"Missing grid search results: {', '.join(missing)}"
            
            return True, f"Grid search completed for all {len(required_pairs)} required pairs"
        
        except Exception as e:
            return False, f"Error checking grid search: {e}"
    
    def check_no_placeholder_values(self) -> Tuple[bool, str]:
        """Ensure no placeholder or test values in production config"""
        
        fallback_file = 'ml/fallback_strategies.json'
        
        if not os.path.exists(fallback_file):
            return False, "Fallback strategies file missing"
        
        try:
            with open(fallback_file, 'r') as f:
                fallbacks = json.load(f)
            
            suspicious = []
            
            for key, config in fallbacks.items():
                for strategy in config.get('strategies', []):
                    # Check for unrealistic win rates
                    if strategy.get('win_rate', 0) >= 0.999:
                        suspicious.append(f"{key}: Win rate too high (99.9%+)")
                    
                    # Check for zero values
                    if strategy.get('trades', 0) == 0:
                        suspicious.append(f"{key}: Zero trades")
                    
                    # Check for None/null values
                    for param_key, param_value in strategy.items():
                        if param_value is None:
                            suspicious.append(f"{key}: Null value in {param_key}")
            
            if suspicious:
                return False, f"Suspicious values found: {', '.join(suspicious[:5])}"
            
            return True, "No placeholder values detected"
        
        except Exception as e:
            return False, f"Error checking for placeholders: {e}"
    
    def run_all_checks(self) -> Dict[str, Tuple[bool, str]]:
        """Run all production readiness checks"""
        
        print(f"\n{'='*80}")
        print(f"🚀 PRODUCTION READINESS CHECKLIST")
        print(f"{'='*80}\n")
        
        checks = [
            ("System Health", self.check_system_health_passed),
            ("Data Validation", self.check_all_data_validated),
            ("Grid Search Completion", self.check_grid_search_completed),
            ("Strategy Recency", self.check_strategies_recent),
            ("Validation Flags", self.check_validation_passed_flag),
            ("Audit Logging", self.check_audit_logs_exist),
            ("No Critical Events", self.check_no_critical_audit_events),
            ("No Placeholders", self.check_no_placeholder_values),
        ]
        
        results = {}
        all_passed = True
        
        for i, (name, check_func) in enumerate(checks, 1):
            print(f"[{i}/{len(checks)}] {name}...", end=" ", flush=True)
            
            try:
                passed, message = check_func()
                results[name] = (passed, message)
                
                if passed:
                    print(f"✅ {message}")
                    self.logger.log_event(
                        event_type="PRODUCTION_CHECK",
                        level=AuditLevel.INFO,
                        message=f"Production check passed: {name}",
                        data={'check': name, 'result': message}
                    )
                else:
                    print(f"❌ {message}")
                    all_passed = False
                    self.logger.log_event(
                        event_type="PRODUCTION_CHECK",
                        level=AuditLevel.ERROR,
                        message=f"Production check failed: {name}",
                        data={'check': name, 'result': message}
                    )
            
            except Exception as e:
                print(f"❌ Error: {e}")
                results[name] = (False, str(e))
                all_passed = False
        
        print(f"\n{'='*80}")
        
        if all_passed:
            print(f"✅ ALL CHECKS PASSED - SYSTEM READY FOR PRODUCTION")
            self.logger.log_event(
                event_type="PRODUCTION_READY",
                level=AuditLevel.INFO,
                message="All production readiness checks passed",
                data={'timestamp': datetime.now().isoformat()}
            )
        else:
            print(f"❌ PRODUCTION READINESS CHECK FAILED")
            print(f"\n⚠️  DO NOT ENABLE LIVE TRADING UNTIL ALL CHECKS PASS")
            
            failed = [name for name, (p, _) in results.items() if not p]
            print(f"\nFailed checks: {', '.join(failed)}")
            
            self.logger.log_event(
                event_type="PRODUCTION_NOT_READY",
                level=AuditLevel.CRITICAL,
                message="Production readiness checks failed",
                data={
                    'timestamp': datetime.now().isoformat(),
                    'failed_checks': failed
                }
            )
        
        print(f"{'='*80}\n")
        
        self.results = results
        self.passed = all_passed
        
        return results
    
    def generate_report(self, output_file='production_readiness_report.json'):
        """Generate detailed JSON report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_passed': self.passed,
            'checks': {
                name: {'passed': passed, 'message': message}
                for name, (passed, message) in self.results.items()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Report saved to {output_file}")
        
        return output_file


def run_production_checklist() -> bool:
    """
    Run complete production readiness checklist.
    
    Returns:
        True if all checks passed, False otherwise
    """
    
    checklist = ProductionReadinessChecklist()
    checklist.run_all_checks()
    checklist.generate_report()
    
    return checklist.passed


if __name__ == "__main__":
    """Run production readiness checklist"""
    
    passed = run_production_checklist()
    
    exit(0 if passed else 1)
