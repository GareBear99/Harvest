# Status Bar System Guide

## Overview

The HARVEST dashboard features a comprehensive status tracking system that logs every keypress, validates commands, tracks operations, and provides detailed feedback on execution status. The status bar is displayed at the bottom of every screen (main dashboard and all modals).

## Features

### 1. **Real-Time Key Press Logging**
- Every keypress is logged with timestamp
- Immediate validation (✓ valid / ✗ invalid)
- History of last 5 commands preserved
- ESC sequences properly detected and displayed

### 2. **Operation Tracking**
- Start/processing/complete/failed states
- Detailed operation names and descriptions
- Error messages with full context
- Execution time tracking

### 3. **Visual Feedback**
Icons indicate current status:
- `ℹ️` **Ready** - Dashboard waiting for commands
- `⏳` **Processing** - Operation in progress
- `✅` **Success** - Operation completed successfully
- `❌` **Failed** - Operation failed with error

### 4. **Command History**
- Shows last 3 commands pressed
- Color-coded: green (valid), red (invalid)
- ESC sequences displayed as `\x1b` format
- Helps debug input issues

## Status Bar Sections

```
[ICON] Message │ Key: q ✓ │ Op: Refresh │ Hist: h, s, r
```

### Section Breakdown

1. **Icon + Message**: Current status and human-readable message
2. **Key**: Last keypress with validation indicator
3. **Op**: Current operation name (if processing)
4. **Hist**: Last 3 commands (color-coded)

## Status States

### Ready State
```
ℹ️  Dashboard ready. Press H for help. │ Key: None
```
- Initial state on startup
- Set after operations complete
- Cyan border color

### Processing State
```
⏳ Processing: Refresh │ Key: r ✓ │ Op: Refresh
```
- Operation started but not complete
- Yellow border color
- Shows operation name

### Success State
```
✅ Data refreshed successfully │ Key: r ✓ │ Hist: r, h, s
```
- Operation completed successfully
- Green border color
- Detailed success message

### Failed State
```
❌ Refresh failed │ Key: x ✗ │ Op: Refresh
```
- Operation failed with error
- Red border color
- Error details available

## Command Validation

### Valid Commands
Main dashboard:
- `Q` - Quit
- `R` - Refresh
- `H` - Help
- `S` - Seeds
- `B` - Backtest
- `M` - ML Control
- `D` - Documentation
- `W` - Wallet
- `L` - Live Mode
- `ESC` - Exit modal

All valid commands show ✓ indicator.

### Invalid Commands
Any other key shows ✗ indicator with message:
```
❌ Unknown command: 'x' - Press H for help │ Key: x ✗
```

## Implementation Details

### Status Dictionary Structure
```python
self.status = {
    'last_key': None,          # Last key pressed
    'key_valid': None,         # Boolean: valid/invalid
    'operation': None,         # Current operation name
    'result': 'ready',         # ready/processing/success/failed
    'message': 'Message',      # Human-readable status
    'details': None            # Error details or extra info
}
```

### Command History Structure
```python
self.command_history = [
    {
        'time': '08:52:28',
        'key': 'q',
        'valid': True
    },
    # ... up to 5 entries
]
```

### Key Methods

#### `log_key_press(key: str) -> bool`
Logs keypress and validates it:
```python
is_valid = dashboard.log_key_press('q')
# Returns: True
# Updates: status['last_key'], status['key_valid']
# Adds to: command_history
```

#### `start_operation(operation: str, details: str = None)`
Start tracking an operation:
```python
dashboard.start_operation("Refresh", "Manual refresh triggered")
# Sets: status['result'] = 'processing'
# Sets: status['operation'] = "Refresh"
# Sets: status['message'] = "Processing: Refresh"
```

#### `complete_operation(success: bool, message: str, details: str = None)`
Complete operation with result:
```python
dashboard.complete_operation(True, "Data refreshed successfully")
# Sets: status['result'] = 'success'
# Sets: status['message'] = message
# Updates: operation_status
```

#### `set_ready(message: str = "Dashboard ready")`
Reset to ready state:
```python
dashboard.set_ready()
# Sets: status['result'] = 'ready'
# Clears: status['operation']
```

## Usage Examples

### Example 1: Successful Operation
```python
def handle_key(self, key: str):
    is_valid = self.log_key_press(key)
    
    if key.lower() == 'r':
        self.start_operation("Refresh", "Manual refresh triggered")
        try:
            self.refresh_data()
            self.complete_operation(True, "Data refreshed successfully")
        except Exception as e:
            self.complete_operation(False, "Refresh failed", str(e))
```

Status bar progression:
1. `ℹ️  Dashboard ready │ Key: r ✓`
2. `⏳ Processing: Refresh │ Key: r ✓ │ Op: Refresh`
3. `✅ Data refreshed successfully │ Key: r ✓ │ Hist: r, ...`

### Example 2: Invalid Command
```python
# User presses 'x'
is_valid = dashboard.log_key_press('x')  # Returns False

if not is_valid:
    if len(key) == 1 and key.isprintable():
        self.status['message'] = f"Unknown command: '{key}' - Press H for help"
        self.status['result'] = 'failed'
```

Status bar:
```
❌ Unknown command: 'x' - Press H for help │ Key: x ✗
```

### Example 3: Modal Exit
```python
if key in ['\\x1b', 'escape'] or key.startswith('\\x1b'):
    self.start_operation(f"Close {self.active_modal}", "ESC pressed")
    self.active_modal = None
    self.complete_operation(True, f"Closed {self.active_modal} screen")
```

Status bar:
```
✅ Closed help screen │ Key: '\\x1b' ✓ │ Op: Close help
```

## Testing

Run comprehensive tests:
```bash
python3 test_status_tracking.py
```

Tests validate:
- ✅ Key press logging with validation
- ✅ Operation tracking (start/complete)
- ✅ Failure handling with error messages
- ✅ Status structure completeness
- ✅ History limit enforcement (max 5)
- ✅ Ready state management

## Debugging

### Check Status Bar State
```python
# In dashboard code, add:
print(f"Status: {dashboard.status}")
print(f"History: {dashboard.command_history}")
print(f"Operation: {dashboard.current_operation}")
```

### Common Issues

**Issue**: Keys not registering
- Check `select` timeout in `run_static()` (should be 0.05)
- Verify terminal is in raw mode
- Check ESC sequence reading logic

**Issue**: Status not updating
- Ensure `log_key_press()` called first in `handle_key()`
- Verify operation tracking calls are paired (start + complete)
- Check status dict has all required keys

**Issue**: History not showing
- Verify `command_history` list exists and populated
- Check max_history limit (default: 5)
- Ensure `log_key_press()` adds entries correctly

## Integration Points

### With Main Dashboard
- Called in `handle_key()` for every keypress
- Rendered in `render_panels()` for status panel
- Displayed in both main layout and modals

### With Modals
- Same status bar shown in all modals
- Modal-specific commands tracked
- ESC key handling tracked across all screens

### With Command Bar
- Command bar shows available commands
- Status bar shows execution results
- Both update in real-time

## Future Enhancements

1. **Expandable Details**
   - Press key to expand error details
   - Show full stack trace on demand

2. **Command Replay**
   - Replay last command with confirmation
   - History browser with selection

3. **Performance Metrics**
   - Operation execution time
   - Average response time tracking

4. **Export History**
   - Save command history to file
   - Generate debug reports

## Best Practices

1. **Always log keypresses first**
   ```python
   is_valid = self.log_key_press(key)
   # Then process the key
   ```

2. **Use operation tracking for async work**
   ```python
   self.start_operation("Long Task", "Details")
   # Do work...
   self.complete_operation(success, message, details)
   ```

3. **Provide detailed error messages**
   ```python
   except Exception as e:
       self.complete_operation(False, "Operation failed", str(e))
   ```

4. **Reset to ready state when done**
   ```python
   self.set_ready("Dashboard ready for next command")
   ```

## Summary

The status bar provides comprehensive feedback on every interaction:
- ✅ Real-time keypress validation
- ✅ Operation progress tracking
- ✅ Success/failure indication
- ✅ Command history preservation
- ✅ Detailed error reporting
- ✅ Visual icons for quick scanning
- ✅ Consistent across all screens

This makes the dashboard highly responsive and debuggable, with every action tracked and validated.
