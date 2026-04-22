#!/usr/bin/env python3
"""
HARVEST Live Trading Daemon
Implements the main trading loop with proper error handling and state management
"""

import time
import signal
import sys
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import Config, AccountState, Engine, OHLCV
from core.data_ingestion import DataIngestion
from core.regime_classifier import RegimeClassifier
from core.risk_governor import RiskGovernor
from core.logging_config import setup_logging, log_trade, log_account_state, log_error_with_context
from core.api_error_handling import APIError, CircuitBreaker
from core.metamask_connector import setup_metamask_connection
from core.auto_wallet_manager import AutoWalletManager
from core.statistics_tracker import get_statistics_tracker
from strategies.er90 import ER90Strategy
from strategies.sib import SIBStrategy


class LiveTrader:
    """
    Live trading daemon for HARVEST system.
    
    Modes:
        - paper: Simulated trading (no real orders)
        - live: Real trading with exchange API
    """
    
    def __init__(self, symbol: str = "ETHUSDT", mode: str = "paper", 
                 initial_equity: float = 10000.0):
        """
        Initialize live trading daemon.
        
        Args:
            symbol: Trading symbol (e.g. ETHUSDT, BTCUSDT)
            mode: Trading mode ('paper' or 'live')
            initial_equity: Starting equity in USD
        """
        self.symbol = symbol
        self.mode = mode
        self.running = False
        
        # Set up logging
        log_level = "DEBUG" if mode == "paper" else "INFO"
        self.logger = setup_logging(log_level=log_level)
        self.logger.info(f"Initializing HARVEST Live Trader - Mode: {mode}")
        
        # Initialize auto wallet manager
        self.wallet_manager = AutoWalletManager()
        self.logger.info(f"Wallet Manager initialized (Client ID: {self.wallet_manager.client_id[:8]}...)")
        
        # Initialize statistics tracker
        self.stats_tracker = get_statistics_tracker()
        self.logger.info("Statistics tracker initialized")
        
        # Initialize balance-aware strategy and slot allocation
        from core.balance_aware_strategy import get_balance_aware_strategy
        from core.slot_allocation_strategy import get_slot_allocation_strategy
        
        self.balance_strategy = get_balance_aware_strategy()
        self.slot_strategy = get_slot_allocation_strategy()
        self.current_tier = None
        self.logger.info("Balance-aware strategy initialized")
        
        # Calculate slot allocation and BTC funding requirements
        active_slots = self.slot_strategy.get_active_slots(initial_equity)
        btc_slots = active_slots // 2  # Even slots are BTC
        total_btc_funding = btc_slots * 10.0
        
        # Calculate fees for ETH→BTC funding
        self.eth_balance = initial_equity
        self.btc_balance = 0.0
        self.setup_fees = 0.0
        
        if total_btc_funding > 0:
            conversion_fee = total_btc_funding * 0.01  # 1% conversion
            btc_transfer_fee = total_btc_funding * 0.02  # 2% BTC fee
            gas_fee = 0.50  # Gas for the transfer
            self.setup_fees = conversion_fee + btc_transfer_fee + gas_fee
            
            # Split balance between ETH and BTC (minus fees)
            self.eth_balance = initial_equity - total_btc_funding - self.setup_fees
            self.btc_balance = total_btc_funding
            
            self.logger.info(f"Slot Allocation: {active_slots} slots ({active_slots - btc_slots} ETH, {btc_slots} BTC)")
            self.logger.info(f"ETH Balance: ${self.eth_balance:.2f}")
            self.logger.info(f"BTC Balance: ${self.btc_balance:.2f}")
            self.logger.info(f"Setup Fees: ${self.setup_fees:.2f} (conv: ${conversion_fee:.2f}, BTC: ${btc_transfer_fee:.2f}, gas: ${gas_fee:.2f})")
        else:
            self.logger.info(f"Slot Allocation: {active_slots} slot (ETH only, no BTC funding needed)")
        
        # Initialize configuration with adjusted equity (minus setup fees)
        net_equity = initial_equity - self.setup_fees
        self.config = Config(initial_equity=net_equity)
        
        # Initialize components
        self.data_ingestion = DataIngestion(symbol)
        self.regime_classifier = RegimeClassifier(self.config)
        self.risk_governor = RiskGovernor(self.config)
        self.er90 = ER90Strategy(self.config)
        self.sib = SIBStrategy(self.config)
        
        # Circuit breaker for API calls
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=300)
        
        # Initialize MetaMask connector (optional, for on-chain trading)
        self.metamask = None
        if mode == "live":
            self.metamask = setup_metamask_connection()
            if self.metamask:
                balance = self.metamask.get_eth_balance()
                self.logger.info(f"MetaMask connected: {self.metamask.account.address}")
                self.logger.info(f"ETH balance: {balance:.6f} ETH")
            else:
                self.logger.warning("MetaMask not configured (set ETH_RPC_URL and ETH_PRIVATE_KEY)")
                self.logger.warning("Live mode will use paper trading without on-chain execution")
        
        # Initialize account state
        self.account = AccountState(
            equity=initial_equity,
            daily_pnl=0.0,
            daily_pnl_pct=0.0,
            consecutive_losses=0,
            trades_today={},
            losses_today={},
            mode=Engine.IDLE
        )
        
        # Trading state
        self.last_update = None
        self.daily_reset_time = None
        self.error_count = 0
        self.max_errors = 10
        self.active_positions = []  # Track positions for live trading
        self.last_trade_time = None
        self.total_trades = 0
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info(f"Live trader initialized for {symbol}")
        self.logger.info(f"Initial equity: ${initial_equity:,.2f}")
        self.logger.info(f"Mode: {mode.upper()}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _should_reset_daily_stats(self) -> bool:
        """Check if daily stats should be reset (new trading day)"""
        now = datetime.utcnow()
        
        # Reset at 00:00 UTC
        if self.daily_reset_time is None:
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return False
        
        if now >= self.daily_reset_time + timedelta(days=1):
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return True
        
        return False
    
    def _reset_daily_stats(self):
        """Reset daily statistics"""
        self.logger.info("Resetting daily statistics (new trading day)")
        
        self.account.daily_pnl = 0.0
        self.account.daily_pnl_pct = 0.0
        self.account.consecutive_losses = 0
        self.account.trades_today = {}
        self.account.losses_today = {}
        self.account.mode = Engine.IDLE
        
        log_account_state(self.logger, {
            'equity': self.account.equity,
            'daily_pnl': 0.0,
            'consecutive_losses': 0,
            'event': 'daily_reset'
        })
    
    def _fetch_market_data(self) -> Optional[Dict[str, list]]:
        """
        Fetch current market data with error handling.
        
        Returns:
            Dictionary with timeframe data or None on error
        """
        try:
            # Fetch data through circuit breaker
            data = self.circuit_breaker.call(
                self.data_ingestion.fetch_multiple_timeframes,
                days=7  # Keep recent data
            )
            
            if not data or not data.get("1h"):
                self.logger.warning("No data received from API")
                return None
            
            return data
            
        except APIError as e:
            self.logger.error(f"API error fetching market data: {e}")
            self.error_count += 1
            return None
        except Exception as e:
            log_error_with_context(self.logger, e, {
                'function': '_fetch_market_data',
                'symbol': self.symbol
            })
            self.error_count += 1
            return None
    
    def _analyze_market(self, data: Dict[str, list]) -> Optional[object]:
        """
        Analyze market and generate trading signal.
        
        Args:
            data: Market data dictionary
        
        Returns:
            ExecutionIntent or None
        """
        try:
            candles_1h = data.get("1h", [])
            candles_4h = data.get("4h", [])
            candles_5m = data.get("5m", [])
            
            if len(candles_1h) < 200 or len(candles_4h) < 50:
                self.logger.debug("Insufficient data for analysis")
                return None
            
            # Classify market regime
            regime = self.regime_classifier.classify(candles_4h, self.account)
            self.logger.debug(f"Market regime: {regime.value}")
            
            # Determine active engine
            active_engine = self.risk_governor.determine_active_engine(regime, self.account)
            self.logger.debug(f"Active engine: {active_engine.value}")
            
            if active_engine == Engine.IDLE:
                self.logger.info("System in IDLE mode (risk limits or no suitable regime)")
                return None
            
            # Check for trading signals
            intent = None
            current_hour = datetime.utcnow().hour
            
            if active_engine == Engine.ER90:
                intent = self.er90.check_entry(candles_5m, candles_1h, self.account)
            elif active_engine == Engine.SIB:
                intent = self.sib.check_entry(candles_1h, candles_4h, self.account, current_hour)
            
            # Validate intent
            if intent and not self.risk_governor.validate_execution_intent(intent, self.account):
                self.logger.warning("Execution intent failed risk validation")
                return None
            
            return intent
            
        except Exception as e:
            log_error_with_context(self.logger, e, {
                'function': '_analyze_market',
                'symbol': self.symbol
            })
            return None
    
    def _execute_intent(self, intent: object):
        """
        Execute trading intent.
        
        Args:
            intent: ExecutionIntent object
        """
        if self.mode == "paper":
            self._execute_paper_trade(intent)
        else:
            self._execute_live_trade(intent)
    
    def _execute_paper_trade(self, intent: object):
        """Execute simulated trade for paper trading mode"""
        self.logger.info("="*70)
        self.logger.info("PAPER TRADE EXECUTION")
        self.logger.info("="*70)
        
        trade_data = {
            'mode': 'PAPER',
            'symbol': self.symbol,
            'engine': intent.engine.value,
            'side': intent.side.value,
            'entry': intent.entry,
            'stop': intent.stop,
            'tp1': intent.tp1,
            'leverage': intent.leverage_cap,
            'notional_usd': intent.notional_usd,
            'risk_pct': intent.risk_pct,
            'timestamp': intent.timestamp.isoformat()
        }
        
        log_trade(self.logger, trade_data)
        
        # Log to console
        self.logger.info(f"Engine: {intent.engine.value}")
        self.logger.info(f"Side: {intent.side.value}")
        self.logger.info(f"Entry: ${intent.entry:,.2f}")
        self.logger.info(f"Stop: ${intent.stop:,.2f}")
        self.logger.info(f"TP1: ${intent.tp1:,.2f}")
        self.logger.info(f"Leverage: {intent.leverage_cap:.1f}x")
        self.logger.info(f"Notional: ${intent.notional_usd:,.2f}")
        self.logger.info(f"Risk: {intent.risk_pct:.3f}%")
        self.logger.info("="*70)
        
        # Update trade tracking
        self.total_trades += 1
        self.last_trade_time = datetime.utcnow()
        
        # Record signal in statistics tracker
        # Determine timeframe from intent if available
        timeframe = getattr(intent, 'timeframe', '1h')  # Default to 1h if not specified
        strategy_name = intent.engine.value
        seed = getattr(intent, 'seed', None)
        
        self.stats_tracker.record_signal(
            timeframe=timeframe,
            strategy=strategy_name,
            side=intent.side.value,
            entry=intent.entry,
            stop=intent.stop,
            tp1=intent.tp1,
            notional=intent.notional_usd,
            seed=seed
        )
        
        # In paper mode, we don't actually track P&L
        # This is just signal generation
    
    def _execute_live_trade(self, intent: object):
        """Execute real trade via exchange API"""
        self.logger.critical("LIVE TRADING NOT IMPLEMENTED")
        self.logger.critical("This would place a real order on the exchange")
        self.logger.critical("Requires exchange API integration and extensive testing")
        
        # TODO: Implement actual exchange API integration
        # This requires:
        # 1. Exchange API credentials
        # 2. Order placement logic
        # 3. Position tracking
        # 4. P&L calculation
        # 5. Order management (modify, cancel)
        # 6. Extensive error handling
        
        raise NotImplementedError("Live trading requires exchange API integration")
    
    def export_status(self) -> Dict:
        """
        Export current trader status for dashboard consumption.
        
        Returns:
            Dictionary with complete trader status
        """
        return {
            'status': 'running' if self.running else 'stopped',
            'mode': self.mode,
            'symbol': self.symbol,
            'balance': {
                'initial': self.config.initial_equity,
                'current': self.account.equity,
                'daily_pnl': self.account.daily_pnl,
                'daily_pnl_pct': self.account.daily_pnl_pct
            },
            'positions': {
                'active': len(self.active_positions),
                'details': self.active_positions
            },
            'trading': {
                'total_trades': self.total_trades,
                'last_trade': self.last_trade_time.isoformat() if self.last_trade_time else None,
                'consecutive_losses': self.account.consecutive_losses,
                'trades_today': sum(self.account.trades_today.values()),
                'engine_mode': self.account.mode.value
            },
            'system': {
                'last_update': datetime.utcnow().isoformat(),
                'error_count': self.error_count,
                'circuit_breaker_status': self.circuit_breaker.state.lower()
            },
            'targets': {
                'target_balance': 100.0,
                'progress_pct': min((self.account.equity / 100.0) * 100, 100)
            },
            'statistics': self.stats_tracker.get_summary_for_dashboard(),
            'tier': {
                'description': self.current_tier.description if self.current_tier else 'Unknown',
                'min_balance': self.current_tier.min_balance if self.current_tier else 0,
                'max_balance': self.current_tier.max_balance if self.current_tier else 0,
                'active_timeframes': self.current_tier.active_timeframes if self.current_tier else [],
                'active_assets': [a.value for a in self.current_tier.active_assets] if self.current_tier else [],
                'max_position': self.current_tier.max_position_per_asset if self.current_tier else 0,
                'btc_wallet_required': self.current_tier.btc_wallet_required if self.current_tier else False
            }
        }
    
    def run(self, update_interval: int = 300):
        """
        Main trading loop.
        
        Args:
            update_interval: Seconds between market updates (default: 5 minutes)
        """
        # Validate wallet setup before starting
        self.logger.info("="*70)
        self.logger.info("WALLET VALIDATION")
        self.logger.info("="*70)
        
        validation = self.wallet_manager.validate_on_startup()
        
        if self.mode == "live" and not validation['ready_for_live_trading']:
            self.logger.error("="*70)
            self.logger.error("❌ CANNOT START LIVE TRADING")
            self.logger.error("="*70)
            self.logger.error("\nRequired actions:")
            for action in validation['actions_required']:
                self.logger.error(f"  - [{action['priority']}] {action['message']}")
            
            if not validation['metamask_connected']:
                self.logger.info("\n💡 To connect MetaMask:")
                self.logger.info("   1. Start API server: python core/wallet_api_server.py")
                self.logger.info("   2. Run: python cli.py wallet setup")
            
            self.logger.error("\nSystem not ready. Fix issues above and try again.")
            return
        
        if validation['warnings']:
            self.logger.warning("\n⚠️  Warnings:")
            for warning in validation['warnings']:
                self.logger.warning(f"  - {warning}")
        
        # Balance-aware validation
        self.logger.info("\n" + "="*70)
        self.logger.info("BALANCE-AWARE TIER VALIDATION")
        self.logger.info("="*70)
        
        tier_validation = self.balance_strategy.validate_trading_requirements(
            balance=self.account.equity,
            has_btc_wallet=validation.get('btc_wallet_generated', False),
            connected_metamask=validation.get('metamask_connected', False)
        )
        
        if not tier_validation['can_trade']:
            self.logger.error("\n❌ BALANCE-AWARE VALIDATION FAILED")
            for issue in tier_validation['issues']:
                self.logger.error(f"  - {issue}")
            if tier_validation['recommendations']:
                self.logger.info("\n💡 Recommendations:")
                for rec in tier_validation['recommendations']:
                    self.logger.info(f"  - {rec}")
            return
        
        # Store and display current tier
        self.current_tier = tier_validation['tier']
        self.logger.info(f"\n✅ Tier Validation Passed")
        self.logger.info(f"Current Tier: {self.current_tier.description}")
        self.logger.info(f"Active Timeframes: {', '.join(tier_validation['active_timeframes'])}")
        self.logger.info(f"Active Assets: {', '.join(tier_validation['active_assets'])}")
        self.logger.info(f"Max Position: ${tier_validation['max_position_per_asset']:.0f} per asset")
        
        # Start statistics tracking session
        self.stats_tracker.start_session()
        self.logger.info("\nStatistics tracking session started")
        
        self.running = True
        self.logger.info("\n" + "="*70)
        self.logger.info("HARVEST LIVE TRADER STARTED")
        self.logger.info("="*70)
        self.logger.info(f"Symbol: {self.symbol}")
        self.logger.info(f"Mode: {self.mode.upper()}")
        self.logger.info(f"Update interval: {update_interval}s")
        if validation['metamask_connected']:
            self.logger.info(f"Wallet: {validation.get('metamask_address', 'N/A')[:10]}...")
        self.logger.info(f"Press Ctrl+C to stop")
        self.logger.info("="*70)
        
        iteration = 0
        
        while self.running:
            try:
                iteration += 1
                self.logger.info(f"\n--- Iteration {iteration} - {datetime.utcnow().isoformat()} ---")
                
                # Check for daily reset
                if self._should_reset_daily_stats():
                    self._reset_daily_stats()
                
                # Check for tier upgrades
                new_tier = self.balance_strategy.get_tier(self.account.equity)
                if new_tier.min_balance != self.current_tier.min_balance:
                    self.logger.info("\n" + "🎉"*35)
                    self.logger.info("🎉 TIER UPGRADE!")
                    self.logger.info("🎉"*35)
                    self.logger.info(f"Old Tier: {self.current_tier.description}")
                    self.logger.info(f"New Tier: {new_tier.description}")
                    self.logger.info(f"New Timeframes: {', '.join(new_tier.active_timeframes)}")
                    self.logger.info(f"New Max Position: ${new_tier.max_position_per_asset:.0f}/asset")
                    if new_tier.btc_wallet_required and not self.wallet_manager.config.get('btc_wallet_generated'):
                        self.logger.warning("⚠️  BTC wallet now required - run dashboard.sh to create")
                    self.current_tier = new_tier
                
                # Check error count
                if self.error_count >= self.max_errors:
                    self.logger.critical(f"Max errors ({self.max_errors}) reached. Stopping.")
                    break
                
                # Fetch market data
                self.logger.debug("Fetching market data...")
                data = self._fetch_market_data()
                
                if data is None:
                    self.logger.warning("Failed to fetch market data, waiting before retry")
                    time.sleep(60)  # Wait 1 minute on error
                    continue
                
                # Reset error count on success
                self.error_count = 0
                
                # Analyze market
                self.logger.debug("Analyzing market conditions...")
                intent = self._analyze_market(data)
                
                if intent:
                    self.logger.info(f"🎯 SIGNAL GENERATED: {intent.engine.value} {intent.side.value}")
                    self._execute_intent(intent)
                else:
                    self.logger.debug("No trading signal generated")
                
                # Log current account state
                log_account_state(self.logger, {
                    'equity': self.account.equity,
                    'daily_pnl': self.account.daily_pnl,
                    'daily_pnl_pct': self.account.daily_pnl_pct,
                    'consecutive_losses': self.account.consecutive_losses,
                    'active_positions': len(self.active_positions),
                    'mode': self.account.mode.value
                })
                
                # Export status for dashboard
                status_file = Path('data/live_trader_status.json')
                status_file.parent.mkdir(exist_ok=True)
                try:
                    with open(status_file, 'w') as f:
                        json.dump(self.export_status(), f, indent=2)
                except Exception as e:
                    self.logger.warning(f"Failed to export status: {e}")
                
                # Check profit threshold for BTC wallet funding
                if self.mode == "live":
                    total_profit = self.account.equity - self.config.initial_equity
                    if total_profit > 0:
                        funding_check = self.wallet_manager.check_and_fund_btc_wallet(total_profit)
                        if funding_check.get('threshold_reached'):
                            self.logger.info("🎉 PROFIT THRESHOLD REACHED!")
                            self.logger.info(f"👋 Funding BTC wallet with ${funding_check['funding_amount']}")
                            self.logger.info(f"💼 BTC Address: {funding_check['btc_address']}")
                
                # Sleep until next iteration
                self.logger.debug(f"Sleeping for {update_interval}s until next update")
                time.sleep(update_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                log_error_with_context(self.logger, e, {
                    'function': 'run',
                    'iteration': iteration
                })
                self.error_count += 1
                time.sleep(60)  # Wait before retry
        
        # Cleanup
        self.stats_tracker.end_session()
        self.logger.info("Statistics tracking session ended")
        
        self.logger.info("="*70)
        self.logger.info("HARVEST LIVE TRADER STOPPED")
        self.logger.info(f"Total iterations: {iteration}")
        self.logger.info(f"Final equity: ${self.account.equity:,.2f}")
        
        # Show session summary
        summary = self.stats_tracker.get_summary_for_dashboard()
        self.logger.info(f"Session trades: {summary['today']['trades']}")
        self.logger.info(f"All-time trades: {summary['all_time']['total_trades']}")
        self.logger.info(f"All-time P&L: ${summary['all_time']['total_pnl']:.2f}")
        self.logger.info("="*70)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='HARVEST Live Trading Daemon')
    parser.add_argument('--symbol', type=str, default='ETHUSDT',
                       help='Trading symbol (default: ETHUSDT)')
    parser.add_argument('--mode', type=str, choices=['paper', 'live'], default='paper',
                       help='Trading mode: paper or live (default: paper)')
    parser.add_argument('--capital', type=float, default=10000.0,
                       help='Initial capital in USD (default: 10000)')
    parser.add_argument('--interval', type=int, default=300,
                       help='Update interval in seconds (default: 300)')
    
    args = parser.parse_args()
    
    # Safety check
    if args.mode == 'live':
        print("\n" + "="*70)
        print("⚠️  WARNING: LIVE TRADING MODE")
        print("="*70)
        print("Live trading is NOT IMPLEMENTED and will fail.")
        print("This mode requires exchange API integration.")
        print("Use --mode paper for simulated trading.")
        print("="*70)
        response = input("\nType 'I UNDERSTAND THE RISKS' to proceed: ")
        if response != 'I UNDERSTAND THE RISKS':
            print("Aborting.")
            return
    
    # Create and run trader
    trader = LiveTrader(
        symbol=args.symbol,
        mode=args.mode,
        initial_equity=args.capital
    )
    
    trader.run(update_interval=args.interval)


if __name__ == '__main__':
    main()
