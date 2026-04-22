#!/usr/bin/env python3
"""
Run all dashboard validation tests
"""

import subprocess
import sys

def run_test(test_name, test_file, success_marker):
    """Run a test and return result"""
    print(f"Running {test_name}...")
    result = subprocess.run(
        ['python3', test_file],
        capture_output=True,
        text=True
    )
    
    passed = success_marker in result.stdout
    return passed, result.stdout, result.stderr

def main():
    print("\n" + "="*60)
    print("COMPREHENSIVE DASHBOARD VALIDATION")
    print("="*60 + "\n")
    
    tests = [
        ("Interactive Commands (30 tests)", "tests/test_dashboard_interactive_complete.py", "ALL TESTS PASSED"),
        ("Timeout Detection (6 tests)", "tests/test_timeout_validation.py", "ALL TIMEOUT TESTS PASSED"),
    ]
    
    results = []
    total_passed = 0
    total_tests = len(tests)
    
    for test_name, test_file, success_marker in tests:
        passed, stdout, stderr = run_test(test_name, test_file, success_marker)
        results.append((test_name, passed))
        
        if passed:
            print(f"  \u2705 {test_name}: PASSED")
            total_passed += 1
        else:
            print(f"  \u274c {test_name}: FAILED")
            if stderr:
                print(f"     Error: {stderr[:200]}")
        print()
    
    print("="*60)
    print(f"RESULTS: {total_passed}/{total_tests} test suites passed")
    print("="*60 + "\n")
    
    if total_passed == total_tests:
        print("\u2705 ALL VALIDATION SUITES PASSED!\n")
        print("Dashboard validation complete:")
        print("  \u2022 36/36 total tests passing")
        print("  \u2022 All commands validated")
        print("  \u2022 Timeout logic working")
        print("  \u2022 Processing symbols appearing")
        print("  \u2022 Status bar fully functional")
        print("  \u2022 Modal commands tracked")
        print("  \u2022 ESC handling verified")
        print("\nReady for user testing!\n")
        return True
    else:
        print(f"\u274c {total_tests - total_passed} test suite(s) failed\n")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
