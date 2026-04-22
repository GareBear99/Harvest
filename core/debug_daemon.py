"""
Dashboard Debug Daemon - Comprehensive Action and Validation Logger

This daemon wraps all dashboard operations with extensive logging and validation:
- Logs every action (data loads, calculations, state changes)
- Validates each action's expected outcome
- Self-validates the validation checks themselves
- Provides real-time debugging terminal view
- Tracks anomalies and unexpected behaviors
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import traceback
import hashlib
import threading
from copy import deepcopy


class ValidationLevel(Enum):
    """Validation severity levels"""
    CRITICAL = "CRITICAL"  # Must pass or system fails
    WARNING = "WARNING"    # Should pass, log if fails
    INFO = "INFO"          # Informational only


class ActionStatus(Enum):
    """Action execution status"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    SKIPPED = "SKIPPED"


class DebugDaemon:
    """
    Comprehensive debugging daemon for dashboard operations.
    Logs all actions with multi-layer validation.
    """
    
    def __init__(self, log_dir: str = "logs/debug_daemon"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread safety
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        
        # Session tracking
        self.session_id = self._generate_session_id()
        self.session_start = datetime.now()
        self.action_count = 0
        self.validation_count = 0
        self.meta_validation_count = 0
        
        # State tracking
        self.actions_log: List[Dict] = []
        self.validations_log: List[Dict] = []
        self.meta_validations_log: List[Dict] = []
        self.errors_log: List[Dict] = []
        self.anomalies_log: List[Dict] = []
        
        # Real-time monitoring
        self.terminal_buffer: List[str] = []
        self.max_buffer_size = 1000
        
        # Initialize session log
        self._init_session_log()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = str(time.time()).encode()
        return hashlib.sha256(timestamp).hexdigest()[:12]
    
    def _init_session_log(self):
        """Initialize session log file"""
        session_file = self.log_dir / f"session_{self.session_id}.json"
        session_data = {
            "session_id": self.session_id,
            "start_time": self.session_start.isoformat(),
            "status": "active"
        }
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
    
    def log_action(self, 
                   action_name: str, 
                   category: str, 
                   details: Dict[str, Any],
                   expected_outcome: Dict[str, Any]) -> str:
        """
        Log an action with expected outcomes (thread-safe).
        
        Args:
            action_name: Name of the action being performed
            category: Category (e.g., 'data_load', 'calculation', 'state_update')
            details: Details about the action
            expected_outcome: What we expect to happen
            
        Returns:
            action_id: Unique identifier for this action
        """
        with self._lock:
            self.action_count += 1
            action_id = f"A{self.action_count:06d}"
            timestamp = datetime.now()
            
            action_entry = {
                "action_id": action_id,
                "session_id": self.session_id,
                "timestamp": timestamp.isoformat(),
                "action_name": action_name,
                "category": category,
                "details": details,
                "expected_outcome": expected_outcome,
                "status": "pending"
            }
            
            self.actions_log.append(action_entry)
            
            # Terminal output
            msg = f"[{timestamp.strftime('%H:%M:%S.%f')[:-3]}] 🔵 ACTION {action_id}: {action_name}"
            self._add_to_terminal(msg)
            
            # Write to file immediately
            self._write_action_log(action_entry)
            
            return action_id
    
    def validate_action(self,
                       action_id: str,
                       actual_outcome: Dict[str, Any],
                       validation_checks: List[Dict[str, Any]]) -> bool:
        """
        Validate an action's outcome with comprehensive checks.
        
        Args:
            action_id: ID of the action to validate
            actual_outcome: What actually happened
            validation_checks: List of validation checks to perform
            
        Returns:
            all_passed: True if all validations passed
        """
        self.validation_count += 1
        validation_id = f"V{self.validation_count:06d}"
        timestamp = datetime.now()
        
        # Find the action
        action = next((a for a in self.actions_log if a["action_id"] == action_id), None)
        if not action:
            self._log_error(f"Action {action_id} not found for validation")
            return False
        
        # Perform each validation check
        results = []
        all_passed = True
        
        for check in validation_checks:
            check_name = check.get("name", "unnamed_check")
            check_func = check.get("function")
            check_level = ValidationLevel[check.get("level", "INFO")]
            expected = check.get("expected")
            
            try:
                # Execute validation function
                if callable(check_func):
                    result = check_func(actual_outcome, action["expected_outcome"])
                else:
                    result = actual_outcome.get(check_name) == expected
                
                check_passed = bool(result)
                
                # Determine if this affects overall status
                if not check_passed and check_level == ValidationLevel.CRITICAL:
                    all_passed = False
                
                check_result = {
                    "check_name": check_name,
                    "level": check_level.value,
                    "expected": expected,
                    "actual": actual_outcome.get(check_name),
                    "passed": check_passed,
                    "details": check.get("details", {})
                }
                results.append(check_result)
                
                # Terminal output
                status_icon = "✅" if check_passed else ("🔴" if check_level == ValidationLevel.CRITICAL else "⚠️")
                msg = f"  {status_icon} CHECK: {check_name} [{check_level.value}] = {check_passed}"
                self._add_to_terminal(msg)
                
            except Exception as e:
                all_passed = False
                error_msg = f"Validation check '{check_name}' failed with error: {str(e)}"
                self._log_error(error_msg)
                results.append({
                    "check_name": check_name,
                    "level": check_level.value,
                    "passed": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
        
        # Create validation entry
        validation_entry = {
            "validation_id": validation_id,
            "action_id": action_id,
            "session_id": self.session_id,
            "timestamp": timestamp.isoformat(),
            "action_name": action["action_name"],
            "expected_outcome": action["expected_outcome"],
            "actual_outcome": actual_outcome,
            "checks": results,
            "all_passed": all_passed,
            "status": ActionStatus.SUCCESS.value if all_passed else ActionStatus.FAILED.value
        }
        
        self.validations_log.append(validation_entry)
        
        # Update action status
        action["status"] = ActionStatus.SUCCESS.value if all_passed else ActionStatus.FAILED.value
        action["validation_id"] = validation_id
        
        # Terminal output
        status_icon = "✅" if all_passed else "❌"
        msg = f"[{timestamp.strftime('%H:%M:%S.%f')[:-3]}] {status_icon} VALIDATION {validation_id}: {action['action_name']} = {all_passed}"
        self._add_to_terminal(msg)
        
        # Write to file
        self._write_validation_log(validation_entry)
        
        # Perform meta-validation
        self._meta_validate(validation_id, validation_entry)
        
        return all_passed
    
    def _meta_validate(self, validation_id: str, validation_entry: Dict[str, Any]):
        """
        Meta-validation: Validate that the validation itself was performed correctly.
        
        Checks:
        - All expected checks were performed
        - Check logic is sound
        - Results are consistent
        - No missing validations
        """
        self.meta_validation_count += 1
        meta_id = f"M{self.meta_validation_count:06d}"
        timestamp = datetime.now()
        
        meta_checks = []
        meta_passed = True
        
        # Check 1: Were all checks executed?
        checks_executed = len(validation_entry.get("checks", []))
        check_1_passed = checks_executed > 0
        meta_checks.append({
            "name": "checks_executed",
            "passed": check_1_passed,
            "expected": "> 0",
            "actual": checks_executed
        })
        
        if not check_1_passed:
            meta_passed = False
        
        # Check 2: Are results consistent with status?
        status = validation_entry.get("all_passed", False)
        has_critical_failures = any(
            not c["passed"] and c.get("level") == "CRITICAL"
            for c in validation_entry.get("checks", [])
        )
        check_2_passed = (not status and has_critical_failures) or (status and not has_critical_failures)
        meta_checks.append({
            "name": "status_consistency",
            "passed": check_2_passed,
            "expected": "status matches critical checks",
            "actual": f"status={status}, critical_failures={has_critical_failures}"
        })
        
        if not check_2_passed:
            meta_passed = False
        
        # Check 3: Do expected and actual outcomes have matching keys?
        expected_keys = set(validation_entry.get("expected_outcome", {}).keys())
        actual_keys = set(validation_entry.get("actual_outcome", {}).keys())
        missing_keys = expected_keys - actual_keys
        check_3_passed = len(missing_keys) == 0
        meta_checks.append({
            "name": "outcome_keys_match",
            "passed": check_3_passed,
            "expected": "all expected keys present",
            "actual": f"missing: {list(missing_keys)}" if missing_keys else "all present"
        })
        
        if not check_3_passed and missing_keys:
            self._log_anomaly(
                f"Meta-validation found missing outcome keys: {missing_keys}",
                {"validation_id": validation_id}
            )
        
        # Check 4: Is timestamp valid?
        try:
            val_time = datetime.fromisoformat(validation_entry["timestamp"])
            time_diff = (datetime.now() - val_time).total_seconds()
            check_4_passed = 0 <= time_diff < 1.0  # Should be very recent
            meta_checks.append({
                "name": "timestamp_valid",
                "passed": check_4_passed,
                "expected": "within 1 second",
                "actual": f"{time_diff:.3f}s ago"
            })
        except Exception as e:
            check_4_passed = False
            meta_checks.append({
                "name": "timestamp_valid",
                "passed": False,
                "error": str(e)
            })
            meta_passed = False
        
        # Create meta-validation entry
        meta_entry = {
            "meta_validation_id": meta_id,
            "validation_id": validation_id,
            "session_id": self.session_id,
            "timestamp": timestamp.isoformat(),
            "checks": meta_checks,
            "all_passed": meta_passed
        }
        
        self.meta_validations_log.append(meta_entry)
        
        # Terminal output (only if meta-validation failed)
        if not meta_passed:
            msg = f"[{timestamp.strftime('%H:%M:%S.%f')[:-3]}] ⚠️  META-VALIDATION {meta_id}: Validation {validation_id} has issues!"
            self._add_to_terminal(msg)
            for check in meta_checks:
                if not check["passed"]:
                    msg = f"    ❌ {check['name']}: expected {check['expected']}, got {check['actual']}"
                    self._add_to_terminal(msg)
        
        # Write to file
        self._write_meta_validation_log(meta_entry)
    
    def _log_error(self, message: str, context: Optional[Dict] = None):
        """Log an error"""
        timestamp = datetime.now()
        error_entry = {
            "timestamp": timestamp.isoformat(),
            "session_id": self.session_id,
            "message": message,
            "context": context or {},
            "traceback": traceback.format_exc()
        }
        self.errors_log.append(error_entry)
        
        msg = f"[{timestamp.strftime('%H:%M:%S.%f')[:-3]}] 🔴 ERROR: {message}"
        self._add_to_terminal(msg)
        
        self._write_error_log(error_entry)
    
    def _log_anomaly(self, message: str, context: Optional[Dict] = None):
        """Log an anomaly (unexpected but not critical)"""
        timestamp = datetime.now()
        anomaly_entry = {
            "timestamp": timestamp.isoformat(),
            "session_id": self.session_id,
            "message": message,
            "context": context or {}
        }
        self.anomalies_log.append(anomaly_entry)
        
        msg = f"[{timestamp.strftime('%H:%M:%S.%f')[:-3]}] ⚠️  ANOMALY: {message}"
        self._add_to_terminal(msg)
        
        self._write_anomaly_log(anomaly_entry)
    
    def _add_to_terminal(self, message: str):
        """Add message to terminal buffer"""
        self.terminal_buffer.append(message)
        if len(self.terminal_buffer) > self.max_buffer_size:
            self.terminal_buffer.pop(0)
    
    def get_terminal_output(self, lines: int = 50) -> List[str]:
        """Get recent terminal output (thread-safe)"""
        with self._lock:
            return self.terminal_buffer[-lines:].copy()
    
    def get_actions_snapshot(self) -> List[Dict]:
        """Get thread-safe snapshot of actions log for iteration"""
        with self._lock:
            return deepcopy(self.actions_log)
    
    def get_validations_snapshot(self) -> List[Dict]:
        """Get thread-safe snapshot of validations log for iteration"""
        with self._lock:
            return deepcopy(self.validations_log)
    
    def get_errors_snapshot(self) -> List[Dict]:
        """Get thread-safe snapshot of errors log for iteration"""
        with self._lock:
            return deepcopy(self.errors_log)
    
    def get_anomalies_snapshot(self) -> List[Dict]:
        """Get thread-safe snapshot of anomalies log for iteration"""
        with self._lock:
            return deepcopy(self.anomalies_log)
    
    def _write_action_log(self, entry: Dict):
        """Write action to log file"""
        log_file = self.log_dir / f"actions_{self.session_id}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    
    def _write_validation_log(self, entry: Dict):
        """Write validation to log file"""
        log_file = self.log_dir / f"validations_{self.session_id}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    
    def _write_meta_validation_log(self, entry: Dict):
        """Write meta-validation to log file"""
        log_file = self.log_dir / f"meta_validations_{self.session_id}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    
    def _write_error_log(self, entry: Dict):
        """Write error to log file"""
        log_file = self.log_dir / f"errors_{self.session_id}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    
    def _write_anomaly_log(self, entry: Dict):
        """Write anomaly to log file"""
        log_file = self.log_dir / f"anomalies_{self.session_id}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        duration = (datetime.now() - self.session_start).total_seconds()
        
        # Calculate success rates
        total_validations = len(self.validations_log)
        passed_validations = sum(1 for v in self.validations_log if v["all_passed"])
        validation_rate = (passed_validations / total_validations * 100) if total_validations > 0 else 0
        
        total_meta = len(self.meta_validations_log)
        passed_meta = sum(1 for m in self.meta_validations_log if m["all_passed"])
        meta_rate = (passed_meta / total_meta * 100) if total_meta > 0 else 0
        
        return {
            "session_id": self.session_id,
            "start_time": self.session_start.isoformat(),
            "duration_seconds": duration,
            "stats": {
                "actions_logged": self.action_count,
                "validations_performed": self.validation_count,
                "meta_validations_performed": self.meta_validation_count,
                "errors_logged": len(self.errors_log),
                "anomalies_logged": len(self.anomalies_log)
            },
            "success_rates": {
                "validation_success_rate": f"{validation_rate:.1f}%",
                "meta_validation_success_rate": f"{meta_rate:.1f}%"
            },
            "health": {
                "overall_status": "healthy" if len(self.errors_log) == 0 else "degraded",
                "critical_errors": len(self.errors_log),
                "warnings": len(self.anomalies_log)
            }
        }
    
    def close_session(self):
        """Close the debugging session and write final summary (thread-safe)"""
        with self._lock:
            timestamp = datetime.now()
            summary = self.get_session_summary()
            summary["end_time"] = timestamp.isoformat()
            summary["status"] = "closed"
            
            # Write final summary
            summary_file = self.log_dir / f"session_{self.session_id}_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            # Update session file
            session_file = self.log_dir / f"session_{self.session_id}.json"
            with open(session_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            msg = f"[{timestamp.strftime('%H:%M:%S.%f')[:-3]}] 🏁 SESSION CLOSED: {self.session_id}"
            self._add_to_terminal(msg)
            
            # Cleanup old sessions (keep only last 3)
            self._cleanup_old_sessions()
    
    def _cleanup_old_sessions(self):
        """Keep only the last 3 sessions, delete older ones"""
        try:
            # Get all session summary files
            session_files = sorted(self.log_dir.glob("session_*_summary.json"))
            
            if len(session_files) > 3:
                # Keep last 3, delete rest
                files_to_delete = session_files[:-3]
                for file in files_to_delete:
                    session_id = file.stem.replace("session_", "").replace("_summary", "")
                    # Delete all files for this session
                    for pattern in [f"session_{session_id}*", f"actions_{session_id}*", 
                                    f"validations_{session_id}*", f"meta_validations_{session_id}*",
                                    f"errors_{session_id}*", f"anomalies_{session_id}*"]:
                        for f in self.log_dir.glob(pattern):
                            f.unlink()
        except Exception as e:
            pass  # Silent fail on cleanup
    
    def get_recent_sessions(self) -> List[Dict[str, Any]]:
        """Get metadata for last 3 sessions (including current)"""
        try:
            # Get all session summary files, sorted by creation time
            session_files = sorted(self.log_dir.glob("session_*_summary.json"), 
                                   key=lambda x: x.stat().st_mtime, reverse=True)
            
            sessions = []
            for session_file in session_files[:3]:  # Last 3 only
                try:
                    with open(session_file, 'r') as f:
                        summary = json.load(f)
                        sessions.append({
                            'session_id': summary['session_id'],
                            'start_time': summary.get('start_time', 'Unknown'),
                            'end_time': summary.get('end_time'),
                            'status': summary.get('status', 'unknown'),
                            'action_count': summary.get('stats', {}).get('actions_logged', 0),
                            'error_count': summary.get('stats', {}).get('errors_logged', 0),
                            'is_current': summary['session_id'] == self.session_id
                        })
                except Exception:
                    continue
            
            return sessions
        except Exception:
            return []
    
    def load_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load complete data for a specific session"""
        try:
            session_data = {
                'actions': [],
                'validations': [],
                'meta_validations': [],
                'errors': [],
                'anomalies': []
            }
            
            # Load actions
            actions_file = self.log_dir / f"actions_{session_id}.jsonl"
            if actions_file.exists():
                with open(actions_file, 'r') as f:
                    session_data['actions'] = [json.loads(line) for line in f]
            
            # Load validations
            validations_file = self.log_dir / f"validations_{session_id}.jsonl"
            if validations_file.exists():
                with open(validations_file, 'r') as f:
                    session_data['validations'] = [json.loads(line) for line in f]
            
            # Load meta-validations
            meta_file = self.log_dir / f"meta_validations_{session_id}.jsonl"
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    session_data['meta_validations'] = [json.loads(line) for line in f]
            
            # Load errors
            errors_file = self.log_dir / f"errors_{session_id}.jsonl"
            if errors_file.exists():
                with open(errors_file, 'r') as f:
                    session_data['errors'] = [json.loads(line) for line in f]
            
            # Load anomalies
            anomalies_file = self.log_dir / f"anomalies_{session_id}.jsonl"
            if anomalies_file.exists():
                with open(anomalies_file, 'r') as f:
                    session_data['anomalies'] = [json.loads(line) for line in f]
            
            return session_data
        except Exception:
            return None


# Global daemon instance
_daemon_instance: Optional[DebugDaemon] = None


def get_daemon() -> DebugDaemon:
    """Get or create global daemon instance"""
    global _daemon_instance
    if _daemon_instance is None:
        _daemon_instance = DebugDaemon()
    return _daemon_instance


def close_daemon():
    """Close global daemon instance"""
    global _daemon_instance
    if _daemon_instance is not None:
        _daemon_instance.close_session()
        _daemon_instance = None
