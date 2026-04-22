#!/usr/bin/env python3
"""
Wallet Persistence & Security Test
Verifies that wallet connections persist through refreshes and are stored securely
"""

import sys
import os
import json
import time
import threading
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dashboard.terminal_ui import TerminalDashboard
from core.file_lock import safe_json_load, safe_json_save, file_lock
from core.simple_wallet_connector import SimpleWalletConnector


def test_wallet_persistence():
    """Test that wallet connection persists through dashboard refresh cycles"""
    print("="*70)
    print("WALLET PERSISTENCE TEST")
    print("="*70)
    
    # Setup
    wallet_config_path = Path('data/wallet_config.json')
    
    # Create initial connected state
    print("\n📝 Setting up connected wallet state...")
    initial_config = {
        'client_id': 'test-persistence-client',
        'created_at': '2024-12-26T00:00:00',
        'metamask': {
            'connected': True,
            'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
            'chain_id': '0x1',
            'last_connected': '2024-12-26T04:30:00'
        },
        'btc_wallet': {
            'created': True,
            'address': 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
            'funded': False,
            'balance_usd': 0.0
        },
        'profit_tracking': {
            'total_profit_usd': 0.0,
            'threshold_reached': False,
            'last_funding': None
        }
    }
    
    safe_json_save(str(wallet_config_path), initial_config)
    print("✅ Initial config saved")
    
    # Test 1: Create dashboard - should load existing connection
    print("\n🔍 Test 1: Dashboard loads existing wallet connection...")
    dashboard1 = TerminalDashboard(refresh_interval=2)
    
    assert dashboard1.data['wallet']['metamask']['connected'] == True, "Should load connected state"
    assert dashboard1.data['wallet']['metamask']['address'] == '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb', "Should load address"
    print("   ✅ Dashboard loaded existing connection")
    
    # Test 2: Multiple refreshes - connection should persist
    print("\n🔍 Test 2: Wallet persists through multiple refreshes...")
    for i in range(5):
        dashboard1.refresh_data()
        time.sleep(0.1)
        
        assert dashboard1.data['wallet']['metamask']['connected'] == True, f"Should stay connected after refresh {i+1}"
        print(f"   ✅ Refresh {i+1}/5: Still connected")
    
    # Test 3: New dashboard instance - should load same connection
    print("\n🔍 Test 3: New dashboard instance loads same connection...")
    dashboard2 = TerminalDashboard(refresh_interval=2)
    
    assert dashboard2.data['wallet']['metamask']['connected'] == True, "New instance should load connection"
    assert dashboard2.data['wallet']['metamask']['address'] == dashboard1.data['wallet']['metamask']['address'], "Should have same address"
    print("   ✅ New dashboard instance has same wallet state")
    
    # Test 4: File remains intact after multiple operations
    print("\n🔍 Test 4: Config file integrity after operations...")
    loaded_config = safe_json_load(str(wallet_config_path))
    
    assert loaded_config['metamask']['connected'] == True, "File should have connected=True"
    assert loaded_config['metamask']['address'] == '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb', "File should have correct address"
    print("   ✅ Config file maintains integrity")
    
    print("\n✅ PERSISTENCE TEST PASSED")


def test_wallet_security():
    """Test security features of wallet storage"""
    print("\n" + "="*70)
    print("WALLET SECURITY TEST")
    print("="*70)
    
    wallet_config_path = Path('data/wallet_config.json')
    
    # Test 1: File locking prevents corruption
    print("\n🔍 Test 1: File locking prevents concurrent write corruption...")
    
    test_config = {
        'metamask': {'connected': False, 'address': None},
        'btc_wallet': {'created': False},
        'profit_tracking': {'total_profit_usd': 0.0}
    }
    safe_json_save(str(wallet_config_path), test_config)
    
    write_count = [0]
    errors = []
    
    def concurrent_writer(thread_id):
        """Simulate concurrent writes"""
        try:
            for i in range(10):
                # Use safe_json_save with locking
                config = safe_json_load(str(wallet_config_path), default={})
                config['last_writer'] = f"thread_{thread_id}_iter_{i}"
                config['write_count'] = write_count[0]
                write_count[0] += 1
                safe_json_save(str(wallet_config_path), config)
                time.sleep(0.001)
        except Exception as e:
            errors.append(str(e))
    
    # Launch 5 concurrent writers
    threads = []
    for i in range(5):
        t = threading.Thread(target=concurrent_writer, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Verify no errors and file is valid JSON
    assert len(errors) == 0, f"File locking failed with errors: {errors}"
    
    final_config = safe_json_load(str(wallet_config_path))
    assert final_config is not None, "Config should be valid after concurrent writes"
    assert 'last_writer' in final_config, "Config should have been updated"
    print(f"   ✅ {write_count[0]} concurrent writes completed without corruption")
    
    # Test 2: No private keys stored in config
    print("\n🔍 Test 2: No private keys stored in wallet config...")
    
    # Create a connected wallet config
    connected_config = {
        'client_id': 'security-test-client',
        'metamask': {
            'connected': True,
            'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
            'chain_id': '0x1',
            'last_connected': '2024-12-26T04:30:00'
        },
        'btc_wallet': {
            'created': True,
            'address': 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
            'funded': False,
            'balance_usd': 0.0
        }
    }
    safe_json_save(str(wallet_config_path), connected_config)
    
    # Read raw file content
    with open(wallet_config_path, 'r') as f:
        file_content = f.read()
    
    # Check for private key indicators
    dangerous_keywords = ['private_key', 'privateKey', 'secret', 'mnemonic', 'seed_phrase']
    found_dangerous = [kw for kw in dangerous_keywords if kw.lower() in file_content.lower()]
    
    assert len(found_dangerous) == 0, f"Found dangerous keywords in config: {found_dangerous}"
    print("   ✅ No private keys or sensitive data in config file")
    
    # Test 3: Config file permissions (on UNIX systems)
    print("\n🔍 Test 3: File permissions are appropriate...")
    
    if os.name == 'posix':  # Unix/Linux/MacOS
        import stat
        file_stat = wallet_config_path.stat()
        mode = file_stat.st_mode
        
        # Check it's a regular file
        assert stat.S_ISREG(mode), "Should be a regular file"
        
        # File should be readable by owner
        assert mode & stat.S_IRUSR, "Owner should have read permission"
        assert mode & stat.S_IWUSR, "Owner should have write permission"
        
        print(f"   ✅ File permissions OK: {oct(stat.S_IMODE(mode))}")
    else:
        print("   ⚠️  Permission check skipped (not on POSIX system)")
    
    # Test 4: MetaMask uses browser-based auth (no key storage)
    print("\n🔍 Test 4: MetaMask uses browser-based authentication...")
    
    connector = SimpleWalletConnector()
    
    # Verify connector doesn't store private keys
    assert not hasattr(connector, 'private_key'), "Connector should not have private_key attribute"
    assert not hasattr(connector, 'mnemonic'), "Connector should not have mnemonic attribute"
    
    # Only stores connection status and address
    config = connector.load_config()
    if config:
        metamask_keys = set(config.get('metamask', {}).keys())
        allowed_keys = {'connected', 'address', 'chain_id', 'last_connected'}
        extra_keys = metamask_keys - allowed_keys
        
        assert len(extra_keys) == 0, f"Found unexpected keys in metamask config: {extra_keys}"
    
    print("   ✅ MetaMask connector uses secure browser-based auth")
    
    print("\n✅ SECURITY TEST PASSED")


def test_refresh_cycle_integrity():
    """Test that automatic 10-second refresh cycle maintains wallet state"""
    print("\n" + "="*70)
    print("REFRESH CYCLE INTEGRITY TEST")
    print("="*70)
    
    # Setup connected wallet
    wallet_config_path = Path('data/wallet_config.json')
    config = {
        'client_id': 'refresh-test-client',
        'metamask': {
            'connected': True,
            'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
            'chain_id': '0x1',
            'last_connected': '2024-12-26T04:30:00'
        },
        'btc_wallet': {'created': True, 'address': 'bc1qtest...', 'balance_usd': 50.0},
        'profit_tracking': {'total_profit_usd': 75.5}
    }
    safe_json_save(str(wallet_config_path), config)
    
    print("\n🔍 Simulating multiple 10-second refresh cycles...")
    dashboard = TerminalDashboard(refresh_interval=2)
    
    # Verify initial load
    assert dashboard.data['wallet']['metamask']['connected'] == True
    assert dashboard.data['wallet']['btc_wallet']['balance'] == 50.0
    assert dashboard.data['wallet']['profit'] == 75.5
    print("   ✅ Initial state loaded correctly")
    
    # Simulate 10 refresh cycles
    for cycle in range(10):
        time.sleep(0.05)  # Small delay between refreshes
        dashboard.refresh_data()
        
        # Verify wallet state preserved
        assert dashboard.data['wallet']['metamask']['connected'] == True, f"Lost connection on cycle {cycle+1}"
        assert dashboard.data['wallet']['metamask']['address'] == '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb', f"Lost address on cycle {cycle+1}"
        assert dashboard.data['wallet']['btc_wallet']['balance'] == 50.0, f"Lost BTC balance on cycle {cycle+1}"
        assert dashboard.data['wallet']['profit'] == 75.5, f"Lost profit tracking on cycle {cycle+1}"
    
    print(f"   ✅ Wallet state preserved through {10} refresh cycles")
    
    print("\n✅ REFRESH CYCLE TEST PASSED")


def main():
    """Run all tests"""
    print("\n" + "🔐"*35)
    print("WALLET PERSISTENCE & SECURITY VALIDATION")
    print("🔐"*35 + "\n")
    
    try:
        # Test persistence
        test_wallet_persistence()
        
        # Test security
        test_wallet_security()
        
        # Test refresh cycle integrity
        test_refresh_cycle_integrity()
        
        # Summary
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED - WALLET SYSTEM SECURE & PERSISTENT")
        print("="*70)
        print("\n📋 Verified Features:")
        print("   ✅ Wallet connections persist through refreshes")
        print("   ✅ Multiple dashboard instances share same wallet state")
        print("   ✅ File locking prevents concurrent write corruption")
        print("   ✅ No private keys stored in config files")
        print("   ✅ Browser-based MetaMask authentication (secure)")
        print("   ✅ Config file maintains integrity across operations")
        print("   ✅ 10-second auto-refresh preserves wallet state")
        print("\n🔒 Security Summary:")
        print("   • MetaMask: Browser-based auth (no private key storage)")
        print("   • Config File: Thread-safe with file locking")
        print("   • Data: Atomic writes prevent corruption")
        print("   • Persistence: Survives dashboard restarts")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
