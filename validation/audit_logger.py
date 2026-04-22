"""
Audit logging system for tracking validation checks and system operations.
Provides comprehensive logging, replay capabilities, and anomaly detection.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class AuditLevel(Enum):
    """Severity levels for audit events"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditEvent:
    """Single audit event"""
    
    def __init__(self, 
                 event_type: str,
                 level: AuditLevel,
                 message: str,
                 data: Optional[Dict[str, Any]] = None):
        self.timestamp = datetime.now().isoformat()
        self.event_type = event_type
        self.level = level.value
        self.message = message
        self.data = data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'event_type': self.event_type,
            'level': self.level,
            'message': self.message,
            'data': self.data
        }


class AuditLogger:
    """Comprehensive audit logging system"""
    
    def __init__(self, log_dir: str = "logs/audit"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Current session log file
        self.session_file = os.path.join(
            log_dir, 
            f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        )
        
        # Summary file for critical events
        self.summary_file = os.path.join(log_dir, "audit_summary.json")
        
        # Session start
        self.log_event(
            event_type="SESSION_START",
            level=AuditLevel.INFO,
            message="Audit logging session started"
        )
    
    def log_event(self, 
                  event_type: str,
                  level: AuditLevel,
                  message: str,
                  data: Optional[Dict[str, Any]] = None):
        """Log an audit event"""
        
        event = AuditEvent(event_type, level, message, data)
        
        # Write to session log (append mode, JSON lines)
        with open(self.session_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
        
        # Update summary for warnings/errors/critical
        if level in [AuditLevel.WARNING, AuditLevel.ERROR, AuditLevel.CRITICAL]:
            self._update_summary(event)
    
    def _update_summary(self, event: AuditEvent):
        """Update summary file with important events"""
        
        # Load existing summary
        if os.path.exists(self.summary_file):
            with open(self.summary_file, 'r') as f:
                summary = json.load(f)
        else:
            summary = {
                'warnings': [],
                'errors': [],
                'critical': [],
                'last_updated': None
            }
        
        # Add event to appropriate list
        event_dict = event.to_dict()
        
        if event.level == AuditLevel.WARNING.value:
            summary['warnings'].append(event_dict)
        elif event.level == AuditLevel.ERROR.value:
            summary['errors'].append(event_dict)
        elif event.level == AuditLevel.CRITICAL.value:
            summary['critical'].append(event_dict)
        
        # Keep only last 100 of each type
        for key in ['warnings', 'errors', 'critical']:
            summary[key] = summary[key][-100:]
        
        summary['last_updated'] = datetime.now().isoformat()
        
        # Save
        with open(self.summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
    
    # Specific validation logging methods
    
    def log_data_validation(self, 
                           symbol: str, 
                           passed: bool, 
                           checks: Dict[str, Any]):
        """Log data validation results"""
        
        self.log_event(
            event_type="DATA_VALIDATION",
            level=AuditLevel.INFO if passed else AuditLevel.ERROR,
            message=f"Data validation for {symbol}: {'PASSED' if passed else 'FAILED'}",
            data={
                'symbol': symbol,
                'passed': passed,
                'checks': checks
            }
        )
    
    def log_strategy_validation(self,
                               asset: str,
                               timeframe: str,
                               strategy_num: int,
                               passed: bool,
                               violations: List[Dict[str, Any]]):
        """Log strategy validation results"""
        
        self.log_event(
            event_type="STRATEGY_VALIDATION",
            level=AuditLevel.INFO if passed else AuditLevel.WARNING,
            message=f"Strategy validation {asset}_{timeframe} #{strategy_num}: {'PASSED' if passed else 'FAILED'}",
            data={
                'asset': asset,
                'timeframe': timeframe,
                'strategy_num': strategy_num,
                'passed': passed,
                'violations': violations
            }
        )
    
    def log_parameter_violation(self,
                               parameter: str,
                               value: Any,
                               expected: str,
                               severity: str = "warning"):
        """Log parameter out of expected bounds"""
        
        level = AuditLevel.WARNING if severity == "warning" else AuditLevel.ERROR
        
        self.log_event(
            event_type="PARAMETER_VIOLATION",
            level=level,
            message=f"Parameter {parameter} = {value} outside expected range: {expected}",
            data={
                'parameter': parameter,
                'value': value,
                'expected': expected,
                'severity': severity
            }
        )
    
    def log_performance_violation(self,
                                 metric: str,
                                 value: Any,
                                 expected: str,
                                 severity: str = "warning"):
        """Log performance metric out of expected bounds"""
        
        level = AuditLevel.WARNING if severity == "warning" else AuditLevel.ERROR
        
        self.log_event(
            event_type="PERFORMANCE_VIOLATION",
            level=level,
            message=f"Performance metric {metric} = {value} outside expected range: {expected}",
            data={
                'metric': metric,
                'value': value,
                'expected': expected,
                'severity': severity
            }
        )
    
    def log_download(self, symbol: str, candle_count: int, success: bool):
        """Log data download"""
        
        self.log_event(
            event_type="DATA_DOWNLOAD",
            level=AuditLevel.INFO if success else AuditLevel.ERROR,
            message=f"Downloaded {candle_count} candles for {symbol}: {'SUCCESS' if success else 'FAILED'}",
            data={
                'symbol': symbol,
                'candle_count': candle_count,
                'success': success
            }
        )
    
    def log_grid_search(self, 
                       asset: str, 
                       timeframe: str, 
                       combinations: int,
                       duration_seconds: float,
                       best_win_rate: float):
        """Log grid search completion"""
        
        self.log_event(
            event_type="GRID_SEARCH",
            level=AuditLevel.INFO,
            message=f"Grid search completed: {asset}_{timeframe}, tested {combinations} combinations",
            data={
                'asset': asset,
                'timeframe': timeframe,
                'combinations': combinations,
                'duration_seconds': duration_seconds,
                'best_win_rate': best_win_rate
            }
        )
    
    def log_fallback_save(self,
                         asset: str,
                         timeframe: str,
                         strategy_count: int,
                         validated: bool):
        """Log saving fallback strategies"""
        
        self.log_event(
            event_type="FALLBACK_SAVE",
            level=AuditLevel.INFO,
            message=f"Saved {strategy_count} fallback strategies for {asset}_{timeframe}",
            data={
                'asset': asset,
                'timeframe': timeframe,
                'strategy_count': strategy_count,
                'validated': validated
            }
        )
    
    def log_system_check(self, check_name: str, passed: bool, details: Dict[str, Any]):
        """Log system health check"""
        
        self.log_event(
            event_type="SYSTEM_CHECK",
            level=AuditLevel.INFO if passed else AuditLevel.ERROR,
            message=f"System check '{check_name}': {'PASSED' if passed else 'FAILED'}",
            data={
                'check_name': check_name,
                'passed': passed,
                'details': details
            }
        )
    
    def log_anomaly(self, anomaly_type: str, description: str, data: Dict[str, Any]):
        """Log detected anomaly"""
        
        self.log_event(
            event_type="ANOMALY_DETECTED",
            level=AuditLevel.CRITICAL,
            message=f"Anomaly detected: {anomaly_type} - {description}",
            data={
                'anomaly_type': anomaly_type,
                'description': description,
                **data
            }
        )
    
    def close(self):
        """Close audit logging session"""
        
        self.log_event(
            event_type="SESSION_END",
            level=AuditLevel.INFO,
            message="Audit logging session ended"
        )


# Global logger instance
_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger"""
    global _logger
    if _logger is None:
        _logger = AuditLogger()
    return _logger


def close_audit_logger():
    """Close global audit logger"""
    global _logger
    if _logger is not None:
        _logger.close()
        _logger = None


# Convenience functions
def log_data_validation(symbol: str, passed: bool, checks: Dict[str, Any]):
    """Log data validation"""
    get_audit_logger().log_data_validation(symbol, passed, checks)


def log_strategy_validation(asset: str, timeframe: str, strategy_num: int, 
                           passed: bool, violations: List[Dict[str, Any]]):
    """Log strategy validation"""
    get_audit_logger().log_strategy_validation(asset, timeframe, strategy_num, passed, violations)


def log_parameter_violation(parameter: str, value: Any, expected: str, severity: str = "warning"):
    """Log parameter violation"""
    get_audit_logger().log_parameter_violation(parameter, value, expected, severity)


def log_performance_violation(metric: str, value: Any, expected: str, severity: str = "warning"):
    """Log performance violation"""
    get_audit_logger().log_performance_violation(metric, value, expected, severity)


def log_download(symbol: str, candle_count: int, success: bool):
    """Log data download"""
    get_audit_logger().log_download(symbol, candle_count, success)


def log_grid_search(asset: str, timeframe: str, combinations: int, 
                   duration_seconds: float, best_win_rate: float):
    """Log grid search"""
    get_audit_logger().log_grid_search(asset, timeframe, combinations, duration_seconds, best_win_rate)


def log_fallback_save(asset: str, timeframe: str, strategy_count: int, validated: bool):
    """Log fallback save"""
    get_audit_logger().log_fallback_save(asset, timeframe, strategy_count, validated)


def log_system_check(check_name: str, passed: bool, details: Dict[str, Any]):
    """Log system check"""
    get_audit_logger().log_system_check(check_name, passed, details)


def log_anomaly(anomaly_type: str, description: str, data: Dict[str, Any]):
    """Log anomaly"""
    get_audit_logger().log_anomaly(anomaly_type, description, data)
