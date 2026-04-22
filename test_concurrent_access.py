#!/usr/bin/env python3
"""
Concurrent Access Stress Test for HARVEST
Tests all unison fixes for race conditions
"""

import threading
import time
import sys
import json
from pathlib import Path
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.file_lock import safe_json_load, safe_json_save, locked_json_update
from core.debug_daemon import get_daemon
from core.auto_wallet_manager import AutoWalletManager
from core.paper_trading_tracker import PaperTradingTracker

class TestResults:
    """Thread-safe test results collector"""
    def __init__(self):
        self.lock = threading.Lock()
        self.passed = []
        self.failed = []
        self.errors = []
    
    def add_pass(self, test_name: str):
        with self.lock:
            self.passed.append(test_name)
            print(f"✅ {test_name}")
    
    def add_fail(self, test_name: str, reason: str):
        with self.lock:
            self.failed.append((test_name, reason))
            print(f"❌ {test_name}: {reason}")
    
    def add_error(self, test_name: str, error: str):
        with self.lock:
            self.errors.append((test_name, error))
            print(f"🔥 {test_name}: ERROR - {error}")
    
    def summary(self):
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"✅ Passed: {len(self.passed)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"🔥 Errors: {len(self.errors)}")
        
        if self.failed:
            print("\nFailed Tests:")
            for test, reason in self.failed:
                print(f"  - {test}: {reason}")
        
        if self.errors:
            print("\nErrors:")
            for test, error in self.errors:
                print(f"  - {test}: {error}")
        
        print("="*70)
        return len(self.failed) == 0 and len(self.errors) == 0


def test_concurrent_wallet_config_access(results: TestResults):
    """Test concurrent read/write to wallet_config.json"""
    test_name = "Concurrent Wallet Config Access"
    
    try:
        # Setup
        wallet_mgr = AutoWalletManager(data_dir="data")
        config_path = wallet_mgr.config_path
        
        def reader(thread_id: int):
            """Reader thread"""
            try:
                for i in range(10):
                    config = safe_json_load(str(config_path), default={})
                    assert isinstance(config, dict), f"Thread {thread_id} got invalid config"
                    time.sleep(0.01)
            except Exception as e:
                results.add_error(f"{test_name} - Reader {thread_id}", str(e))
        
        def writer(thread_id: int):
            """Writer thread"""
            try:
                for i in range(5):
                    def update(config):
                        if 'test_counter' not in config:
                            config['test_counter'] = 0
                        config['test_counter'] += 1
                        return config
                    
                    locked_json_update(str(config_path), update, default={})
                    time.sleep(0.02)
            except Exception as e:
                results.add_error(f"{test_name} - Writer {thread_id}", str(e))
        
        # Launch threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=reader, args=(i,))
            threads.append(t)
            t.start()
        
        for i in range(2):
            t = threading.Thread(target=writer, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join(timeout=10)
        
        # Verify final state
        final_config = safe_json_load(str(config_path), default={})
        expected_count = 2 * 5  # 2 writers, 5 increments each
        actual_count = final_config.get('test_counter', 0)
        
        # File locking should preserve all writes
        # Some writes may have been from initial config load, so check >= expected
        if actual_count >= expected_count:
            results.add_pass(test_name)
        else:
            results.add_fail(test_name, f"Counter too low: expected at least {expected_count}, got {actual_count}")
    
    except Exception as e:
        results.add_error(test_name, str(e))


def test_debug_daemon_concurrent_iteration(results: TestResults):
    """Test concurrent iteration over debug daemon data"""
    test_name = "Debug Daemon Concurrent Iteration"
    
    try:
        daemon = get_daemon()
        errors = []
        
        def logger_thread(thread_id: int):
            """Thread that logs actions"""
            try:
                for i in range(20):
                    daemon.log_action(
                        action_name=f"test_action_{thread_id}_{i}",
                        category="test",
                        details={"thread": thread_id, "iteration": i},
                        expected_outcome={"success": True}
                    )
                    time.sleep(0.005)
            except Exception as e:
                errors.append(f"Logger {thread_id}: {e}")
        
        def reader_thread(thread_id: int):
            """Thread that reads snapshots"""
            try:
                for i in range(30):
                    # Get snapshots (should never raise RuntimeError)
                    actions = daemon.get_actions_snapshot()
                    validations = daemon.get_validations_snapshot()
                    
                    # Iterate over snapshots
                    for action in actions:
                        _ = action.get('action_id')
                    
                    for validation in validations:
                        _ = validation.get('validation_id')
                    
                    time.sleep(0.003)
            except RuntimeError as e:
                errors.append(f"Reader {thread_id}: RuntimeError during iteration - {e}")
            except Exception as e:
                errors.append(f"Reader {thread_id}: {e}")
        
        # Launch threads
        threads = []
        for i in range(2):
            t = threading.Thread(target=logger_thread, args=(i,))
            threads.append(t)
            t.start()
        
        for i in range(3):
            t = threading.Thread(target=reader_thread, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join(timeout=10)
        
        if errors:
            results.add_fail(test_name, f"{len(errors)} errors: {errors[0]}")
        else:
            results.add_pass(test_name)
    
    except Exception as e:
        results.add_error(test_name, str(e))


def test_paper_trading_atomic_writes(results: TestResults):
    """Test atomic writes to paper trading tracker"""
    test_name = "Paper Trading Atomic Writes"
    
    try:
        tracker = PaperTradingTracker(tracker_file="data/paper_trading_tracker.json")
        errors = []
        
        def trade_thread(thread_id: int):
            """Thread that simulates trades"""
            try:
                # Ensure paper trading is started
                if tracker.data.get('status') != 'running':
                    tracker.start_paper_trading(starting_balance=100.0)
                
                for i in range(5):
                    # Record a trade using the actual API
                    trade_data = {
                        'timeframe': '5m',
                        'asset': 'BTC',
                        'entry_price': 50000 + thread_id * 100,
                        'exit_price': 50500,
                        'position_size': 0.01,
                        'pnl': 5.0,
                        'outcome': 'win'
                    }
                    tracker.record_trade(trade_data)
                    time.sleep(0.02)
            except Exception as e:
                errors.append(f"Trade thread {thread_id}: {e}")
        
        def reader_thread(thread_id: int):
            """Thread that reads tracker state"""
            try:
                for i in range(15):
                    # Should never get corrupt data when reading tracker
                    # Access the data dict directly (matches actual usage)
                    data = tracker.data
                    trades = data.get('trades', [])
                    status = data.get('status', 'unknown')
                    balance = data.get('current_balance', 0.0)
                    
                    assert isinstance(trades, list)
                    assert isinstance(status, str)
                    assert isinstance(balance, (int, float))
                    time.sleep(0.01)
            except AssertionError as e:
                errors.append(f"Reader {thread_id}: Invalid data type")
            except json.JSONDecodeError as e:
                errors.append(f"Reader {thread_id}: Corrupt JSON")
            except Exception as e:
                errors.append(f"Reader {thread_id}: {e}")
        
        # Launch threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=trade_thread, args=(i,))
            threads.append(t)
            t.start()
        
        for i in range(2):
            t = threading.Thread(target=reader_thread, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join(timeout=15)
        
        if errors:
            results.add_fail(test_name, f"{len(errors)} errors: {errors[0]}")
        else:
            results.add_pass(test_name)
    
    except Exception as e:
        results.add_error(test_name, str(e))


def test_refresh_coordinator_debouncing(results: TestResults):
    """Test RefreshCoordinator prevents concurrent refreshes"""
    test_name = "Refresh Coordinator Debouncing"
    
    try:
        # Import coordinator from terminal_ui
        from dashboard.terminal_ui import RefreshCoordinator
        
        coordinator = RefreshCoordinator()
        refresh_counts = {'concurrent': 0, 'sequential': 0}
        errors = []
        
        def refresh_thread(thread_id: int):
            """Thread that attempts refresh"""
            try:
                if coordinator.start_refresh():
                    refresh_counts['concurrent'] += 1
                    time.sleep(0.1)  # Simulate work
                    coordinator.end_refresh()
                    refresh_counts['sequential'] += 1
            except Exception as e:
                errors.append(f"Refresh thread {thread_id}: {e}")
        
        # Launch 5 threads simultaneously
        threads = []
        for i in range(5):
            t = threading.Thread(target=refresh_thread, args=(i,))
            threads.append(t)
        
        # Start all at once
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join(timeout=5)
        
        # Verify only 1 was allowed to run concurrently
        if errors:
            results.add_fail(test_name, f"Errors: {errors[0]}")
        elif refresh_counts['concurrent'] > 1:
            results.add_fail(test_name, f"Multiple concurrent refreshes: {refresh_counts['concurrent']}")
        elif refresh_counts['sequential'] < 1:
            results.add_fail(test_name, "No refreshes completed")
        else:
            results.add_pass(test_name)
    
    except Exception as e:
        results.add_error(test_name, str(e))


def main():
    """Run all concurrent access tests"""
    print("="*70)
    print("HARVEST CONCURRENT ACCESS STRESS TEST")
    print("="*70)
    print()
    
    results = TestResults()
    
    # Run tests
    print("Testing concurrent wallet config access...")
    test_concurrent_wallet_config_access(results)
    
    print("\nTesting debug daemon concurrent iteration...")
    test_debug_daemon_concurrent_iteration(results)
    
    print("\nTesting paper trading atomic writes...")
    test_paper_trading_atomic_writes(results)
    
    print("\nTesting refresh coordinator debouncing...")
    test_refresh_coordinator_debouncing(results)
    
    # Summary
    success = results.summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
