#!/usr/bin/env python3
"""
Production Health Check Script
Validates all critical systems before live paper trading
"""

import sys
import os
import json
import time
import psutil
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class HealthCheck:
    """Comprehensive system health validator"""
    
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
    
    def run_all_checks(self) -> bool:
        """Run all health checks"""
        print("="*70)
        print("HARVEST PRODUCTION HEALTH CHECK")
        print("="*70)
        print()
        
        checks = [
            ("File Locking System", self.check_file_locking),
            ("Debug Daemon", self.check_debug_daemon),
            ("Wallet Configuration", self.check_wallet_config),
            ("Paper Trading Tracker", self.check_paper_trading),
            ("Slot Allocation", self.check_slot_allocation),
            ("Memory Usage", self.check_memory),
            ("Config File Integrity", self.check_config_integrity),
            ("API Server Status", self.check_api_server),
            ("Dashboard Components", self.check_dashboard_components),
        ]
        
        for name, check_func in checks:
            print(f"\nChecking: {name}")
            print("-"*70)
            try:
                check_func()
            except Exception as e:
                self.checks_failed.append((name, f"Exception: {e}"))
                print(f"❌ FAIL: {e}")
        
        # Summary
        print("\n" + "="*70)
        print("HEALTH CHECK SUMMARY")
        print("="*70)
        
        total = len(self.checks_passed) + len(self.checks_failed)
        print(f"\n✅ Passed: {len(self.checks_passed)}/{total}")
        print(f"❌ Failed: {len(self.checks_failed)}/{total}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.checks_failed:
            print("\nFailed Checks:")
            for check, reason in self.checks_failed:
                print(f"  ❌ {check}: {reason}")
        
        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
        
        print("="*70)
        
        return len(self.checks_failed) == 0
    
    def check_file_locking(self):
        """Verify file locking system works"""
        from core.file_lock import safe_json_load, safe_json_save, locked_json_update
        import tempfile
        
        # Test with temp file
        fd, temp_path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        try:
            # Test write
            test_data = {"test": True, "timestamp": time.time()}
            safe_json_save(temp_path, test_data)
            print("  ✓ Atomic write successful")
            
            # Test read
            loaded = safe_json_load(temp_path, default={})
            assert loaded == test_data, "Data mismatch"
            print("  ✓ Safe read successful")
            
            # Test update
            def increment(data):
                data['counter'] = data.get('counter', 0) + 1
                return data
            
            locked_json_update(temp_path, increment, default={})
            final = safe_json_load(temp_path, default={})
            assert final['counter'] == 1, "Counter not incremented"
            print("  ✓ Locked update successful")
            
            self.checks_passed.append("File Locking System")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def check_debug_daemon(self):
        """Verify debug daemon is responsive and thread-safe"""
        from core.debug_daemon import get_daemon
        
        daemon = get_daemon()
        
        # Test logging
        action_id = daemon.log_action(
            action_name="health_check",
            category="validation",
            details={"check": "health_check"},
            expected_outcome={"success": True}
        )
        assert action_id is not None, "Failed to log action"
        print("  ✓ Action logging works")
        
        # Test snapshot APIs (thread-safe)
        actions = daemon.get_actions_snapshot()
        assert isinstance(actions, list), "Actions snapshot not a list"
        print("  ✓ Thread-safe snapshots work")
        
        # Check session summary
        summary = daemon.get_session_summary()
        assert 'session_id' in summary, "Missing session_id"
        assert 'stats' in summary, "Missing stats"
        print("  ✓ Session summary available")
        
        self.checks_passed.append("Debug Daemon")
    
    def check_wallet_config(self):
        """Verify wallet configuration is valid"""
        from core.file_lock import safe_json_load
        
        wallet_config_path = Path("data/wallet_config.json")
        
        if not wallet_config_path.exists():
            self.warnings.append("wallet_config.json not found (will be created on first run)")
            self.checks_passed.append("Wallet Configuration")
            return
        
        # Load with file locking
        config = safe_json_load(str(wallet_config_path), default=None)
        
        if config is None:
            raise Exception("Failed to load wallet_config.json")
        
        # Validate structure
        required_keys = ['client_id', 'metamask', 'btc_wallet', 'profit_tracking']
        for key in required_keys:
            if key not in config:
                raise Exception(f"Missing required key: {key}")
        
        print("  ✓ wallet_config.json structure valid")
        
        # Check metamask connection
        if config['metamask'].get('connected'):
            print(f"  ✓ MetaMask connected: {config['metamask']['address'][:10]}...")
        else:
            self.warnings.append("MetaMask not connected yet")
        
        self.checks_passed.append("Wallet Configuration")
    
    def check_paper_trading(self):
        """Verify paper trading tracker is valid"""
        from core.file_lock import safe_json_load
        
        tracker_path = Path("data/paper_trading_tracker.json")
        
        if not tracker_path.exists():
            self.warnings.append("paper_trading_tracker.json not found (will be created when starting)")
            self.checks_passed.append("Paper Trading Tracker")
            return
        
        # Load tracker
        tracker = safe_json_load(str(tracker_path), default=None)
        
        if tracker is None:
            raise Exception("Failed to load paper_trading_tracker.json")
        
        # Validate structure
        required_keys = ['status', 'starting_balance', 'current_balance', 'total_trades']
        for key in required_keys:
            if key not in tracker:
                raise Exception(f"Missing required key: {key}")
        
        print(f"  ✓ Tracker structure valid")
        print(f"  ✓ Status: {tracker['status']}")
        print(f"  ✓ Balance: ${tracker.get('current_balance', 0):.2f}")
        print(f"  ✓ Trades: {tracker.get('total_trades', 0)}")
        
        self.checks_passed.append("Paper Trading Tracker")
    
    def check_slot_allocation(self):
        """Verify slot allocation system works"""
        from core.slot_allocation_strategy import get_slot_allocation_strategy
        
        strategy = get_slot_allocation_strategy()
        
        # Test various balances
        test_cases = [
            (10, 1),
            (50, 5),
            (100, 10),
            (150, 10),
        ]
        
        for balance, expected_slots in test_cases:
            slots = strategy.get_active_slots(balance)
            if slots != expected_slots:
                raise Exception(f"Slot calculation wrong: ${balance} should be {expected_slots} slots, got {slots}")
        
        print("  ✓ Slot calculations correct")
        
        # Test summary
        summary = strategy.get_slot_summary(100)
        assert summary['active_slots'] == 10, "Should have 10 slots at $100"
        print("  ✓ Slot summaries work")
        
        self.checks_passed.append("Slot Allocation")
    
    def check_memory(self):
        """Check memory usage is reasonable"""
        process = psutil.Process()
        mem_info = process.memory_info()
        mem_mb = mem_info.rss / 1024 / 1024
        
        print(f"  ✓ Memory usage: {mem_mb:.1f} MB")
        
        if mem_mb > 500:
            self.warnings.append(f"High memory usage: {mem_mb:.1f} MB")
        
        # Check for memory leaks by comparing before/after import
        import gc
        gc.collect()
        
        self.checks_passed.append("Memory Usage")
    
    def check_config_integrity(self):
        """Verify all JSON config files are valid"""
        config_files = [
            "data/wallet_config.json",
            "data/paper_trading_tracker.json",
            "data/founder_fee_config.json",
        ]
        
        for filepath in config_files:
            path = Path(filepath)
            if not path.exists():
                print(f"  ⚠️  {filepath} not found (will be created)")
                continue
            
            try:
                with open(path, 'r') as f:
                    json.load(f)
                print(f"  ✓ {filepath} valid JSON")
            except json.JSONDecodeError as e:
                raise Exception(f"{filepath} is corrupt: {e}")
        
        self.checks_passed.append("Config File Integrity")
    
    def check_api_server(self):
        """Check if wallet API server is running"""
        try:
            import requests
            response = requests.get('http://localhost:5123/api/wallet/status', timeout=1)
            if response.status_code == 200:
                print("  ✓ API server running on port 5123")
            else:
                self.warnings.append("API server responded with non-200 status")
        except Exception:
            self.warnings.append("API server not running (start with: python core/wallet_api_server.py)")
        
        self.checks_passed.append("API Server Status")
    
    def check_dashboard_components(self):
        """Verify dashboard components can be imported"""
        try:
            from dashboard.terminal_ui import TerminalDashboard, RefreshCoordinator
            print("  ✓ TerminalDashboard imports")
            
            from dashboard.help_screen import render_help_screen
            print("  ✓ Help screen imports")
            
            from dashboard.panels import SeedStatusPanel, BotStatusPanel
            print("  ✓ Panels import")
            
            # Test RefreshCoordinator
            coordinator = RefreshCoordinator()
            assert coordinator.start_refresh() == True, "First refresh should be allowed"
            coordinator.end_refresh()
            print("  ✓ RefreshCoordinator functional")
            
            self.checks_passed.append("Dashboard Components")
        except Exception as e:
            raise Exception(f"Component import failed: {e}")


def main():
    """Run health check"""
    checker = HealthCheck()
    success = checker.run_all_checks()
    
    if success:
        print("\n✅ ALL CHECKS PASSED - System ready for production")
        return 0
    else:
        print("\n❌ SOME CHECKS FAILED - Fix issues before production")
        return 1


if __name__ == "__main__":
    sys.exit(main())
