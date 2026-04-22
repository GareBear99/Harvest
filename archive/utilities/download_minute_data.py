#!/usr/bin/env python3
"""Download last 7 days of 1-minute data for accurate backtesting."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.data_ingestion import DataIngestion
from datetime import datetime, timedelta
import json

print('=' * 80)
print('DOWNLOADING LAST 7 DAYS OF 1-MINUTE DATA')
print('=' * 80)

symbol = "BTCUSDT"
data_ingestion = DataIngestion(symbol)

# Calculate date range (last 7 days)
end_time = datetime.utcnow()
start_time = end_time - timedelta(days=7)

print(f'\nSymbol: {symbol}')
print(f'Period: {start_time.strftime("%Y-%m-%d")} to {end_time.strftime("%Y-%m-%d")}')
print(f'Timeframe: 1 minute')
print(f'\nDownloading from Binance API...')

# Binance 1m data limit is 1000 candles per request
# 7 days = 7 * 24 * 60 = 10,080 minutes
# Need multiple requests

all_candles_1m = []
total_expected = 7 * 24 * 60

print(f'Expected candles: {total_expected:,}')
print('This will take multiple requests...\n')

# Download in chunks
current_start = start_time
request_count = 0
max_requests = 15  # 15 requests * 1000 = 15,000 candles (more than enough)

while current_start < end_time and request_count < max_requests:
    request_count += 1
    print(f'Request {request_count}: Fetching from {current_start.strftime("%Y-%m-%d %H:%M")}...', end=' ')
    
    try:
        # Fetch 1000 candles at a time
        candles = data_ingestion.fetch_klines(
            interval='1m',
            limit=1000,
            start_time=current_start
        )
        
        if not candles:
            print('No data returned')
            break
        
        all_candles_1m.extend(candles)
        print(f'Got {len(candles)} candles')
        
        # Move to next chunk (last timestamp + 1 minute)
        current_start = candles[-1].timestamp + timedelta(minutes=1)
        
        # Stop if we've reached current time
        if candles[-1].timestamp >= end_time:
            break
            
    except Exception as e:
        print(f'Error: {e}')
        break

print(f'\n{"=" * 80}')
print(f'DOWNLOAD COMPLETE')
print(f'{"=" * 80}')
print(f'\nTotal 1-minute candles: {len(all_candles_1m):,}')
print(f'Coverage: {len(all_candles_1m) / 60:.1f} hours')
print(f'Coverage: {len(all_candles_1m) / 1440:.1f} days')

if all_candles_1m:
    print(f'\nData range:')
    print(f'  First: {all_candles_1m[0].timestamp.strftime("%Y-%m-%d %H:%M")}')
    print(f'  Last: {all_candles_1m[-1].timestamp.strftime("%Y-%m-%d %H:%M")}')
    
    # Calculate some stats
    closes = [c.close for c in all_candles_1m]
    volumes = [c.volume for c in all_candles_1m]
    
    price_min = min(closes)
    price_max = max(closes)
    price_change = ((closes[-1] / closes[0]) - 1) * 100
    
    print(f'\nPrice stats:')
    print(f'  Start: ${closes[0]:,.2f}')
    print(f'  End: ${closes[-1]:,.2f}')
    print(f'  Min: ${price_min:,.2f}')
    print(f'  Max: ${price_max:,.2f}')
    print(f'  Change: {price_change:+.2f}%')
    print(f'  Range: {((price_max - price_min) / price_min) * 100:.2f}%')
    
    print(f'\nVolume stats:')
    print(f'  Average: {sum(volumes)/len(volumes):,.2f}')
    print(f'  Max: {max(volumes):,.2f}')

# Save to file
output_file = 'data/minute_data_7days.json'
os.makedirs('data', exist_ok=True)

print(f'\n{"=" * 80}')
print(f'SAVING DATA')
print(f'{"=" * 80}')

data_dict = {
    'symbol': symbol,
    'interval': '1m',
    'start_time': all_candles_1m[0].timestamp.isoformat() if all_candles_1m else None,
    'end_time': all_candles_1m[-1].timestamp.isoformat() if all_candles_1m else None,
    'candle_count': len(all_candles_1m),
    'candles': [
        {
            'timestamp': c.timestamp.isoformat(),
            'open': c.open,
            'high': c.high,
            'low': c.low,
            'close': c.close,
            'volume': c.volume
        }
        for c in all_candles_1m
    ]
}

with open(output_file, 'w') as f:
    json.dump(data_dict, f, indent=2)

file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
print(f'\nSaved to: {output_file}')
print(f'File size: {file_size_mb:.2f} MB')

print(f'\n{"=" * 80}')
print('✅ DATA READY FOR BACKTESTING')
print('=' * 80)
print(f'\nYou can now run accurate backtests on the last 7 days.')
print(f'Use this data to test all strategies on real minute-by-minute price action.')
print('=' * 80)
