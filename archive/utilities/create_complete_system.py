#!/usr/bin/env python3
"""
Create backtest_90_complete.py with full integration
"""

# Read validated base
with open('backtest_multi_timeframe.py', 'r') as f:
    base_lines = f.readlines()

# Read additions
with open('backtest_90_additions.py', 'r') as f:
    additions_content = f.read()

# Extract the enhanced check_entry_opportunity method
check_start = additions_content.find('def check_entry_opportunity(')
check_end = additions_content.find('\ndef print_enhanced_results(')
enhanced_check = additions_content[check_start:check_end].strip()

# Extract validate method  
validate_start = additions_content.find('def _validate_pnl_calculation(')
validate_end = additions_content.find('\ndef check_entry_opportunity(')
validate_method = additions_content[validate_start:validate_end].strip()

# Step 1: Update imports (find line with "from analysis.ml_confidence_model")
for i, line in enumerate(base_lines):
    if 'from analysis.ml_confidence_model import' in line:
        # Add new imports after this line
        base_lines[i] = line.rstrip() + '\n'
        base_lines.insert(i+1, 'from analysis.prediction_tracker import PredictionTracker\n')
        base_lines.insert(i+2, 'from analysis.high_accuracy_filter import HighAccuracyFilter, get_position_size_multiplier\n')
        base_lines.insert(i+3, 'from datetime import datetime\n')
        base_lines.insert(i+4, 'from collections import defaultdict\n')
        break

# Step 2: Update confidence thresholds to 0.85
for i, line in enumerate(base_lines):
    if "'confidence_threshold': 0.75" in line:
        base_lines[i] = line.replace('0.75', '0.85  # RAISED for 90% win rate')

# Step 3: Add initialization in __init__
for i, line in enumerate(base_lines):
    if 'self.leverage_scaler = LeverageScaler()' in line:
        base_lines.insert(i+1, '        self.prediction_tracker = PredictionTracker()\n')
        base_lines.insert(i+2, '        self.high_accuracy_filter = HighAccuracyFilter()\n')
        break

# Step 4: Add tracking dicts after self.all_trades = []
for i, line in enumerate(base_lines):
    if 'self.all_trades = []' in line:
        base_lines.insert(i+1, '        self.daily_profits = defaultdict(lambda: {\'pnl\': 0.0, \'trades\': 0, \'wins\': 0})\n')
        base_lines.insert(i+2, '        self.trade_durations = {\'15m\': [], \'1h\': [], \'4h\': []}\n')
        base_lines.insert(i+3, '        self.calculation_checks = []\n')
        break

# Step 5: Find and replace check_entry_opportunity
check_entry_start = None
for i, line in enumerate(base_lines):
    if 'def check_entry_opportunity(self, minute_index: int, timeframe: str):' in line:
        check_entry_start = i
        break

if check_entry_start:
    # Find end of method (next def or run method)
    check_entry_end = None
    for i in range(check_entry_start + 1, len(base_lines)):
        if base_lines[i].startswith('    def run(self):'):
            check_entry_end = i
            break
    
    # Replace method
    if check_entry_end:
        # Remove old method
        del base_lines[check_entry_start:check_entry_end]
        
        # Insert new method with proper indentation
        enhanced_lines = enhanced_check.split('\n')
        for j, method_line in enumerate(enhanced_lines):
            if j == 0:
                base_lines.insert(check_entry_start + j, '    ' + method_line + '\n')
            else:
                base_lines.insert(check_entry_start + j, '        ' + method_line + '\n')
        
        # Insert validate method before check_entry
        validate_lines = validate_method.split('\n')
        for j, val_line in enumerate(validate_lines):
            if j == 0:
                base_lines.insert(check_entry_start + j, '    ' + val_line + '\n')
            else:
                base_lines.insert(check_entry_start + j, '        ' + val_line + '\n')

# Write complete system
with open('backtest_90_complete.py', 'w') as f:
    f.writelines(base_lines)

print("✅ Created backtest_90_complete.py")
print("   - Enhanced imports")
print("   - Raised confidence to 0.85")
print("   - Added prediction tracker and filter")
print("   - Added daily/duration tracking")
print("   - Integrated enhanced check_entry_opportunity")
print("   - Added PnL validation method")
