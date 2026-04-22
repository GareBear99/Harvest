#!/usr/bin/env python3
"""
Test Wallet Refresh Fix
Verifies that wallet panel updates correctly after MetaMask connection
"""

import sys
import os
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dashboard.terminal_ui import TerminalDashboard


def setup_test_environment():
    """Create test wallet config file"""
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    wallet_config_path = data_dir / 'wallet_config.json'
    
    # Initial state - no connection
    initial_config = {
        'client_id': 'test-client-id',
        'created_at': '2024-12-26T00:00:00',
        'metamask': {
            'connected': False,
            'address': None,
            'last_connected': None
        },
        'btc_wallet': {
            'created': False,
            'address': None,
            'funded': False,
            'balance_usd': 0.0
        },
        'profit_tracking': {
            'total_profit_usd': 0.0,
            'threshold_reached': False,
            'last_funding': None
        }
    }
    
    with open(wallet_config_path, 'w') as f:
        json.dump(initial_config, f, indent=2)
    
    print("✅ Test environment setup complete")
    return wallet_config_path


def simulate_wallet_connection(wallet_config_path):
    """Simulate MetaMask connection by updating config file"""
    print("\n🔄 Simulating MetaMask connection...")
    
    with open(wallet_config_path, 'r') as f:
        config = json.load(f)
    
    # Update to connected state
    config['metamask'] = {
        'connected': True,
        'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
        'chain_id': '0x1',
        'last_connected': '2024-12-26T04:30:00'
    }
    
    with open(wallet_config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Wallet config updated (simulating browser connection)")


def test_wallet_refresh():
    """Test the wallet refresh functionality"""
    print("="*70)
    print("WALLET REFRESH FIX TEST")
    print("="*70)
    
    # Setup test environment
    wallet_config_path = setup_test_environment()
    
    # Create dashboard instance
    print("\n📊 Creating dashboard instance...")
    dashboard = TerminalDashboard(refresh_interval=2)
    
    # Check initial state
    print("\n🔍 Checking initial wallet state...")
    initial_connected = dashboard.data['wallet']['metamask']['connected']
    initial_address = dashboard.data['wallet']['metamask']['address']
    
    print(f"   Connected: {initial_connected}")
    print(f"   Address: {initial_address}")
    
    assert initial_connected == False, "Initial state should be disconnected"
    assert initial_address == None, "Initial address should be None"
    print("   ✅ Initial state correct")
    
    # Simulate wallet connection
    simulate_wallet_connection(wallet_config_path)
    time.sleep(0.5)  # Brief delay to ensure file write completes
    
    # Test force wallet refresh
    print("\n🔄 Testing _force_wallet_refresh() method...")
    dashboard._force_wallet_refresh()
    
    # Check updated state
    print("\n🔍 Checking updated wallet state...")
    updated_connected = dashboard.data['wallet']['metamask']['connected']
    updated_address = dashboard.data['wallet']['metamask']['address']
    
    print(f"   Connected: {updated_connected}")
    print(f"   Address: {updated_address}")
    
    # Verify the fix worked
    assert updated_connected == True, "Should be connected after refresh"
    assert updated_address is not None, "Address should be set after refresh"
    assert updated_address.startswith('0x'), "Address should be valid Ethereum address"
    
    print("   ✅ Wallet panel data updated successfully!")
    
    # Test that manual refresh also works
    print("\n🔄 Testing manual refresh (R key simulation)...")
    
    # Simulate disconnection
    with open(wallet_config_path, 'r') as f:
        config = json.load(f)
    config['metamask']['connected'] = False
    config['metamask']['address'] = None
    with open(wallet_config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Call refresh_data (simulates pressing 'R')
    dashboard.refresh_data()
    
    # Verify disconnect was detected
    refreshed_connected = dashboard.data['wallet']['metamask']['connected']
    print(f"   Connected after refresh: {refreshed_connected}")
    assert refreshed_connected == False, "Should detect disconnection on refresh"
    print("   ✅ Manual refresh working correctly!")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED")
    print("="*70)
    print("\n📋 Summary:")
    print("   ✅ Force wallet refresh bypasses coordinator")
    print("   ✅ Wallet panel data updates immediately")
    print("   ✅ Manual refresh (R key) includes wallet check")
    print("   ✅ Both connection and disconnection detected")
    print("\n🎯 Fix verified: Wallet stats panel will now refresh correctly!")


if __name__ == '__main__':
    try:
        test_wallet_refresh()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
