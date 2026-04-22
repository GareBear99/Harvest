#!/usr/bin/env python3
"""
HARVEST CLI - Terminal-based trading bot interface
"""
import sys
import os
import argparse
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import Config
# from backtester import Backtester  # Not currently available


class HarvestCLI:
    """Command-line interface for HARVEST trading bot."""
    
    def __init__(self):
        self.config = Config()
        self.version = "1.0.0"
    
    def run_backtest(self, symbol="ETHUSDT", days=30, output=None):
        """Run backtest on historical data."""
        print(f"🚀 HARVEST v{self.version} - Running backtest")
        print(f"Symbol: {symbol}, Period: {days} days\n")
        
        try:
            bt = Backtester(symbol=symbol, initial_equity=self.config.initial_equity)
            data = bt.fetch_data(days=days)
            
            if not data:
                print("❌ Failed to fetch market data")
                return 1
            
            results = bt.run_backtest(data)
            
            # Export results
            output_file = output or f"{symbol.lower()}_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            bt.export_results(output_file)
            
            print(f"\n✅ Backtest complete")
            print(f"📊 Results exported to: {output_file}")
            
            return 0
        
        except Exception as e:
            print(f"❌ Error during backtest: {e}")
            return 1
    
    def validate(self):
        """Run validation tests."""
        print(f"🔍 HARVEST v{self.version} - Running validation tests\n")
        
        try:
            # Run indicator tests
            from tests.test_indicators import run_all_tests
            success = run_all_tests()
            
            if success:
                print("\n✅ All validation tests passed")
                return 0
            else:
                print("\n❌ Some tests failed")
                return 1
        
        except Exception as e:
            print(f"❌ Error during validation: {e}")
            return 1
    
    def live(self, symbol="ETHUSDT", mode="paper"):
        """Run live trading bot (paper trading by default)."""
        print(f"🤖 HARVEST v{self.version} - Live Trading Mode")
        print(f"Symbol: {symbol}, Mode: {mode}\n")
        
        if mode != "paper":
            print("⚠️  WARNING: Live trading with real money!")
            print("⚠️  This feature is NOT YET FULLY IMPLEMENTED")
            print("⚠️  Requires exchange API integration")
            print("⚠️  Use --mode paper for paper trading only")
            return 1
        
        print("📝 Paper trading mode (simulated signals only)")
        print("🔄 Starting trading bot daemon...")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            # Import and run live trader
            from live_trader import LiveTrader
            
            trader = LiveTrader(
                symbol=symbol,
                mode=mode,
                initial_equity=self.config.initial_equity
            )
            
            # Run with 5-minute intervals
            trader.run(update_interval=300)
            return 0
        
        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped by user")
            return 0
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    def status(self):
        """Show system status."""
        print(f"📊 HARVEST v{self.version} - System Status\n")
        
        print("Configuration:")
        print(f"  Initial Equity: ${self.config.initial_equity:,.2f}")
        print(f"  Max Daily Drawdown: {self.config.max_daily_drawdown_pct}%")
        print(f"  Max Consecutive Losses: {self.config.max_consecutive_losses}")
        print(f"\nER-90 Strategy:")
        print(f"  RSI Thresholds: {self.config.er90_rsi_upper}/{self.config.er90_rsi_lower}")
        print(f"  Leverage: {self.config.er90_leverage_min}-{self.config.er90_leverage_max}x")
        print(f"  Risk per Trade: {self.config.er90_risk_pct_min}-{self.config.er90_risk_pct_max}%")
        print(f"\nSIB Strategy:")
        print(f"  ADX Threshold: {self.config.sib_adx_threshold}")
        print(f"  Leverage: {self.config.sib_leverage_min}-{self.config.sib_leverage_max}x")
        print(f"  Risk per Trade: {self.config.sib_risk_pct_min}-{self.config.sib_risk_pct_max}%")
        
        return 0
    
    def info(self):
        """Show system information."""
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║           HARVEST - Dual-Engine Trading System              ║
║                     Version {self.version}                           ║
╚══════════════════════════════════════════════════════════════╝

📊 DESCRIPTION
  Automated leveraged trading system with dual strategies:
  - ER-90: Exhaustion reversion (85-92% win rate target)
  - SIB: Single impulse breakout (trend following)

⚠️  RISK WARNING
  This system uses leverage (10-40x) which amplifies both
  gains and losses. You can lose more than your initial capital.
  Trade responsibly and never risk more than you can afford to lose.

🛡️  SAFETY FEATURES
  ✓ Risk governor (cannot be bypassed)
  ✓ Mandatory stop-losses on every trade
  ✓ 2% max daily drawdown limit
  ✓ Max 2 consecutive losses before pause
  ✓ Liquidation buffer validation
  ✓ Regime-based strategy switching
  ✓ MetaMask wallet integration for on-chain ETH trading

📦 COMPONENTS
  • Data ingestion (Binance API)
  • Technical indicators (RSI, ATR, EMA, ADX)
  • Regime classifier
  • Risk governance
  • Backtesting framework
  • Execution intent generator
  • MetaMask connector (Web3)

📚 DOCUMENTATION
  README: ./README.md
  Validation: ./VALIDATION_PROGRESS.md
  MetaMask Setup: ./METAMASK_SETUP.md
  GitHub: https://github.com/yourusername/harvest

💬 SUPPORT
  Issues: https://github.com/yourusername/harvest/issues
  Discussions: https://github.com/yourusername/harvest/discussions

⚖️  LICENSE
  See LICENSE file for terms and conditions
""")
        return 0
    
    def wallet_balance(self):
        """Check ETH wallet balance."""
        print("\n" + "="*70)
        print("WALLET BALANCE")
        print("="*70 + "\n")
        
        try:
            from core.metamask_connector import setup_metamask_connection
            
            connector = setup_metamask_connection()
            
            if not connector:
                print("❌ Failed to connect to wallet")
                print("\n💡 Make sure ETH_RPC_URL and ETH_PRIVATE_KEY are set")
                print("   See METAMASK_SETUP.md for instructions")
                return 1
            
            print(f"📍 Address: {connector.account.address}")
            
            balance = connector.get_eth_balance()
            if balance is not None:
                print(f"💰 Balance: {balance:.6f} ETH")
                
                print(f"\n⛽ Current gas prices:")
                gas_prices = connector.get_gas_price()
                for speed, price_wei in gas_prices.items():
                    gwei = price_wei / 10**9
                    print(f"  {speed.capitalize():8} {gwei:6.2f} Gwei")
                return 0
            else:
                print("❌ Failed to fetch balance")
                return 1
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    
    def wallet_gas(self):
        """Check current gas prices."""
        print("\n" + "="*70)
        print("GAS PRICES")
        print("="*70 + "\n")
        
        try:
            from core.metamask_connector import setup_metamask_connection
            
            connector = setup_metamask_connection()
            
            if not connector:
                print("❌ Failed to connect to network")
                return 1
            
            gas_prices = connector.get_gas_price()
            
            print(f"⛽ Current gas prices (Chain ID {connector.chain_id}):\n")
            
            # Calculate cost for standard transfer (21,000 gas)
            gas_limit = 21000
            
            for speed, price_wei in gas_prices.items():
                gwei = price_wei / 10**9
                cost_eth = (gas_limit * price_wei) / 10**18
                print(f"  {speed.capitalize():8} {gwei:6.2f} Gwei  (~{cost_eth:.6f} ETH per tx)")
            
            print(f"\n📊 Estimate based on {gas_limit:,} gas (simple transfer)")
            return 0
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    
    def wallet_connect(self, rpc_url=None, chain_id=1, testnet=False):
        """Connect to MetaMask wallet and test connection."""
        print("\n" + "="*70)
        print("METAMASK WALLET CONNECT")
        print("="*70 + "\n")
        
        # Auto-detect testnet chain IDs
        if testnet:
            if chain_id == 1:  # If default mainnet, switch to Sepolia
                chain_id = 11155111
                print("🧪 Testnet mode: Using Sepolia (Chain ID 11155111)")
        
        chain_names = {
            1: "Ethereum Mainnet",
            5: "Goerli Testnet (deprecated)",
            11155111: "Sepolia Testnet",
            137: "Polygon Mainnet",
            80001: "Polygon Mumbai Testnet"
        }
        
        print(f"🌐 Target Network: {chain_names.get(chain_id, f'Chain ID {chain_id}')}")
        
        # Check environment or use provided RPC
        if rpc_url is None:
            rpc_url = os.getenv('ETH_RPC_URL')
        
        private_key = os.getenv('ETH_PRIVATE_KEY')
        
        if not rpc_url:
            print("\n❌ No RPC URL provided!\n")
            print("💡 Options:")
            print("   1. Set environment variable:")
            print("      export ETH_RPC_URL='https://mainnet.infura.io/v3/YOUR-PROJECT-ID'")
            print("\n   2. Use --rpc-url flag:")
            print("      python cli.py wallet connect --rpc-url https://...")
            print("\n📚 See METAMASK_SETUP.md for detailed instructions")
            return 1
        
        print(f"\n📡 RPC URL: {rpc_url}")
        print(f"🔑 Private Key: {'✅ Set (secure)' if private_key else '⚠️  Not set (read-only mode)'}")
        
        if not private_key:
            print("\n⚠️  WARNING: No private key provided")
            print("   You can view balances but cannot send transactions.")
            print("   To enable transactions, set ETH_PRIVATE_KEY environment variable.")
            print("   ⚠️  NEVER commit private keys to git!\n")
        
        # Attempt connection
        print("\n🔌 Connecting to Ethereum network...\n")
        
        try:
            from core.metamask_connector import setup_metamask_connection
            
            connector = setup_metamask_connection(
                private_key=private_key,
                rpc_url=rpc_url,
                chain_id=chain_id
            )
            
            if not connector:
                print("❌ Connection failed!\n")
                print("💡 Troubleshooting:")
                print("   - Check your RPC URL is valid")
                print("   - Verify network is accessible")
                print("   - Try a different RPC endpoint")
                return 1
            
            # Connection successful
            print("✅ Successfully connected to Ethereum network!\n")
            print("="*70)
            print("CONNECTION DETAILS")
            print("="*70 + "\n")
            
            print(f"🌐 Network Information:")
            print(f"   Chain ID:      {connector.w3.eth.chain_id}")
            print(f"   Chain Name:    {chain_names.get(connector.w3.eth.chain_id, 'Unknown')}")
            print(f"   Latest Block:  {connector.w3.eth.block_number:,}")
            print(f"   Syncing:       {connector.w3.eth.syncing if connector.w3.eth.syncing else '✅ Synced'}")
            
            # Show account info if private key provided
            if connector.account:
                print(f"\n📍 Wallet Address:")
                print(f"   {connector.account.address}")
                
                # Get balance
                print(f"\n💰 Account Balance:")
                balance = connector.get_eth_balance()
                print(f"   {balance:.6f} ETH")
                
                # Convert to USD equivalent (would need price oracle)
                print(f"\n💵 Estimated Value:")
                print(f"   ~$--- USD (requires price oracle)")
            
            # Get gas prices
            print(f"\n⛽ Current Gas Prices:")
            gas_prices = connector.get_gas_price()
            gas_limit = 21000  # Standard transfer
            
            for speed, price_wei in gas_prices.items():
                gwei = price_wei / 10**9
                cost_eth = (gas_limit * price_wei) / 10**18
                print(f"   {speed.capitalize():8}  {gwei:6.2f} Gwei  (~{cost_eth:.6f} ETH per tx)")
            
            print(f"\n📊 Gas estimate based on {gas_limit:,} gas (simple transfer)")
            
            # Connection test complete
            print("\n" + "="*70)
            print("✅ CONNECTION TEST COMPLETE")
            print("="*70 + "\n")
            
            if connector.account:
                print("✓ Wallet connected successfully")
                print("✓ Ready for trading operations")
                print("\n💡 Next steps:")
                print("   - Check balance: python cli.py wallet balance")
                print("   - View gas prices: python cli.py wallet gas")
                print("   - Run backtest: python cli.py backtest")
            else:
                print("✓ Network connected (read-only mode)")
                print("\n💡 To enable transactions:")
                print("   export ETH_PRIVATE_KEY='0xYOUR_PRIVATE_KEY'")
            
            return 0
        
        except ImportError as e:
            print(f"❌ Missing dependencies: {e}\n")
            print("💡 Install required packages:")
            print("   pip install web3")
            return 1
        except Exception as e:
            print(f"❌ Connection error: {e}\n")
            print("💡 Common issues:")
            print("   - Invalid RPC URL format")
            print("   - Network connectivity problems")
            print("   - Invalid private key format")
            print("   - Firewall blocking connection")
            return 1
    
    def wallet_setup(self):
        """Setup wallet with browser connection."""
        print("\n" + "="*70)
        print("WALLET SETUP")
        print("="*70 + "\n")
        
        try:
            from core.auto_wallet_manager import AutoWalletManager
            
            manager = AutoWalletManager()
            
            print("👋 Welcome to HARVEST Wallet Setup!")
            print("\nThis will:")
            print("  1. Connect your MetaMask wallet (browser)")
            print("  2. Create a Bitcoin trading wallet")
            print("  3. Validate minimum balance ($10)")
            print("\n" + "="*70)
            
            # Run validation first
            validation = manager.validate_on_startup()
            
            if validation['ready_for_live_trading']:
                print("\n✅ System already fully configured!")
                print("\n💰 Status:")
                print(f"  MetaMask: Connected")
                print(f"  BTC Wallet: Created")
                print(f"  Balance: Sufficient")
                return 0
            
            # Setup MetaMask if needed
            if not validation['metamask_connected']:
                print("\n🔗 Step 1: Connect MetaMask")
                print("   A browser window will open...")
                
                result = manager.connect_metamask_browser()
                
                if not result['success']:
                    print(f"\n❌ Setup failed: {result['message']}")
                    return 1
                
                print(f"\n✅ MetaMask connected: {result['address']}")
            
            # Re-validate
            validation = manager.validate_on_startup()
            
            if validation['ready_for_live_trading']:
                print("\n" + "="*70)
                print("✅ WALLET SETUP COMPLETE!")
                print("="*70)
                print("\n🚀 You're ready for live trading!")
                print("\n💡 Next steps:")
                print("   - Run backtest: python cli.py backtest")
                print("   - Start paper trading: python cli.py live --mode paper")
                print("   - Start live trading: python cli.py live --mode live")
                return 0
            else:
                print("\n⚠️  Setup incomplete. Remaining actions:")
                for action in validation['actions_required']:
                    print(f"  - {action['message']}")
                return 1
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    def wallet_status_extended(self):
        """Show extended wallet status with all details."""
        print("\n" + "="*70)
        print("WALLET STATUS")
        print("="*70 + "\n")
        
        try:
            from core.auto_wallet_manager import AutoWalletManager
            
            manager = AutoWalletManager()
            status = manager.get_status()
            
            print("🆔 Client ID: " + status['client_id'][:8] + "...")
            print("\n🦊 MetaMask:")
            if status['metamask']['connected']:
                print(f"  ✅ Connected: {status['metamask']['address']}")
                print(f"  🕒 Last connected: {status['metamask']['last_connected'][:19]}")
            else:
                print("  ❌ Not connected")
            
            print("\n₿ Bitcoin Wallet:")
            if status['btc_wallet']['created']:
                print(f"  ✅ Created: {status['btc_wallet']['address']}")
                print(f"  💵 Funded: {'Yes' if status['btc_wallet']['funded'] else 'No'}")
                print(f"  💰 Balance: ${status['btc_wallet']['balance_usd']:.2f}")
                if status['btc_wallet'].get('mnemonic_file'):
                    print(f"  🔐 Mnemonic: {status['btc_wallet']['mnemonic_file']}")
            else:
                print("  ❌ Not created yet")
            
            print("\n📈 Profit Tracking:")
            print(f"  Total Profit: ${status['profit_tracking']['total_profit_usd']:.2f}")
            print(f"  Threshold: ${status['thresholds']['profit_threshold']:.2f}")
            if status['profit_tracking']['threshold_reached']:
                print(f"  ✅ Threshold reached!")
                print(f"  🕒 Last funding: {status['profit_tracking']['last_funding'][:19]}")
            else:
                remaining = status['thresholds']['profit_threshold'] - status['profit_tracking']['total_profit_usd']
                print(f"  ⏳ Remaining: ${remaining:.2f}")
            
            print("\n⚙️  Thresholds:")
            print(f"  Min Live Balance: ${status['thresholds']['min_live_balance']:.2f}")
            print(f"  Profit Threshold: ${status['thresholds']['profit_threshold']:.2f}")
            print(f"  Funding Amount: ${status['thresholds']['funding_amount']:.2f}")
            
            return 0
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return 1
    
    def wallet_info(self):
        """Show wallet connection info."""
        print("\n" + "="*70)
        print("WALLET INFO")
        print("="*70 + "\n")
        
        # Check environment
        rpc_url = os.getenv('ETH_RPC_URL')
        has_key = bool(os.getenv('ETH_PRIVATE_KEY'))
        
        print(f"📡 RPC URL: {rpc_url if rpc_url else '❌ Not set'}")
        print(f"🔑 Private Key: {'✅ Set' if has_key else '❌ Not set'}")
        
        if not rpc_url or not has_key:
            print(f"\n⚠️  Missing configuration!")
            print(f"\n💡 Set environment variables:")
            print(f"   export ETH_RPC_URL='https://mainnet.infura.io/v3/YOUR-PROJECT-ID'")
            print(f"   export ETH_PRIVATE_KEY='0xYOUR_PRIVATE_KEY'")
            print(f"\n📚 See METAMASK_SETUP.md for detailed instructions")
            return 1
        
        # Try to connect
        try:
            from core.metamask_connector import setup_metamask_connection
            
            connector = setup_metamask_connection()
            
            if connector:
                print(f"\n✅ Connected to Ethereum network")
                print(f"\n🌐 Network details:")
                print(f"  Chain ID:      {connector.chain_id}")
                print(f"  Latest block:  {connector.w3.eth.block_number:,}")
                print(f"\n📍 Wallet address:")
                print(f"  {connector.account.address}")
                
                balance = connector.get_eth_balance()
                if balance is not None:
                    print(f"\n💰 Balance: {balance:.6f} ETH")
                return 0
            else:
                print(f"\n❌ Failed to connect to network")
                print(f"\n💡 Check your RPC URL and try again")
                return 1
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="HARVEST - Dual-Engine Leveraged Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  harvest backtest --symbol ETHUSDT --days 30
  harvest validate
  harvest live --mode paper
  harvest status
  harvest info
  harvest wallet connect
  harvest wallet connect --testnet
  harvest wallet connect --rpc-url https://mainnet.infura.io/v3/YOUR-KEY
  harvest wallet info
  harvest wallet balance
  harvest wallet gas

For more information, visit: https://github.com/yourusername/harvest
"""
    )
    
    parser.add_argument('--version', action='version', version='HARVEST 1.0.0')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run backtest on historical data')
    backtest_parser.add_argument('--symbol', default='ETHUSDT', help='Trading symbol (default: ETHUSDT)')
    backtest_parser.add_argument('--days', type=int, default=30, help='Days of history (default: 30)')
    backtest_parser.add_argument('--output', help='Output file path')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Run validation tests')
    
    # Live command
    live_parser = subparsers.add_parser('live', help='Run live trading bot')
    live_parser.add_argument('--symbol', default='ETHUSDT', help='Trading symbol (default: ETHUSDT)')
    live_parser.add_argument('--mode', choices=['paper', 'live'], default='paper',
                           help='Trading mode (default: paper)')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show system information')
    
    # Wallet commands
    wallet_parser = subparsers.add_parser('wallet', help='MetaMask wallet operations')
    wallet_subparsers = wallet_parser.add_subparsers(dest='wallet_command', help='Wallet commands')
    
    wallet_setup_parser = wallet_subparsers.add_parser('setup', help='Interactive wallet setup (browser connection)')
    wallet_status_parser = wallet_subparsers.add_parser('status', help='Show complete wallet status')
    
    wallet_connect_parser = wallet_subparsers.add_parser('connect', help='Connect to MetaMask wallet and test')
    wallet_connect_parser.add_argument('--rpc-url', help='Ethereum RPC URL (or set ETH_RPC_URL env var)')
    wallet_connect_parser.add_argument('--chain-id', type=int, default=1, help='Chain ID (1=Mainnet, 11155111=Sepolia)')
    wallet_connect_parser.add_argument('--testnet', action='store_true', help='Use testnet (Sepolia)')
    
    wallet_balance_parser = wallet_subparsers.add_parser('balance', help='Check ETH balance')
    wallet_gas_parser = wallet_subparsers.add_parser('gas', help='Check gas prices')
    wallet_info_parser = wallet_subparsers.add_parser('info', help='Show wallet connection info')
    
    args = parser.parse_args()
    
    # Show help if no command
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute command
    cli = HarvestCLI()
    
    if args.command == 'backtest':
        return cli.run_backtest(args.symbol, args.days, args.output)
    elif args.command == 'validate':
        return cli.validate()
    elif args.command == 'live':
        return cli.live(args.symbol, args.mode)
    elif args.command == 'status':
        return cli.status()
    elif args.command == 'info':
        return cli.info()
    elif args.command == 'wallet':
        if not args.wallet_command:
            wallet_parser.print_help()
            return 0
        
        if args.wallet_command == 'setup':
            return cli.wallet_setup()
        elif args.wallet_command == 'status':
            return cli.wallet_status_extended()
        elif args.wallet_command == 'connect':
            return cli.wallet_connect(
                rpc_url=args.rpc_url,
                chain_id=args.chain_id,
                testnet=args.testnet
            )
        elif args.wallet_command == 'balance':
            return cli.wallet_balance()
        elif args.wallet_command == 'gas':
            return cli.wallet_gas()
        elif args.wallet_command == 'info':
            return cli.wallet_info()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
