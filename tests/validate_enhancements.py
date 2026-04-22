#!/usr/bin/env python3
"""
Final validation script for dashboard enhancements
Validates all components are working correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

def validate_all():
    """Run complete validation suite"""
    console = Console()
    
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]🔍 HARVEST Dashboard Enhancement Validation[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    results = []
    
    # Test 1: Terminal UI Status Tracking
    console.print("[yellow]Test 1:[/yellow] Terminal UI Status Tracking System")
    try:
        from dashboard.terminal_ui import TerminalDashboard
        dashboard = TerminalDashboard()
        
        # Check attributes
        has_status = hasattr(dashboard, 'status') and bool(dashboard.status)
        has_history = hasattr(dashboard, 'command_history')
        has_methods = (
            hasattr(dashboard, 'log_key_press') and
            hasattr(dashboard, 'start_operation') and
            hasattr(dashboard, 'complete_operation') and
            hasattr(dashboard, 'set_ready')
        )
        
        # Test functionality
        is_valid = dashboard.log_key_press('q')
        dashboard.start_operation("Test", "Details")
        dashboard.complete_operation(True, "Success")
        
        all_passed = has_status and has_history and has_methods and is_valid
        
        console.print(f"  Status dict: {'✅' if has_status else '❌'}")
        console.print(f"  Command history: {'✅' if has_history else '❌'}")
        console.print(f"  Methods available: {'✅' if has_methods else '❌'}")
        console.print(f"  Functionality: {'✅' if is_valid else '❌'}")
        
        results.append(("Status Tracking", all_passed))
        console.print(f"  [{'green' if all_passed else 'red'}]Result: {'PASSED ✅' if all_passed else 'FAILED ❌'}[/]\n")
        
    except Exception as e:
        console.print(f"  [red]Error: {e}[/]\n")
        results.append(("Status Tracking", False))
    
    # Test 2: Help Screen
    console.print("[yellow]Test 2:[/yellow] Help Screen Comprehensive Update")
    try:
        from dashboard.help_screen import render_help_screen, open_documentation
        
        # Render help screen
        panel = render_help_screen()
        
        # Check content
        content = str(panel.renderable)
        has_navigation = "CORE NAVIGATION" in content
        has_features = "MAIN FEATURES" in content
        has_status_guide = "STATUS BAR GUIDE" in content
        has_tips = "TIPS & TRICKS" in content
        has_system_status = "CURRENT SYSTEM STATUS" in content
        
        all_sections = all([has_navigation, has_features, has_status_guide, has_tips, has_system_status])
        
        console.print(f"  Navigation section: {'✅' if has_navigation else '❌'}")
        console.print(f"  Features section: {'✅' if has_features else '❌'}")
        console.print(f"  Status guide: {'✅' if has_status_guide else '❌'}")
        console.print(f"  Tips section: {'✅' if has_tips else '❌'}")
        console.print(f"  System status: {'✅' if has_system_status else '❌'}")
        
        results.append(("Help Screen", all_sections))
        console.print(f"  [{'green' if all_sections else 'red'}]Result: {'PASSED ✅' if all_sections else 'FAILED ❌'}[/]\n")
        
    except Exception as e:
        console.print(f"  [red]Error: {e}[/]\n")
        results.append(("Help Screen", False))
    
    # Test 3: Status Tracking Functionality
    console.print("[yellow]Test 3:[/yellow] Status Tracking Detailed Functionality")
    try:
        from dashboard.terminal_ui import TerminalDashboard
        dashboard = TerminalDashboard()
        
        # Test key validation
        valid_keys = ['q', 'r', 's', 'h', 'b', 'w', 'd', 'm', 'l']
        invalid_keys = ['x', 'z', '1', '!']
        
        valid_results = [dashboard.log_key_press(k) for k in valid_keys]
        invalid_results = [dashboard.log_key_press(k) for k in invalid_keys]
        
        all_valid = all(valid_results)
        none_invalid = not any(invalid_results)
        
        # Test operation tracking
        dashboard.start_operation("Test Op", "Details")
        processing = dashboard.status['result'] == 'processing'
        
        dashboard.complete_operation(True, "Success")
        success = dashboard.status['result'] == 'success'
        
        dashboard.complete_operation(False, "Failed", "Error")
        failed = dashboard.status['result'] == 'failed'
        
        dashboard.set_ready()
        ready = dashboard.status['result'] == 'ready'
        
        # Test history limit
        for i in range(10):
            dashboard.log_key_press(str(i))
        history_limited = len(dashboard.command_history) <= dashboard.max_history
        
        all_passed = (all_valid and none_invalid and processing and 
                     success and failed and ready and history_limited)
        
        console.print(f"  Valid key detection: {'✅' if all_valid else '❌'}")
        console.print(f"  Invalid key rejection: {'✅' if none_invalid else '❌'}")
        console.print(f"  Processing state: {'✅' if processing else '❌'}")
        console.print(f"  Success state: {'✅' if success else '❌'}")
        console.print(f"  Failed state: {'✅' if failed else '❌'}")
        console.print(f"  Ready state: {'✅' if ready else '❌'}")
        console.print(f"  History limit: {'✅' if history_limited else '❌'}")
        
        results.append(("Detailed Functionality", all_passed))
        console.print(f"  [{'green' if all_passed else 'red'}]Result: {'PASSED ✅' if all_passed else 'FAILED ❌'}[/]\n")
        
    except Exception as e:
        console.print(f"  [red]Error: {e}[/]\n")
        results.append(("Detailed Functionality", False))
    
    # Test 4: Documentation Files
    console.print("[yellow]Test 4:[/yellow] Documentation Files")
    try:
        status_guide = os.path.exists('STATUS_BAR_GUIDE.md')
        summary = os.path.exists('DASHBOARD_ENHANCEMENTS_SUMMARY.md')
        test_script = os.path.exists('test_status_tracking.py')
        
        all_docs = status_guide and summary and test_script
        
        console.print(f"  STATUS_BAR_GUIDE.md: {'✅' if status_guide else '❌'}")
        console.print(f"  DASHBOARD_ENHANCEMENTS_SUMMARY.md: {'✅' if summary else '❌'}")
        console.print(f"  test_status_tracking.py: {'✅' if test_script else '❌'}")
        
        results.append(("Documentation", all_docs))
        console.print(f"  [{'green' if all_docs else 'red'}]Result: {'PASSED ✅' if all_docs else 'FAILED ❌'}[/]\n")
        
    except Exception as e:
        console.print(f"  [red]Error: {e}[/]\n")
        results.append(("Documentation", False))
    
    # Final Summary
    console.print("\n")
    console.print(Panel.fit(
        "[bold]📊 Validation Summary[/bold]",
        border_style="cyan"
    ))
    console.print()
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Component", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Result", justify="center")
    
    for component, passed in results:
        status_icon = "✅" if passed else "❌"
        status_text = "PASSED" if passed else "FAILED"
        status_color = "green" if passed else "red"
        table.add_row(
            component,
            f"[{status_color}]{status_text}[/]",
            status_icon
        )
    
    console.print(table)
    console.print()
    
    # Overall result
    all_passed = all(result[1] for result in results)
    total_tests = len(results)
    passed_tests = sum(1 for result in results if result[1])
    
    console.print(Panel.fit(
        f"[bold {'green' if all_passed else 'red'}]"
        f"Overall: {passed_tests}/{total_tests} tests passed "
        f"({'✅ ALL PASSED' if all_passed else '❌ SOME FAILED'})"
        f"[/]",
        border_style="green" if all_passed else "red"
    ))
    console.print()
    
    if all_passed:
        console.print("[bold green]🎉 All enhancements validated successfully![/]\n")
        console.print("[cyan]The dashboard is ready for production use with:[/]")
        console.print("  • Comprehensive status tracking")
        console.print("  • Real-time command validation")
        console.print("  • Extensive help screen")
        console.print("  • Complete documentation")
        console.print()
    else:
        console.print("[bold red]⚠️  Some tests failed. Please review the results above.[/]\n")
    
    return all_passed


if __name__ == "__main__":
    success = validate_all()
    sys.exit(0 if success else 1)
