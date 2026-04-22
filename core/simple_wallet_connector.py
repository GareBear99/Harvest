#!/usr/bin/env python3
"""
Simplified Wallet Connector
Direct browser-based MetaMask connection without server requirement
"""
import os
import json
import webbrowser
import tempfile
from pathlib import Path
from typing import Optional, Dict

class SimpleWalletConnector:
    """Simple wallet connector using browser + file-based communication"""
    
    def __init__(self):
        self.config_file = Path("data/wallet_config.json")
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Temp file for browser → Python communication
        self.response_file = Path(tempfile.gettempdir()) / "harvest_wallet_response.json"
    
    def load_config(self) -> Optional[Dict]:
        """Load existing wallet configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return None
    
    def save_config(self, config: Dict):
        """Save wallet configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def is_connected(self) -> bool:
        """Check if wallet is currently connected"""
        config = self.load_config()
        return config and config.get('metamask_connected', False)
    
    def get_address(self) -> Optional[str]:
        """Get connected wallet address"""
        config = self.load_config()
        if config and config.get('metamask_connected'):
            return config.get('metamask_address')
        return None
    
    def connect(self) -> bool:
        """
        Initiate wallet connection via browser.
        Opens browser page that connects to MetaMask and writes result to temp file.
        """
        # Clean up any old response
        if self.response_file.exists():
            self.response_file.unlink()
        
        # Check if already connected
        if self.is_connected():
            address = self.get_address()
            print(f"✅ Wallet already connected: {address}")
            print("   Press 'W' again to disconnect")
            return True
        
        # Create minimal HTML page for MetaMask connection
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>HARVEST - Connect Wallet</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            color: white;
        }
        .container {
            background: white;
            color: #333;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 500px;
        }
        h1 { color: #667eea; margin-top: 0; }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            margin: 20px 0;
        }
        button:hover { transform: scale(1.05); }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .status {
            margin: 20px 0;
            padding: 15px;
            border-radius: 8px;
            font-weight: bold;
        }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .info { background: #d1ecf1; color: #0c5460; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🦊 Connect MetaMask</h1>
        <p>Click the button below to connect your MetaMask wallet to HARVEST</p>
        
        <button id="connectBtn" onclick="connectWallet()">Connect Wallet</button>
        
        <div id="status"></div>
        
        <p style="font-size: 12px; color: #999; margin-top: 30px;">
            Make sure MetaMask extension is installed and unlocked
        </p>
    </div>
    
    <script>
        const statusDiv = document.getElementById('status');
        const connectBtn = document.getElementById('connectBtn');
        
        async function connectWallet() {
            try {
                // Check if MetaMask is installed
                if (typeof window.ethereum === 'undefined') {
                    showStatus('MetaMask not detected. Please install MetaMask extension.', 'error');
                    return;
                }
                
                connectBtn.disabled = true;
                showStatus('Connecting to MetaMask...', 'info');
                
                // Request account access
                const accounts = await window.ethereum.request({ 
                    method: 'eth_requestAccounts' 
                });
                
                if (accounts.length === 0) {
                    showStatus('No accounts found. Please unlock MetaMask.', 'error');
                    connectBtn.disabled = false;
                    return;
                }
                
                const address = accounts[0];
                
                // Get chain ID
                const chainId = await window.ethereum.request({ 
                    method: 'eth_chainId' 
                });
                
                showStatus(`✅ Connected: ${address.substring(0, 10)}...`, 'success');
                
                // Save to temp file (via download)
                const result = {
                    success: true,
                    address: address,
                    chain_id: chainId,
                    timestamp: new Date().toISOString()
                };
                
                // Trigger download of result JSON
                const blob = new Blob([JSON.stringify(result, null, 2)], 
                    { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'harvest_wallet_response.json';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                setTimeout(() => {
                    showStatus('✅ Connection successful! You can close this window and return to HARVEST.', 'success');
                }, 1000);
                
            } catch (error) {
                console.error('Connection error:', error);
                showStatus(`❌ Error: ${error.message}`, 'error');
                connectBtn.disabled = false;
            }
        }
        
        function showStatus(message, type) {
            statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
        }
        
        // Auto-connect if user already approved
        window.addEventListener('load', async () => {
            if (typeof window.ethereum !== 'undefined') {
                try {
                    const accounts = await window.ethereum.request({ 
                        method: 'eth_accounts' 
                    });
                    if (accounts.length > 0) {
                        showStatus('Wallet already connected. Click "Connect Wallet" to update.', 'info');
                    }
                } catch (error) {
                    console.error('Error checking accounts:', error);
                }
            }
        });
    </script>
</body>
</html>"""
        
        # Save HTML to temp file
        html_file = Path(tempfile.gettempdir()) / "harvest_wallet_connect.html"
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        # Start a simple HTTP server for MetaMask to detect
        import http.server
        import socketserver
        import threading
        import functools
        import socket
        
        PORT = 8765
        
        # Check if port is already in use
        def is_port_in_use(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('', port))
                    return False
                except OSError:
                    return True
        
        # Only start server if not already running
        if not is_port_in_use(PORT):
            # Create custom handler that serves from temp directory
            temp_dir = str(tempfile.gettempdir())
            handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=temp_dir)
            
            # Start server in background thread
            httpd = socketserver.TCPServer(("", PORT), handler)
            server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            server_thread.start()
            print(f"🔑 Server started on port {PORT}")
        else:
            print(f"✅ Server already running on port {PORT}")
        
        # Open in browser with HTTP URL
        webbrowser.open(f'http://localhost:{PORT}/harvest_wallet_connect.html')
        
        print(f"✅ Browser opened for MetaMask connection (http://localhost:{PORT})")
        print("📥 After connecting, the JSON file will download automatically")
        print("💡 Dashboard will auto-detect the connection in 10 seconds")
        print("\n🔑 Server running in background...")
        
        return True
    
    def check_response(self) -> Optional[Dict]:
        """Check if browser has responded with wallet info"""
        # Check temp file
        if self.response_file.exists():
            try:
                with open(self.response_file, 'r') as f:
                    response = json.load(f)
                
                if response.get('success'):
                    # Load existing config or create new one
                    existing_config = self.load_config() or {}
                    
                    # Update metamask section in dashboard format
                    existing_config['metamask'] = {
                        'connected': True,
                        'address': response['address'],
                        'chain_id': response.get('chain_id', '0x1'),
                        'last_connected': response['timestamp']
                    }
                    
                    # Keep backward compatibility
                    existing_config['metamask_connected'] = True
                    existing_config['metamask_address'] = response['address']
                    
                    self.save_config(existing_config)
                    
                    # Clean up response file
                    self.response_file.unlink()
                    
                    return existing_config
            except Exception as e:
                print(f"Error reading response: {e}")
        
        # Also check Downloads folder
        downloads = Path.home() / "Downloads" / "harvest_wallet_response.json"
        if downloads.exists():
            try:
                with open(downloads, 'r') as f:
                    response = json.load(f)
                
                if response.get('success'):
                    # Load existing config or create new one
                    existing_config = self.load_config() or {}
                    
                    # Update metamask section in dashboard format
                    existing_config['metamask'] = {
                        'connected': True,
                        'address': response['address'],
                        'chain_id': response.get('chain_id', '0x1'),
                        'last_connected': response['timestamp']
                    }
                    
                    # Keep backward compatibility
                    existing_config['metamask_connected'] = True
                    existing_config['metamask_address'] = response['address']
                    
                    self.save_config(existing_config)
                    downloads.unlink()  # Clean up
                    return existing_config
            except Exception as e:
                print(f"Error reading Downloads response: {e}")
        
        return None
    
    def disconnect(self):
        """Disconnect wallet"""
        # Load existing config to preserve other data
        existing_config = self.load_config() or {}
        
        # Update metamask section
        existing_config['metamask'] = {
            'connected': False,
            'address': None,
            'chain_id': None,
            'last_connected': None
        }
        
        # Keep backward compatibility
        existing_config['metamask_connected'] = False
        existing_config['metamask_address'] = None
        
        self.save_config(existing_config)
        print("✅ Wallet disconnected")


# Convenience functions
_connector = None

def get_connector() -> SimpleWalletConnector:
    """Get global connector instance"""
    global _connector
    if _connector is None:
        _connector = SimpleWalletConnector()
    return _connector


if __name__ == "__main__":
    """Test the connector"""
    connector = SimpleWalletConnector()
    
    if connector.is_connected():
        print(f"✅ Wallet connected: {connector.get_address()}")
        print("\nPress 'd' to disconnect, any other key to reconnect")
        choice = input().lower()
        if choice == 'd':
            connector.disconnect()
        else:
            connector.connect()
    else:
        print("No wallet connected. Starting connection...")
        connector.connect()
        
        print("\n⏳ Waiting for response...")
        print("After connecting in browser, press Enter to check...")
        input()
        
        result = connector.check_response()
        if result:
            print(f"✅ Connected: {result['metamask_address']}")
        else:
            print("❌ No response found. Make sure to save the downloaded JSON file.")
