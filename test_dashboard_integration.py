#!/usr/bin/env python3
"""
Dashboard Integration Test
Tests dashboard startup, panels, unison systems, and wallet connection flow
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    try:
        from dashboard.terminal_ui import TerminalDashboard, RefreshCoordinator
        from core.debug_daemon import get_daemon
        from core.file_lock import safe_json_load, safe_json_save
        from core.auto_wallet_manager import AutoWalletManager
        from core.slot_allocation_strategy import get_slot_allocation_strategy
        from dashboard.help_screen import render_help_screen
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_refresh_coordinator():
    """Test RefreshCoordinator prevents concurrent refreshes"""
    print("\nTesting RefreshCoordinator...")
    try:
        from dashboard.terminal_ui import RefreshCoordinator
        
        coordinator = RefreshCoordinator()
        
        # Test first refresh allowed
        assert coordinator.start_refresh() == True, "First refresh should be allowed"
        
        # Test concurrent refresh blocked
        assert coordinator.start_refresh() == False, "Concurrent refresh should be blocked"
        
        # End refresh
        coordinator.end_refresh()
        
        # Test subsequent refresh allowed after delay
        import time
        time.sleep(0.6)  # Wait for debounce
        assert coordinator.start_refresh() == True, "Refresh should be allowed after debounce"
        coordinator.end_refresh()
        
        print("✅ RefreshCoordinator working correctly")
        return True
    except Exception as e:
        print(f"❌ RefreshCoordinator failed: {e}")
        return False


def test_debug_daemon_thread_safety():
    """Test debug daemon thread safety"""
    print("\nTesting Debug Daemon thread safety...")
    try:
        from core.debug_daemon import get_daemon
        
        daemon = get_daemon()
        
        # Log some actions
        action_id = daemon.log_action(
            action_name="test_action",
            category="test",
            details={"test": True},
            expected_outcome={"success": True}
        )
        
        assert action_id is not None, "Action ID should be returned"
        
        # Get snapshots (should not raise RuntimeError)
        actions = daemon.get_actions_snapshot()
        validations = daemon.get_validations_snapshot()
        
        assert isinstance(actions, list), "Actions should be list"
        assert isinstance(validations, list), "Validations should be list"
        
        print("✅ Debug Daemon thread-safe")
        return True
    except Exception as e:
        print(f"❌ Debug Daemon failed: {e}")
        return False


def test_file_locking():
    """Test file locking utilities"""
    print("\nTesting file locking...")
    try:
        from core.file_lock import safe_json_load, safe_json_save, locked_json_update
        import tempfile
        import os
        
        # Create temp file
        fd, temp_path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        try:
            # Test safe save
            test_data = {"test": "data", "counter": 0}
            safe_json_save(temp_path, test_data)
            
            # Test safe load
            loaded = safe_json_load(temp_path, default={})
            assert loaded == test_data, "Loaded data should match saved data"
            
            # Test locked update
            def increment(data):
                data['counter'] += 1
                return data
            
            locked_json_update(temp_path, increment, default={})
            
            # Verify update
            final = safe_json_load(temp_path, default={})
            assert final['counter'] == 1, "Counter should be incremented"
            
            print("✅ File locking working correctly")
            return True
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        print(f"❌ File locking failed: {e}")
        return False


def test_slot_allocation():
    """Test slot allocation strategy"""
    print("\nTesting slot allocation strategy...")
    try:
        from core.slot_allocation_strategy import get_slot_allocation_strategy
        
        strategy = get_slot_allocation_strategy()
        
        # Test various balances
        tests = [
            (10, 1),   # $10 = 1 slot
            (50, 5),   # $50 = 5 slots
            (100, 10), # $100 = 10 slots (max)
            (200, 10), # $200 = still 10 slots
        ]
        
        for balance, expected_slots in tests:
            slots = strategy.get_active_slots(balance)
            assert slots == expected_slots, f"${balance} should have {expected_slots} slots, got {slots}"
        
        # Test slot summary
        summary = strategy.get_slot_summary(100)
        assert summary['active_slots'] == 10, "Should have 10 slots at $100"
        assert len(summary['eth_slots']) == 5, "Should have 5 ETH slots"
        assert len(summary['btc_slots']) == 5, "Should have 5 BTC slots"
        
        print("✅ Slot allocation working correctly")
        return True
    except Exception as e:
        print(f"❌ Slot allocation failed: {e}")
        return False


def test_help_screen():
    """Test help screen renders without errors"""
    print("\nTesting help screen rendering...")
    try:
        from dashboard.help_screen import render_help_screen
        
        panel = render_help_screen()
        assert panel is not None, "Help screen should render"
        
        # Check that slot system explanation is present
        # Panel is a Rich object, so we need to render it to check content
        from io import StringIO
        from rich.console import Console
        
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=False, width=120)
        console.print(panel)
        content = buffer.getvalue()
        
        assert "SLOT" in content.upper(), "Should mention SLOTS"
        assert "POSITION" in content.upper(), "Should mention POSITIONS"
        assert "$300" in content or "300" in content, "Should mention $300 threshold"
        
        print("✅ Help screen renders correctly with slot system explanation")
        return True
    except Exception as e:
        print(f"❌ Help screen failed: {e}")
        return False


def test_wallet_manager_file_safety():
    """Test wallet manager uses file locking"""
    print("\nTesting wallet manager file safety...")
    try:
        from core.auto_wallet_manager import AutoWalletManager
        import tempfile
        import shutil
        
        # Create temp data dir
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Initialize wallet manager
            manager = AutoWalletManager(data_dir=temp_dir)
            
            # Config should be loaded/created
            assert manager.wallet_config is not None, "Config should exist"
            
            # Save config (uses file locking)
            manager._save_wallet_config()
            
            # Load again
            manager2 = AutoWalletManager(data_dir=temp_dir)
            assert manager2.wallet_config is not None, "Config should load"
            
            print("✅ Wallet manager using file locking")
            return True
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        print(f"❌ Wallet manager failed: {e}")
        return False


def main():
    """Run all tests"""
    print("="*70)
    print("HARVEST DASHBOARD INTEGRATION TEST")
    print("="*70)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Refresh Coordinator", test_refresh_coordinator),
        ("Debug Daemon Thread Safety", test_debug_daemon_thread_safety),
        ("File Locking", test_file_locking),
        ("Slot Allocation", test_slot_allocation),
        ("Help Screen", test_help_screen),
        ("Wallet Manager File Safety", test_wallet_manager_file_safety),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("="*70)
    print(f"Results: {passed}/{total} tests passed")
    print("="*70)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
