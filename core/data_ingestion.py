"""Data ingestion module for fetching market data."""
import requests
from datetime import datetime, timedelta
from typing import List
import time

from .models import OHLCV


class DataIngestion:
    """Fetch OHLCV data from Binance public API."""
    
    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        self.base_url = "https://api.binance.com/api/v3"
    
    def fetch_klines(self, interval: str, limit: int = 1000, 
                     start_time: datetime = None, end_time: datetime = None) -> List[OHLCV]:
        """
        Fetch kline/candlestick data.
        
        Args:
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            limit: Number of candles to fetch (max 1000)
            start_time: Start time for historical data
            end_time: End time for historical data
        
        Returns:
            List of OHLCV objects
        """
        endpoint = f"{self.base_url}/klines"
        params = {
            "symbol": self.symbol,
            "interval": interval,
            "limit": min(limit, 1000)
        }
        
        if start_time:
            params["startTime"] = int(start_time.timestamp() * 1000)
        if end_time:
            params["endTime"] = int(end_time.timestamp() * 1000)
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            candles = []
            for kline in data:
                candle = OHLCV(
                    timestamp=datetime.fromtimestamp(kline[0] / 1000),
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5])
                )
                candles.append(candle)
            
            return candles
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return []
    
    def fetch_multiple_timeframes(self, days: int = 30) -> dict:
        """
        Fetch data for multiple timeframes.
        
        Args:
            days: Number of days of historical data
        
        Returns:
            Dictionary with timeframe keys and OHLCV lists as values
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        timeframes = {
            "5m": self.fetch_klines("5m", limit=1000, start_time=start_time, end_time=end_time),
            "1h": self.fetch_klines("1h", limit=1000, start_time=start_time, end_time=end_time),
            "4h": self.fetch_klines("4h", limit=1000, start_time=start_time, end_time=end_time),
        }
        
        # Add small delay to avoid rate limiting
        time.sleep(0.5)
        
        return timeframes
    
    def fetch_latest_price(self) -> float:
        """Fetch latest price for the symbol."""
        endpoint = f"{self.base_url}/ticker/price"
        params = {"symbol": self.symbol}
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data["price"])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching latest price: {e}")
            return 0.0
