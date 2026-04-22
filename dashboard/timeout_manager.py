#!/usr/bin/env python3
"""
Timeout Manager for Dashboard Operations
Handles timeouts, error recovery, and user feedback
"""

import time
import threading
import subprocess
from typing import Optional, Callable, Any
from datetime import datetime


class TimeoutManager:
    """Manages command execution with timeout and error handling"""
    
    def __init__(self, default_timeout: int = 300):
        """
        Initialize timeout manager
        
        Args:
            default_timeout: Default timeout in seconds (5 minutes)
        """
        self.default_timeout = default_timeout
        self.current_process = None
        self.is_running = False
        self.start_time = None
        self.result = None
        self.error = None
    
    def execute_with_timeout(
        self, 
        command: str, 
        timeout: Optional[int] = None,
        callback: Optional[Callable] = None
    ) -> dict:
        """
        Execute command with timeout
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds (uses default if None)
            callback: Optional callback for progress updates
        
        Returns:
            dict with 'status', 'output', 'error', 'duration'
        """
        timeout = timeout or self.default_timeout
        self.is_running = True
        self.start_time = time.time()
        self.result = None
        self.error = None
        
        try:
            # Start process
            self.current_process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait with timeout
            try:
                stdout, stderr = self.current_process.communicate(timeout=timeout)
                duration = time.time() - self.start_time
                
                self.result = {
                    'status': 'success',
                    'output': stdout,
                    'error': stderr if stderr else None,
                    'duration': duration,
                    'exit_code': self.current_process.returncode
                }
                
            except subprocess.TimeoutExpired:
                # Timeout occurred
                self.current_process.kill()
                duration = time.time() - self.start_time
                
                self.result = {
                    'status': 'timeout',
                    'output': None,
                    'error': f'Command timed out after {timeout} seconds',
                    'duration': duration,
                    'exit_code': -1
                }
        
        except Exception as e:
            duration = time.time() - self.start_time if self.start_time else 0
            
            self.result = {
                'status': 'error',
                'output': None,
                'error': str(e),
                'duration': duration,
                'exit_code': -1
            }
        
        finally:
            self.is_running = False
            self.current_process = None
        
        return self.result
    
    def cancel(self):
        """Cancel currently running process"""
        if self.current_process and self.is_running:
            try:
                self.current_process.kill()
                self.is_running = False
                return True
            except:
                return False
        return False
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time of current operation"""
        if self.start_time:
            return time.time() - self.start_time
        return 0.0
    
    def format_duration(self, seconds: float) -> str:
        """Format duration as human-readable string"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"


class ProgressSpinner:
    """Animated spinner for progress indication"""
    
    FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    def __init__(self, message: str = "Processing"):
        self.message = message
        self.is_running = False
        self.thread = None
        self.frame_index = 0
    
    def start(self):
        """Start spinner animation"""
        self.is_running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop spinner animation"""
        self.is_running = False
        if self.thread:
            self.thread.join()
    
    def _animate(self):
        """Animation loop"""
        while self.is_running:
            frame = self.FRAMES[self.frame_index % len(self.FRAMES)]
            print(f"\r{frame} {self.message}...", end='', flush=True)
            self.frame_index += 1
            time.sleep(0.1)
        print("\r" + " " * 80 + "\r", end='', flush=True)  # Clear line


def execute_backtest_with_progress(
    seed: Optional[int] = None,
    timeout: int = 600
) -> dict:
    """
    Execute backtest with progress indicator
    
    Args:
        seed: Optional seed for deterministic testing
        timeout: Timeout in seconds (default 10 minutes)
    
    Returns:
        dict with results
    """
    manager = TimeoutManager(default_timeout=timeout)
    
    # Build command
    cmd = "python backtest_90_complete.py --skip-check"
    if seed is not None:
        cmd += f" --seed {seed}"
    
    print(f"\n🔬 Starting backtest...")
    if seed:
        print(f"   Seed: {seed}")
    print(f"   Timeout: {manager.format_duration(timeout)}\n")
    
    # Start spinner
    spinner = ProgressSpinner("Running backtest")
    spinner.start()
    
    # Execute with timeout
    result = manager.execute_with_timeout(cmd, timeout=timeout)
    
    # Stop spinner
    spinner.stop()
    
    # Handle result
    if result['status'] == 'success':
        print(f"✅ Backtest completed in {manager.format_duration(result['duration'])}")
        return result
    
    elif result['status'] == 'timeout':
        print(f"\n⏱️  TIMEOUT: Backtest exceeded {manager.format_duration(timeout)}")
        print(f"   The operation was automatically cancelled.")
        return result
    
    else:  # error
        print(f"\n❌ ERROR: {result['error']}")
        return result


def execute_seed_test_with_progress(
    timeframe: str,
    test_type: str = 'top10',
    timeout: int = 900
) -> dict:
    """
    Execute seed testing with progress
    
    Args:
        timeframe: Timeframe to test (1m, 5m, 15m, 1h, 4h)
        test_type: 'top10' or 'all'
        timeout: Timeout in seconds (default 15 minutes)
    
    Returns:
        dict with results
    """
    manager = TimeoutManager(default_timeout=timeout)
    
    print(f"\n🌱 Generating seed test list for {timeframe}...")
    
    # Step 1: Generate test list
    cmd1 = f"python ml/seed_tester.py test-{test_type} {timeframe}"
    result1 = manager.execute_with_timeout(cmd1, timeout=60)
    
    if result1['status'] != 'success':
        print(f"❌ Failed to generate test list: {result1['error']}")
        return result1
    
    print(f"✅ Test list generated")
    
    # Step 2: Run tests
    test_file = f"ml/test_{test_type}_{timeframe}.json"
    cmd2 = f"python backtest_90_complete.py --test-seeds-file {test_file} --skip-check"
    
    print(f"\n🔬 Running seed tests...")
    print(f"   Timeout: {manager.format_duration(timeout)}\n")
    
    spinner = ProgressSpinner(f"Testing {test_type} seeds for {timeframe}")
    spinner.start()
    
    result2 = manager.execute_with_timeout(cmd2, timeout=timeout)
    
    spinner.stop()
    
    if result2['status'] == 'success':
        print(f"✅ Tests completed in {manager.format_duration(result2['duration'])}")
    elif result2['status'] == 'timeout':
        print(f"\n⏱️  TIMEOUT: Tests exceeded {manager.format_duration(timeout)}")
        print(f"   The operation was automatically cancelled.")
    else:
        print(f"\n❌ ERROR: {result2['error']}")
    
    return result2


def show_error_menu(error_type: str, error_msg: str) -> str:
    """
    Show error menu and get user choice
    
    Args:
        error_type: 'timeout' or 'error'
        error_msg: Error message
    
    Returns:
        User choice: 'retry', 'main', 'cancel'
    """
    print("\n" + "="*60)
    
    if error_type == 'timeout':
        print("⏱️  OPERATION TIMED OUT")
        print("="*60)
        print("\nThe operation took too long and was automatically cancelled.")
        print("This can happen with:")
        print("  • Large datasets")
        print("  • Many seeds to test")
        print("  • Slow system performance")
    else:
        print("❌ OPERATION FAILED")
        print("="*60)
        print(f"\nError: {error_msg}")
    
    print("\n" + "="*60)
    print("Options:")
    print("  [R] Retry with longer timeout")
    print("  [M] Return to main menu")
    print("  [C] Cancel operation")
    print("="*60)
    
    while True:
        choice = input("\nYour choice (R/M/C): ").strip().upper()
        if choice in ['R', 'M', 'C']:
            return {'R': 'retry', 'M': 'main', 'C': 'cancel'}[choice]
        print("Invalid choice. Please enter R, M, or C.")


def wait_for_user_acknowledgment(message: str = "Press ENTER to continue..."):
    """Wait for user to press ENTER"""
    input(f"\n{message}")


if __name__ == "__main__":
    # Test the timeout manager
    print("🧪 Testing Timeout Manager\n")
    
    # Test 1: Quick command
    print("Test 1: Quick command (should succeed)")
    manager = TimeoutManager()
    result = manager.execute_with_timeout("echo 'Hello'", timeout=5)
    print(f"Status: {result['status']}")
    print(f"Output: {result['output']}")
    print()
    
    # Test 2: Timeout
    print("Test 2: Long command (should timeout)")
    result = manager.execute_with_timeout("sleep 10", timeout=2)
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")
    print()
    
    # Test 3: Error
    print("Test 3: Invalid command (should error)")
    result = manager.execute_with_timeout("invalid_command_xyz", timeout=5)
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")
    print()
    
    print("✅ All tests completed")
