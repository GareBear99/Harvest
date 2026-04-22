#!/usr/bin/env python3
"""
ML Control Panel
Enable/disable machine learning per asset (ETH/BTC)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.panel import Panel
from rich.console import Console
from ml.ml_config import get_ml_config


def render_ml_control_panel() -> Panel:
    """Render ML control panel display"""
    try:
        config = get_ml_config()
        
        # Build content
        lines = []
        
        # ETH Bot status
        eth_enabled = config.is_ml_enabled('ETH')
        eth_status = "✅ ENABLED (ML features active)" if eth_enabled else "❌ DISABLED (BASE_STRATEGY only)"
        lines.append("🔹 ETH Bot")
        lines.append(f"   ML Status: {eth_status}")
        lines.append("   [E] Enable ML  [D] Disable ML")
        lines.append("")
        
        # BTC Bot status
        btc_enabled = config.is_ml_enabled('BTC')
        btc_status = "✅ ENABLED (ML features active)" if btc_enabled else "❌ DISABLED (BASE_STRATEGY only)"
        lines.append("🔹 BTC Bot")
        lines.append(f"   ML Status: {btc_status}")
        lines.append("   [E] Enable ML  [D] Disable ML")
        lines.append("")
        
        # Current mode and timeframes
        lines.append("Current Mode: BACKTEST")
        lines.append("Timeframes: 15m ✅ | 1h ✅ | 4h ✅")
        lines.append("")
        
        # Controls
        lines.append("[A] Enable All  [N] Disable All  [ESC] Back")
        
        content = "\n".join(lines)
        
        return Panel(
            content,
            title="⚙️  ML CONTROL PANEL",
            border_style="magenta",
            padding=(1, 2)
        )
    
    except Exception as e:
        return Panel(
            f"Error rendering ML control: {e}",
            title="⚙️  ML CONTROL PANEL",
            border_style="red",
            padding=(1, 2)
        )


def handle_ml_control_key(key: str, selected_asset: str = 'ETH') -> tuple:
    """
    Handle keyboard input for ML control
    
    Args:
        key: The pressed key
        selected_asset: Currently selected asset (ETH or BTC)
    
    Returns:
        tuple: (should_close, message, new_selected_asset)
    """
    try:
        config = get_ml_config()
        
        if key.lower() == 'e':
            # Enable ML for selected asset
            config.enable_ml(selected_asset, True)
            return (False, f"✅ {selected_asset} ML enabled", selected_asset)
        
        elif key.lower() == 'd':
            # Disable ML for selected asset
            config.enable_ml(selected_asset, False)
            return (False, f"❌ {selected_asset} ML disabled", selected_asset)
        
        elif key.lower() == 'a':
            # Enable all
            config.enable_all_ml(True)
            return (False, "✅ ML enabled for all assets", selected_asset)
        
        elif key.lower() == 'n':
            # Disable all
            config.enable_all_ml(False)
            return (False, "❌ ML disabled for all assets", selected_asset)
        
        elif key == 'escape' or key.lower() == 'q':
            # Close panel
            return (True, None, selected_asset)
        
        elif key == 'tab':
            # Switch selected asset
            new_asset = 'BTC' if selected_asset == 'ETH' else 'ETH'
            return (False, f"Selected: {new_asset}", new_asset)
        
        else:
            return (False, None, selected_asset)
    
    except Exception as e:
        return (False, f"Error: {e}", selected_asset)


def show_ml_control_interactive():
    """Show ML control panel in interactive mode (for testing)"""
    console = Console()
    
    console.print("\n[bold magenta]ML Control Panel[/bold magenta]")
    console.print("This is a test mode. In the dashboard, use keyboard controls.\n")
    
    config = get_ml_config()
    config.print_status()
    
    console.print("\n[yellow]Press Ctrl+C to exit[/yellow]")
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n\n[green]Exiting...[/green]")


if __name__ == "__main__":
    # Test the ML control panel
    show_ml_control_interactive()
