#!/usr/bin/env python3
"""
Seed Browser
Interactive seed viewer with performance history
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from typing import Dict, List
from dashboard.formatters import format_currency, format_seed, format_status_icon


def load_seed_data() -> Dict:
    """Load seed performance data from tracker"""
    try:
        tracker_file = 'ml/seed_performance_tracker.json'
        
        if os.path.exists(tracker_file):
            with open(tracker_file, 'r') as f:
                return json.load(f)
        else:
            return {
                'seeds': {},
                'whitelist': [],
                'blacklist': []
            }
    except Exception as e:
        print(f"Error loading seed data: {e}")
        return {
            'seeds': {},
            'whitelist': [],
            'blacklist': []
        }


def render_seed_browser(view: str = 'all', page: int = 0, page_size: int = 10) -> Panel:
    """
    Render seed browser panel
    
    Args:
        view: 'all', 'whitelist', or 'blacklist'
        page: Current page number
        page_size: Number of seeds per page
    """
    try:
        data = load_seed_data()
        
        # Filter seeds based on view
        if view == 'whitelist':
            seed_ids = data.get('whitelist', [])
            title = "✅ SEED BROWSER - WHITELIST"
            border = "green"
        elif view == 'blacklist':
            seed_ids = data.get('blacklist', [])
            title = "⛔ SEED BROWSER - BLACKLIST"
            border = "red"
        else:
            seed_ids = list(data.get('seeds', {}).keys())
            title = "🔍 SEED BROWSER - ALL SEEDS"
            border = "blue"
        
        # Paginate
        total_seeds = len(seed_ids)
        start_idx = page * page_size
        end_idx = min(start_idx + page_size, total_seeds)
        page_seeds = seed_ids[start_idx:end_idx]
        
        # Build table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Seed", justify="right", style="cyan")
        table.add_column("TF", justify="center")
        table.add_column("WR", justify="right")
        table.add_column("Trades", justify="right")
        table.add_column("P&L", justify="right")
        table.add_column("Status", justify="center")
        
        seeds_dict = data.get('seeds', {})
        
        for seed_id in page_seeds:
            seed_data = seeds_dict.get(seed_id, {})
            
            seed_num = seed_data.get('seed', seed_id)
            timeframe = seed_data.get('timeframe', '?')
            win_rate = seed_data.get('average_win_rate', 0) * 100
            total_trades = seed_data.get('total_trades', 0)
            pnl = seed_data.get('total_pnl', 0.0)
            
            # Determine status
            if seed_id in data.get('whitelist', []):
                status = format_status_icon('whitelist')
            elif seed_id in data.get('blacklist', []):
                status = format_status_icon('blacklist')
            else:
                status = format_status_icon('neutral')
            
            table.add_row(
                format_seed(int(seed_num)),
                timeframe,
                f"{win_rate:.1f}%",
                str(total_trades),
                format_currency(pnl),
                status
            )
        
        # Footer with pagination info
        footer = f"\nPage {page + 1}/{(total_seeds + page_size - 1) // page_size if total_seeds > 0 else 1} | Total: {total_seeds} seeds\n"
        footer += "[W]hitelist [B]lacklist [A]ll  [←][→] Page  [ESC] Back"
        
        content = table
        
        return Panel(
            content,
            title=title,
            subtitle=footer,
            border_style=border,
            padding=(1, 2)
        )
    
    except Exception as e:
        return Panel(
            f"Error rendering seed browser: {e}",
            title="🔍 SEED BROWSER",
            border_style="red",
            padding=(1, 2)
        )


def render_seed_detail(seed_id: str) -> Panel:
    """Render detailed view of a single seed"""
    try:
        data = load_seed_data()
        seed_data = data.get('seeds', {}).get(seed_id, {})
        
        if not seed_data:
            return Panel(
                f"Seed {seed_id} not found",
                title="SEED DETAIL",
                border_style="red"
            )
        
        # Build content
        lines = []
        lines.append(f"Seed: {format_seed(int(seed_data.get('seed', seed_id)))}")
        lines.append(f"Timeframe: {seed_data.get('timeframe', '?')}")
        lines.append(f"Input Seed: {seed_data.get('input_seed', 'N/A')}")
        lines.append("")
        
        lines.append("Performance:")
        lines.append(f"  Win Rate: {seed_data.get('average_win_rate', 0) * 100:.1f}%")
        lines.append(f"  Total Trades: {seed_data.get('total_trades', 0)}")
        lines.append(f"  Total P&L: {format_currency(seed_data.get('total_pnl', 0.0))}")
        lines.append(f"  First Tested: {seed_data.get('first_tested', 'Unknown')}")
        lines.append(f"  Last Tested: {seed_data.get('last_tested', 'Unknown')}")
        lines.append("")
        
        # Status
        if seed_id in data.get('whitelist', []):
            lines.append(f"Status: {format_status_icon('whitelist')} WHITELISTED")
        elif seed_id in data.get('blacklist', []):
            lines.append(f"Status: {format_status_icon('blacklist')} BLACKLISTED")
        else:
            lines.append(f"Status: {format_status_icon('neutral')} NEUTRAL")
        
        lines.append("")
        lines.append("[ESC] Back to list")
        
        content = "\n".join(lines)
        
        return Panel(
            content,
            title="📊 SEED DETAIL",
            border_style="yellow",
            padding=(1, 2)
        )
    
    except Exception as e:
        return Panel(
            f"Error rendering seed detail: {e}",
            title="📊 SEED DETAIL",
            border_style="red",
            padding=(1, 2)
        )


def show_seed_browser_interactive():
    """Show seed browser in interactive mode (for testing)"""
    console = Console()
    
    console.print("\n[bold]Seed Browser Test[/bold]\n")
    
    # Test different views
    for view in ['all', 'whitelist', 'blacklist']:
        panel = render_seed_browser(view=view, page=0)
        console.print(panel)
        console.print()


if __name__ == "__main__":
    # Test the seed browser
    show_seed_browser_interactive()
