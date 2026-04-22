#!/usr/bin/env python3
"""
Validate Grid Search Configuration

Ensures that:
1. Parameter grid covers BASE_STRATEGY values
2. Grid search will test all relevant parameter combinations
3. Total combination count is correct
"""

import sys
sys.path.insert(0, '.')

from grid_search_all_strategies import PARAMETER_GRID
from ml.base_strategy import BASE_STRATEGY


def validate_parameter_coverage():
    """Verify that BASE_STRATEGY values are covered in parameter grid"""
    
    print("\n" + "="*80)
    print("🔍 PARAMETER GRID VALIDATION")
    print("="*80 + "\n")
    
    all_valid = True
    
    for timeframe in ['15m', '1h', '4h']:
        print(f"\n📊 Timeframe: {timeframe}")
        print("-" * 40)
        
        base = BASE_STRATEGY[timeframe]
        
        for param, base_value in base.items():
            if param == 'min_roc':  # Skip min_roc (constant)
                continue
            
            if param not in PARAMETER_GRID:
                print(f"  ❌ {param}: NOT IN GRID")
                all_valid = False
                continue
            
            grid_values = PARAMETER_GRID[param]
            
            # Check if base value is in grid or very close to one
            in_grid = any(abs(base_value - gv) < 0.01 for gv in grid_values)
            
            # Check range
            min_grid = min(grid_values)
            max_grid = max(grid_values)
            in_range = min_grid <= base_value <= max_grid
            
            status = "✅" if (in_grid or in_range) else "⚠️"
            coverage = "IN GRID" if in_grid else f"IN RANGE ({min_grid} - {max_grid})"
            
            print(f"  {status} {param:18s}: {base_value:6.2f} - {coverage}")
            
            if not (in_grid or in_range):
                all_valid = False
                print(f"      WARNING: Base value {base_value} outside grid range!")
    
    return all_valid


def calculate_total_combinations():
    """Calculate and display total combinations"""
    
    print(f"\n{'='*80}")
    print("📈 GRID SEARCH SCOPE")
    print(f"{'='*80}\n")
    
    total = 1
    print("Parameter Grid:")
    for param, values in PARAMETER_GRID.items():
        count = len(values)
        total *= count
        print(f"  {param:18s}: {count:3d} values  {values}")
    
    print(f"\n🎯 Total Combinations: {total:,}")
    
    # Estimate time
    seconds_per_strategy = 0.5  # Rough estimate
    total_seconds = total * seconds_per_strategy
    hours = total_seconds / 3600
    
    print(f"\n⏱️  Estimated Time:")
    print(f"   {seconds_per_strategy} seconds/strategy")
    print(f"   Total: {total_seconds:,.0f} seconds ({hours:.1f} hours)")
    
    return total


def compare_with_base_strategy():
    """Show how BASE_STRATEGY compares to grid"""
    
    print(f"\n{'='*80}")
    print("📋 BASE_STRATEGY REFERENCE")
    print(f"{'='*80}\n")
    
    for tf in ['15m', '1h', '4h']:
        print(f"{tf}:")
        for param, value in BASE_STRATEGY[tf].items():
            print(f"  {param:18s}: {value}")
        print()


def verify_grid_search_script():
    """Verify grid search script exists and looks correct"""
    
    print(f"\n{'='*80}")
    print("🔧 GRID SEARCH SCRIPT VALIDATION")
    print(f"{'='*80}\n")
    
    import os
    
    script = 'grid_search_all_strategies.py'
    
    if not os.path.exists(script):
        print(f"❌ {script} not found")
        return False
    
    print(f"✅ {script} exists")
    
    # Check data file path
    with open(script, 'r') as f:
        content = f.read()
    
    if '_90days.json' in content:
        print(f"✅ Uses 90-day data files")
    elif '_21days.json' in content:
        print(f"⚠️  Uses 21-day data files (should use 90-day)")
        print(f"   Update line: data_file = f\"data/{{args.asset.lower()}}_90days.json\"")
    
    # Check if it imports correctly
    try:
        import grid_search_all_strategies
        print(f"✅ Script imports successfully")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True


def main():
    print("\n" + "="*80)
    print("🎯 GRID SEARCH VALIDATION SUITE")
    print("="*80)
    
    # Run all validations
    param_valid = validate_parameter_coverage()
    total_combos = calculate_total_combinations()
    compare_with_base_strategy()
    script_valid = verify_grid_search_script()
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 VALIDATION SUMMARY")
    print(f"{'='*80}\n")
    
    checks = [
        ("Parameter Coverage", param_valid),
        ("Grid Search Script", script_valid),
        ("Total Combinations", total_combos == 121500)  # Expected
    ]
    
    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status:10s} {check_name}")
    
    all_passed = all(c[1] for c in checks)
    
    print(f"\n{'='*80}")
    if all_passed:
        print("✅ ALL VALIDATIONS PASSED")
        print("="*80)
        print("\n🚀 Grid search is ready to run!")
        print("\nRun:")
        print("  python run_complete_optimization.py --asset ETH --timeframe 15m")
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("="*80)
        print("\nPlease fix the issues above before running grid search.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
