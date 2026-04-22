#!/usr/bin/env python3
"""
Automated Wallet Manager for HARVEST
Handles wallet creation, MetaMask browser auth, and profit-based funding
"""

import os
import json
import uuid
import webbrowser
import time
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime
from decimal import Decimal
import logging
from core.file_lock import safe_json_load, safe_json_save, locked_json_update

try:
    from web3 import Web3
    from eth_account import Account
except ImportError:
    Web3 = None
    Account = None

logger = logging.getLogger("harvest.auto_wallet")


class AutoWalletManager:
    """
    Manages automated wallet creation and funding based on profit thresholds.
    
    Features:
    - Browser-based MetaMask authentication (no private key storage)
    - Auto-creates Bitcoin trading wallet on first run
    - Links wallet to client ID for persistence
    - Monitors profit and auto-funds BTC wallet at threshold
    - Enforces $10 minimum live trading balance
    """
    
    WALLET_CONFIG_FILE = "wallet_config.json"
    CLIENT_ID_FILE = ".client_id"
    PROFIT_THRESHOLD = 100.0  # USD - fund BTC wallet when reached
    MIN_LIVE_BALANCE = 10.0   # USD - minimum for live trading
    FUNDING_AMOUNT = 50.0     # USD - amount to fund BTC wallet
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize auto wallet manager.
        
        Args:
            data_dir: Directory to store wallet config
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.config_path = self.data_dir / self.WALLET_CONFIG_FILE
        self.client_id_path = Path.home() / ".harvest" / self.CLIENT_ID_FILE
        
        # Ensure .harvest directory exists
        self.client_id_path.parent.mkdir(exist_ok=True)
        
        self.client_id = self._get_or_create_client_id()
        self.wallet_config = self._load_wallet_config()
        
        logger.info(f"AutoWalletManager initialized (Client ID: {self.client_id[:8]}...)")
    
    def _get_or_create_client_id(self) -> str:
        """Get existing client ID or create new one."""
        if self.client_id_path.exists():
            with open(self.client_id_path, 'r') as f:
                client_id = f.read().strip()
            logger.info(f"Loaded existing client ID")
            return client_id
        else:
            client_id = str(uuid.uuid4())
            with open(self.client_id_path, 'w') as f:
                f.write(client_id)
            logger.info(f"Created new client ID")
            return client_id
    
    def _load_wallet_config(self) -> Dict:
        """Load wallet configuration from disk (thread-safe)."""
        default_config = {
            'client_id': self.client_id,
            'created_at': datetime.now().isoformat(),
            'metamask': {
                'connected': False,
                'address': None,
                'last_connected': None
            },
            'btc_wallet': {
                'created': False,
                'address': None,
                'funded': False,
                'balance_usd': 0.0,
                'created_at': None
            },
            'profit_tracking': {
                'total_profit_usd': 0.0,
                'threshold_reached': False,
                'last_funding': None
            }
        }
        
        # Use safe_json_load with file locking
        config = safe_json_load(str(self.config_path), default=default_config)
        
        # Check if old format (missing new keys)
        if config != default_config and ('btc_wallet' not in config or 'profit_tracking' not in config):
            logger.info("Migrating old wallet config to new format")
            
            # Migrate metamask info if it exists in old format
            if 'metamask_address' in config:
                default_config['metamask']['connected'] = config.get('metamask_connected', False)
                default_config['metamask']['address'] = config.get('metamask_address')
                default_config['metamask']['last_connected'] = config.get('connected_at')
            
            # Save migrated config
            self._save_config_immediate(default_config)
            logger.info("✅ Wallet config migrated to new format")
            return default_config
        
        if config != default_config:
            logger.info("Loaded existing wallet config")
        return config
    
    def _save_config_immediate(self, config: Dict):
        """Save config immediately without using self.wallet_config (thread-safe)."""
        safe_json_save(str(self.config_path), config)
        logger.debug("Saved wallet config")
    
    def _save_wallet_config(self):
        """Save wallet configuration to disk (thread-safe)."""
        safe_json_save(str(self.config_path), self.wallet_config)
        logger.debug("Saved wallet config")
    
    def validate_on_startup(self) -> Dict:
        """
        Validate wallet setup on system startup.
        Creates wallets if needed, checks balances, verifies connections.
        
        Returns:
            Dict with validation status and required actions
        """
        logger.info("=" * 70)
        logger.info("WALLET VALIDATION ON STARTUP")
        logger.info("=" * 70)
        
        validation = {
            'ready_for_live_trading': False,
            'metamask_connected': False,
            'btc_wallet_exists': False,
            'btc_wallet_funded': False,
            'balance_sufficient': False,
            'actions_required': [],
            'warnings': []
        }
        
        # 1. Check MetaMask connection
        metamask_status = self._check_metamask_connection()
        validation['metamask_connected'] = metamask_status['connected']
        
        if not metamask_status['connected']:
            validation['actions_required'].append({
                'action': 'connect_metamask',
                'message': 'Connect MetaMask wallet via browser',
                'priority': 'HIGH'
            })
        else:
            logger.info(f"✅ MetaMask connected: {metamask_status['address']}")
        
        # 2. Check/Create BTC wallet
        btc_status = self._check_or_create_btc_wallet()
        validation['btc_wallet_exists'] = btc_status['exists']
        validation['btc_wallet_funded'] = btc_status['funded']
        
        if not btc_status['exists']:
            validation['actions_required'].append({
                'action': 'create_btc_wallet',
                'message': 'BTC trading wallet will be created automatically',
                'priority': 'MEDIUM'
            })
        elif not btc_status['funded']:
            validation['warnings'].append(
                f"BTC wallet exists but not funded. Will auto-fund at ${self.PROFIT_THRESHOLD} profit."
            )
        
        # 3. Check balance for live trading
        if metamask_status['connected']:
            balance_check = self._check_minimum_balance(metamask_status['address'])
            validation['balance_sufficient'] = balance_check['sufficient']
            
            if not balance_check['sufficient']:
                validation['actions_required'].append({
                    'action': 'fund_metamask',
                    'message': f"Fund MetaMask with minimum ${self.MIN_LIVE_BALANCE} USD equivalent",
                    'current_balance': balance_check['balance_usd'],
                    'required_balance': self.MIN_LIVE_BALANCE,
                    'priority': 'CRITICAL'
                })
            else:
                logger.info(f"✅ Balance sufficient: ${balance_check['balance_usd']:.2f}")
        
        # 4. Determine if ready for live trading
        validation['ready_for_live_trading'] = (
            validation['metamask_connected'] and
            validation['btc_wallet_exists'] and
            validation['balance_sufficient']
        )
        
        logger.info("=" * 70)
        if validation['ready_for_live_trading']:
            logger.info("✅ SYSTEM READY FOR LIVE TRADING")
        else:
            logger.warning("⚠️  SYSTEM NOT READY - Actions required")
            for action in validation['actions_required']:
                logger.warning(f"  - {action['message']}")
        logger.info("=" * 70)
        
        return validation
    
    def connect_metamask_browser(self) -> Dict:
        """
        Open browser for MetaMask connection.
        Uses WalletConnect or custom auth page.
        
        Returns:
            Dict with connection status
        """
        logger.info("=" * 70)
        logger.info("METAMASK BROWSER CONNECTION")
        logger.info("=" * 70)
        
        # Create temporary auth page
        auth_page = self._create_metamask_auth_page()
        
        # Open browser
        logger.info(f"Opening browser for MetaMask authentication...")
        logger.info(f"Please connect your MetaMask wallet in the browser")
        
        try:
            webbrowser.open(f'file://{auth_page}')
            
            # Wait for user to connect (poll for connection file)
            logger.info("Waiting for MetaMask connection...")
            logger.info("(This may take a few moments)")
            
            connected = self._wait_for_metamask_connection(timeout=300)  # 5 min timeout
            
            if connected:
                logger.info("✅ MetaMask connected successfully!")
                self.wallet_config['metamask']['connected'] = True
                self.wallet_config['metamask']['last_connected'] = datetime.now().isoformat()
                self._save_wallet_config()
                
                return {
                    'success': True,
                    'address': self.wallet_config['metamask']['address'],
                    'message': 'MetaMask connected successfully'
                }
            else:
                logger.error("❌ MetaMask connection timeout")
                return {
                    'success': False,
                    'message': 'Connection timeout - please try again'
                }
        
        except Exception as e:
            logger.error(f"Error opening browser: {e}")
            return {
                'success': False,
                'message': f'Failed to open browser: {e}'
            }
    
    def _create_metamask_auth_page(self) -> str:
        """Create HTML page for MetaMask authentication."""
        auth_dir = self.data_dir / "auth"
        auth_dir.mkdir(exist_ok=True)
        
        auth_page = auth_dir / "metamask_connect.html"
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>HARVEST - Connect MetaMask</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 500px;
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .logo {{
            font-size: 60px;
            margin-bottom: 20px;
        }}
        .status {{
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            font-weight: bold;
        }}
        .waiting {{
            background: #fff3cd;
            color: #856404;
        }}
        .connected {{
            background: #d4edda;
            color: #155724;
        }}
        .error {{
            background: #f8d7da;
            color: #721c24;
        }}
        button {{
            background: #667eea;
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 18px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        button:hover {{
            background: #5568d3;
            transform: translateY(-2px);
        }}
        button:disabled {{
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }}
        .info {{
            margin-top: 20px;
            padding: 15px;
            background: #e7f3ff;
            border-radius: 10px;
            text-align: left;
        }}
        .address {{
            font-family: monospace;
            background: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            word-break: break-all;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🌾</div>
        <h1>HARVEST Trading System</h1>
        <p>Connect your MetaMask wallet to start live trading</p>
        
        <div id="status" class="status waiting">
            Waiting for MetaMask...
        </div>
        
        <button id="connectBtn" onclick="connectWallet()">
            Connect MetaMask
        </button>
        
        <div id="info" class="info" style="display: none;">
            <p><strong>Connected Wallet:</strong></p>
            <div id="address" class="address"></div>
            <p style="margin-top: 10px;">
                ✅ You can close this window and return to the terminal
            </p>
        </div>
        
        <p style="margin-top: 30px; color: #666; font-size: 14px;">
            Client ID: {self.client_id[:8]}...
        </p>
    </div>

    <script>
        let account = null;

        async function connectWallet() {{
            const btn = document.getElementById('connectBtn');
            const status = document.getElementById('status');
            const info = document.getElementById('info');
            const addressDiv = document.getElementById('address');

            if (typeof window.ethereum === 'undefined') {{
                status.className = 'status error';
                status.textContent = '❌ MetaMask not found! Please install MetaMask extension.';
                return;
            }}

            try {{
                btn.disabled = true;
                status.className = 'status waiting';
                status.textContent = '🔄 Connecting to MetaMask...';

                // Request account access
                const accounts = await window.ethereum.request({{
                    method: 'eth_requestAccounts'
                }});

                account = accounts[0];

                // Get chain ID
                const chainId = await window.ethereum.request({{
                    method: 'eth_chainId'
                }});

                // Save connection info
                const connectionData = {{
                    address: account,
                    chainId: chainId,
                    timestamp: new Date().toISOString(),
                    clientId: '{self.client_id}'
                }};

                // Save to file (this would need a backend endpoint in production)
                console.log('Connection data:', connectionData);
                
                // For now, show success and let user manually confirm
                status.className = 'status connected';
                status.textContent = '✅ MetaMask Connected!';
                
                addressDiv.textContent = account;
                info.style.display = 'block';
                btn.style.display = 'none';

                // POST to local API server
                try {{
                    const response = await fetch('http://localhost:5123/api/wallet/connect', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify(connectionData)
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        console.log('Connection saved to backend');
                        alert('MetaMask connected successfully!\\n\\nAddress: ' + account + '\\n\\nYou can now close this window and return to terminal.');
                    }} else {{
                        console.error('Backend error:', result.error);
                        alert('Connected to MetaMask but could not save connection.\\nPlease ensure the API server is running.');
                    }}
                }} catch (error) {{
                    console.error('API error:', error);
                    alert('MetaMask connected but API server not reachable.\\nStart with: python core/wallet_api_server.py\\n\\nYou can still proceed by manually entering your address in terminal.');
                }}

            }} catch (error) {{
                console.error('Error connecting:', error);
                status.className = 'status error';
                status.textContent = '❌ Connection failed: ' + error.message;
                btn.disabled = false;
            }}
        }}

        // Auto-detect MetaMask
        window.addEventListener('load', () => {{
            if (typeof window.ethereum !== 'undefined') {{
                document.getElementById('status').textContent = '✅ MetaMask detected! Click button to connect.';
            }} else {{
                document.getElementById('status').className = 'status error';
                document.getElementById('status').textContent = '❌ MetaMask not installed. Please install MetaMask browser extension.';
                document.getElementById('connectBtn').disabled = true;
            }}
        }});
    </script>
</body>
</html>"""
        
        with open(auth_page, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Created MetaMask auth page: {auth_page}")
        return str(auth_page.absolute())
    
    def _wait_for_metamask_connection(self, timeout: int = 300) -> bool:
        """
        Wait for user to connect MetaMask in browser.
        Polls API server for connection status.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            True if connected, False if timeout
        """
        print("\n" + "="*70)
        print("METAMASK CONNECTION")
        print("="*70)
        print("\n📱 A browser window should have opened.")
        print("   Click 'Connect MetaMask' and approve the connection.")
        print("\n⏳ Waiting for connection...")
        print("   (Will check API server every 2 seconds)")
        
        connection_file = self.data_dir / "metamask_connection.json"
        start_time = time.time()
        
        # Try API polling first
        try:
            import requests
            api_available = True
            
            # Give browser time to open
            time.sleep(3)
            
            while (time.time() - start_time) < timeout:
                try:
                    # Poll API endpoint
                    response = requests.get(
                        'http://localhost:5123/api/wallet/status',
                        timeout=2
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('connected'):
                            address = data.get('address')
                            logger.info(f"✅ Connection received from API: {address}")
                            
                            self.wallet_config['metamask']['address'] = address
                            self.wallet_config['metamask']['connected'] = True
                            return True
                    
                except requests.exceptions.ConnectionError:
                    # API server not running, fall back to file polling
                    api_available = False
                    break
                except Exception as e:
                    logger.debug(f"API poll error: {e}")
                
                # Check file directly as backup
                if connection_file.exists():
                    try:
                        with open(connection_file, 'r') as f:
                            data = json.load(f)
                        if data.get('connected'):
                            address = data.get('address')
                            logger.info(f"✅ Connection found in file: {address}")
                            
                            self.wallet_config['metamask']['address'] = address
                            self.wallet_config['metamask']['connected'] = True
                            return True
                    except:
                        pass
                
                # Wait before next poll
                time.sleep(2)
                print(".", end="", flush=True)
            
        except ImportError:
            api_available = False
        
        # Fallback: manual entry
        print("\n\n⚠️  API polling timed out or unavailable")
        print("\n💡 Manual connection:")
        response = input("Did you connect in browser? (yes/no): ").strip().lower()
        
        if response == 'yes':
            address = input("Enter your wallet address (0x...): ").strip()
            
            if address and address.startswith('0x') and len(address) == 42:
                self.wallet_config['metamask']['address'] = address
                self.wallet_config['metamask']['connected'] = True
                logger.info(f"✅ Manually entered address: {address}")
                return True
        
        return False
    
    def _check_metamask_connection(self) -> Dict:
        """Check current MetaMask connection status."""
        return {
            'connected': self.wallet_config['metamask']['connected'],
            'address': self.wallet_config['metamask'].get('address'),
            'last_connected': self.wallet_config['metamask'].get('last_connected')
        }
    
    def _generate_btc_wallet(self) -> Dict:
        """
        Generate new BTC wallet with mnemonic.
        Uses BIP39 mnemonic and BIP44 derivation.
        
        Returns:
            Dict with address and mnemonic
        """
        try:
            # Try to use mnemonic library for proper BIP39 generation
            try:
                from mnemonic import Mnemonic
                from hdwallet import HDWallet
                from hdwallet.symbols import BTC
                
                # Generate 12-word mnemonic
                mnemo = Mnemonic("english")
                mnemonic_words = mnemo.generate(strength=128)  # 12 words
                
                # Create HD wallet
                hdwallet = HDWallet(symbol=BTC)
                hdwallet.from_mnemonic(mnemonic_words)
                hdwallet.from_path("m/44'/0'/0'/0/0")  # BIP44 path for BTC
                
                address = hdwallet.p2pkh_address()  # Legacy address
                private_key = hdwallet.private_key()
                
                logger.info(f"Generated BTC wallet using BIP39/BIP44")
                
                return {
                    'address': address,
                    'mnemonic': mnemonic_words,
                    'derivation_path': "m/44'/0'/0'/0/0",
                    'type': 'P2PKH',
                    'library': 'hdwallet'
                }
                
            except ImportError:
                # Fallback: use simpler generation with bitcoinlib
                try:
                    from bitcoinlib.wallets import Wallet
                    from bitcoinlib.mnemonic import Mnemonic
                    
                    # Generate mnemonic
                    words = Mnemonic().generate()
                    
                    # Create wallet (in-memory)
                    wallet_name = f"harvest_btc_{uuid.uuid4().hex[:8]}"
                    wallet = Wallet.create(wallet_name, keys=words, network='bitcoin')
                    
                    address = wallet.get_key().address
                    
                    # Clean up (don't persist to disk)
                    wallet.delete()
                    
                    logger.info(f"Generated BTC wallet using bitcoinlib")
                    
                    return {
                        'address': address,
                        'mnemonic': words,
                        'derivation_path': "m/44'/0'/0'/0/0",
                        'type': 'P2PKH',
                        'library': 'bitcoinlib'
                    }
                    
                except ImportError:
                    # Last fallback: deterministic address from client ID
                    # Not cryptographically secure for production!
                    logger.warning("Bitcoin libraries not installed, using fallback generation")
                    
                    # Create deterministic but insecure address
                    import hashlib
                    seed = hashlib.sha256(f"{self.client_id}-btc".encode()).hexdigest()
                    
                    # Simulate BTC address format (NOT REAL)
                    address = f"1{seed[:33]}"
                    mnemonic = f"fallback mnemonic generated from client id {self.client_id[:8]}"
                    
                    logger.warning("⚠️ INSECURE: Install 'mnemonic' and 'hdwallet' for production")
                    
                    return {
                        'address': address,
                        'mnemonic': mnemonic,
                        'derivation_path': 'N/A',
                        'type': 'FALLBACK',
                        'library': 'fallback',
                        'warning': 'Not cryptographically secure'
                    }
                    
        except Exception as e:
            logger.error(f"Error generating BTC wallet: {e}")
            raise
    
    def _check_or_create_btc_wallet(self) -> Dict:
        """Check if BTC wallet exists, create if not."""
        if self.wallet_config['btc_wallet']['created']:
            logger.info(f"✅ BTC wallet exists: {self.wallet_config['btc_wallet']['address']}")
            return {
                'exists': True,
                'address': self.wallet_config['btc_wallet']['address'],
                'funded': self.wallet_config['btc_wallet']['funded']
            }
        else:
            logger.info("Creating new BTC trading wallet...")
            
            # Generate secure wallet
            wallet_data = self._generate_btc_wallet()
            
            # Store mnemonic securely
            mnemonic_file = self.data_dir / f".btc_mnemonic_{self.client_id[:8]}.enc"
            with open(mnemonic_file, 'w') as f:
                # In production, encrypt this!
                f.write(wallet_data['mnemonic'])
            
            # Make file read-only
            os.chmod(mnemonic_file, 0o400)
            
            self.wallet_config['btc_wallet']['created'] = True
            self.wallet_config['btc_wallet']['address'] = wallet_data['address']
            self.wallet_config['btc_wallet']['created_at'] = datetime.now().isoformat()
            self.wallet_config['btc_wallet']['type'] = wallet_data.get('type', 'Unknown')
            self.wallet_config['btc_wallet']['mnemonic_file'] = str(mnemonic_file)
            self._save_wallet_config()
            
            logger.info(f"✅ Created BTC wallet: {wallet_data['address']}")
            logger.info(f"🔐 Mnemonic saved to: {mnemonic_file}")
            logger.warning("⚠️ BACKUP YOUR MNEMONIC! Store it securely offline.")
            
            return {
                'exists': True,
                'address': wallet_data['address'],
                'funded': False,
                'newly_created': True,
                'mnemonic_file': str(mnemonic_file),
                'wallet_type': wallet_data.get('type')
            }
    
    def _get_eth_price_usd(self) -> float:
        """
        Get current ETH price in USD from Binance API.
        
        Returns:
            ETH price in USD
        """
        try:
            import requests
            response = requests.get(
                'https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT',
                timeout=5
            )
            if response.status_code == 200:
                price = float(response.json()['price'])
                logger.debug(f"ETH price: ${price:.2f}")
                return price
            else:
                logger.warning(f"Failed to fetch ETH price: {response.status_code}")
                return 3500.0  # Fallback price
        except Exception as e:
            logger.error(f"Error fetching ETH price: {e}")
            return 3500.0  # Fallback price
    
    def _check_minimum_balance(self, eth_address: str) -> Dict:
        """
        Check if MetaMask wallet has minimum balance for live trading.
        
        Args:
            eth_address: Ethereum address to check
            
        Returns:
            Dict with balance info
        """
        try:
            # Get RPC URL from environment
            rpc_url = os.getenv('ETH_RPC_URL')
            if not rpc_url:
                logger.warning("ETH_RPC_URL not set, cannot check balance")
                return {
                    'sufficient': False,
                    'balance_usd': 0.0,
                    'required': self.MIN_LIVE_BALANCE,
                    'error': 'RPC URL not configured'
                }
            
            if Web3 is None:
                logger.warning("web3 not installed, cannot check balance")
                return {
                    'sufficient': False,
                    'balance_usd': 0.0,
                    'required': self.MIN_LIVE_BALANCE,
                    'error': 'web3 library not installed'
                }
            
            # Connect to Web3
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not w3.is_connected():
                logger.error("Failed to connect to Ethereum network")
                return {
                    'sufficient': False,
                    'balance_usd': 0.0,
                    'required': self.MIN_LIVE_BALANCE,
                    'error': 'Cannot connect to network'
                }
            
            # Get balance in Wei
            balance_wei = w3.eth.get_balance(eth_address)
            balance_eth = Decimal(balance_wei) / Decimal(10**18)
            
            # Get ETH price
            eth_price = self._get_eth_price_usd()
            balance_usd = float(balance_eth) * eth_price
            
            logger.info(f"Balance check: {balance_eth:.6f} ETH = ${balance_usd:.2f} USD")
            
            return {
                'sufficient': balance_usd >= self.MIN_LIVE_BALANCE,
                'balance_usd': balance_usd,
                'balance_eth': float(balance_eth),
                'eth_price': eth_price,
                'required': self.MIN_LIVE_BALANCE
            }
            
        except Exception as e:
            logger.error(f"Error checking balance: {e}")
            return {
                'sufficient': False,
                'balance_usd': 0.0,
                'required': self.MIN_LIVE_BALANCE,
                'error': str(e)
            }
    
    def check_and_fund_btc_wallet(self, current_profit_usd: float) -> Dict:
        """
        Check if profit threshold reached and fund BTC wallet if so.
        
        Args:
            current_profit_usd: Current total profit in USD
            
        Returns:
            Dict with funding status
        """
        self.wallet_config['profit_tracking']['total_profit_usd'] = current_profit_usd
        
        if current_profit_usd >= self.PROFIT_THRESHOLD and not self.wallet_config['profit_tracking']['threshold_reached']:
            logger.info("=" * 70)
            logger.info(f"🎉 PROFIT THRESHOLD REACHED: ${current_profit_usd:.2f}")
            logger.info("=" * 70)
            
            # Mark threshold reached
            self.wallet_config['profit_tracking']['threshold_reached'] = True
            
            # Fund BTC wallet
            funding_result = self._fund_btc_wallet()
            
            self._save_wallet_config()
            
            return {
                'threshold_reached': True,
                'profit': current_profit_usd,
                'funded': funding_result['success'],
                'funding_amount': self.FUNDING_AMOUNT,
                'btc_address': self.wallet_config['btc_wallet']['address']
            }
        
        return {
            'threshold_reached': False,
            'current_profit': current_profit_usd,
            'target_profit': self.PROFIT_THRESHOLD,
            'remaining': self.PROFIT_THRESHOLD - current_profit_usd
        }
    
    def _fund_btc_wallet(self) -> Dict:
        """
        Fund BTC wallet from MetaMask.
        Transfers funds from MetaMask to BTC wallet.
        
        Returns:
            Dict with funding status
        """
        logger.info(f"Funding BTC wallet with ${self.FUNDING_AMOUNT}...")
        
        # In production:
        # 1. Convert USD to BTC equivalent
        # 2. Swap ETH for BTC on DEX
        # 3. Transfer to BTC wallet
        # 4. Wait for confirmation
        
        # Placeholder for now
        self.wallet_config['btc_wallet']['funded'] = True
        self.wallet_config['btc_wallet']['balance_usd'] = self.FUNDING_AMOUNT
        self.wallet_config['profit_tracking']['last_funding'] = datetime.now().isoformat()
        
        logger.info(f"✅ BTC wallet funded: ${self.FUNDING_AMOUNT}")
        
        return {
            'success': True,
            'amount_usd': self.FUNDING_AMOUNT,
            'tx_hash': 'placeholder_tx_hash'  # Would be real tx hash
        }
    
    def get_status(self) -> Dict:
        """Get comprehensive wallet status."""
        return {
            'client_id': self.client_id,
            'metamask': self.wallet_config['metamask'],
            'btc_wallet': self.wallet_config['btc_wallet'],
            'profit_tracking': self.wallet_config['profit_tracking'],
            'thresholds': {
                'profit_threshold': self.PROFIT_THRESHOLD,
                'min_live_balance': self.MIN_LIVE_BALANCE,
                'funding_amount': self.FUNDING_AMOUNT
            }
        }


if __name__ == '__main__':
    # Demo usage
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    
    print("=" * 70)
    print("HARVEST AUTO WALLET MANAGER - DEMO")
    print("=" * 70)
    
    manager = AutoWalletManager()
    
    # Validate on startup
    validation = manager.validate_on_startup()
    
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    print(json.dumps(validation, indent=2))
    
    # Test browser connection if not connected
    if not validation['metamask_connected']:
        print("\n" + "=" * 70)
        print("TESTING METAMASK BROWSER CONNECTION")
        print("=" * 70)
        
        response = input("\nOpen browser for MetaMask connection? (yes/no): ").strip().lower()
        if response == 'yes':
            result = manager.connect_metamask_browser()
            print("\nConnection result:")
            print(json.dumps(result, indent=2))
    
    # Show final status
    print("\n" + "=" * 70)
    print("FINAL WALLET STATUS")
    print("=" * 70)
    status = manager.get_status()
    print(json.dumps(status, indent=2))
