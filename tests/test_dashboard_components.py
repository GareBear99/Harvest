#!/usr/bin/env python3
"""
Test all dashboard components
"""

from rich.console import Console
from rich.layout import Layout

# Import all dashboard components
from dashboard.panels import SeedStatusPanel, BotStatusPanel, PerformancePanel, SystemHealthPanel
from dashboard.help_screen import render_help_screen, open_documentation
from dashboard.ml_control import render_ml_control_panel
from dashboard.seed_browser import render_seed_browser
from dashboard.backtest_control import BacktestController, render_backtest_control

console = Console()

def test_panels():
    """Test 4 main panels with mock data"""
    console.print("\n[bold cyan]Testing Dashboard Panels[/bold cyan]\n")
    
    # Mock data for testing
    seed_data = {
        'total_tested': 125,
        'whitelisted': 23,
        'blacklisted': 45,
        'top_performer': {'seed': 15913535, 'win_rate': 0.82, 'pnl': 18.30},
        'current_seeds_by_timeframe': {
            '15m': {'seed': 15542880, 'input_seed': 777},
            '1h': {'seed': 60507652, 'input_seed': 888},
            '4h': {'seed': 240966292, 'input_seed': 999}
        }
    }
    
    bot_data = {
        'status': 'running',
        'mode': 'BACKTEST',
        'seed_info': {'strategy_seed': 15913535, 'timeframe': '15m', 'input_seed': 777},
        'balance': {'initial': 10.0, 'current': 28.30},
        'active_positions': [],
        'max_positions': 2,
        'last_trade': None
    }
    
    performance_data = {
        'wins': 15,
        'losses': 3,
        'pnl': 18.30,
        'max_drawdown': 5.2,
        'by_timeframe': {
            '15m': {'wins': 6, 'losses': 2, 'pnl': 8.50},
            '1h': {'wins': 7, 'losses': 2, 'pnl': 7.20},
            '4h': {'wins': 4, 'losses': 0, 'pnl': 2.60}
        }
    }
    
    system_data = {
        'data_status': {'fresh': True, 'updated_ago': '2h ago'},
        'connections': 'operational',
        'warnings': []
    }
    
    # Test each panel
    seed_panel = SeedStatusPanel()
    console.print(seed_panel.render(seed_data))
    
    bot_panel = BotStatusPanel()
    console.print(bot_panel.render(bot_data))
    
    perf_panel = PerformancePanel()
    console.print(perf_panel.render(performance_data))
    
    sys_panel = SystemHealthPanel()
    console.print(sys_panel.render(system_data))
    
    console.print("[green]✅ All 4 panels rendered successfully[/green]\n")


def test_ml_control():
    """Test ML control panel"""
    console.print("\n[bold cyan]Testing ML Control Panel[/bold cyan]\n")
    
    panel = render_ml_control_panel()
    console.print(panel)
    
    console.print("[green]✅ ML control panel rendered successfully[/green]\n")


def test_help_screen():
    """Test help screen"""
    console.print("\n[bold cyan]Testing Help Screen[/bold cyan]\n")
    
    panel = render_help_screen()
    console.print(panel)
    
    console.print("[green]✅ Help screen rendered successfully[/green]\n")


def test_seed_browser():
    """Test seed browser"""
    console.print("\n[bold cyan]Testing Seed Browser[/bold cyan]\n")
    
    for view in ['all', 'whitelist', 'blacklist']:
        panel = render_seed_browser(view=view, page=0)
        console.print(panel)
    
    console.print("[green]✅ Seed browser rendered successfully[/green]\n")


def test_backtest_control():
    """Test backtest control"""
    console.print("\n[bold cyan]Testing Backtest Control[/bold cyan]\n")
    
    controller = BacktestController()
    
    for view in ['status', 'history', 'start']:
        panel = render_backtest_control(controller, view=view)
        console.print(panel)
    
    console.print("[green]✅ Backtest control rendered successfully[/green]\n")


def test_documentation_launcher():
    """Test documentation launcher"""
    console.print("\n[bold cyan]Testing Documentation Launcher[/bold cyan]\n")
    
    result = open_documentation()
    
    if result:
        console.print("[green]✅ Documentation opened successfully[/green]\n")
    else:
        console.print("[yellow]⚠️  Documentation file not found (expected)[/yellow]\n")


def main():
    """Run all tests"""
    console.print("\n" + "="*70)
    console.print("[bold magenta]HARVEST DASHBOARD - COMPONENT TESTS[/bold magenta]")
    console.print("="*70)
    
    try:
        test_panels()
        test_ml_control()
        test_help_screen()
        test_seed_browser()
        test_backtest_control()
        test_documentation_launcher()
        
        console.print("\n" + "="*70)
        console.print("[bold green]✅ ALL TESTS PASSED[/bold green]")
        console.print("="*70 + "\n")
        
        console.print("[cyan]Dashboard components are ready for integration![/cyan]")
        console.print("[cyan]Next step: Create terminal_ui.py and live_monitor.py[/cyan]\n")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Test failed: {e}[/bold red]\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
