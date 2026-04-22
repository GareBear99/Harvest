#!/usr/bin/env python3
"""
Help Screen
Display keyboard commands and system information
"""

import sys
import os
import webbrowser
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.panel import Panel
from rich.console import Console
from ml.ml_config import get_ml_config


def render_help_screen() -> Panel:
    """Render comprehensive help screen with all commands and system info"""
    try:
        config = get_ml_config()
        
        # Get current ML status
        eth_ml = "ENABLED" if config.is_ml_enabled('ETH') else "DISABLED"
        btc_ml = "ENABLED" if config.is_ml_enabled('BTC') else "DISABLED"
        
        # Build content with improved formatting
        lines = []
        
        # Title section
        lines.append("═" * 80)
        lines.append("              🌾 HARVEST - Automated Crypto Trading Made Simple")
        lines.append("═" * 80)
        lines.append("")
        lines.append("┌─── QUICK START ─────────────────────────────────────────────────────────┐")
        lines.append("│  1. Press [W] to connect your MetaMask wallet                                  │")
        lines.append("│  2. That's it! We handle everything else automatically:                       │")
        lines.append("│     • Create your Bitcoin trading wallet                                      │")
        lines.append("│     • Manage all fees and transactions                                        │")
        lines.append("│     • Execute trades when opportunities arise                                 │")
        lines.append("│     • Grow your account with our proven strategies                            │")
        lines.append("└─────────────────────────────────────────────────────────────────────────────┘")
        lines.append("")
        
        # Core Navigation
        lines.append("┌─── CORE NAVIGATION ───────────────────────────────────────────────────────┐")
        lines.append("│  [Q] Quit            Exit dashboard and return to terminal                │")
        lines.append("│  [R] Refresh         Force immediate refresh of all panels                │")
        lines.append("│  [H] Help            Show this help screen (toggle on/off)                │")
        lines.append("│  [ESC] Exit Modal    Close any open modal/screen and return to dashboard  │")
        lines.append("└───────────────────────────────────────────────────────────────────────────┘")
        lines.append("")
        
        # What You Can Do
        lines.append("┌─── WHAT YOU CAN DO ──────────────────────────────────────────────────────┐")
        lines.append("│                                                                             │")
        lines.append("│  [W] Connect Your Wallet                                                    │")
        lines.append("│      Connect MetaMask in your browser → We do the rest!                     │")
        lines.append("│      • Your wallet stays secure in MetaMask (we never see your keys)        │")
        lines.append("│      • We automatically create a Bitcoin wallet for trading                  │")
        lines.append("│      • All fees handled automatically (gas, trading, conversions)            │")
        lines.append("│                                                                             │")
        lines.append("│  [S] Browse Trading Strategies                                              │")
        lines.append("│      See which strategies are making money                                   │")
        lines.append("│      • View past performance and success rates                               │")
        lines.append("│      • Filter by best performers (whitelist) or poor ones (blacklist)       │")
        lines.append("│      • We tested billions of strategies to find the best ones                │")
        lines.append("│                                                                             │")
        lines.append("│  [B] Test Strategies (Backtest)                                             │")
        lines.append("│      Try strategies with fake money first to see how they work              │")
        lines.append("│      • Start with $10 and watch it grow (or not) over 90 days              │")
        lines.append("│      • See detailed reports on wins, losses, and profits                     │")
        lines.append("│      • No risk - this is practice mode with historical data                 │")
        lines.append("│                                                                             │")
        lines.append("│  [X] Debug Terminal (For Advanced Users)                                    │")
        lines.append("│      See exactly what the system is doing behind the scenes                  │")
        lines.append("│      • Every action logged with timestamps                                   │")
        lines.append("│      • Check for errors or issues                                            │")
        lines.append("│      • Review past sessions (up to 3 historical sessions saved)              │")
        lines.append("│                                                                             │")
        lines.append("│  [D] Read Documentation                                                     │")
        lines.append("│      Opens full guide in your browser with pictures and examples             │")
        lines.append("│                                                                             │")
        lines.append("└─────────────────────────────────────────────────────────────────────────────┘")
        lines.append("")
        
        # How It Works
        lines.append("┌─── HOW IT WORKS ──────────────────────────────────────────────────────────┐")
        lines.append("│                                                                             │")
        lines.append("│  💰 Start Small, Grow Big                                                    │")
        lines.append("│     Begin with as little as $10. The system automatically increases your    │")
        lines.append("│     trading size as you profit ($10 → $20 → $30 → $50 → $100 → more!)      │")
        lines.append("│                                                                             │")
        lines.append("│  🔒 Safety First                                                             │")
        lines.append("│     • Practice mode first (paper trading) for 48 hours before real money     │")
        lines.append("│     • Maximum $100 per trade (until you reach $5,000 total)                 │")
        lines.append("│     • Your keys stay in MetaMask - we never have access to your wallet      │")
        lines.append("│                                                                             │")
        lines.append("│  🤖 AI-Powered Trading                                                       │")
        lines.append(f"│     Smart predictions for Ethereum: {eth_ml:<35} │")
        lines.append(f"│     Smart predictions for Bitcoin:  {btc_ml:<35} │")
        lines.append("│     (These help us make better buy/sell decisions)                          │")
        lines.append("│                                                                             │")
        lines.append("└─────────────────────────────────────────────────────────────────────────────┘")
        lines.append("")
        
        # Slot & Position System Explanation
        lines.append("┌─── UNDERSTANDING SLOTS & POSITIONS ───────────────────────────────────────┐")
        lines.append("│                                                                             │")
        lines.append("│  📊 What are SLOTS? (The Foundation: $10-$100)                              │")
        lines.append("│     Each $10 you have unlocks ONE SLOT for trading:                         │")
        lines.append("│     • $10  = 1 slot  (ETH, 1m timeframe only)                               │")
        lines.append("│     • $20  = 2 slots (ETH + BTC, 1m timeframe)                              │")
        lines.append("│     • $30  = 3 slots (ETH, BTC, ETH - 1m+5m timeframes)                     │")
        lines.append("│     • $40  = 4 slots (ETH, BTC, ETH, BTC - 1m+5m timeframes)                │")
        lines.append("│     • ...continue pattern...                                                │")
        lines.append("│     • $100 = 10 slots MAX (5 ETH + 5 BTC, ALL 5 timeframes) ← BASE SYSTEM   │")
        lines.append("│                                                                             │")
        lines.append("│     Slots alternate: ETH → BTC → ETH → BTC (odds=ETH, evens=BTC)           │")
        lines.append("│     More slots = More timeframes unlock (1m, 5m, 15m, 1h, 4h)              │")
        lines.append("│                                                                             │")
        lines.append("│  🚀 What are POSITIONS? (Growth Beyond $100)                                 │")
        lines.append("│     At $100+, slots are maxed (10 total). Now POSITIONS grow:               │")
        lines.append("│     • $100-$109: 1 position per timeframe per asset (10 total)              │")
        lines.append("│       → 5 timeframes × 2 assets × 1 position = 10 positions                 │")
        lines.append("│                                                                             │")
        lines.append("│     • $110: Pay $10 founder fee → Unlock 2nd position set                   │")
        lines.append("│       → 5 timeframes × 2 assets × 2 positions = 20 positions!               │")
        lines.append("│                                                                             │")
        lines.append("│     • $210: Pay $10 founder fee → Unlock 3rd position set                   │")
        lines.append("│       → 5 timeframes × 2 assets × 3 positions = 30 positions!! (MAXED)      │")
        lines.append("│                                                                             │")
        lines.append("│     • $300+: Position count MAXED at 30, but SIZE grows indefinitely!       │")
        lines.append("│       Your positions get BIGGER as balance increases. No limit!             │")
        lines.append("│                                                                             │")
        lines.append("│  📉 What if I lose money?                                                    │")
        lines.append("│     • Drop below $100? Slots reduce automatically (lose timeframes/assets)   │")
        lines.append("│     • Drop from $110 to $105? Keep 2nd position set (paid fee stays)        │")
        lines.append("│     • Drop from $210 to $150? Keep all 3 position sets (fees don't reset)   │")
        lines.append("│     • Baseline is always $100 - fees at $110, $210, $310, $410...           │")
        lines.append("│     • You only LOSE position sets if you drop below their unlock threshold   │")
        lines.append("│                                                                             │")
        lines.append("│  🎯 The Path to Maximum Earning:                                             │")
        lines.append("│     $10 → $100:  Unlock all 10 base slots (foundation complete)             │")
        lines.append("│     $110:        Unlock 20 positions (2× earning power)                      │")
        lines.append("│     $210:        Unlock 30 positions (3× earning power - MAXED)              │")
        lines.append("│     $300+:       Positions grow BIGGER → Earn more per trade forever!       │")
        lines.append("│                                                                             │")
        lines.append("└─────────────────────────────────────────────────────────────────────────────┘")
        lines.append("")
        
        # Status Bar Guide
        lines.append("┌─── STATUS BAR GUIDE ──────────────────────────────────────────────────────┐")
        lines.append("│  The status bar at the bottom tracks all your interactions:                │")
        lines.append("│                                                                             │")
        lines.append("│  Icons:   ℹ️  Ready    ⏳ Processing    ✅ Success    ❌ Failed             │")
        lines.append("│  Key:     Shows last keypress with validation (✓ valid / ✗ invalid)        │")
        lines.append("│  History: Shows last 3 commands pressed                                     │")
        lines.append("│  Op:      Current operation being executed                                  │")
        lines.append("│  Result:  Operation outcome with detailed error messages                    │")
        lines.append("│                                                                             │")
        lines.append("│  Every keypress is logged and validated in real-time!                       │")
        lines.append("└───────────────────────────────────────────────────────────────────────────┘")
        lines.append("")
        
        # Helpful Tips
        lines.append("┌─── HELPFUL TIPS ────────────────────────────────────────────────────────────┐")
        lines.append("│  • The screen updates automatically every 10 seconds                         │")
        lines.append("│  • Press R if you want to see updates faster                                │")
        lines.append("│  • ESC or Q closes any screen and returns to main dashboard                │")
        lines.append("│  • Watch the bottom bar for feedback on every button you press             │")
        lines.append("│  • Once connected, your wallet stays connected (no need to reconnect)      │")
        lines.append("│  • Check the debug terminal (X key) if something seems wrong               │")
        lines.append("└─────────────────────────────────────────────────────────────────────────────┘")
        lines.append("")
        
        # Footer with exit instruction
        lines.append("═" * 80)
        lines.append("                     Press [ESC] or [Q] to close this help screen")
        lines.append("═" * 80)
        
        content = "\n".join(lines)
        
        return Panel(
            content,
            title="📖 HARVEST HELP & DOCUMENTATION",
            border_style="bright_cyan",
            padding=(1, 2)
        )
    
    except Exception as e:
        return Panel(
            f"Error rendering help screen: {e}",
            title="📖 HARVEST DASHBOARD - HELP",
            border_style="red",
            padding=(1, 2)
        )


def open_documentation() -> bool:
    """
    Open HTML documentation in default browser
    
    Returns:
        bool: True if successfully opened, False otherwise
    """
    try:
        doc_path = os.path.abspath('documentation_package/index.html')
        
        if os.path.exists(doc_path):
            webbrowser.open(f'file://{doc_path}')
            return True
        else:
            return False
    
    except Exception as e:
        print(f"Error opening documentation: {e}")
        return False


def show_help_interactive():
    """Show help screen in interactive mode (for testing)"""
    console = Console()
    
    panel = render_help_screen()
    console.print("\n")
    console.print(panel)
    
    console.print("\n[yellow]Press 'D' to test documentation launcher, Ctrl+C to exit[/yellow]")
    
    try:
        import time
        while True:
            time.sleep(0.1)
            # In real implementation, keyboard input would be handled here
    except KeyboardInterrupt:
        console.print("\n\n[green]Exiting...[/green]")


if __name__ == "__main__":
    # Test the help screen
    console = Console()
    
    console.print("\n[bold]Testing Help Screen[/bold]\n")
    
    # Test render
    panel = render_help_screen()
    console.print(panel)
    
    # Test documentation launcher
    console.print("\n[bold]Testing Documentation Launcher[/bold]")
    result = open_documentation()
    
    if result:
        console.print("[green]✅ Documentation opened successfully[/green]")
    else:
        console.print("[red]❌ Documentation file not found[/red]")
        console.print("[yellow]Expected location: documentation_package/index.html[/yellow]")
