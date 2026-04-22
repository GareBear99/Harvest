"""
Hyperliquid DEX Connector for HARVEST
Enables leveraged perpetual trading with minimal gas costs
"""

import os
import json
from decimal import Decimal
from typing import Optional, Dict, List
import logging
from eth_account.signers.local import LocalAccount
from eth_account import Account

logger = logging.getLogger("harvest.hyperliquid")

# Check if Hyperliquid SDK is available
try:
    from hyperliquid.exchange import Exchange
    from hyperliquid.info import Info
    from hyperliquid.utils import constants
    HYPERLIQUID_AVAILABLE = True
except ImportError:
    HYPERLIQUID_AVAILABLE = False
    logger.warning("Hyperliquid SDK not installed. Install with: pip install hyperliquid-python-sdk")


class HyperliquidConnector:
    """
    Connect to Hyperliquid DEX for leveraged perpetual trading.
    
    Features:
    - Ultra-low fees (~$0.01 per trade)
    - Up to 50x leverage
    - Minimum $10 positions
    - Non-custodial (your keys, your crypto)
    - Python SDK integration
    """
    
    def __init__(self, testnet: bool = False):
        """
        Initialize Hyperliquid connector.
        
        Args:
            testnet: Use testnet (True) or mainnet (False)
        """
        if not HYPERLIQUID_AVAILABLE:
            raise ImportError("Hyperliquid SDK not installed. Run: pip install hyperliquid-python-sdk")
        
        self.testnet = testnet
        self.api_url = constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL
        self.wallet: Optional[LocalAccount] = None
        self.exchange: Optional[Exchange] = None
        self.info: Optional[Info] = None
        self.connected = False
        
        logger.info(f"Initializing Hyperliquid connector ({'testnet' if testnet else 'mainnet'})")
    
    def connect(self, private_key: Optional[str] = None) -> bool:
        """
        Connect to Hyperliquid.
        
        Args:
            private_key: Ethereum private key (0x... format)
        
        Returns:
            True if connected successfully
        """
        try:
            # Get private key from env if not provided
            if private_key is None:
                private_key = os.getenv('ETH_PRIVATE_KEY')
            
            if not private_key:
                logger.error("No private key provided. Set ETH_PRIVATE_KEY environment variable")
                return False
            
            # Create wallet from private key
            self.wallet = Account.from_key(private_key)
            
            # Initialize Exchange and Info clients
            self.exchange = Exchange(self.wallet, self.api_url)
            self.info = Info(self.api_url, skip_ws=True)
            
            # Test connection by fetching account state
            user_state = self.info.user_state(self.wallet.address)
            
            self.connected = True
            logger.info(f"✅ Connected to Hyperliquid")
            logger.info(f"Address: {self.wallet.address}")
            
            # Log account info
            if user_state:
                margin_summary = user_state.get('marginSummary', {})
                account_value = margin_summary.get('accountValue', '0')
                logger.info(f"Account Value: ${float(account_value):.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Hyperliquid: {e}")
            self.connected = False
            return False
    
    def get_account_value(self) -> Decimal:
        """
        Get total account value (margin + unrealized PnL).
        
        Returns:
            Account value in USD
        """
        if not self.connected or not self.info:
            raise RuntimeError("Not connected to Hyperliquid")
        
        try:
            user_state = self.info.user_state(self.wallet.address)
            margin_summary = user_state.get('marginSummary', {})
            account_value = margin_summary.get('accountValue', '0')
            return Decimal(account_value)
        except Exception as e:
            logger.error(f"Error fetching account value: {e}")
            return Decimal('0')
    
    def get_available_balance(self) -> Decimal:
        """
        Get available balance for trading (withdrawable).
        
        Returns:
            Available balance in USD
        """
        if not self.connected or not self.info:
            raise RuntimeError("Not connected to Hyperliquid")
        
        try:
            user_state = self.info.user_state(self.wallet.address)
            margin_summary = user_state.get('marginSummary', {})
            # withdrawable is the actual available balance
            withdrawable = margin_summary.get('withdrawable', '0')
            return Decimal(withdrawable)
        except Exception as e:
            logger.error(f"Error fetching available balance: {e}")
            return Decimal('0')
    
    def get_positions(self) -> List[Dict]:
        """
        Get all open positions.
        
        Returns:
            List of position dictionaries
        """
        if not self.connected or not self.info:
            raise RuntimeError("Not connected to Hyperliquid")
        
        try:
            user_state = self.info.user_state(self.wallet.address)
            positions = user_state.get('assetPositions', [])
            
            # Filter out positions with zero size
            active_positions = []
            for pos in positions:
                position_dict = pos.get('position', {})
                size = float(position_dict.get('szi', 0))
                if abs(size) > 0:
                    active_positions.append({
                        'coin': position_dict.get('coin', ''),
                        'size': size,
                        'entry_px': float(position_dict.get('entryPx', 0)),
                        'position_value': float(position_dict.get('positionValue', 0)),
                        'unrealized_pnl': float(position_dict.get('unrealizedPnl', 0)),
                        'leverage': float(position_dict.get('leverage', {}).get('value', 0)),
                        'liquidation_px': float(position_dict.get('liquidationPx', 0)),
                        'margin_used': float(position_dict.get('marginUsed', 0))
                    })
            
            return active_positions
            
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []
    
    def get_market_info(self, coin: str = "ETH") -> Optional[Dict]:
        """
        Get market information for a coin.
        
        Args:
            coin: Coin symbol (e.g., "ETH", "BTC")
        
        Returns:
            Market info dict or None
        """
        if not self.connected or not self.info:
            raise RuntimeError("Not connected to Hyperliquid")
        
        try:
            meta = self.info.meta()
            universe = meta.get('universe', [])
            
            for market in universe:
                if market.get('name') == coin:
                    return {
                        'coin': coin,
                        'max_leverage': int(market.get('maxLeverage', 0)),
                        'min_size': float(market.get('szDecimals', 0)),
                        'tick_size': float(market.get('tickSize', 0))
                    }
            
            logger.warning(f"Market {coin} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching market info: {e}")
            return None
    
    def get_mark_price(self, coin: str = "ETH") -> Decimal:
        """
        Get current mark price for a coin.
        
        Args:
            coin: Coin symbol
        
        Returns:
            Mark price in USD
        """
        if not self.connected or not self.info:
            raise RuntimeError("Not connected to Hyperliquid")
        
        try:
            all_mids = self.info.all_mids()
            price = all_mids.get(coin)
            if price:
                return Decimal(price)
            else:
                logger.warning(f"Price for {coin} not found")
                return Decimal('0')
        except Exception as e:
            logger.error(f"Error fetching mark price: {e}")
            return Decimal('0')
    
    def market_open(self, coin: str, is_long: bool, size_usd: Decimal, 
                    leverage: int, reduce_only: bool = False) -> Optional[str]:
        """
        Open a market order position.
        
        Args:
            coin: Coin to trade (e.g., "ETH")
            is_long: True for long, False for short
            size_usd: Position size in USD
            leverage: Leverage multiplier (1-50x)
            reduce_only: Only reduce existing position
        
        Returns:
            Order ID or None on error
        """
        if not self.connected or not self.exchange:
            raise RuntimeError("Not connected to Hyperliquid")
        
        try:
            # Set leverage first
            self.exchange.update_leverage(leverage, coin)
            logger.info(f"Set leverage to {leverage}x for {coin}")
            
            # Get current price to calculate size in coins
            mark_price = self.get_mark_price(coin)
            if mark_price == 0:
                logger.error(f"Could not get price for {coin}")
                return None
            
            # Calculate size in coins
            size_coins = float(size_usd / mark_price)
            
            # Round to appropriate decimals (0.001 for most coins)
            size_coins = round(size_coins, 3)
            
            logger.info(f"Opening {('LONG' if is_long else 'SHORT')} position:")
            logger.info(f"  Coin: {coin}")
            logger.info(f"  Size: {size_coins} coins (${size_usd})")
            logger.info(f"  Leverage: {leverage}x")
            logger.info(f"  Entry price: ${mark_price}")
            
            # Place market order
            result = self.exchange.market_open(
                coin=coin,
                is_buy=is_long,
                sz=size_coins,
                reduce_only=reduce_only
            )
            
            if result and result.get('status') == 'ok':
                response = result.get('response', {})
                data = response.get('data', {})
                statuses = data.get('statuses', [])
                
                if statuses and len(statuses) > 0:
                    status = statuses[0]
                    if 'filled' in status:
                        filled = status['filled']
                        logger.info(f"✅ Position opened successfully")
                        logger.info(f"  Filled size: {filled.get('totalSz', 0)} coins")
                        logger.info(f"  Avg price: ${filled.get('avgPx', 0)}")
                        return str(filled.get('oid', ''))
                
                logger.warning(f"Order placed but status unclear: {result}")
                return "pending"
            else:
                logger.error(f"Failed to open position: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error opening position: {e}")
            return None
    
    def market_close(self, coin: str, size_coins: Optional[float] = None) -> bool:
        """
        Close position with market order.
        
        Args:
            coin: Coin to close position for
            size_coins: Size to close (None = close entire position)
        
        Returns:
            True if successful
        """
        if not self.connected or not self.exchange:
            raise RuntimeError("Not connected to Hyperliquid")
        
        try:
            logger.info(f"Closing position for {coin}")
            
            result = self.exchange.market_close(coin=coin, sz=size_coins)
            
            if result and result.get('status') == 'ok':
                logger.info(f"✅ Position closed successfully")
                return True
            else:
                logger.error(f"Failed to close position: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False
    
    def place_limit_order(self, coin: str, is_long: bool, size_coins: float,
                          limit_price: Decimal, reduce_only: bool = False) -> Optional[str]:
        """
        Place a limit order (for stop-loss/take-profit).
        
        Args:
            coin: Coin symbol
            is_long: True for buy, False for sell
            size_coins: Size in coins
            limit_price: Limit price
            reduce_only: Only reduce existing position
        
        Returns:
            Order ID or None
        """
        if not self.connected or not self.exchange:
            raise RuntimeError("Not connected to Hyperliquid")
        
        try:
            result = self.exchange.order(
                coin=coin,
                is_buy=is_long,
                sz=size_coins,
                limit_px=float(limit_price),
                reduce_only=reduce_only
            )
            
            if result and result.get('status') == 'ok':
                response = result.get('response', {})
                data = response.get('data', {})
                statuses = data.get('statuses', [])
                
                if statuses and len(statuses) > 0:
                    oid = statuses[0].get('resting', {}).get('oid')
                    if oid:
                        logger.info(f"✅ Limit order placed: {oid}")
                        return str(oid)
                
                logger.warning(f"Limit order placed but no order ID: {result}")
                return "pending"
            else:
                logger.error(f"Failed to place limit order: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            return None
    
    def cancel_order(self, coin: str, order_id: str) -> bool:
        """
        Cancel an open order.
        
        Args:
            coin: Coin symbol
            order_id: Order ID to cancel
        
        Returns:
            True if successful
        """
        if not self.connected or not self.exchange:
            raise RuntimeError("Not connected to Hyperliquid")
        
        try:
            result = self.exchange.cancel(coin=coin, oid=int(order_id))
            
            if result and result.get('status') == 'ok':
                logger.info(f"✅ Order {order_id} cancelled")
                return True
            else:
                logger.error(f"Failed to cancel order: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False


def setup_hyperliquid_connection(testnet: bool = False) -> Optional[HyperliquidConnector]:
    """
    Convenience function to set up Hyperliquid connection.
    
    Args:
        testnet: Use testnet or mainnet
    
    Returns:
        Connected HyperliquidConnector or None
    """
    try:
        connector = HyperliquidConnector(testnet=testnet)
        
        if connector.connect():
            return connector
        else:
            logger.error("Failed to connect to Hyperliquid")
            return None
            
    except Exception as e:
        logger.error(f"Error setting up Hyperliquid connection: {e}")
        return None


# Test mode
if __name__ == "__main__":
    print("=" * 70)
    print("HARVEST Hyperliquid Connector Test")
    print("=" * 70)
    print()
    
    # Check environment
    private_key = os.getenv('ETH_PRIVATE_KEY')
    
    if not private_key:
        print("⚠️  ETH_PRIVATE_KEY not set")
        print("Set it to your wallet private key:")
        print("  export ETH_PRIVATE_KEY='0xYOUR_PRIVATE_KEY'")
        exit(1)
    
    print("🔌 Connecting to Hyperliquid testnet...")
    connector = setup_hyperliquid_connection(testnet=True)
    
    if not connector:
        print("❌ Failed to connect")
        exit(1)
    
    print()
    print("💰 Checking account balance...")
    account_value = connector.get_account_value()
    available = connector.get_available_balance()
    
    print(f"Account Value: ${account_value}")
    print(f"Available Balance: ${available}")
    
    print()
    print("📊 Checking ETH market info...")
    market_info = connector.get_market_info("ETH")
    if market_info:
        print(f"Max Leverage: {market_info['max_leverage']}x")
        print(f"Min Size: {market_info['min_size']}")
    
    mark_price = connector.get_mark_price("ETH")
    print(f"Current ETH Price: ${mark_price}")
    
    print()
    print("📈 Checking open positions...")
    positions = connector.get_positions()
    if positions:
        for pos in positions:
            print(f"  {pos['coin']}: {pos['size']} coins @ ${pos['entry_px']}")
            print(f"    PnL: ${pos['unrealized_pnl']:.2f}, Leverage: {pos['leverage']:.1f}x")
    else:
        print("  No open positions")
    
    print()
    print("✅ Hyperliquid connector test complete")
