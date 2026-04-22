#!/usr/bin/env python3
"""
Lightweight API Server for MetaMask Browser Connection
Handles communication between browser and Python for wallet authentication
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    CORS = None

logger = logging.getLogger("harvest.wallet_api")


class WalletAPIServer:
    """
    Simple Flask API server for MetaMask wallet connection.
    Runs on localhost to receive wallet address from browser.
    """
    
    def __init__(self, data_dir: str = "data", port: int = 5123):
        """
        Initialize API server.
        
        Args:
            data_dir: Directory to store connection data
            port: Port to run server on
        """
        if not FLASK_AVAILABLE:
            raise ImportError("Flask not installed. Run: pip install flask flask-cors")
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.port = port
        self.connection_file = self.data_dir / "metamask_connection.json"
        
        # Create Flask app
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for browser requests
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"WalletAPIServer initialized on port {port}")
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return jsonify({
                'status': 'ok',
                'server': 'HARVEST Wallet API',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/wallet/connect', methods=['POST'])
        def connect_wallet():
            """Receive wallet connection from browser"""
            try:
                data = request.get_json()
                
                if not data or 'address' not in data:
                    return jsonify({
                        'success': False,
                        'error': 'Missing wallet address'
                    }), 400
                
                # Validate address format
                address = data['address']
                if not address.startswith('0x') or len(address) != 42:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid Ethereum address format'
                    }), 400
                
                # Save connection data
                connection_data = {
                    'address': address,
                    'chainId': data.get('chainId', 'unknown'),
                    'clientId': data.get('clientId'),
                    'timestamp': datetime.now().isoformat(),
                    'connected': True
                }
                
                with open(self.connection_file, 'w') as f:
                    json.dump(connection_data, f, indent=2)
                
                logger.info(f"Wallet connected: {address}")
                
                return jsonify({
                    'success': True,
                    'message': 'Wallet connected successfully',
                    'address': address
                })
                
            except Exception as e:
                logger.error(f"Error connecting wallet: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/wallet/status', methods=['GET'])
        def wallet_status():
            """Check if wallet is connected"""
            try:
                if self.connection_file.exists():
                    with open(self.connection_file, 'r') as f:
                        data = json.load(f)
                    
                    return jsonify({
                        'connected': data.get('connected', False),
                        'address': data.get('address'),
                        'timestamp': data.get('timestamp')
                    })
                else:
                    return jsonify({
                        'connected': False,
                        'message': 'No wallet connected'
                    })
                    
            except Exception as e:
                logger.error(f"Error checking wallet status: {e}")
                return jsonify({
                    'connected': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/wallet/disconnect', methods=['POST'])
        def disconnect_wallet():
            """Disconnect wallet"""
            try:
                if self.connection_file.exists():
                    self.connection_file.unlink()
                
                return jsonify({
                    'success': True,
                    'message': 'Wallet disconnected'
                })
                
            except Exception as e:
                logger.error(f"Error disconnecting wallet: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def run(self, debug: bool = False):
        """
        Start the API server.
        
        Args:
            debug: Enable Flask debug mode
        """
        logger.info(f"Starting Wallet API Server on http://localhost:{self.port}")
        logger.info(f"API Endpoints:")
        logger.info(f"  GET  /health")
        logger.info(f"  POST /api/wallet/connect")
        logger.info(f"  GET  /api/wallet/status")
        logger.info(f"  POST /api/wallet/disconnect")
        
        self.app.run(
            host='127.0.0.1',
            port=self.port,
            debug=debug,
            use_reloader=False  # Prevent double initialization
        )
    
    def get_connection_data(self) -> Optional[dict]:
        """
        Get current connection data from file.
        
        Returns:
            Connection dict or None
        """
        try:
            if self.connection_file.exists():
                with open(self.connection_file, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error reading connection data: {e}")
            return None


def run_server_standalone(port: int = 5123):
    """
    Run server in standalone mode.
    
    Args:
        port: Port to run on
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    
    print("=" * 70)
    print("HARVEST WALLET API SERVER")
    print("=" * 70)
    print(f"\nStarting server on http://localhost:{port}")
    print("\nPress Ctrl+C to stop")
    print("=" * 70 + "\n")
    
    server = WalletAPIServer(port=port)
    
    try:
        server.run(debug=False)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")


if __name__ == '__main__':
    import sys
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5123
    run_server_standalone(port)
