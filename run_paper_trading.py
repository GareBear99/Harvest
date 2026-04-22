#!/usr/bin/env python3
"""
Live Paper Trading Runner
Runs 48-hour paper trading session with real-time stats display
"""

import sys
import os
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.paper_trading_tracker import get_paper_trading_tracker
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout


def create_stats_display(tracker) -> Layout:
    """Create comprehensive stats display"""
    status = tracker.get_status()
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="stats", size=12),
        Layout(name="requirements", size=8),
        Layout(name="recent", size=10),
        Layout(name="footer", size=3)
    )
    
    # Header
    header_text = Text()
    header_text.append("📄 LIVE PAPER TRADING SESSION", style="bold cyan")
    header_text.append(f" • Status: {status['status'].upper()}", style="bold yellow")
    layout["header"].update(Panel(header_text, border_style="cyan"))
    
    # Stats Panel
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column("Label", style="cyan")
    stats_table.add_column("Value", style="white bold")
    
    # Calculate elapsed time
    elapsed_h = int(status['duration_hours'])
    elapsed_m = int((status['duration_hours'] - elapsed_h) * 60)
    remaining_h = max(0, 48 - status['duration_hours'])
    
    stats_table.add_row("Starting Balance:", f"${status['starting_balance']:.2f}")
    stats_table.add_row("Current Balance:", f"${status['current_balance']:.2f}")
    
    # Show P&L with fee breakdown
    total_pnl = status['total_pnl']
    pnl_style = "[green]" if total_pnl > 0 else "[red]" if total_pnl < 0 else "[yellow]"
    pnl_sign = "+" if total_pnl > 0 else ""
    stats_table.add_row("Total P&L:", f"{pnl_style}{pnl_sign}${total_pnl:.2f}[/{pnl_style[1:]}")
    
    # Fee breakdown
    total_fees = status['total_fees_paid']
    if total_fees > 0:
        gas_fees = status.get('gas_fees_paid', 0)
        btc_fees = status.get('btc_fees_paid', 0)
        conv_fees = status.get('conversion_fees_paid', 0)
        stats_table.add_row("Total Fees:", f"[yellow]${total_fees:.2f}[/yellow]")
        stats_table.add_row("  ├─ Gas:", f"[dim]${gas_fees:.2f}[/dim]")
        if conv_fees > 0:
            stats_table.add_row("  ├─ Conversion:", f"[dim]${conv_fees:.2f}[/dim]")
        if btc_fees > 0:
            stats_table.add_row("  └─ BTC Transfer:", f"[dim]${btc_fees:.2f}[/dim]")
    
    stats_table.add_row("Active Slots:", f"{status.get('active_slots', 10)} (Full Base System)")
    stats_table.add_row("", "")
    stats_table.add_row("Duration:", f"{elapsed_h}h {elapsed_m}m / 48h")
    stats_table.add_row("Remaining:", f"{remaining_h:.1f}h")
    stats_table.add_row("Total Trades:", f"{status['total_trades']}")
    stats_table.add_row("Win Rate:", f"{status['win_rate']:.1%}" if status['total_trades'] > 0 else "N/A")
    stats_table.add_row("Wins/Losses:", f"{status['winning_trades']}W / {status['losing_trades']}L")
    
    # Batch progress
    wins = status.get('winning_trades', 0)
    if wins > 0:
        batch_progress = wins % 5
        stats_table.add_row("Batch Progress:", f"[cyan]{batch_progress}/5 wins → next BTC transfer[/cyan]")
    
    layout["stats"].update(Panel(stats_table, title="📊 Session Stats", border_style="blue"))
    
    # Requirements Panel
    reqs = tracker.check_requirements()
    req_table = Table(show_header=True, box=None)
    req_table.add_column("Requirement", style="cyan")
    req_table.add_column("Status", justify="center")
    req_table.add_column("Progress", justify="right")
    
    # Duration
    dur_icon = "✅" if reqs['duration']['met'] else "❌"
    dur_prog = f"{reqs['duration']['current']:.1f}h / {reqs['duration']['required']}h"
    req_table.add_row("48 Hours Duration", dur_icon, dur_prog)
    
    # Trades
    trades_icon = "✅" if reqs['trades']['met'] else "❌"
    trades_prog = f"{reqs['trades']['current']} / {reqs['trades']['required']}"
    req_table.add_row("Min 1 Trade", trades_icon, trades_prog)
    
    # P&L
    pnl_icon = "✅" if reqs['pnl']['met'] else "❌"
    pnl_prog = f"${reqs['pnl']['current']:.2f}"
    req_table.add_row("Positive P&L", pnl_icon, pnl_prog)
    
    approval_status = "✅ APPROVED FOR LIVE" if reqs['all_met'] else "⏳ PENDING"
    layout["requirements"].update(Panel(
        req_table,
        title=f"📋 Requirements • {approval_status}",
        border_style="green" if reqs['all_met'] else "yellow"
    ))
    
    # Recent Trades
    recent_trades = tracker.get_recent_trades(n=5)
    if recent_trades:
        trades_table = Table(show_header=True, box=None)
        trades_table.add_column("Time", style="dim")
        trades_table.add_column("TF", justify="center")
        trades_table.add_column("Asset")
        trades_table.add_column("P&L", justify="right")
        trades_table.add_column("Result")
        
        for trade in reversed(recent_trades[-5:]):
            ts = datetime.fromisoformat(trade['timestamp'])
            time_str = ts.strftime("%H:%M:%S")
            tf = trade.get('timeframe', '?')
            asset = trade.get('asset', '?')
            pnl = trade.get('pnl', 0)
            btc_fee = trade.get('btc_fee', 0)
            net_pnl = pnl - btc_fee
            
            pnl_str = f"${net_pnl:+.2f}"
            if btc_fee > 0:
                pnl_str += f" (fee: ${btc_fee:.2f})"
            
            outcome = trade.get('outcome', '?')
            outcome_style = "green" if outcome == "win" else "red" if outcome == "loss" else "white"
            
            trades_table.add_row(
                time_str,
                tf,
                asset,
                f"[{outcome_style}]{pnl_str}[/{outcome_style}]",
                f"[{outcome_style}]{outcome.upper()}[/{outcome_style}]"
            )
        
        layout["recent"].update(Panel(trades_table, title="📈 Recent Trades", border_style="magenta"))
    else:
        layout["recent"].update(Panel(
            "[dim]No trades yet - waiting for opportunities...[/dim]",
            title="📈 Recent Trades",
            border_style="magenta"
        ))
    
    # Footer
    footer_text = Text()
    footer_text.append("Press ", style="dim")
    footer_text.append("Ctrl+C", style="bold")
    footer_text.append(" to stop • Data auto-saves every update", style="dim")
    layout["footer"].update(Panel(footer_text, border_style="dim"))
    
    return layout


def run_live_paper_trading():
    """Run live paper trading with real-time display"""
    console = Console()
    
    # Check wallet connection before starting
    console.print("\n[cyan]Checking wallet connection...[/cyan]")
    try:
        from core.auto_wallet_manager import AutoWalletManager
        wallet_manager = AutoWalletManager()
        metamask_connected = wallet_manager.wallet_config.get('metamask', {}).get('connected', False)
        metamask_address = wallet_manager.wallet_config.get('metamask', {}).get('address')
        
        if not metamask_connected or not metamask_address:
            console.print("\n[red]❌ MetaMask wallet not connected![/red]")
            console.print("[yellow]⚠️  Live paper trading requires a connected wallet[/yellow]\n")
            console.print("How to connect:")
            console.print("  1. Run: [cyan]python check_wallet_for_paper_trading.py[/cyan]")
            console.print("  2. Or launch dashboard and press 'W'")
            console.print("  3. Or run: [cyan]python cli.py wallet connect[/cyan]\n")
            return
        
        console.print(f"[green]✅ MetaMask connected: {metamask_address}[/green]\n")
    except Exception as e:
        console.print(f"[red]Error checking wallet: {e}[/red]\n")
        return
    
    tracker = get_paper_trading_tracker()
    
    # Check if already running
    status = tracker.get_status()
    if status['status'] == 'running':
        console.print("\n[yellow]⚠️  Paper trading session already in progress[/yellow]")
        console.print(f"Started: {status['started_at']}")
        console.print(f"Duration: {status['duration_hours']:.1f}h / 48h")
        console.print(f"Trades: {status['total_trades']}")
        console.print(f"P&L: ${status['total_pnl']:.2f}\n")
        console.print("[cyan]Continuing with existing session...[/cyan]\n")
        time.sleep(1)
    else:
        # Start new session
        console.print("\n" + "="*80)
        console.print("🚀 STARTING PAPER TRADING SESSION")
        console.print("="*80)
        console.print()
        console.print("Configuration:")
        console.print("  • Balance: $300.00 (Maximum Earning Potential)")
        console.print("  • Active Slots: 30 (All timeframes, Position Tier 3 MAXED)")
        console.print("  • Duration: 48 hours")
        console.print("  • Requirements: 1+ trade, positive P&L")
        console.print()
        
        result = tracker.start_paper_trading()
        if not result['success']:
            console.print(f"[red]Error: {result['message']}[/red]")
            return
        
        console.print(f"[green]✅ {result['message']}[/green]")
        console.print()
        time.sleep(2)
    
    # Monitor session
    console.print("[cyan]Starting live monitor...[/cyan]\n")
    time.sleep(1)
    
    try:
        with Live(create_stats_display(tracker), refresh_per_second=1, console=console) as live:
            while True:
                # Update display
                live.update(create_stats_display(tracker))
                
                # Check if requirements met
                reqs = tracker.check_requirements()
                if reqs['all_met'] and tracker.data['status'] == 'running':
                    console.print("\n[green]🎉 ALL REQUIREMENTS MET![/green]")
                    console.print("[green]You can now complete the session and start live trading.[/green]\n")
                    
                    response = input("Complete paper trading now? (yes/no): ").strip().lower()
                    if response == 'yes':
                        result = tracker.complete_paper_trading()
                        console.print(f"\n[green]✅ {result['message']}[/green]\n")
                        break
                
                time.sleep(1)
    
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⏸️  Monitoring paused[/yellow]")
        console.print("[dim]Paper trading continues in background[/dim]")
        console.print("[dim]Run this script again to resume monitoring[/dim]\n")


def show_menu():
    """Show command menu"""
    console = Console()
    tracker = get_paper_trading_tracker()
    status = tracker.get_status()
    
    console.print("\n" + "="*80)
    console.print("📄 PAPER TRADING MANAGEMENT")
    console.print("="*80)
    console.print()
    console.print(f"Current Status: {status['status'].upper()}")
    console.print(f"Duration: {status['duration_hours']:.1f}h / 48h")
    console.print(f"Total Trades: {status['total_trades']}")
    console.print(f"Total P&L: ${status['total_pnl']:.2f}")
    console.print()
    console.print("Available Commands:")
    console.print("  [1] Start/Monitor Live Session")
    console.print("  [2] View Current Stats")
    console.print("  [3] Reset Session (Clear All Data)")
    console.print("  [4] Complete Session (if requirements met)")
    console.print("  [5] Stop Session (without completing)")
    console.print("  [6] Exit")
    console.print()
    
    choice = input("Enter choice (1-6): ").strip()
    return choice


def show_stats():
    """Show current stats"""
    console = Console()
    tracker = get_paper_trading_tracker()
    status = tracker.get_status()
    
    console.print("\n" + "="*80)
    console.print("📊 PAPER TRADING STATS")
    console.print("="*80)
    console.print()
    console.print(f"Status: {status['status']}")
    console.print(f"Balance: ${status['starting_balance']:.2f} → ${status['current_balance']:.2f}")
    console.print(f"Active Slots: {status.get('active_slots', 10)}")
    console.print(f"Duration: {status['duration_hours']:.1f}h / 48h")
    console.print(f"Total Trades: {status['total_trades']} (W:{status['winning_trades']} L:{status['losing_trades']})")
    console.print(f"Win Rate: {status['win_rate']:.1%}" if status['total_trades'] > 0 else "Win Rate: N/A")
    console.print(f"Total P&L: ${status['total_pnl']:.2f}")
    if status.get('btc_fees_paid', 0) > 0:
        console.print(f"BTC Fees: ${status['btc_fees_paid']:.2f}")
    console.print()
    
    # Requirements with setup fee context
    reqs = tracker.check_requirements()
    setup_fees = status.get('setup_fees', 0.0)
    
    console.print("Requirements:")
    console.print(f"  Duration (48h): {'✅' if reqs['duration']['met'] else '❌'} {reqs['duration']['current']:.1f}h / {reqs['duration']['required']}h")
    console.print(f"  Min Trades (1): {'✅' if reqs['trades']['met'] else '❌'} {reqs['trades']['current']} / {reqs['trades']['required']}")
    
    # Show P&L with setup fee context
    pnl = reqs['pnl']['current']
    if setup_fees > 0:
        console.print(f"  Positive P&L: {'✅' if reqs['pnl']['met'] else '❌'} ${pnl:.2f} (started at -${setup_fees:.2f})")
        if pnl < 0:
            needed = abs(pnl)
            console.print(f"    [dim]Need ${needed:.2f} more to break even[/dim]")
    else:
        console.print(f"  Positive P&L: {'✅' if reqs['pnl']['met'] else '❌'} ${pnl:.2f}")
    
    console.print(f"  All Met: {'✅ APPROVED' if reqs['all_met'] else '❌ NOT READY'}")
    console.print()


def reset_session():
    """Reset the paper trading session"""
    console = Console()
    
    console.print("\n[yellow]⚠️  WARNING: This will delete all paper trading data![/yellow]")
    console.print("[yellow]This includes:[/yellow]")
    console.print("  • All trade history")
    console.print("  • Duration tracking")
    console.print("  • P&L records")
    console.print("  • Completion status")
    console.print()
    
    confirm = input("Type 'RESET' to confirm: ").strip()
    if confirm == 'RESET':
        tracker = get_paper_trading_tracker()
        result = tracker.reset()
        console.print(f"\n[green]✅ {result['message']}[/green]")
        console.print("[green]You can now start a fresh 48-hour session[/green]\n")
    else:
        console.print("\n[red]Reset cancelled[/red]\n")


def complete_session():
    """Complete the paper trading session"""
    console = Console()
    tracker = get_paper_trading_tracker()
    
    reqs = tracker.check_requirements()
    if not reqs['all_met']:
        console.print("\n[red]❌ Cannot complete - requirements not met:[/red]")
        if not reqs['duration']['met']:
            console.print(f"  • Duration: {reqs['duration']['current']:.1f}h / {reqs['duration']['required']}h")
        if not reqs['trades']['met']:
            console.print(f"  • Trades: {reqs['trades']['current']} / {reqs['trades']['required']}")
        if not reqs['pnl']['met']:
            console.print(f"  • P&L: ${reqs['pnl']['current']:.2f} (must be positive)")
        console.print()
        return
    
    console.print("\n[green]✅ All requirements met![/green]")
    confirm = input("Complete paper trading and approve for live? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        result = tracker.complete_paper_trading()
        if result['success']:
            console.print(f"\n[green]🎉 {result['message']}[/green]")
            console.print("[green]You are now approved for live trading![/green]")
            console.print("\nRun: python3 pre_trading_check.py --live")
            console.print()
        else:
            console.print(f"\n[red]Error: {result['message']}[/red]\n")
    else:
        console.print("\n[yellow]Completion cancelled[/yellow]\n")


def stop_session():
    """Stop the paper trading session without completing"""
    console = Console()
    
    console.print("\n[yellow]⚠️  This will stop paper trading without completing it[/yellow]")
    console.print("[yellow]You will need to start over to get approved for live trading[/yellow]\n")
    
    confirm = input("Stop paper trading? (yes/no): ").strip().lower()
    if confirm == 'yes':
        tracker = get_paper_trading_tracker()
        result = tracker.stop_paper_trading()
        console.print(f"\n[green]✅ {result['message']}[/green]\n")
    else:
        console.print("\n[yellow]Cancelled[/yellow]\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Paper Trading Management")
    parser.add_argument('--reset', action='store_true', help='Reset all paper trading data')
    parser.add_argument('--stats', action='store_true', help='Show current stats')
    parser.add_argument('--complete', action='store_true', help='Complete session')
    parser.add_argument('--stop', action='store_true', help='Stop session')
    parser.add_argument('--monitor', action='store_true', help='Start live monitoring')
    
    args = parser.parse_args()
    
    try:
        if args.reset:
            reset_session()
        elif args.stats:
            show_stats()
        elif args.complete:
            complete_session()
        elif args.stop:
            stop_session()
        elif args.monitor:
            run_live_paper_trading()
        else:
            # Interactive menu
            while True:
                choice = show_menu()
                
                if choice == '1':
                    run_live_paper_trading()
                elif choice == '2':
                    show_stats()
                elif choice == '3':
                    reset_session()
                elif choice == '4':
                    complete_session()
                elif choice == '5':
                    stop_session()
                elif choice == '6':
                    console = Console()
                    console.print("\n[cyan]Goodbye![/cyan]\n")
                    break
                else:
                    console = Console()
                    console.print("\n[red]Invalid choice[/red]\n")
    
    except KeyboardInterrupt:
        console = Console()
        console.print("\n\n[yellow]Interrupted[/yellow]\n")
        sys.exit(0)
    except Exception as e:
        console = Console()
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
