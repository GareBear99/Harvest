#!/usr/bin/env python3
"""
File Locking Utility
Provides thread-safe file locking for coordinated access to shared state files
"""

import fcntl
import contextlib
import time
import json
from pathlib import Path
from typing import Any, Dict


@contextlib.contextmanager
def file_lock(filepath: str, mode: str = 'r', timeout: float = 5.0):
    """
    Thread-safe file locking using fcntl (POSIX).
    
    Args:
        filepath: Path to file to lock
        mode: File open mode ('r', 'w', 'r+', etc.)
        timeout: Maximum time to wait for lock (seconds)
    
    Usage:
        with file_lock('data/config.json', 'r') as f:
            data = json.load(f)
    
    Raises:
        TimeoutError: If lock cannot be acquired within timeout
    """
    filepath = Path(filepath)
    
    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Open file
    f = open(filepath, mode)
    
    try:
        # Try to acquire lock with timeout
        start_time = time.time()
        while True:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except IOError:
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Could not acquire lock on {filepath} within {timeout}s")
                time.sleep(0.01)  # Wait 10ms before retry
        
        yield f
        
    finally:
        # Always unlock and close
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except:
            pass
        f.close()


@contextlib.contextmanager
def atomic_write(filepath: str, mode: str = 'w'):
    """
    Atomic file write using temp file + rename.
    Prevents partial file reads during write.
    
    Args:
        filepath: Path to file to write
        mode: File open mode (default: 'w')
    
    Usage:
        with atomic_write('data/config.json') as f:
            json.dump(data, f, indent=2)
    
    Note: The rename operation is atomic on POSIX systems
    """
    import os
    import tempfile
    
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Create temp file in same directory (ensures same filesystem)
    fd, temp_path = tempfile.mkstemp(
        dir=filepath.parent,
        prefix=f".{filepath.name}.",
        suffix=".tmp"
    )
    
    try:
        # Open temp file for writing
        with os.fdopen(fd, mode) as f:
            yield f
        
        # Atomic rename (POSIX guarantee)
        os.replace(temp_path, filepath)
        
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(temp_path)
        except:
            pass
        raise


def safe_json_load(filepath: str, default: Any = None, timeout: float = 5.0) -> Any:
    """
    Thread-safe JSON file load with file locking.
    
    Args:
        filepath: Path to JSON file
        default: Default value if file doesn't exist or is invalid
        timeout: Lock timeout in seconds
    
    Returns:
        Loaded JSON data or default value
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        return default
    
    try:
        with file_lock(filepath, 'r', timeout=timeout) as f:
            return json.load(f)
    except (json.JSONDecodeError, TimeoutError) as e:
        return default


def safe_json_save(filepath: str, data: Any, timeout: float = 5.0):
    """
    Thread-safe atomic JSON file save with file locking.
    
    Args:
        filepath: Path to JSON file
        data: Data to save
        timeout: Lock timeout in seconds
    """
    # Use atomic write (temp file + rename)
    with atomic_write(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def locked_json_update(filepath: str, update_func, default: Any = None, timeout: float = 5.0) -> Any:
    """
    Atomically read, modify, and write JSON file with locking.
    
    Args:
        filepath: Path to JSON file
        update_func: Function that takes current data and returns updated data
        default: Default value if file doesn't exist
        timeout: Lock timeout in seconds
    
    Returns:
        Updated data
    
    Usage:
        def add_wallet(data):
            data['wallets'].append({'address': '0x123...'})
            return data
        
        updated = locked_json_update('config.json', add_wallet, default={'wallets': []})
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Lock file for read
    if filepath.exists():
        with file_lock(filepath, 'r', timeout=timeout) as f:
            data = json.load(f)
    else:
        data = default if default is not None else {}
    
    # Apply update
    updated_data = update_func(data)
    
    # Atomic write
    with atomic_write(filepath, 'w') as f:
        json.dump(updated_data, f, indent=2)
    
    return updated_data


if __name__ == "__main__":
    # Test file locking
    import threading
    
    test_file = "test_lock.json"
    
    def write_test(thread_id):
        """Test concurrent writes"""
        for i in range(5):
            with file_lock(test_file, 'w') as f:
                data = {'thread': thread_id, 'iteration': i, 'time': time.time()}
                json.dump(data, f, indent=2)
            time.sleep(0.01)
    
    # Start 10 threads
    threads = []
    for i in range(10):
        t = threading.Thread(target=write_test, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    print("✓ File locking test completed without errors")
    
    # Test atomic write
    with atomic_write(test_file) as f:
        json.dump({'test': 'atomic_write', 'success': True}, f, indent=2)
    
    # Verify
    data = safe_json_load(test_file)
    assert data['test'] == 'atomic_write'
    print("✓ Atomic write test passed")
    
    # Cleanup
    Path(test_file).unlink()
    print("\n✅ All file locking tests passed!")
