#!/usr/bin/env python3
"""
Test timeout detection and processing symbol validation
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.terminal_ui import TerminalDashboard
from rich.console import Console

def test_timeout_detection():
    """Test operation timeout detection"""
    console = Console()
    
    console.print("\n[bold cyan]🕐 Testing Timeout Detection & Processing Symbols[/bold cyan]\n")
    
    results = []
    total_tests = 0
    passed_tests = 0
    
    # Test 1: Processing symbol appears
    console.print("[yellow]Test 1: Processing Symbol Validation[/yellow]")
    total_tests += 1
    
    dashboard = TerminalDashboard()
    dashboard.start_operation("Test Operation", "Testing processing symbol")
    
    has_processing_symbol = "⏳" in dashboard.status['message']
    is_processing_state = dashboard.status['result'] == 'processing'
    has_operation_name = "Test Operation" in dashboard.status['message']
    
    if has_processing_symbol and is_processing_state and has_operation_name:
        console.print(f"  ✅ Processing symbol present: {dashboard.status['message']}")
        console.print(f"  ✅ State is 'processing': {dashboard.status['result']}")
        console.print(f"  ✅ Operation name shown: {dashboard.status['operation']}")
        passed_tests += 1
        results.append(("Processing symbol", True, None))
    else:
        error = f"Symbol: {has_processing_symbol}, State: {is_processing_state}, Name: {has_operation_name}"
        console.print(f"  ❌ Processing validation failed: {error}")
        results.append(("Processing symbol", False, error))
    
    console.print()
    
    # Test 2: Start time tracking
    console.print("[yellow]Test 2: Start Time Tracking[/yellow]")
    total_tests += 1
    
    dashboard = TerminalDashboard()
    dashboard.start_operation("Timed Operation", "Testing start time")
    
    has_start_time = hasattr(dashboard, '_operation_start_time')
    start_time_valid = False
    
    if has_start_time:
        # Check start time is recent (within last 2 seconds)
        elapsed = time.time() - dashboard._operation_start_time
        start_time_valid = elapsed < 2
    
    if has_start_time and start_time_valid:
        console.print(f"  ✅ Start time tracked: {elapsed:.3f}s ago")
        passed_tests += 1
        results.append(("Start time tracking", True, None))
    else:
        error = f"Has time: {has_start_time}, Valid: {start_time_valid}"
        console.print(f"  ❌ Start time tracking failed: {error}")
        results.append(("Start time tracking", False, error))
    
    console.print()
    
    # Test 3: Timeout detection (simulated)
    console.print("[yellow]Test 3: Timeout Detection (Fast Simulation)[/yellow]")
    total_tests += 1
    
    dashboard = TerminalDashboard()
    dashboard.start_operation("Slow Operation", "Testing timeout")
    
    # Manually set start time to 31 seconds ago to simulate timeout
    dashboard._operation_start_time = time.time() - 31
    
    # Call complete_operation which should detect timeout
    dashboard.complete_operation(True, "Should timeout")
    
    is_failed = dashboard.status['result'] == 'failed'
    has_timeout_message = 'timeout' in dashboard.status['message'].lower()
    has_elapsed_time = dashboard.status['details'] and '31' in dashboard.status['details']
    
    if is_failed and has_timeout_message and has_elapsed_time:
        console.print(f"  ✅ Timeout detected: {dashboard.status['message']}")
        console.print(f"  ✅ Result is 'failed': {dashboard.status['result']}")
        console.print(f"  ✅ Details show elapsed time: {dashboard.status['details']}")
        passed_tests += 1
        results.append(("Timeout detection", True, None))
    else:
        error = f"Failed: {is_failed}, Timeout msg: {has_timeout_message}, Details: {has_elapsed_time}"
        console.print(f"  ❌ Timeout detection failed: {error}")
        console.print(f"     Message: {dashboard.status['message']}")
        console.print(f"     Details: {dashboard.status['details']}")
        results.append(("Timeout detection", False, error))
    
    console.print()
    
    # Test 4: check_operation_timeout method
    console.print("[yellow]Test 4: Check Operation Timeout Method[/yellow]")
    total_tests += 1
    
    dashboard = TerminalDashboard()
    dashboard.start_operation("Stuck Operation", "Testing manual timeout check")
    
    # Manually set to 31 seconds ago
    dashboard._operation_start_time = time.time() - 31
    
    # Call check method
    timed_out = dashboard.check_operation_timeout()
    
    is_failed = dashboard.status['result'] == 'failed'
    has_timeout_message = 'timeout' in dashboard.status['message'].lower()
    
    if timed_out and is_failed and has_timeout_message:
        console.print(f"  ✅ Timeout check returned True: {timed_out}")
        console.print(f"  ✅ Status changed to failed: {dashboard.status['result']}")
        console.print(f"  ✅ Timeout message: {dashboard.status['message']}")
        passed_tests += 1
        results.append(("Check timeout method", True, None))
    else:
        error = f"Timed out: {timed_out}, Failed: {is_failed}, Message: {has_timeout_message}"
        console.print(f"  ❌ Check timeout failed: {error}")
        results.append(("Check timeout method", False, error))
    
    console.print()
    
    # Test 5: No timeout on normal operation
    console.print("[yellow]Test 5: No False Timeout on Quick Operation[/yellow]")
    total_tests += 1
    
    dashboard = TerminalDashboard()
    dashboard.start_operation("Quick Operation", "Testing no false timeout")
    
    # Complete immediately (should not timeout)
    time.sleep(0.1)
    dashboard.complete_operation(True, "Completed quickly")
    
    is_success = dashboard.status['result'] == 'success'
    no_timeout_message = 'timeout' not in dashboard.status['message'].lower()
    
    if is_success and no_timeout_message:
        console.print(f"  ✅ Quick operation succeeded: {dashboard.status['result']}")
        console.print(f"  ✅ No timeout message: {dashboard.status['message']}")
        passed_tests += 1
        results.append(("No false timeout", True, None))
    else:
        error = f"Success: {is_success}, No timeout: {no_timeout_message}"
        console.print(f"  ❌ False timeout detected: {error}")
        results.append(("No false timeout", False, error))
    
    console.print()
    
    # Test 6: Start time cleanup on set_ready
    console.print("[yellow]Test 6: Start Time Cleanup on Ready[/yellow]")
    total_tests += 1
    
    dashboard = TerminalDashboard()
    dashboard.start_operation("Operation", "Testing cleanup")
    
    has_time_before = hasattr(dashboard, '_operation_start_time')
    dashboard.set_ready("Ready state")
    has_time_after = hasattr(dashboard, '_operation_start_time')
    
    if has_time_before and not has_time_after:
        console.print(f"  ✅ Start time existed: {has_time_before}")
        console.print(f"  ✅ Start time cleaned up: not {has_time_after}")
        console.print(f"  ✅ Status is ready: {dashboard.status['result']}")
        passed_tests += 1
        results.append(("Start time cleanup", True, None))
    else:
        error = f"Before: {has_time_before}, After: {has_time_after}"
        console.print(f"  ❌ Cleanup failed: {error}")
        results.append(("Start time cleanup", False, error))
    
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
        console.print("[bold green]🎉 ALL TIMEOUT TESTS PASSED![/bold green]")
        console.print("\n[cyan]Timeout detection fully validated:[/cyan]")
        console.print("  • Processing symbol (⏳) appears")
        console.print("  • Start time tracked accurately")
        console.print("  • Timeout detection at 30s")
        console.print("  • Manual timeout check works")
        console.print("  • No false timeouts")
        console.print("  • Cleanup on set_ready")
        console.print("\n[bold]Status bar timeout logic ready![/bold]\n")
        return True
    else:
        console.print(f"[bold red]⚠️  {total_tests - passed_tests} TESTS FAILED[/bold red]")
        console.print("\n[yellow]Timeout logic needs fixes.[/yellow]\n")
        return False


if __name__ == "__main__":
    success = test_timeout_detection()
    sys.exit(0 if success else 1)
