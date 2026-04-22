"""
MetaMask Wallet Connector for HARVEST
Connects to MetaMask via Web3.py for on-chain ETH trading
"""

import os
import json
from decimal import Decimal
from typing import Optional, Dict
from web3 import Web3
try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    # For web3.py >= 6.0, POA middleware handling changed
    geth_poa_middleware = None
import logging

logger = logging.getLogger("harvest.metamask")


class MetaMaskConnector:
    """
    Connect to MetaMask wallet for ETH trading.
    Uses Web3.py to interact with Ethereum blockchain via MetaMask's RPC.
    """
    
    def __init__(self, rpc_url: str = None, chain_id: int = 1):
        """
        Initialize MetaMask connector.
        
        Args:
            rpc_url: Ethereum RPC endpoint (defaults to local MetaMask)
            chain_id: Chain ID (1=Mainnet, 5=Goerli, 11155111=Sepolia)
        """
        # Default to local MetaMask or Infura
        if rpc_url is None:
            rpc_url = os.getenv('ETH_RPC_URL', 'http://127.0.0.1:8545')
        
        self.rpc_url = rpc_url
        self.chain_id = chain_id
        self.w3 = None
        self.account = None
        
        logger.info(f"Initializing MetaMask connector for chain {chain_id}")
    
    def connect(self, private_key: Optional[str] = None) -> bool:
        """
        Connect to Ethereum network.
        
        Args:
            private_key: Optional private key (use env var for security)
        
        Returns:
            True if connected successfully
        """
        try:
            # Connect to Web3
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            # Add PoA middleware for testnets (if available)
            if self.chain_id != 1 and geth_poa_middleware is not None:
                try:
                    self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                except Exception:
                    pass  # Middleware not needed in newer versions
            
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
            else:
                logger.warning("No private key provided - read-only mode")
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Ethereum: {e}")
            return False
    
    def get_eth_balance(self, address: Optional[str] = None) -> Decimal:
        """
        Get ETH balance for address.
        
        Args:
            address: Ethereum address (uses connected account if None)
        
        Returns:
            ETH balance as Decimal
        """
        if not self.w3:
            raise RuntimeError("Not connected to Ethereum network")
        
        if address is None:
            if not self.account:
                raise ValueError("No address provided and no account connected")
            address = self.account.address
        
        # Get balance in Wei
        balance_wei = self.w3.eth.get_balance(address)
        
        # Convert to ETH
        balance_eth = Decimal(balance_wei) / Decimal(10**18)
        
        return balance_eth
    
    def get_gas_price(self) -> Dict[str, int]:
        """
        Get current gas prices.
        
        Returns:
            Dict with gas prices in Gwei
        """
        if not self.w3:
            raise RuntimeError("Not connected to Ethereum network")
        
        gas_price = self.w3.eth.gas_price
        
        # Estimate fast/slow based on current price
        return {
            'slow': int(gas_price * 0.8),
            'standard': gas_price,
            'fast': int(gas_price * 1.2),
            'rapid': int(gas_price * 1.5)
        }
    
    def estimate_gas(self, transaction: Dict) -> int:
        """
        Estimate gas for a transaction.
        
        Args:
            transaction: Transaction dict
        
        Returns:
            Estimated gas units
        """
        if not self.w3:
            raise RuntimeError("Not connected to Ethereum network")
        
        try:
            gas_estimate = self.w3.eth.estimate_gas(transaction)
            return gas_estimate
        except Exception as e:
            logger.error(f"Error estimating gas: {e}")
            return 21000  # Default for simple transfer
    
    def send_eth(self, to_address: str, amount_eth: Decimal, 
                 gas_price: Optional[int] = None) -> Optional[str]:
        """
        Send ETH to an address.
        
        Args:
            to_address: Recipient address
            amount_eth: Amount in ETH
            gas_price: Gas price in Wei (uses current if None)
        
        Returns:
            Transaction hash or None on error
        """
        if not self.w3 or not self.account:
            raise RuntimeError("Not connected or no account loaded")
        
        try:
            # Convert ETH to Wei
            amount_wei = int(amount_eth * Decimal(10**18))
            
            # Get gas price
            if gas_price is None:
                gas_price = self.w3.eth.gas_price
            
            # Build transaction
            transaction = {
                'from': self.account.address,
                'to': to_address,
                'value': amount_wei,
                'gas': 21000,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'chainId': self.chain_id
            }
            
            # Sign transaction
            signed_txn = self.account.sign_transaction(transaction)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error sending ETH: {e}")
            return None
    
    def wait_for_transaction(self, tx_hash: str, timeout: int = 120) -> Optional[Dict]:
        """
        Wait for transaction to be mined.
        
        Args:
            tx_hash: Transaction hash
            timeout: Timeout in seconds
        
        Returns:
            Transaction receipt or None
        """
        if not self.w3:
            raise RuntimeError("Not connected to Ethereum network")
        
        try:
            logger.info(f"Waiting for transaction {tx_hash}...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            
            if receipt['status'] == 1:
                logger.info(f"✅ Transaction confirmed in block {receipt['blockNumber']}")
            else:
                logger.error(f"❌ Transaction failed")
            
            return dict(receipt)
            
        except Exception as e:
            logger.error(f"Error waiting for transaction: {e}")
            return None
    
    def get_transaction_status(self, tx_hash: str) -> Optional[Dict]:
        """
        Get transaction status.
        
        Args:
            tx_hash: Transaction hash
        
        Returns:
            Transaction info dict
        """
        if not self.w3:
            raise RuntimeError("Not connected to Ethereum network")
        
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                status = 'confirmed' if receipt['status'] == 1 else 'failed'
                block_number = receipt['blockNumber']
            except:
                status = 'pending'
                block_number = None
            
            return {
                'hash': tx_hash,
                'from': tx['from'],
                'to': tx['to'],
                'value': Decimal(tx['value']) / Decimal(10**18),
                'gas': tx['gas'],
                'gasPrice': tx['gasPrice'],
                'status': status,
                'blockNumber': block_number
            }
            
        except Exception as e:
            logger.error(f"Error getting transaction status: {e}")
            return None


def setup_metamask_connection(
    private_key: Optional[str] = None,
    rpc_url: Optional[str] = None,
    chain_id: int = 1
) -> Optional[MetaMaskConnector]:
    """
    Helper function to set up MetaMask connection.
    
    Args:
        private_key: Private key (use env var: ETH_PRIVATE_KEY)
        rpc_url: RPC URL (use env var: ETH_RPC_URL)
        chain_id: Chain ID (1=Mainnet, 5=Goerli, 11155111=Sepolia)
    
    Returns:
        Connected MetaMaskConnector or None
    """
    # Get from environment if not provided
    if private_key is None:
        private_key = os.getenv('ETH_PRIVATE_KEY')
    
    if rpc_url is None:
        rpc_url = os.getenv('ETH_RPC_URL')
    
    # Create connector
    connector = MetaMaskConnector(rpc_url=rpc_url, chain_id=chain_id)
    
    # Connect
    if connector.connect(private_key=private_key):
        return connector
    else:
        return None


# Example usage
if __name__ == '__main__':
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    
    print("="*70)
    print("HARVEST MetaMask Connector Test")
    print("="*70)
    
    # Check for environment variables
    rpc_url = os.getenv('ETH_RPC_URL')
    private_key = os.getenv('ETH_PRIVATE_KEY')
    
    if not rpc_url:
        print("\n⚠️  ETH_RPC_URL not set")
        print("Set it to your Ethereum RPC endpoint:")
        print("  export ETH_RPC_URL='https://mainnet.infura.io/v3/YOUR-PROJECT-ID'")
        print("  or for local: export ETH_RPC_URL='http://127.0.0.1:8545'")
        sys.exit(1)
    
    print(f"\n📡 RPC URL: {rpc_url}")
    
    if not private_key:
        print("\n⚠️  ETH_PRIVATE_KEY not set (read-only mode)")
        print("Set it to enable transactions:")
        print("  export ETH_PRIVATE_KEY='0x...'")
        print("\n⚠️  WARNING: Never commit private keys to git!")
    
    # Connect
    print("\n🔌 Connecting to Ethereum network...")
    connector = setup_metamask_connection(
        private_key=private_key,
        rpc_url=rpc_url,
        chain_id=1  # Mainnet
    )
    
    if not connector:
        print("❌ Failed to connect")
        sys.exit(1)
    
    print("\n✅ Connected successfully!")
    
    # Get balance if account loaded
    if connector.account:
        print(f"\n💰 Checking balance...")
        balance = connector.get_eth_balance()
        print(f"Address: {connector.account.address}")
        print(f"Balance: {balance:.6f} ETH")
    
    # Get gas prices
    print(f"\n⛽ Current gas prices:")
    gas_prices = connector.get_gas_price()
    for speed, price in gas_prices.items():
        gwei = price / 10**9
        print(f"  {speed.capitalize()}: {gwei:.2f} Gwei")
    
    print("\n✅ MetaMask connector test complete")
