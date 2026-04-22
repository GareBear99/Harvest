#!/usr/bin/env python3
"""Check wallet connection and status"""

from core.auto_wallet_manager import AutoWalletManager
from web3 import Web3
import json
import os

print('='*80)
print('WALLET CONNECTION STATUS CHECK')
print('='*80)
print()

# Initialize wallet manager
manager = AutoWalletManager()

# Check if wallet exists and is loaded
if manager.client_id:
    print('✅ Wallet System: Initialized')
    print(f'   Client ID: {manager.client_id[:16]}...')
else:
    print('❌ Wallet System: Not initialized')

print()

# Check wallet address
if manager.address:
    print(f'✅ Wallet Address: {manager.address}')
else:
    print('❌ Wallet Address: Not found')

print()

# Check Web3 connection
if manager.w3:
    try:
        is_connected = manager.w3.is_connected()
        status = "Connected" if is_connected else "Disconnected"
        print(f'✅ Web3 Connection: {status}')
        if is_connected:
            chain_id = manager.w3.eth.chain_id
            chain_name = "Mainnet" if chain_id == 1 else f"Chain {chain_id}"
            print(f'   Chain ID: {chain_id} ({chain_name})')
    except Exception as e:
        print(f'❌ Web3 Connection Error: {e}')
else:
    print('❌ Web3: Not initialized')

print()

# Check wallet balance (if connected)
if manager.address and manager.w3:
    try:
        balance_wei = manager.w3.eth.get_balance(manager.address)
        balance_eth = Web3.from_wei(balance_wei, 'ether')
        print(f'✅ Wallet Balance: {balance_eth:.6f} ETH')
    except Exception as e:
        print(f'⚠️  Balance Check Failed: {e}')

print()
print('='*80)
print('WALLET FILE CHECK')
print('='*80)
print()

# Check if wallet file exists
wallet_path = os.path.expanduser('~/.harvest_wallet/wallet.json')
if os.path.exists(wallet_path):
    print(f'✅ Wallet File: Found')
    print(f'   Path: {wallet_path}')
    try:
        with open(wallet_path, 'r') as f:
            wallet_data = json.load(f)
            print(f'   Keys: {list(wallet_data.keys())}')
    except Exception as e:
        print(f'⚠️  Could not read: {e}')
else:
    print(f'❌ Wallet File: Not found')
    print(f'   Expected: {wallet_path}')

print()
print('='*80)
print('METAMASK CONNECTION')
print('='*80)
print()
print('ℹ️  MetaMask Integration:')
print('   - HARVEST uses an auto-generated wallet (not MetaMask directly)')
print('   - The wallet is stored locally at ~/.harvest_wallet/')
print('   - For founder fees, you will need to send ETH to the address shown above')
print()
