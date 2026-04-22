#!/usr/bin/env python3
"""Download 21 days of 1-minute data for ETH and BTC."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.data_ingestion import DataIngestion
from datetime import datetime, timedelta
import json

def download_21days(symbol: str):
    """Download 21 days of 1-minute data."""
    print(f'\nDownloading 21 days of {symbol} 1-minute data...')
    data_ingestion = DataIngestion(symbol)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=21)
    
    all_candles = []
    current_start = start_time
    request_count = 0
    
    while current_start < end_time and request_count < 45:
        request_count += 1
        print(f'Request {request_count}: {current_start.strftime("%Y-%m-%d %H:%M")}...', end=' ')
        try:
            candles = data_ingestion.fetch_klines(
                interval='1m',
                limit=1000,
                start_time=current_start
            )
            if not candles:
                print('No data')
                break
            all_candles.extend(candles)
            print(f'{len(candles)} candles')
            current_start = candles[-1].timestamp + timedelta(minutes=1)
            if candles[-1].timestamp >= end_time:
                break
        except Exception as e:
            print(f'Error: {e}')
            break
    
    print(f'\nTotal: {len(all_candles):,} candles')
    
    # Save to file
    os.makedirs('data', exist_ok=True)
    filename = f'data/{symbol.lower().replace("usdt", "")}_21days.json'
    
    data_dict = {
        'symbol': symbol,
        'interval': '1m',
        'candle_count': len(all_candles),
        'start_time': all_candles[0].timestamp.isoformat() if all_candles else None,
        'end_time': all_candles[-1].timestamp.isoformat() if all_candles else None,
        'candles': [
            {
                'timestamp': c.timestamp.isoformat(),
                'open': c.open,
                'high': c.high,
                'low': c.low,
                'close': c.close,
                'volume': c.volume
            }
            for c in all_candles
        ]
    }
    
    with open(filename, 'w') as f:
        json.dump(data_dict, f)
    
    file_size_mb = os.path.getsize(filename) / (1024 * 1024)
    
    if all_candles:
        closes = [c.close for c in all_candles]
        price_change = ((closes[-1] / closes[0]) - 1) * 100
        print(f'{symbol}: ${closes[0]:.2f} → ${closes[-1]:.2f} ({price_change:+.2f}%)')
    
    print(f'Saved to {filename} ({file_size_mb:.2f} MB)')
    return len(all_candles)

if __name__ == '__main__':
    print('='*70)
    print('21-DAY DATA DOWNLOADER')
    print('='*70)
    
    # Download ETH
    eth_candles = download_21days('ETHUSDT')
    
    # Download BTC
    btc_candles = download_21days('BTCUSDT')
    
    print('\n' + '='*70)
    print('✅ DOWNLOAD COMPLETE')
    print('='*70)
    print(f'\nETH: {eth_candles:,} candles')
    print(f'BTC: {btc_candles:,} candles')
    print('\nReady for aggressive backtesting!')
