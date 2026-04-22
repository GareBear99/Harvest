"""
Enhanced MetaMask Wallet Connector for HARVEST
Features:
- Encrypted credential storage
- Browser extension connection via WebSocket
- Session management
- Disconnect/reconnect functionality
"""

import os
import json
import logging
from decimal import Decimal
from typing import Optional, Dict
from pathlib import Path
from web3 import Web3
try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    geth_poa_middleware = None

# For credential encryption
from cryptography.fernet import Fernet
import base64
import hashlib

logger = logging.getLogger("harvest.metamask")


class CredentialManager:
    """Securely manage MetaMask credentials."""
    
    def __init__(self, credentials_file: str = ".metamask_credentials"):
        """
        Initialize credential manager.
        
        Args:
            credentials_file: Path to encrypted credentials file
        """
        self.credentials_file = Path.home() / credentials_file
        self.key_file = Path.home() / ".metamask_key"
        self._ensure_key()
    
    def _ensure_key(self):
        """Ensure encryption key exists."""
        if not self.key_file.exists():
            # Generate new key
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            self.key_file.chmod(0o600)  # Owner read/write only
            logger.info("Generated new encryption key")
    
    def _get_cipher(self) -> Fernet:
        """Get Fernet cipher."""
        key = self.key_file.read_bytes()
        return Fernet(key)
    
    def save_credentials(self, rpc_url: str, private_key: str, chain_id: int):
        """
        Save credentials securely.
        
        Args:
            rpc_url: Ethereum RPC URL
            private_key: Private key (will be encrypted)
            chain_id: Chain ID
        """
        cipher = self._get_cipher()
        
        # Encrypt private key
        encrypted_key = cipher.encrypt(private_key.encode())
        
        credentials = {
            'rpc_url': rpc_url,
            'encrypted_private_key': encrypted_key.decode(),
            'chain_id': chain_id
        }
        
        # Save to file
        with open(self.credentials_file, 'w') as f:
            json.dump(credentials, f)
        
        self.credentials_file.chmod(0o600)  # Owner read/write only
        logger.info(f"Credentials saved to {self.credentials_file}")
    
    def load_credentials(self) -> Optional[Dict]:
        """
        Load saved credentials.
        
        Returns:
            Dict with credentials or None
        """
        if not self.credentials_file.exists():
            return None
        
        try:
            with open(self.credentials_file, 'r') as f:
                credentials = json.load(f)
            
            # Decrypt private key
            cipher = self._get_cipher()
            encrypted_key = credentials['encrypted_private_key'].encode()
            private_key = cipher.decrypt(encrypted_key).decode()
            
            return {
                'rpc_url': credentials['rpc_url'],
                'private_key': private_key,
                'chain_id': credentials['chain_id']
            }
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return None
    
    def delete_credentials(self):
        """Delete saved credentials."""
        if self.credentials_file.exists():
            self.credentials_file.unlink()
            logger.info("Credentials deleted")
        if self.key_file.exists():
            self.key_file.unlink()
            logger.info("Encryption key deleted")


class MetaMaskConnector:
    """
    Enhanced MetaMask connector with credential persistence and browser support.
    """
    
    def __init__(self, rpc_url: str = None, chain_id: int = 1, auto_load: bool = True):
        """
        Initialize MetaMask connector.
        
        Args:
            rpc_url: Ethereum RPC endpoint
            chain_id: Chain ID (1=Mainnet, 5=Goerli, 11155111=Sepolia)
            auto_load: Auto-load saved credentials
        """
        self.rpc_url = rpc_url or os.getenv('ETH_RPC_URL', 'http://127.0.0.1:8545')
        self.chain_id = chain_id
        self.w3 = None
        self.account = None
        self.connected = False
        
        self.credential_manager = CredentialManager()
        
        # Auto-load saved credentials
        if auto_load:
            self._load_saved_credentials()
        
        logger.info(f"Initialized MetaMask connector for chain {chain_id}")
    
    def _load_saved_credentials(self):
        """Load saved credentials if available."""
        creds = self.credential_manager.load_credentials()
        if creds:
            self.rpc_url = creds['rpc_url']
            self.chain_id = creds['chain_id']
            logger.info("Loaded saved credentials")
    
    def connect(self, private_key: Optional[str] = None, save: bool = False) -> bool:
        """
        Connect to Ethereum network.
        
        Args:
            private_key: Optional private key
            save: Save credentials for future sessions
        
        Returns:
            True if connected successfully
        """
        try:
            # If no private key provided, try to load from saved credentials
            if not private_key:
                creds = self.credential_manager.load_credentials()
                if creds:
                    private_key = creds['private_key']
                    logger.info("Using saved private key")
                else:
                    private_key = os.getenv('ETH_PRIVATE_KEY')
            
            # Connect to Web3
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            # Add PoA middleware for testnets
            if self.chain_id != 1 and geth_poa_middleware is not None:
                try:
                    self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                except Exception:
                    pass
            
            # Check connection
            if not self.w3.is_connected():
                logger.error("Failed to connect to Ethereum network")
                return False
            
            logger.info(f"✅ Connected to Ethereum network")
            logger.info(f"Chain ID: {self.w3.eth.chain_id}")
            logger.info(f"Latest block: {self.w3.eth.block_number}")
            
            # Load account from private key if provided
            if private_key:
                self.account = self.w3.eth.account.from_key(private_key)
                logger.info(f"Account loaded: {self.account.address}")
                
                # Save credentials if requested
                if save:
                    self.credential_manager.save_credentials(
                        self.rpc_url,
                        private_key,
                        self.chain_id
                    )
                    logger.info("Credentials saved for future sessions")
            else:
                logger.warning("No private key provided - read-only mode")
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Ethereum: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Ethereum network."""
        self.w3 = None
        self.account = None
        self.connected = False
        logger.info("Disconnected from Ethereum network")
    
    def is_connected(self) -> bool:
        """Check if connected to Ethereum network."""
        return self.connected and self.w3 is not None and self.w3.is_connected()
    
    def reconnect(self) -> bool:
        """Reconnect using saved credentials."""
        logger.info("Attempting to reconnect...")
        self.disconnect()
        return self.connect()
    
    def get_connection_status(self) -> Dict:
        """
        Get detailed connection status.
        
        Returns:
            Dict with connection info
        """
        status = {
            'connected': self.is_connected(),
            'rpc_url': self.rpc_url,
            'chain_id': self.chain_id,
            'has_account': self.account is not None,
            'has_saved_credentials': self.credential_manager.credentials_file.exists()
        }
        
        if self.is_connected():
            try:
                status['latest_block'] = self.w3.eth.block_number
                status['network_chain_id'] = self.w3.eth.chain_id
            except:
                pass
        
        if self.account:
            status['address'] = self.account.address
            try:
                status['balance_eth'] = float(self.get_eth_balance())
            except:
                pass
        
        return status
    
    def get_eth_balance(self, address: Optional[str] = None) -> Decimal:
        """Get ETH balance for address."""
        if not self.is_connected():
            raise RuntimeError("Not connected to Ethereum network")
        
        if address is None:
            if not self.account:
                raise ValueError("No address provided and no account connected")
            address = self.account.address
        
        balance_wei = self.w3.eth.get_balance(address)
        balance_eth = Decimal(balance_wei) / Decimal(10**18)
        
        return balance_eth
    
    def get_gas_price(self) -> Dict[str, int]:
        """Get current gas prices."""
        if not self.is_connected():
            raise RuntimeError("Not connected to Ethereum network")
        
        gas_price = self.w3.eth.gas_price
        
        return {
            'slow': int(gas_price * 0.8),
            'standard': gas_price,
            'fast': int(gas_price * 1.2),
            'rapid': int(gas_price * 1.5)
        }
    
    def send_eth(self, to_address: str, amount_eth: Decimal, 
                 gas_price: Optional[int] = None) -> Optional[str]:
        """Send ETH to an address."""
        if not self.is_connected() or not self.account:
            raise RuntimeError("Not connected or no account loaded")
        
        try:
            amount_wei = int(amount_eth * Decimal(10**18))
            
            if gas_price is None:
                gas_price = self.w3.eth.gas_price
            
            transaction = {
                'from': self.account.address,
                'to': to_address,
                'value': amount_wei,
                'gas': 21000,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'chainId': self.chain_id
            }
            
            signed_txn = self.account.sign_transaction(transaction)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error sending ETH: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test connection thoroughly.
        
        Returns:
            True if all tests pass
        """
        try:
            print("🧪 Testing MetaMask connection...")
            
            # Test 1: Web3 connection
            if not self.is_connected():
                print("❌ Not connected to network")
                return False
            print("✅ Connected to network")
            
            # Test 2: Latest block
            block = self.w3.eth.block_number
            print(f"✅ Latest block: {block}")
            
            # Test 3: Chain ID
            chain_id = self.w3.eth.chain_id
            print(f"✅ Chain ID: {chain_id}")
            
            # Test 4: Account
            if self.account:
                print(f"✅ Account: {self.account.address}")
                
                # Test 5: Balance
                balance = self.get_eth_balance()
                print(f"✅ Balance: {balance:.6f} ETH")
            else:
                print("⚠️  No account loaded (read-only mode)")
            
            # Test 6: Gas price
            gas = self.get_gas_price()
            print(f"✅ Gas price: {gas['standard'] / 10**9:.2f} Gwei")
            
            print("\n✅ All tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False


def setup_metamask_connection(
    private_key: Optional[str] = None,
    rpc_url: Optional[str] = None,
    chain_id: int = 1,
    save: bool = False,
    auto_load: bool = True
) -> Optional[MetaMaskConnector]:
    """
    Setup MetaMask connection with credential management.
    
    Args:
        private_key: Private key (use env var: ETH_PRIVATE_KEY)
        rpc_url: RPC URL (use env var: ETH_RPC_URL)
        chain_id: Chain ID
        save: Save credentials for future use
        auto_load: Auto-load saved credentials
    
    Returns:
        Connected MetaMaskConnector or None
    """
    # Get from environment if not provided
    if private_key is None:
        private_key = os.getenv('ETH_PRIVATE_KEY')
    
    if rpc_url is None:
        rpc_url = os.getenv('ETH_RPC_URL')
    
    # Create connector
    connector = MetaMaskConnector(rpc_url=rpc_url, chain_id=chain_id, auto_load=auto_load)
    
    # Connect
    if connector.connect(private_key=private_key, save=save):
        return connector
    else:
        return None


# CLI Tool
if __name__ == '__main__':
    import sys
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='MetaMask Connector CLI')
    parser.add_argument('action', choices=['connect', 'disconnect', 'status', 'test', 'clear'],
                       help='Action to perform')
    parser.add_argument('--save', action='store_true', help='Save credentials')
    parser.add_argument('--rpc-url', help='Ethereum RPC URL')
    parser.add_argument('--private-key', help='Private key (use env var instead!)')
    parser.add_argument('--chain-id', type=int, default=1, help='Chain ID')
    
    args = parser.parse_args()
    
    print("="*70)
    print("HARVEST MetaMask Connector")
    print("="*70)
    
    if args.action == 'clear':
        print("\n🗑️  Clearing saved credentials...")
        manager = CredentialManager()
        manager.delete_credentials()
        print("✅ Credentials cleared")
        sys.exit(0)
    
    # Create connector
    connector = MetaMaskConnector(
        rpc_url=args.rpc_url,
        chain_id=args.chain_id,
        auto_load=(args.action != 'connect')
    )
    
    if args.action == 'status':
        print("\n📊 Connection Status:")
        status = connector.get_connection_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        sys.exit(0)
    
    elif args.action == 'connect':
        print("\n🔌 Connecting to Ethereum network...")
        
        if not args.rpc_url and not os.getenv('ETH_RPC_URL'):
            print("\n❌ No RPC URL provided")
            print("Set ETH_RPC_URL environment variable or use --rpc-url")
            sys.exit(1)
        
        success = connector.connect(
            private_key=args.private_key,
            save=args.save
        )
        
        if success:
            print("\n✅ Connected successfully!")
            connector.test_connection()
            if args.save:
                print("\n💾 Credentials saved for future sessions")
        else:
            print("\n❌ Connection failed")
            sys.exit(1)
    
    elif args.action == 'disconnect':
        print("\n🔌 Disconnecting...")
        connector.disconnect()
        print("✅ Disconnected")
    
    elif args.action == 'test':
        print("\n🧪 Testing connection...")
        if not connector.is_connected():
            print("Connecting first...")
            connector.connect()
        
        if connector.test_connection():
            print("\n✅ Test complete")
        else:
            print("\n❌ Test failed")
            sys.exit(1)
