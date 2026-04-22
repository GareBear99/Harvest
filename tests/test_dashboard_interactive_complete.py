#!/usr/bin/env python3
"""
Comprehensive Dashboard Interactive Validation Test
Tests EVERY command, button, modal with status bar tracking validation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.terminal_ui import TerminalDashboard
from rich.console import Console
import time

def test_command_with_status_validation(dashboard, key, expected_valid, expected_operation, test_name):
    """
    Test a command and validate status bar response
    
    Returns: (success, error_message)
    """
    console = Console()
    
    # Log the keypress
    is_valid = dashboard.log_key_press(key)
    
    # Validate key was logged
    if dashboard.status['last_key'] != key:
        return False, f"Last key not recorded correctly. Expected: {key}, Got: {dashboard.status['last_key']}"
    
    # Validate validation result
    if is_valid != expected_valid:
        return False, f"Key validation incorrect. Expected: {expected_valid}, Got: {is_valid}"
    
    # Validate key_valid status
    if dashboard.status['key_valid'] != expected_valid:
        return False, f"Status key_valid incorrect. Expected: {expected_valid}, Got: {dashboard.status['key_valid']}"
    
    # Check command history updated
    if len(dashboard.command_history) == 0:
        return False, "Command history not updated"
    
    if dashboard.command_history[0]['key'] != key:
        return False, f"Command history incorrect. Expected: {key}, Got: {dashboard.command_history[0]['key']}"
    
    # For valid keys, simulate the command execution
    if expected_valid:
        try:
            # Note: log_key_press is already called above
            # For modal ESC keys, log_key_press is enough since handle_key does operation tracking
            # For non-modal or the first call, we need handle_key
            if expected_operation:
                # Only call handle_key if we expect operation tracking
                # This simulates the actual dashboard behavior
                dashboard.handle_key(key)
                
                # Validate operation was tracked
                if dashboard.status['result'] not in ['processing', 'success', 'failed']:
                    return False, f"Operation not tracked. Status: {dashboard.status['result']}"
            
        except Exception as e:
            return False, f"Command execution failed: {str(e)}"
    
    return True, None


def run_comprehensive_test():
    """Run comprehensive dashboard interactive test"""
    console = Console()
    
    console.print("\n[bold cyan]🧪 Comprehensive Dashboard Interactive Validation[/bold cyan]\n")
    console.print("Testing every command with status bar validation...\n")
    
    # Create dashboard instance
    dashboard = TerminalDashboard()
    
    results = []
    total_tests = 0
    passed_tests = 0
    
    # Test Suite 1: Valid Main Dashboard Commands
    console.print("[yellow]Test Suite 1: Valid Main Dashboard Commands[/yellow]")
    
    valid_commands = [
        ('q', True, 'Exit', 'Quit command'),
        ('r', True, 'Refresh', 'Refresh command'),
        ('h', True, 'Help', 'Help screen'),
        ('s', True, 'Seed Browser', 'Seeds browser'),
        ('b', True, 'Backtest Control', 'Backtest control'),
        ('w', True, 'Wallet', 'Wallet command'),
        ('d', True, 'Documentation', 'Documentation'),
        ('l', True, 'Live Mode', 'Live mode (not available)'),
        ('m', True, 'ML Control', 'ML control panel'),
    ]
    
    for key, expected_valid, expected_op, test_name in valid_commands:
        total_tests += 1
        
        # Reset dashboard state
        dashboard = TerminalDashboard()
        
        success, error = test_command_with_status_validation(
            dashboard, key, expected_valid, expected_op, test_name
        )
        
        if success:
            console.print(f"  ✅ {test_name}: PASSED")
            passed_tests += 1
            results.append((test_name, True, None))
        else:
            console.print(f"  ❌ {test_name}: FAILED - {error}")
            results.append((test_name, False, error))
    
    console.print()
    
    # Test Suite 2: Invalid Commands
    console.print("[yellow]Test Suite 2: Invalid Commands (Should Show ✗)[/yellow]")
    
    invalid_commands = [
        ('x', False, None, 'Invalid key x'),
        ('z', False, None, 'Invalid key z'),
        ('1', False, None, 'Invalid key 1'),
        ('!', False, None, 'Invalid key !'),
        ('abc', False, None, 'Invalid multi-char'),
    ]
    
    for key, expected_valid, expected_op, test_name in invalid_commands:
        total_tests += 1
        
        dashboard = TerminalDashboard()
        
        success, error = test_command_with_status_validation(
            dashboard, key, expected_valid, expected_op, test_name
        )
        
        if success:
            console.print(f"  ✅ {test_name}: PASSED (correctly rejected)")
            passed_tests += 1
            results.append((test_name, True, None))
        else:
            console.print(f"  ❌ {test_name}: FAILED - {error}")
            results.append((test_name, False, error))
    
    console.print()
    
    # Test Suite 3: ESC Key Variants
    console.print("[yellow]Test Suite 3: ESC Key Variants[/yellow]")
    
    # Test ESC key - just validate it's recognized as valid and closes modal
    total_tests += 1
    dashboard = TerminalDashboard()
    dashboard.active_modal = 'help'
    
    # Call handle_key which will log and process
    dashboard.handle_key('\x1b')
    
    if dashboard.status['key_valid'] and dashboard.status['result'] == 'success':
        console.print(f"  ✅ ESC as \x1b: PASSED")
        passed_tests += 1
        results.append(("ESC as \\x1b", True, None))
    else:
        console.print(f"  ❌ ESC as \x1b: FAILED - Status: {dashboard.status['result']}, Valid: {dashboard.status['key_valid']}")
        results.append(("ESC as \\x1b", False, f"Status: {dashboard.status['result']}"))
    
    # Test 'escape' string variant
    total_tests += 1
    dashboard = TerminalDashboard()
    dashboard.active_modal = 'help'
    dashboard.handle_key('escape')
    
    if dashboard.status['key_valid'] and dashboard.status['result'] == 'success':
        console.print(f"  ✅ ESC as escape: PASSED")
        passed_tests += 1
        results.append(("ESC as escape", True, None))
    else:
        console.print(f"  ❌ ESC as escape: FAILED - Status: {dashboard.status['result']}")
        results.append(("ESC as escape", False, f"Status: {dashboard.status['result']}"))
    
    console.print()
    
    # Test Suite 4: Modal Commands
    console.print("[yellow]Test Suite 4: Modal Commands[/yellow]")
    
    # Help modal
    total_tests += 1
    dashboard = TerminalDashboard()
    dashboard.active_modal = 'help'
    success, error = test_command_with_status_validation(
        dashboard, 'q', True, 'Close help', 'Help modal: Q to close'
    )
    if success:
        console.print(f"  ✅ Help modal Q: PASSED")
        passed_tests += 1
        results.append(("Help modal Q", True, None))
    else:
        console.print(f"  ❌ Help modal Q: FAILED - {error}")
        results.append(("Help modal Q", False, error))
    
    # Seed browser modal
    total_tests += 1
    dashboard = TerminalDashboard()
    dashboard.active_modal = 'seed'
    success, error = test_command_with_status_validation(
        dashboard, 'w', True, 'Whitelist view', 'Seed modal: W for whitelist'
    )
    if success:
        console.print(f"  ✅ Seed modal W: PASSED")
        passed_tests += 1
        results.append(("Seed modal W", True, None))
    else:
        console.print(f"  ❌ Seed modal W: FAILED - {error}")
        results.append(("Seed modal W", False, error))
    
    console.print()
    
    # Test Suite 5: Command History
    console.print("[yellow]Test Suite 5: Command History Tracking[/yellow]")
    
    total_tests += 1
    dashboard = TerminalDashboard()
    
    # Press multiple keys
    test_sequence = ['h', 's', 'r', 'x', 'q']
    for key in test_sequence:
        dashboard.log_key_press(key)
    
    # Check history limit (max 5)
    if len(dashboard.command_history) <= dashboard.max_history:
        console.print(f"  ✅ History limit enforced: {len(dashboard.command_history)}/{dashboard.max_history}")
        passed_tests += 1
        results.append(("History limit", True, None))
    else:
        console.print(f"  ❌ History limit failed: {len(dashboard.command_history)}/{dashboard.max_history}")
        results.append(("History limit", False, "Too many entries"))
    
    # Check history order (most recent first)
    total_tests += 1
    if dashboard.command_history[0]['key'] == 'q':
        console.print(f"  ✅ History order correct: most recent first")
        passed_tests += 1
        results.append(("History order", True, None))
    else:
        console.print(f"  ❌ History order wrong: {dashboard.command_history[0]['key']} != q")
        results.append(("History order", False, "Wrong order"))
    
    console.print()
    
    # Test Suite 6: Operation Tracking
    console.print("[yellow]Test Suite 6: Operation Tracking Lifecycle[/yellow]")
    
    total_tests += 1
    dashboard = TerminalDashboard()
    
    # Start operation
    dashboard.start_operation("Test Operation", "Testing details")
    
    if dashboard.status['result'] == 'processing' and dashboard.status['operation'] == "Test Operation":
        console.print(f"  ✅ Operation start: PASSED")
        passed_tests += 1
        results.append(("Operation start", True, None))
    else:
        console.print(f"  ❌ Operation start: FAILED")
        results.append(("Operation start", False, "Not processing"))
    
    # Complete success
    total_tests += 1
    dashboard.complete_operation(True, "Success message", "Details")
    
    if dashboard.status['result'] == 'success' and dashboard.status['message'] == "Success message":
        console.print(f"  ✅ Operation success: PASSED")
        passed_tests += 1
        results.append(("Operation success", True, None))
    else:
        console.print(f"  ❌ Operation success: FAILED")
        results.append(("Operation success", False, "Not success"))
    
    # Complete failure
    total_tests += 1
    dashboard.start_operation("Fail Test", "Testing failure")
    dashboard.complete_operation(False, "Failed message", "Error details")
    
    if dashboard.status['result'] == 'failed' and dashboard.status['message'] == "Failed message":
        console.print(f"  ✅ Operation failure: PASSED")
        passed_tests += 1
        results.append(("Operation failure", True, None))
    else:
        console.print(f"  ❌ Operation failure: FAILED")
        results.append(("Operation failure", False, "Not failed"))
    
    # Set ready
    total_tests += 1
    dashboard.set_ready("Ready message")
    
    if dashboard.status['result'] == 'ready' and dashboard.status['operation'] is None:
        console.print(f"  ✅ Set ready: PASSED")
        passed_tests += 1
        results.append(("Set ready", True, None))
    else:
        console.print(f"  ❌ Set ready: FAILED")
        results.append(("Set ready", False, "Not ready"))
    
    console.print()
    
    # Test Suite 7: Status Structure
    console.print("[yellow]Test Suite 7: Status Structure Validation[/yellow]")
    
    required_keys = ['last_key', 'key_valid', 'operation', 'result', 'message', 'details']
    
    for key in required_keys:
        total_tests += 1
        if key in dashboard.status:
            console.print(f"  ✅ Status has '{key}': PASSED")
            passed_tests += 1
            results.append((f"Status key {key}", True, None))
        else:
            console.print(f"  ❌ Status missing '{key}': FAILED")
            results.append((f"Status key {key}", False, "Missing key"))
    
    console.print()
    
    # Final Summary
    console.print("\n[bold]📊 Test Summary[/bold]\n")
    
    console.print(f"Total Tests: {total_tests}")
    console.print(f"Passed: {passed_tests} ✅")
    console.print(f"Failed: {total_tests - passed_tests} ❌")
    console.print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n")
    
    # List failures
    failures = [r for r in results if not r[1]]
    if failures:
        console.print("[bold red]Failed Tests:[/bold red]")
        for test_name, _, error in failures:
            console.print(f"  ❌ {test_name}: {error}")
        console.print()
    
    # Overall result
    if passed_tests == total_tests:
        console.print("[bold green]🎉 ALL TESTS PASSED![/bold green]")
        console.print("\n[cyan]Dashboard commands fully validated:[/cyan]")
        console.print("  • All keys logged correctly")
        console.print("  • Validation working (✓/✗)")
        console.print("  • Command history tracking")
        console.print("  • Operation lifecycle complete")
        console.print("  • Status structure validated")
        console.print("  • Modal commands functional")
        console.print("\n[bold]Ready for user testing![/bold]\n")
        return True
    else:
        console.print(f"[bold red]⚠️  {total_tests - passed_tests} TESTS FAILED[/bold red]")
        console.print("\n[yellow]Issues need to be fixed before user testing.[/yellow]\n")
        return False


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
