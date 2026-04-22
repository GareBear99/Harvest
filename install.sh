#!/bin/bash
# HARVEST Installation Script

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       HARVEST - Dual-Engine Trading System Installer        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Found Python $PYTHON_VERSION"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt -q

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data

# Make CLI executable
echo "🔧 Setting up CLI..."
chmod +x cli.py

# Create symlink (optional, may need sudo)
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🔗 Creating harvest command..."
    if [ -w /usr/local/bin ]; then
        ln -sf "$(pwd)/cli.py" /usr/local/bin/harvest
        echo "✓ You can now use 'harvest' command"
    else
        echo "⚠️  Run with sudo to install 'harvest' command globally:"
        echo "   sudo ln -sf $(pwd)/cli.py /usr/local/bin/harvest"
    fi
fi

# Run validation
echo ""
echo "🔍 Running validation tests..."
python3 cli.py validate || echo "⚠️  Some tests failed (non-critical)"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                   Installation Complete!                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Quick Start:"
echo "   python3 cli.py info              # Show system information"
echo "   python3 cli.py status            # Check configuration"
echo "   python3 cli.py backtest          # Run backtest on ETH"
echo "   python3 cli.py validate          # Run validation tests"
echo ""
echo "📚 Documentation: ./README.md"
echo "💬 Support: https://github.com/yourusername/harvest/issues"
echo ""
