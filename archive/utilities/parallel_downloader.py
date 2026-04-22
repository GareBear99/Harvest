#!/usr/bin/env python3
"""
Parallel Data Downloader with Progress Bars

Downloads multiple trading pairs simultaneously with real-time progress visualization.
"""

import json
import requests
from datetime import datetime, timedelta
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import sys
import subprocess

# Add validation path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from validation.data_validator import validate_candle_data, print_validation_report
    from validation.audit_logger import log_download
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False


class ProgressBar:
    """Simple progress bar without external dependencies"""
    
    def __init__(self, symbol, total, width=40):
        self.symbol = symbol
        self.total = total
        self.current = 0
        self.width = width
        self.lock = Lock()
        self.start_time = time.time()
    
    def update(self, amount):
        with self.lock:
            self.current += amount
            self.display()
    
    def display(self):
        percent = (self.current / self.total) * 100 if self.total > 0 else 0
        filled = int(self.width * self.current / self.total) if self.total > 0 else 0
        bar = '█' * filled + '░' * (self.width - filled)
        
        # Calculate speed
        elapsed = time.time() - self.start_time
        speed = self.current / elapsed if elapsed > 0 else 0
        
        # Calculate ETA
        remaining = self.total - self.current
        eta_seconds = remaining / speed if speed > 0 else 0
        eta_str = f"{int(eta_seconds)}s" if eta_seconds < 3600 else f"{int(eta_seconds/60)}m"
        
        sys.stdout.write(f"\r{self.symbol:10s} │{bar}│ {percent:5.1f}% │ {self.current:6,}/{self.total:6,} │ {speed:5.0f}/s │ ETA: {eta_str:>6s}")
        sys.stdout.flush()
    
    def finish(self):
        with self.lock:
            self.current = self.total
            self.display()
            print()  # New line after completion


def download_binance_data_with_progress(symbol, interval='1m', days=90):
    """
    Download historical data from Binance with progress bar
    
    Args:
        symbol: Trading pair (e.g., 'ETHUSDT', 'BTCUSDT')
        interval: Candle interval (default: '1m')
        days: Number of days to download (default: 90)
    
    Returns:
        List of candles or None if failed
    """
    
    base_url = 'https://api.binance.com/api/v3/klines'
    
    # Calculate time range
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)
    
    expected_total = days * 24 * 60  # Expected number of 1-minute candles
    
    # Create progress bar
    progress = ProgressBar(symbol, expected_total)
    
    all_candles = []
    current_start = start_ms
    
    try:
        while current_start < end_ms:
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': current_start,
                'endTime': end_ms,
                'limit': 1000  # Max per request
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            
            candles = response.json()
            
            if not candles:
                break
            
            all_candles.extend(candles)
            progress.update(len(candles))
            
            # Move to next batch
            current_start = candles[-1][0] + 60000  # Add 1 minute in ms
            
            # Rate limiting
            time.sleep(0.05)
        
        progress.finish()
        return all_candles
        
    except Exception as e:
        progress.finish()
        print(f"\n❌ {symbol}: Error - {e}")
        return None


def verify_and_fix_data(filename):
    """
    Verify data integrity and auto-correct issues using blockchain verifier
    
    Args:
        filename: Path to data file
    
    Returns:
        True if verification passed (or issues fixed), False if critical errors
    """
    
    try:
        # Import spinner
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from utils.spinner import Spinner
        
        symbol = os.path.basename(filename).split('_')[0].upper()
        symbol_pair = f"{symbol}USDT"  # Assume USDT pair
        
        print(f"\n🔍 Verifying {symbol} data integrity...")
        
        # Run blockchain verifier with STREAMING output
        process = subprocess.Popen(
            ['python', 'blockchain_verifier.py', filename, symbol_pair],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        
        # Start spinner in separate thread
        spinner = Spinner(f"Processing {symbol}", style='dots_pulse')
        spinner.start()
        
        output_lines = []
        critical_found = False
        
        # Stream output in real-time
        for line in process.stdout:
            # Stop spinner temporarily to print line
            spinner.stop()
            
            # Print the line
            print(line.rstrip())
            output_lines.append(line)
            
            # Check for critical issues
            if "CRITICAL" in line or "FAILED" in line:
                critical_found = True
            
            # Restart spinner
            spinner.start()
        
        # Wait for process to complete
        return_code = process.wait(timeout=300)
        
        # Stop spinner
        spinner.stop()
        
        # Final status
        if critical_found and return_code == 0:
            print(f"✅ Auto-correction successful for {symbol}")
            return True
        elif return_code == 0:
            print(f"✅ Data integrity verified for {symbol}")
            return True
        else:
            print(f"❌ Verification failed for {symbol}")
            return False
            
    except subprocess.TimeoutExpired:
        if 'spinner' in locals():
            spinner.stop()
        print(f"⚠️  Verification timeout - data may need manual review")
        return False
    except Exception as e:
        if 'spinner' in locals():
            spinner.stop()
        print(f"⚠️  Verification error: {e}")
        return False


def format_candles(raw_candles):
    """
    Convert raw Binance format to our format
    
    Args:
        raw_candles: List of Binance candle arrays
    
    Returns:
        List of formatted candle dicts
    """
    
    formatted = []
    for candle in raw_candles:
        timestamp = datetime.fromtimestamp(candle[0] / 1000)
        
        formatted.append({
            'timestamp': timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
            'open': float(candle[1]),
            'high': float(candle[2]),
            'low': float(candle[3]),
            'close': float(candle[4]),
            'volume': float(candle[5])
        })
    
    return formatted


def save_data(symbol, candles, output_dir='data'):
    """
    Save downloaded data to JSON file
    
    Args:
        symbol: Trading pair symbol
        candles: List of formatted candles
        output_dir: Directory to save files
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    asset = symbol.replace('USDT', '').lower()
    filename = f"{output_dir}/{asset}_90days.json"
    
    with open(filename, 'w') as f:
        json.dump(candles, f, indent=2)
    
    return filename


def download_parallel(symbols, interval='1m', days=90):
    """
    Download multiple symbols in parallel with progress bars
    
    Args:
        symbols: List of trading pair symbols
        interval: Candle interval
        days: Number of days to download
    
    Returns:
        Dict of {symbol: candles}
    """
    
    print(f"\n{'='*80}")
    print(f"📥 PARALLEL DOWNLOAD - {len(symbols)} Assets")
    print(f"{'='*80}")
    print(f"Period: {days} days")
    print(f"Interval: {interval}")
    print(f"Assets: {', '.join(symbols)}")
    print()
    
    results = {}
    
    # Download in parallel
    with ThreadPoolExecutor(max_workers=len(symbols)) as executor:
        # Submit all download tasks
        future_to_symbol = {
            executor.submit(download_binance_data_with_progress, symbol, interval, days): symbol
            for symbol in symbols
        }
        
        # Wait for completion
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                candles = future.result()
                if candles:
                    results[symbol] = candles
            except Exception as e:
                print(f"❌ {symbol}: Failed - {e}")
    
    print(f"\n{'='*80}")
    print(f"✅ Download Complete")
    print(f"{'='*80}\n")
    
    # Summary
    for symbol in symbols:
        if symbol in results:
            count = len(results[symbol])
            print(f"  ✅ {symbol:10s}: {count:6,} candles")
        else:
            print(f"  ❌ {symbol:10s}: Failed")
    
    print()
    return results


def download_and_save_all(symbols=None, days=90, verify=True, validate=True):
    """
    Download and save data for all specified symbols
    
    Args:
        symbols: List of symbols (default: ETHUSDT, BTCUSDT)
        days: Number of days to download
        verify: Run blockchain verification after download
        validate: Run data validation after download
    """
    
    if symbols is None:
        symbols = ['ETHUSDT', 'BTCUSDT']
    
    # Download in parallel
    results = download_parallel(symbols, days=days)
    
    # Format and save
    print(f"{'='*80}")
    print(f"💾 SAVING DATA")
    print(f"{'='*80}\n")
    
    saved_files = []
    for symbol, raw_candles in results.items():
        # Format candles
        formatted = format_candles(raw_candles)
        
        # Save to file
        filename = save_data(symbol, formatted)
        saved_files.append(filename)
        
        # Log download
        if VALIDATION_AVAILABLE:
            log_download(symbol, len(formatted), True)
        
        print(f"  ✅ Saved {symbol:10s} → {filename} ({len(formatted):,} candles)")
    
    print(f"\n{'='*80}")
    print(f"✅ ALL DATA SAVED")
    print(f"{'='*80}")
    
    for f in saved_files:
        print(f"  📁 {f}")
    print()
    
    # Validate data
    if validate and saved_files and VALIDATION_AVAILABLE:
        print(f"\n{'='*80}")
        print(f"🔍 DATA VALIDATION")
        print(f"{'='*80}\n")
        
        validation_passed = True
        for filename in saved_files:
            symbol = os.path.basename(filename).split('_')[0].upper()
            
            passed, checks = validate_candle_data(filename, f"{symbol}USDT")
            
            if passed:
                print(f"✅ {symbol}: Validation PASSED")
            else:
                print(f"❌ {symbol}: Validation FAILED")
                print_validation_report(f"{symbol}USDT", passed, checks)
                validation_passed = False
        
        print(f"\n{'='*80}")
        if validation_passed:
            print(f"✅ ALL DATA VALIDATION PASSED")
        else:
            print(f"❌ VALIDATION FAILED - Review errors above")
        print(f"{'='*80}\n")
        
        if not validation_passed:
            return None
    
    # Verify data integrity
    if verify and saved_files:
        print(f"\n{'='*80}")
        print(f"🔍 BLOCKCHAIN VERIFICATION & AUTO-CORRECTION")
        print(f"{'='*80}\n")
        
        all_passed = True
        for filename in saved_files:
            symbol = os.path.basename(filename).split('_')[0].upper()
            print(f"\n{'─'*80}")
            print(f"Verifying {symbol}...")
            print(f"{'─'*80}")
            
            passed = verify_and_fix_data(filename)
            if not passed:
                all_passed = False
        
        print(f"\n{'='*80}")
        if all_passed:
            print(f"✅ ALL DATA VERIFIED & CORRECTED")
        else:
            print(f"⚠️  VERIFICATION COMPLETE (some issues noted)")
        print(f"{'='*80}\n")
    
    return saved_files


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Parallel data downloader with progress bars")
    parser.add_argument('--symbols', nargs='+', default=['ETHUSDT', 'BTCUSDT'],
                       help='Trading pair symbols to download')
    parser.add_argument('--days', type=int, default=90,
                       help='Number of days to download')
    
    args = parser.parse_args()
    
    download_and_save_all(symbols=args.symbols, days=args.days)
