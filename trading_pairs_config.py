#!/usr/bin/env python3
"""
Trading Pairs Configuration for Leverage Trading

Defines which pairs to trade, leverage limits, and bidirectional support.
"""

import json
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class TradingPair:
    """Configuration for a trading pair"""
    symbol: str
    base_asset: str
    quote_asset: str
    leverage_enabled: bool
    max_leverage: int
    supports_short: bool
    min_position_size_usd: float
    max_position_size_usd: float
    liquidity_tier: str  # 'high', 'medium', 'low'
    data_file: str


# Trading pairs configuration
TRADING_PAIRS = {
    'ETHUSDT': TradingPair(
        symbol='ETHUSDT',
        base_asset='ETH',
        quote_asset='USDT',
        leverage_enabled=True,
        max_leverage=20,  # Conservative for production
        supports_short=True,
        min_position_size_usd=10.0,
        max_position_size_usd=10000.0,
        liquidity_tier='high',
        data_file='data/eth_90days.json'
    ),
    
    'BTCUSDT': TradingPair(
        symbol='BTCUSDT',
        base_asset='BTC',
        quote_asset='USDT',
        leverage_enabled=True,
        max_leverage=20,  # Conservative for production
        supports_short=True,
        min_position_size_usd=10.0,
        max_position_size_usd=10000.0,
        liquidity_tier='high',
        data_file='data/btc_90days.json'
    ),
    
    # ETH/BTC pair - usually NOT recommended for leverage due to low liquidity
    # Commented out by default
    # 'ETHBTC': TradingPair(
    #     symbol='ETHBTC',
    #     base_asset='ETH',
    #     quote_asset='BTC',
    #     leverage_enabled=False,  # Not recommended
    #     max_leverage=1,
    #     supports_short=False,
    #     min_position_size_usd=10.0,
    #     max_position_size_usd=1000.0,
    #     liquidity_tier='low',
    #     data_file='data/ethbtc_90days.json'
    # )
}


# Active pairs for trading (can be modified at runtime)
ACTIVE_PAIRS = ['ETHUSDT', 'BTCUSDT']


def get_pair_config(symbol: str) -> TradingPair:
    """Get configuration for a trading pair"""
    return TRADING_PAIRS.get(symbol)


def get_active_pairs() -> List[TradingPair]:
    """Get all active trading pairs"""
    return [TRADING_PAIRS[symbol] for symbol in ACTIVE_PAIRS if symbol in TRADING_PAIRS]


def get_leverage_pairs() -> List[TradingPair]:
    """Get pairs enabled for leverage trading"""
    return [pair for pair in get_active_pairs() if pair.leverage_enabled]


def get_shortable_pairs() -> List[TradingPair]:
    """Get pairs that support short selling"""
    return [pair for pair in get_active_pairs() if pair.supports_short]


def can_trade_pair(symbol: str, direction: str = 'long') -> bool:
    """
    Check if a pair can be traded in given direction
    
    Args:
        symbol: Trading pair symbol
        direction: 'long' or 'short'
    
    Returns:
        True if pair can be traded in that direction
    """
    pair = get_pair_config(symbol)
    
    if not pair:
        return False
    
    if symbol not in ACTIVE_PAIRS:
        return False
    
    if direction == 'short' and not pair.supports_short:
        return False
    
    return True


def validate_leverage(symbol: str, leverage: int) -> bool:
    """
    Validate if leverage amount is allowed for pair
    
    Args:
        symbol: Trading pair symbol
        leverage: Requested leverage amount
    
    Returns:
        True if leverage is valid
    """
    pair = get_pair_config(symbol)
    
    if not pair:
        return False
    
    if not pair.leverage_enabled:
        return leverage == 1
    
    return 1 <= leverage <= pair.max_leverage


def print_trading_config():
    """Print current trading pairs configuration"""
    
    print(f"\n{'='*80}")
    print(f"📊 TRADING PAIRS CONFIGURATION")
    print(f"{'='*80}\n")
    
    print(f"Active Pairs: {len(ACTIVE_PAIRS)}\n")
    
    for symbol in ACTIVE_PAIRS:
        pair = TRADING_PAIRS[symbol]
        
        print(f"📈 {symbol}")
        print(f"   Base: {pair.base_asset} | Quote: {pair.quote_asset}")
        print(f"   Leverage: {'✅ Yes' if pair.leverage_enabled else '❌ No'} (Max: {pair.max_leverage}x)")
        print(f"   Shorting: {'✅ Yes' if pair.supports_short else '❌ No'}")
        print(f"   Position Size: ${pair.min_position_size_usd:.0f} - ${pair.max_position_size_usd:,.0f}")
        print(f"   Liquidity: {pair.liquidity_tier.upper()}")
        print(f"   Data File: {pair.data_file}")
        print()


def get_data_files_needed() -> Dict[str, str]:
    """
    Get list of data files needed for active pairs
    
    Returns:
        Dict mapping symbol to data file path
    """
    return {symbol: TRADING_PAIRS[symbol].data_file for symbol in ACTIVE_PAIRS}


# Leverage trading best practices
LEVERAGE_GUIDELINES = """
🎯 LEVERAGE TRADING GUIDELINES

1. POSITION SIZING
   - Use 1-5x leverage for learning
   - Max 10x for experienced traders
   - Max 20x only for very experienced (high risk)
   - Never use more than 50% of account on one position

2. TRADING DIRECTIONS
   - LONG: Buy low, sell high (bullish market)
   - SHORT: Sell high, buy low (bearish market)
   - Both directions available for ETHUSDT and BTCUSDT

3. RISK MANAGEMENT
   - Always use stop losses
   - Position size should account for leverage
   - Higher leverage = smaller position size
   - Account for liquidation price

4. PAIR SELECTION
   - ✅ ETHUSDT: Highest liquidity, best for leverage
   - ✅ BTCUSDT: Highest liquidity, best for leverage
   - ❌ ETHBTC: Low liquidity, NOT recommended for leverage

5. MARKET CONDITIONS
   - Use lower leverage in volatile markets
   - Higher leverage in stable, trending markets
   - Reduce positions during major news events
   - Watch funding rates (can eat into profits)

6. LIQUIDATION RISK
   - 10x leverage: Liquidated at ~10% move against you
   - 20x leverage: Liquidated at ~5% move against you
   - Always maintain margin buffer
   - Monitor liquidation price constantly

7. BIDIRECTIONAL TRADING
   - Can switch between LONG and SHORT based on market
   - Don't fight the trend
   - Use technical analysis for direction
   - Respect support/resistance levels
"""


if __name__ == "__main__":
    # Display configuration
    print_trading_config()
    
    print(f"{'='*80}")
    print(f"📁 DATA FILES NEEDED")
    print(f"{'='*80}\n")
    
    for symbol, data_file in get_data_files_needed().items():
        print(f"{symbol:10s} → {data_file}")
    
    print(LEVERAGE_GUIDELINES)
