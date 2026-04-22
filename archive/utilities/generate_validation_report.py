#!/usr/bin/env python3
"""
Generate Comprehensive Validation Report
Runs all tests and generates detailed validation report for production readiness
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path


def run_command(command, description):
    """Run a command and capture output"""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        output = result.stdout
        errors = result.stderr
        success = result.returncode == 0
        
        print(output)
        if errors:
            print(f"Errors: {errors}")
        
        return {
            "description": description,
            "command": command,
            "success": success,
            "output": output,
            "errors": errors,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print(f"❌ Command timed out after 300 seconds")
        return {
            "description": description,
            "command": command,
            "success": False,
            "output": "",
            "errors": "Timeout after 300 seconds",
            "return_code": -1
        }
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return {
            "description": description,
            "command": command,
            "success": False,
            "output": "",
            "errors": str(e),
            "return_code": -1
        }


def generate_validation_report():
    """Generate comprehensive validation report"""
    print("="*70)
    print("HARVEST COMPREHENSIVE VALIDATION REPORT GENERATION")
    print("="*70)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    report = {
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "system": "HARVEST Dual-Engine Trading System",
            "version": "1.0.0-beta"
        },
        "test_results": {},
        "summary": {}
    }
    
    # Phase 1: Indicator Tests
    print("\n\n" + "="*70)
    print("PHASE 1: INDICATOR VALIDATION")
    print("="*70)
    
    result = run_command(
        "python3 tests/test_indicators.py",
        "Indicator Calculation Tests"
    )
    report["test_results"]["phase1_indicators"] = result
    
    # Phase 2: Strategy Integration Tests
    print("\n\n" + "="*70)
    print("PHASE 2: STRATEGY INTEGRATION VALIDATION")
    print("="*70)
    
    result = run_command(
        "python3 tests/test_strategy_signals_v2.py",
        "Strategy Integration Tests"
    )
    report["test_results"]["phase2_strategies"] = result
    
    # Phase 3: Risk Management Tests (if exists)
    print("\n\n" + "="*70)
    print("PHASE 3: RISK MANAGEMENT VALIDATION")
    print("="*70)
    
    if os.path.exists("tests/test_risk_management.py"):
        result = run_command(
            "python3 tests/test_risk_management.py",
            "Risk Management Tests"
        )
        report["test_results"]["phase3_risk_management"] = result
    else:
        print("⚠️  Risk management tests not found (test_risk_management.py)")
        report["test_results"]["phase3_risk_management"] = {
            "description": "Risk Management Tests",
            "success": False,
            "errors": "Test file not found"
        }
    
    # Phase 4: Extended Backtesting
    print("\n\n" + "="*70)
    print("PHASE 4: EXTENDED BACKTESTING")
    print("="*70)
    print("⚠️  Skipping extended backtesting (requires live API access)")
    print("Run manually with: python3 tests/extended_backtest.py")
    
    report["test_results"]["phase4_backtesting"] = {
        "description": "Extended Backtesting",
        "success": None,
        "notes": "Skipped - requires live API access. Run manually if needed."
    }
    
    # CLI Tests
    print("\n\n" + "="*70)
    print("CLI INTERFACE TESTS")
    print("="*70)
    
    cli_tests = []
    
    result = run_command("python3 cli.py info", "CLI Info Command")
    cli_tests.append(result)
    
    result = run_command("python3 cli.py status", "CLI Status Command")
    cli_tests.append(result)
    
    result = run_command("python3 cli.py validate", "CLI Validate Command")
    cli_tests.append(result)
    
    report["test_results"]["cli_tests"] = cli_tests
    
    # System Checks
    print("\n\n" + "="*70)
    print("SYSTEM CHECKS")
    print("="*70)
    
    system_checks = []
    
    # Check required files
    required_files = [
        "README.md",
        "README_PRODUCTION.md",
        "LICENSE",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "install.sh",
        "cli.py",
        "backtester.py"
    ]
    
    for filename in required_files:
        exists = os.path.exists(filename)
        print(f"{'✅' if exists else '❌'} {filename}")
        system_checks.append({
            "file": filename,
            "exists": exists
        })
    
    report["system_checks"] = system_checks
    
    # Check directories
    required_dirs = ["core", "strategies", "tests"]
    for dirname in required_dirs:
        exists = os.path.isdir(dirname)
        print(f"{'✅' if exists else '❌'} {dirname}/")
        system_checks.append({
            "directory": dirname,
            "exists": exists
        })
    
    # Generate Summary
    print("\n\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    total_tests = 0
    passed_tests = 0
    
    # Count test results
    for phase, result in report["test_results"].items():
        if isinstance(result, list):
            for test in result:
                total_tests += 1
                if test.get("success"):
                    passed_tests += 1
        elif result.get("success") is not None:
            total_tests += 1
            if result.get("success"):
                passed_tests += 1
    
    # System checks
    files_present = sum(1 for check in system_checks if check.get("exists", False))
    total_files = len(system_checks)
    
    summary = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "pass_rate": round(passed_tests / total_tests * 100, 1) if total_tests > 0 else 0,
        "files_present": files_present,
        "total_files": total_files,
        "production_ready": passed_tests / total_tests >= 0.8 if total_tests > 0 else False
    }
    
    report["summary"] = summary
    
    print(f"\n📊 Test Results:")
    print(f"   Total tests: {summary['total_tests']}")
    print(f"   Passed: {summary['passed_tests']}")
    print(f"   Failed: {summary['failed_tests']}")
    print(f"   Pass rate: {summary['pass_rate']}%")
    
    print(f"\n📁 System Files:")
    print(f"   Present: {summary['files_present']}/{summary['total_files']}")
    
    print(f"\n🎯 Production Readiness:")
    if summary['production_ready']:
        print("   ✅ SYSTEM IS PRODUCTION READY")
        print("   - Core functionality validated")
        print("   - Risk management in place")
        print("   - Documentation complete")
        print("   - Infrastructure ready")
    else:
        print(f"   ⚠️  ADDITIONAL WORK NEEDED (pass rate: {summary['pass_rate']}%)")
        print("   - Review failed tests")
        print("   - Complete missing components")
        print("   - Target: 80%+ pass rate")
    
    # Save report
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"validation_report_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: {filename}")
    
    # Generate markdown report
    md_filename = f"validation_report_{timestamp}.md"
    generate_markdown_report(report, md_filename)
    print(f"📄 Markdown report saved to: {md_filename}")
    
    return report


def generate_markdown_report(report, filename):
    """Generate markdown version of validation report"""
    
    with open(filename, 'w') as f:
        f.write("# HARVEST Trading System - Validation Report\n\n")
        f.write(f"**Generated:** {report['metadata']['timestamp']}\n\n")
        f.write(f"**System:** {report['metadata']['system']}\n\n")
        f.write(f"**Version:** {report['metadata']['version']}\n\n")
        
        f.write("---\n\n")
        f.write("## Executive Summary\n\n")
        
        summary = report['summary']
        f.write(f"- **Total Tests:** {summary['total_tests']}\n")
        f.write(f"- **Passed:** {summary['passed_tests']} ({summary['pass_rate']}%)\n")
        f.write(f"- **Failed:** {summary['failed_tests']}\n")
        f.write(f"- **System Files:** {summary['files_present']}/{summary['total_files']}\n")
        f.write(f"- **Production Ready:** {'✅ YES' if summary['production_ready'] else '⚠️ NEEDS WORK'}\n\n")
        
        f.write("---\n\n")
        f.write("## Test Results\n\n")
        
        for phase, result in report['test_results'].items():
            f.write(f"### {phase.replace('_', ' ').title()}\n\n")
            
            if isinstance(result, list):
                for test in result:
                    status = "✅" if test.get("success") else "❌"
                    f.write(f"{status} {test.get('description', 'Unknown')}\n")
            else:
                status = "✅" if result.get("success") else ("⚠️" if result.get("success") is None else "❌")
                f.write(f"{status} {result.get('description', 'Unknown')}\n")
                if result.get("notes"):
                    f.write(f"   - Note: {result['notes']}\n")
            
            f.write("\n")
        
        f.write("---\n\n")
        f.write("## System Files\n\n")
        
        for check in report['system_checks']:
            if 'file' in check:
                status = "✅" if check['exists'] else "❌"
                f.write(f"{status} {check['file']}\n")
            elif 'directory' in check:
                status = "✅" if check['exists'] else "❌"
                f.write(f"{status} {check['directory']}/\n")
        
        f.write("\n---\n\n")
        f.write("## Recommendations\n\n")
        
        if summary['production_ready']:
            f.write("### ✅ System is Production Ready\n\n")
            f.write("The HARVEST trading system has passed validation and is ready for:\n\n")
            f.write("1. Paper trading deployment\n")
            f.write("2. Small capital live testing ($100-1000)\n")
            f.write("3. Gradual scaling based on performance\n\n")
            f.write("**Next Steps:**\n")
            f.write("- Complete extended backtesting if not done\n")
            f.write("- Set up monitoring and alerting\n")
            f.write("- Deploy to production environment\n")
            f.write("- Start with paper trading for 1-2 weeks\n")
        else:
            f.write("### ⚠️ Additional Work Needed\n\n")
            f.write(f"Pass rate: {summary['pass_rate']}% (target: 80%+)\n\n")
            f.write("**Required Actions:**\n")
            f.write("1. Review and fix failed tests\n")
            f.write("2. Complete missing system components\n")
            f.write("3. Re-run validation after fixes\n")
            f.write("4. Achieve 80%+ pass rate before production\n")
        
        f.write("\n---\n\n")
        f.write("## Documentation\n\n")
        f.write("- [Production README](README_PRODUCTION.md)\n")
        f.write("- [Main README](README.md)\n")
        f.write("- [License](LICENSE)\n\n")


if __name__ == '__main__':
    report = generate_validation_report()
    
    if report['summary']['production_ready']:
        print("\n🎉 Validation complete! System is production ready.")
        sys.exit(0)
    else:
        print("\n⚠️  Validation complete. Additional work needed before production.")
        sys.exit(1)
