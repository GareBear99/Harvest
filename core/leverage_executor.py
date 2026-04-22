"""
Leverage Trading Executor for HARVEST
Converts trading signals into leveraged positions on Hyperliquid
"""

import logging
from decimal import Decimal
from typing import Optional, Dict
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.models import Config, ExecutionIntent, Side, Engine
    from core.hyperliquid_connector import HyperliquidConnector
except ImportError:
    # When run as script from harvest directory
    from models import Config, ExecutionIntent, Side, Engine
    from hyperliquid_connector import HyperliquidConnector

logger = logging.getLogger("harvest.leverage_executor")


class LeverageExecutor:
    """
    Execute leveraged trades on Hyperliquid based on HARVEST signals.
    
    Features:
    - Converts ExecutionIntent to actual positions
    - Manages stop-loss and take-profit orders
    - Tracks position state
    - Handles position sizing for small capital
    - Paper trading mode for testing
    """
    
    def __init__(self, config: Config, hyperliquid: Optional[HyperliquidConnector] = None):
        """
        Initialize leverage executor.
        
        Args:
            config: System configuration
            hyperliquid: HyperliquidConnector instance (None for paper trading)
        """
        self.config = config
        self.hyperliquid = hyperliquid
        self.paper_mode = config.enable_paper_leverage or hyperliquid is None
        
        # Track open positions
        self.open_positions: Dict[str, Dict] = {}  # {coin: position_info}
        
        # Track paper trading state
        self.paper_equity = config.initial_equity
        self.paper_positions: Dict[str, Dict] = {}
        
        logger.info(f"Leverage executor initialized ({'PAPER' if self.paper_mode else 'LIVE'} mode)")
    
    def calculate_position_size(self, intent: ExecutionIntent, 
                               available_balance: Decimal) -> Decimal:
        """
        Calculate position size based on intent and available capital.
        
        Args:
            intent: ExecutionIntent from strategy
            available_balance: Available balance in USD
        
        Returns:
            Position size in USD
        """
        # Use notional from intent as starting point
        base_size = Decimal(str(intent.notional_usd))
        
        # Apply small capital adjustments if needed
        if self.config.small_capital_mode and available_balance < 100:
            # For small capital, be more aggressive with position sizing
            risk_amount = available_balance * Decimal(str(self.config.small_capital_risk_pct / 100))
            
            # Calculate position size from risk and stop distance
            stop_distance_pct = abs(intent.entry - intent.stop) / intent.entry
            position_size = risk_amount / Decimal(str(stop_distance_pct))
            
            # Apply leverage
            position_size = position_size * Decimal(str(intent.leverage_cap))
            
            logger.info(f"Small capital sizing: ${risk_amount} risk, {stop_distance_pct*100:.2f}% stop = ${position_size} position")
        else:
            position_size = base_size
        
        # Enforce min/max limits
        min_size = Decimal(str(self.config.min_position_size_usd))
        max_size = Decimal(str(self.config.max_position_size_usd))
        
        position_size = max(min_size, min(position_size, max_size))
        
        # Don't exceed available balance
        max_allowed = available_balance * Decimal('0.95')  # Leave 5% buffer
        position_size = min(position_size, max_allowed)
        
        return position_size
    
    def execute_intent(self, intent: ExecutionIntent, coin: str = "ETH") -> bool:
        """
        Execute trading intent - open leveraged position.
        
        Args:
            intent: ExecutionIntent from strategy
            coin: Coin to trade (default ETH)
        
        Returns:
            True if executed successfully
        """
        try:
            logger.info(f"Executing {intent.engine.value} {intent.side.value} intent for {coin}")
            logger.info(f"  Entry: ${intent.entry}, Stop: ${intent.stop}, TP: ${intent.tp1}")
            logger.info(f"  Leverage: {intent.leverage_cap}x, Risk: {intent.risk_pct}%")
            
            if self.paper_mode:
                return self._execute_paper(intent, coin)
            else:
                return self._execute_live(intent, coin)
                
        except Exception as e:
            logger.error(f"Error executing intent: {e}")
            return False
    
    def _execute_paper(self, intent: ExecutionIntent, coin: str) -> bool:
        """Execute in paper trading mode (simulated)."""
        # Calculate position size
        available = Decimal(str(self.paper_equity))
        position_size = self.calculate_position_size(intent, available)
        
        # Check if we can afford this trade
        margin_required = position_size / Decimal(str(intent.leverage_cap))
        if margin_required > available:
            logger.warning(f"Insufficient paper capital: need ${margin_required}, have ${available}")
            return False
        
        # Simulate opening position
        self.paper_positions[coin] = {
            'intent': intent,
            'size_usd': float(position_size),
            'margin_used': float(margin_required),
            'entry_price': intent.entry,
            'entry_time': datetime.utcnow(),
            'coin': coin,
            'leverage': intent.leverage_cap,
            'side': intent.side.value
        }
        
        # Deduct margin from paper equity
        self.paper_equity -= float(margin_required)
        
        logger.info(f"📝 PAPER TRADE: Opened {intent.side.value} position")
        logger.info(f"   Position size: ${position_size}")
        logger.info(f"   Margin used: ${margin_required}")
        logger.info(f"   Paper equity remaining: ${self.paper_equity:.2f}")
        
        return True
    
    def _execute_live(self, intent: ExecutionIntent, coin: str) -> bool:
        """Execute on Hyperliquid (real money)."""
        if not self.hyperliquid or not self.hyperliquid.connected:
            logger.error("Hyperliquid not connected")
            return False
        
        # Get available balance
        available = self.hyperliquid.get_available_balance()
        logger.info(f"Available balance: ${available}")
        
        # Calculate position size
        position_size = self.calculate_position_size(intent, available)
        
        # Check margin requirement
        margin_required = position_size / Decimal(str(intent.leverage_cap))
        if margin_required > available:
            logger.warning(f"Insufficient funds: need ${margin_required}, have ${available}")
            return False
        
        # Open position on Hyperliquid
        is_long = (intent.side == Side.LONG)
        leverage = int(intent.leverage_cap)
        
        order_id = self.hyperliquid.market_open(
            coin=coin,
            is_long=is_long,
            size_usd=position_size,
            leverage=leverage
        )
        
        if not order_id:
            logger.error("Failed to open position on Hyperliquid")
            return False
        
        # Store position info
        self.open_positions[coin] = {
            'order_id': order_id,
            'intent': intent,
            'size_usd': float(position_size),
            'entry_price': intent.entry,
            'entry_time': datetime.utcnow(),
            'coin': coin,
            'leverage': leverage,
            'side': intent.side.value,
            'stop_loss': intent.stop,
            'take_profit': intent.tp1
        }
        
        logger.info(f"✅ LIVE TRADE: Position opened successfully")
        logger.info(f"   Order ID: {order_id}")
        logger.info(f"   Position size: ${position_size}")
        logger.info(f"   Leverage: {leverage}x")
        
        # TODO: Place stop-loss and take-profit orders
        # This requires limit orders which we'll implement in position monitoring
        
        return True
    
    def close_position(self, coin: str, reason: str = "manual") -> bool:
        """
        Close an open position.
        
        Args:
            coin: Coin symbol
            reason: Reason for closing (manual, stop-loss, take-profit, signal)
        
        Returns:
            True if closed successfully
        """
        try:
            logger.info(f"Closing {coin} position (reason: {reason})")
            
            if self.paper_mode:
                return self._close_paper(coin, reason)
            else:
                return self._close_live(coin, reason)
                
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False
    
    def _close_paper(self, coin: str, reason: str) -> bool:
        """Close paper trading position."""
        if coin not in self.paper_positions:
            logger.warning(f"No paper position for {coin}")
            return False
        
        position = self.paper_positions[coin]
        
        # Simulate closing (would need current price for real P&L calculation)
        # For now, just return margin
        margin = position['margin_used']
        self.paper_equity += margin
        
        logger.info(f"📝 PAPER TRADE: Closed {coin} position")
        logger.info(f"   Returned margin: ${margin}")
        logger.info(f"   Paper equity: ${self.paper_equity:.2f}")
        
        del self.paper_positions[coin]
        return True
    
    def _close_live(self, coin: str, reason: str) -> bool:
        """Close live Hyperliquid position."""
        if not self.hyperliquid or not self.hyperliquid.connected:
            logger.error("Hyperliquid not connected")
            return False
        
        if coin not in self.open_positions:
            logger.warning(f"No open position for {coin}")
            return False
        
        # Close on Hyperliquid
        success = self.hyperliquid.market_close(coin=coin)
        
        if success:
            logger.info(f"✅ LIVE TRADE: Position closed successfully")
            del self.open_positions[coin]
            return True
        else:
            logger.error(f"Failed to close position on Hyperliquid")
            return False
    
    def close_all_positions(self, reason: str = "emergency") -> int:
        """
        Close all open positions.
        
        Args:
            reason: Reason for closing
        
        Returns:
            Number of positions closed
        """
        logger.info(f"Closing all positions (reason: {reason})")
        
        closed_count = 0
        
        if self.paper_mode:
            coins = list(self.paper_positions.keys())
        else:
            coins = list(self.open_positions.keys())
        
        for coin in coins:
            if self.close_position(coin, reason):
                closed_count += 1
        
        logger.info(f"Closed {closed_count} position(s)")
        return closed_count
    
    def get_position_status(self, coin: str = "ETH") -> Optional[Dict]:
        """
        Get current position status.
        
        Args:
            coin: Coin symbol
        
        Returns:
            Position info dict or None
        """
        if self.paper_mode:
            return self.paper_positions.get(coin)
        else:
            if self.hyperliquid and self.hyperliquid.connected:
                positions = self.hyperliquid.get_positions()
                for pos in positions:
                    if pos['coin'] == coin:
                        return pos
            return None
    
    def get_account_summary(self) -> Dict:
        """
        Get account summary.
        
        Returns:
            Dict with account info
        """
        if self.paper_mode:
            return {
                'mode': 'paper',
                'equity': self.paper_equity,
                'open_positions': len(self.paper_positions),
                'positions': list(self.paper_positions.keys())
            }
        else:
            if self.hyperliquid and self.hyperliquid.connected:
                account_value = self.hyperliquid.get_account_value()
                available = self.hyperliquid.get_available_balance()
                positions = self.hyperliquid.get_positions()
                
                return {
                    'mode': 'live',
                    'account_value': float(account_value),
                    'available_balance': float(available),
                    'open_positions': len(positions),
                    'positions': [p['coin'] for p in positions]
                }
            else:
                return {
                    'mode': 'live',
                    'error': 'Not connected to Hyperliquid'
                }
    
    def check_stop_loss_take_profit(self, coin: str, current_price: float) -> Optional[str]:
        """
        Check if stop-loss or take-profit should trigger.
        
        Args:
            coin: Coin symbol
            current_price: Current market price
        
        Returns:
            'stop-loss', 'take-profit', or None
        """
        position = None
        
        if self.paper_mode:
            position = self.paper_positions.get(coin)
        else:
            if coin in self.open_positions:
                position = self.open_positions[coin]
        
        if not position:
            return None
        
        intent = position.get('intent')
        if not intent:
            return None
        
        # Check stop-loss
        if intent.side == Side.LONG:
            if current_price <= intent.stop:
                return 'stop-loss'
            if current_price >= intent.tp1:
                return 'take-profit'
        else:  # SHORT
            if current_price >= intent.stop:
                return 'stop-loss'
            if current_price <= intent.tp1:
                return 'take-profit'
        
        return None


# Test mode
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from core.models import Config, ExecutionIntent, Side, Engine
    from datetime import datetime
    
    print("=" * 70)
    print("HARVEST Leverage Executor Test")
    print("=" * 70)
    print()
    
    # Create config with small capital mode
    config = Config(
        initial_equity=10.0,
        small_capital_mode=True,
        enable_paper_leverage=True
    )
    
    # Create executor in paper mode
    executor = LeverageExecutor(config=config)
    
    print(f"Mode: {'PAPER' if executor.paper_mode else 'LIVE'}")
    print(f"Initial equity: ${executor.paper_equity}")
    print()
    
    # Create test intent
    intent = ExecutionIntent(
        timestamp=datetime.utcnow(),
        engine=Engine.ER90,
        side=Side.LONG,
        entry=4000.0,
        stop=3960.0,  # 1% stop
        tp1=4080.0,   # 2% TP
        runner=None,
        leverage_cap=20.0,
        notional_usd=200.0,
        risk_pct=5.0,
        symbol="ETHUSDT"
    )
    
    print("Test Intent:")
    print(f"  Engine: {intent.engine.value}")
    print(f"  Side: {intent.side.value}")
    print(f"  Entry: ${intent.entry}")
    print(f"  Stop: ${intent.stop}")
    print(f"  TP: ${intent.tp1}")
    print(f"  Leverage: {intent.leverage_cap}x")
    print()
    
    # Execute
    print("Executing intent...")
    success = executor.execute_intent(intent, coin="ETH")
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    print()
    
    # Check position
    position = executor.get_position_status("ETH")
    if position:
        print("Open position:")
        print(f"  Size: ${position['size_usd']}")
        print(f"  Margin: ${position['margin_used']}")
        print(f"  Leverage: {position['leverage']}x")
        print()
    
    # Account summary
    summary = executor.get_account_summary()
    print("Account summary:")
    print(f"  Mode: {summary['mode']}")
    print(f"  Equity: ${summary['equity']:.2f}")
    print(f"  Open positions: {summary['open_positions']}")
    print()
    
    # Test close
    print("Closing position...")
    executor.close_position("ETH", reason="test")
    
    summary = executor.get_account_summary()
    print(f"Final equity: ${summary['equity']:.2f}")
    
    print()
    print("✅ Leverage executor test complete")
