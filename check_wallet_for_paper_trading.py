#!/usr/bin/env python3
"""
Wallet Connection Checker for Live Paper Trading
Ensures MetaMask is connected before starting paper trading
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.auto_wallet_manager import AutoWalletManager
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def check_wallet_connection() -> tuple[bool, str]:
    """
    Check if MetaMask wallet is connected.
    
    Returns:
        (is_connected, message)
    """
    console = Console()
    
    try:
        wallet_manager = AutoWalletManager()
        
        # Check MetaMask connection
        metamask_connected = wallet_manager.wallet_config.get('metamask', {}).get('connected', False)
        metamask_address = wallet_manager.wallet_config.get('metamask', {}).get('address')
        
        if metamask_connected and metamask_address:
            return True, f"MetaMask connected: {metamask_address}"
        else:
            return False, "MetaMask not connected"
            
    except Exception as e:
        return False, f"Error checking wallet: {e}"


def display_wallet_status():
    """Display wallet connection status with rich formatting"""
    console = Console()
    
    is_connected, message = check_wallet_connection()
    
    # Create status table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Item", style="cyan")
    table.add_column("Status")
    
    status_icon = "✅" if is_connected else "❌"
    status_style = "green" if is_connected else "red"
    
    table.add_row("MetaMask Connection", f"[{status_style}]{status_icon} {message}[/{status_style}]")
    
    if not is_connected:
        table.add_row("", "")
        table.add_row("Action Required", "[yellow]⚠️  Connect MetaMask before starting paper trading[/yellow]")
        table.add_row("How to Connect", "[cyan]1. Press 'W' in dashboard\n2. Or run: python cli.py wallet connect[/cyan]")
    
    panel = Panel(
        table,
        title="🔐 Wallet Status for Live Paper Trading",
        border_style="green" if is_connected else "red"
    )
    
    console.print()
    console.print(panel)
    console.print()
    
    return is_connected


if __name__ == "__main__":
    is_connected = display_wallet_status()
    sys.exit(0 if is_connected else 1)
