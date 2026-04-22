#!/usr/bin/env python3
"""
Animated Spinner Utility

Provides loading animations for long-running operations.
"""

import sys
import time
import threading
from itertools import cycle


class Spinner:
    """
    Animated spinner for terminal
    
    Usage:
        with Spinner("Loading..."):
            # do work
            pass
    
    Or:
        spinner = Spinner("Processing")
        spinner.start()
        # do work
        spinner.stop()
    """
    
    # Different spinner styles
    STYLES = {
        'dots': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
        'line': ['|', '/', '-', '\\'],
        'arrows': ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
        'box': ['◰', '◳', '◲', '◱'],
        'circle': ['◐', '◓', '◑', '◒'],
        'dots_pulse': ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
        'clock': ['🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚', '🕛'],
        'moon': ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘'],
        'earth': ['🌍', '🌎', '🌏'],
        'bar': ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃', '▂'],
    }
    
    def __init__(self, message="Loading", style='dots', delay=0.1):
        """
        Initialize spinner
        
        Args:
            message: Text to display
            style: Spinner style (see STYLES)
            delay: Animation speed (seconds between frames)
        """
        self.message = message
        self.frames = cycle(self.STYLES.get(style, self.STYLES['dots']))
        self.delay = delay
        self.running = False
        self.thread = None
        self._stop_event = threading.Event()
    
    def _animate(self):
        """Animation loop"""
        while not self._stop_event.is_set():
            frame = next(self.frames)
            sys.stdout.write(f'\r{frame} {self.message}')
            sys.stdout.flush()
            time.sleep(self.delay)
    
    def start(self):
        """Start the spinner"""
        if not self.running:
            self.running = True
            self._stop_event.clear()
            self.thread = threading.Thread(target=self._animate, daemon=True)
            self.thread.start()
        return self
    
    def stop(self, final_message=None):
        """Stop the spinner"""
        if self.running:
            self._stop_event.set()
            if self.thread:
                self.thread.join()
            self.running = False
            
            # Clear the line
            sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
            
            # Print final message if provided
            if final_message:
                print(final_message)
            
            sys.stdout.flush()
    
    def update(self, message):
        """Update spinner message while running"""
        self.message = message
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is None:
            self.stop("✅ Complete")
        else:
            self.stop("❌ Failed")
        return False


class MultiSpinner:
    """
    Multiple spinners for parallel operations
    
    Usage:
        spinners = MultiSpinner()
        spinners.add("task1", "Downloading ETH")
        spinners.add("task2", "Downloading BTC")
        spinners.start()
        
        # Update individual spinners
        spinners.update("task1", "✅ ETH Complete")
        spinners.update("task2", "✅ BTC Complete")
        
        spinners.stop()
    """
    
    def __init__(self, style='dots', delay=0.1):
        self.spinners = {}
        self.style = style
        self.delay = delay
        self.running = False
        self.thread = None
        self._stop_event = threading.Event()
        self.frames = cycle(Spinner.STYLES.get(style, Spinner.STYLES['dots']))
    
    def add(self, key, message):
        """Add a new spinner"""
        self.spinners[key] = {'message': message, 'done': False}
    
    def update(self, key, message, done=False):
        """Update a spinner's message"""
        if key in self.spinners:
            self.spinners[key] = {'message': message, 'done': done}
    
    def _animate(self):
        """Animation loop for all spinners"""
        while not self._stop_event.is_set():
            frame = next(self.frames)
            
            # Move cursor to start
            sys.stdout.write('\r')
            
            # Clear lines
            for _ in self.spinners:
                sys.stdout.write('\033[K\n')
            
            # Move cursor back up
            if self.spinners:
                sys.stdout.write(f'\033[{len(self.spinners)}A')
            
            # Draw all spinners
            for key, data in self.spinners.items():
                icon = '✅' if data['done'] else frame
                sys.stdout.write(f'\r{icon} {data["message"]}\033[K\n')
            
            sys.stdout.flush()
            time.sleep(self.delay)
    
    def start(self):
        """Start all spinners"""
        if not self.running:
            self.running = True
            self._stop_event.clear()
            
            # Print initial lines
            for _ in self.spinners:
                print()
            
            self.thread = threading.Thread(target=self._animate, daemon=True)
            self.thread.start()
        return self
    
    def stop(self):
        """Stop all spinners"""
        if self.running:
            self._stop_event.set()
            if self.thread:
                self.thread.join()
            self.running = False
            sys.stdout.flush()


def loading_animation(message, duration=2, style='dots'):
    """
    Show a loading animation for a fixed duration
    
    Args:
        message: Text to display
        duration: How long to show (seconds)
        style: Spinner style
    """
    with Spinner(message, style=style):
        time.sleep(duration)


if __name__ == "__main__":
    # Demo different spinner styles
    print("Spinner Styles Demo\n")
    
    for style_name in ['dots', 'line', 'arrows', 'box', 'circle', 'dots_pulse']:
        with Spinner(f"Testing {style_name} style", style=style_name):
            time.sleep(2)
    
    print("\n✅ All styles demonstrated!")
    
    # Demo multi-spinner
    print("\nMulti-Spinner Demo\n")
    
    multi = MultiSpinner()
    multi.add("task1", "Downloading ETH...")
    multi.add("task2", "Downloading BTC...")
    multi.add("task3", "Verifying data...")
    multi.start()
    
    time.sleep(2)
    multi.update("task1", "ETH complete!", done=True)
    
    time.sleep(2)
    multi.update("task2", "BTC complete!", done=True)
    
    time.sleep(2)
    multi.update("task3", "Verification complete!", done=True)
    
    time.sleep(1)
    multi.stop()
    
    print("\n✅ Demo complete!")
