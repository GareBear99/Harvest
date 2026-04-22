#!/usr/bin/env python3
"""
Integrate enhanced methods into backtest_90_percent.py
"""

# Read the additional methods
with open('backtest_90_additions.py', 'r') as f:
    additions = f.read()

# Read the current backtest
with open('backtest_90_percent.py', 'r') as f:
    content = f.read()

# Find the location to insert new methods
insertion_point = content.find("    def check_entry_opportunity(self, minute_index: int, timeframe: str):")

if insertion_point > 0:
    # Extract the methods from additions
    methods_start = additions.find("def _validate_pnl_calculation")
    methods_code = additions[methods_start:]
    
    # Indent properly for class methods
    methods_code = '\n    ' + methods_code.replace('\ndef ', '\n    def ')
    
    # Find end of check_entry_opportunity (before run method)
    next_method = content.find("    def run(self):", insertion_point)
    
    # Insert before run()
    new_content = content[:insertion_point] + methods_code + '\n' + content[next_method:]
    
    # Replace print_results with print_enhanced_results call
    new_content = new_content.replace('self.print_results()', 'self.print_enhanced_results()')
    
    with open('backtest_90_percent.py', 'w') as f:
        f.write(new_content)
    
    print("Done! Successfully integrated all methods")
    print("Enhanced methods added:")
    print("  - _validate_pnl_calculation")
    print("  - check_entry_opportunity (with high accuracy filter + prediction tracking)")
    print("  - print_enhanced_results")
else:
    print("ERROR: Could not find insertion point")
