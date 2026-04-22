#!/usr/bin/env python3
"""
HARVEST Dashboard Launcher
Starts the terminal dashboard with proper initialization
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dashboard.terminal_ui import main as dashboard_main


def launch_dashboard():
    """Launch the HARVEST terminal dashboard"""
    
    print("=" * 80)
    print("     HARVEST Trading Dashboard")
    print("=" * 80)
    print()
    
    # Initialize wallet system
    print("🔧 Initializing wallet system...")
    try:
        from core.auto_wallet_manager import AutoWalletManager
        
        manager = AutoWalletManager()
        
        # Ensure BTC wallet exists
        if not manager.wallet_config['btc_wallet']['created']:
            print('📝 Generating BTC wallet for profit collection...')
            result = manager._check_or_create_btc_wallet()
            if result['exists']:
                print(f"✅ BTC Wallet created: {result['address'][:20]}...")
            else:
                print(f"⚠️  Warning: Could not create BTC wallet")
        else:
            btc_addr = manager.wallet_config['btc_wallet']['address']
            print(f"✅ BTC Wallet exists: {btc_addr[:20]}...")
        
        print(f"🆔 Client ID: {manager.client_id[:16]}...")
        
    except Exception as e:
        print(f"❌ Wallet initialization error: {e}")
        sys.exit(1)
    
    print()
    print("🚀 Starting dashboard...")
    print("   Press 'H' for help")
    print("   Press 'W' to connect MetaMask")
    print("   Press 'Q' to quit")
    print()
    
    # Start the dashboard in test mode (with mock data)
    sys.argv = ['dashboard.py', '--test']
    dashboard_main()
    
    print()
    print("✅ Dashboard closed")
    print()


if __name__ == "__main__":
    try:
        launch_dashboard()
    except KeyboardInterrupt:
        print("\n\n✅ Dashboard closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Dashboard error: {e}")
        sys.exit(1)
