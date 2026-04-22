#!/bin/bash
# HARVEST Dashboard Launcher
# Automatically initializes wallet system and starts the terminal dashboard

echo "========================================="
echo "     HARVEST Trading Dashboard"
echo "========================================="
echo ""

# Check Python availability
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Initialize wallet system (creates BTC wallet if needed)
echo "🔧 Initializing wallet system..."
python3 -c "
from core.auto_wallet_manager import AutoWalletManager
import sys

try:
    manager = AutoWalletManager()
    
    # Ensure BTC wallet exists
    if not manager.wallet_config['btc_wallet']['created']:
        print('📝 Generating BTC wallet for profit collection...')
        result = manager._check_or_create_btc_wallet()
        if result['exists']:
            print(f'✅ BTC Wallet created: {result["address"][:20]}...')
        else:
            print(f'⚠️  Warning: Could not create BTC wallet')
    else:
        btc_addr = manager.wallet_config['btc_wallet']['address']
        print(f'✅ BTC Wallet exists: {btc_addr[:20]}...')
    
    print(f'🆔 Client ID: {manager.client_id[:16]}...')
    
except Exception as e:
    print(f'❌ Wallet initialization error: {e}', file=sys.stderr)
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Failed to initialize wallet system"
    exit 1
fi

echo ""
echo "🚀 Starting dashboard..."
echo "   Press 'W' to connect MetaMask"
echo "   Press 'Q' to quit"
echo ""

# Start the dashboard
python3 dashboard/terminal_ui.py --test

# Cleanup message
echo ""
echo "✅ Dashboard closed"
echo ""
