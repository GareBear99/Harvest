#!/usr/bin/env python3
"""
Dashboard Panel Components
Individual panels for seed status, bot status, performance, and system health
"""

import os
import sys
import psutil
from datetime import datetime
from typing import Dict, List, Optional
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.formatters import (
    format_currency, format_percentage, format_percentage_change,
    format_timestamp, format_time_ago, format_memory, format_seed,
    format_win_rate, format_status_icon, format_trade_outcome
)


class SeedStatusPanel:
    """Display seed system status and performance"""
    
    def __init__(self):
        self.title = "🌱 SEED STATUS"
    
    def render(self, data: Dict) -> Panel:
        """Render seed status panel"""
        try:
            # Extract seed data
            total_tested = data.get('total_tested', 0)
            whitelisted = data.get('whitelisted', 0)
            blacklisted = data.get('blacklisted', 0)
            neutral = total_tested - whitelisted - blacklisted
            
            top_seed = data.get('top_performer', {})
            current_seed = data.get('current_seed', None)
            
            # Calculate percentages
            white_pct = (whitelisted / total_tested * 100) if total_tested > 0 else 0
            black_pct = (blacklisted / total_tested * 100) if total_tested > 0 else 0
            neutral_pct = (neutral / total_tested * 100) if total_tested > 0 else 0
            
            # Build content
            lines = []
            lines.append(f"Total Tested: {total_tested}")
            lines.append(f"{format_status_icon('whitelist')} Whitelisted: {whitelisted} seeds ({white_pct:.1f}%)")
            lines.append(f"{format_status_icon('blacklist')} Blacklisted: {blacklisted} seeds ({black_pct:.1f}%)")
            lines.append(f"{format_status_icon('neutral')} Neutral: {neutral} seeds ({neutral_pct:.1f}%)")
            lines.append("")
            
            if top_seed:
                seed_num = top_seed.get('seed', 'N/A')
                win_rate = top_seed.get('win_rate', 0) * 100
                pnl = top_seed.get('pnl', 0)
                lines.append(f"Top Performer: Seed {format_seed(seed_num)} ({win_rate:.0f}% WR, {format_currency(pnl)})")
            else:
                lines.append("Top Performer: None yet")
            lines.append("")
            
            # Current seeds per timeframe (BASE_STRATEGY for each)
            current_seeds = data.get('current_seeds_by_timeframe', {})
            if current_seeds:
                lines.append("Active Seeds:")
                for tf in ['1m', '5m', '15m', '1h', '4h']:
                    if tf in current_seeds:
                        seed_info = current_seeds[tf]
                        seed_num = seed_info.get('seed', 'N/A')
                        input_seed = seed_info.get('input_seed', '')
                        if input_seed:
                            lines.append(f"  {tf}: {format_seed(seed_num)} (input: {input_seed})")
                        else:
                            lines.append(f"  {tf}: {format_seed(seed_num)}")
                    else:
                        lines.append(f"  {tf}: BASE_STRATEGY")
            else:
                # Fallback to single current seed if available
                if current_seed:
                    seed_num = current_seed.get('seed', 'N/A')
                    timeframe = current_seed.get('timeframe', 'N/A')
                    lines.append(f"Currently Testing: Seed {format_seed(seed_num)} ({timeframe})")
                else:
                    lines.append("Active Seeds: Using BASE_STRATEGY (all timeframes)")
            
            content = "\n".join(lines)
            
            return Panel(
                content,
                title=self.title,
                border_style="green",
                padding=(1, 2)
            )
        
        except Exception as e:
            return Panel(
                f"Error rendering seed status: {e}",
                title=self.title,
                border_style="red",
                padding=(1, 2)
            )


class BotStatusPanel:
    """Display active bot operations"""
    
    def __init__(self):
        self.title = "🤖 BOT STATUS"
    
    def render(self, data: Dict) -> Panel:
        """Render bot status panel"""
        try:
            # Extract bot data
            status = data.get('status', 'unknown')
            mode = data.get('mode', 'UNKNOWN')
            seed_info = data.get('seed_info', {})
            balance = data.get('balance', {})
            positions = data.get('active_positions', [])
            last_trade = data.get('last_trade', None)
            
            # Build content
            lines = []
            
            # Status line with uptime
            status_icon = format_status_icon(status)
            lines.append(f"Status: {status_icon} {status.upper()}")
            
            # Mode-specific info
            if mode == 'BACKTEST':
                backtest_days = data.get('backtest_days', 0)
                lines.append(f"Mode: {mode} ({backtest_days} days)")
            else:
                lines.append(f"Mode: {mode}")
            
            # Trading session info
            session_start = data.get('session_start_time', None)
            if session_start:
                uptime = format_time_ago(session_start) if isinstance(session_start, datetime) else 'N/A'
                lines.append(f"Uptime: {uptime}")
            
            # Seed info
            if seed_info:
                seed_num = seed_info.get('strategy_seed', 'N/A')
                timeframe = seed_info.get('timeframe', 'N/A')
                input_seed = seed_info.get('input_seed', 'N/A')
                lines.append(f"Seed: {format_seed(seed_num)} ({timeframe}) | Input: {input_seed}")
            lines.append("")
            
            # Balance with $100 progress bar
            if balance:
                initial = balance.get('initial', 10.0)
                current = balance.get('current', 10.0)
                target = data.get('target_balance', 100.0)
                pnl = current - initial
                pnl_pct = (pnl / initial * 100) if initial > 0 else 0
                progress_pct = max(0, min((current / target * 100), 100))
                filled = int(20 * progress_pct / 100)
                bar = "█" * filled + "░" * (20 - filled)
                
                lines.append(f"Balance: {format_currency(initial)} → {format_currency(current)}")
                lines.append(f"Target $100: [{bar}] {progress_pct:.0f}%")
                lines.append(f"P&L: {format_currency(pnl)} ({format_percentage_change(pnl_pct)})")
                
                # Daily stats
                daily_pnl = data.get('daily_pnl', 0.0)
                if daily_pnl != 0:
                    lines.append(f"Today: {format_currency(daily_pnl)}")
            lines.append("")
            
            # Active positions - only show in LIVE mode
            if mode != 'BACKTEST':
                max_positions = data.get('max_positions', 2)
                lines.append(f"Live Positions: {len(positions)}/{max_positions}")
                
                if positions:
                    for pos in positions[:2]:  # Show max 2 positions
                        tf = pos.get('timeframe', '?')
                        side = pos.get('side', '?')
                        entry = pos.get('entry_price', 0)
                        current_price = pos.get('current_price', entry)
                        size = pos.get('position_value', 0)
                        pnl_pos = pos.get('unrealized_pnl', 0)
                        opened_at = pos.get('opened_at', datetime.now())
                        time_ago = format_time_ago(opened_at) if isinstance(opened_at, datetime) else 'unknown'
                        
                        lines.append(f"  {tf} {side} @ ${entry:.2f} | Size: ${size:.0f}")
                        lines.append(f"    Current: ${current_price:.2f} | P&L: {format_currency(pnl_pos)} ({time_ago})")
                else:
                    lines.append("  No active positions")
                lines.append("")
            
            # Slot allocation information (new stair-climbing system)
            slot_info = data.get('slot_allocation', {})
            if slot_info:
                active_slots = slot_info.get('active_slots', 0)
                total_slots = slot_info.get('total_slots', 10)
                eth_slots = slot_info.get('eth_slots', [])
                btc_slots = slot_info.get('btc_slots', [])
                active_tfs = slot_info.get('active_timeframes', [])
                next_unlock = slot_info.get('next_unlock', {})
                position_tier = slot_info.get('position_tier', 0)
                total_position_slots = slot_info.get('total_position_slots', 10)
                
                lines.append(f"💎 Slot Allocation: {active_slots}/{total_slots} active")
                
                # Show asset slots
                if eth_slots:
                    lines.append(f"   ETH Slots: {eth_slots}")
                if btc_slots:
                    lines.append(f"   BTC Slots: {btc_slots}")
                
                # Show active timeframes
                if active_tfs:
                    lines.append(f"   Timeframes: {', '.join(active_tfs)}")
                
                # Show next unlock
                if next_unlock and next_unlock.get('balance'):
                    next_bal = next_unlock['balance']
                    next_slot = next_unlock['slot_number']
                    next_asset = next_unlock['asset']
                    current_bal = balance.get('current', 0) if balance else 0
                    to_next = next_bal - current_bal
                    if to_next > 0:
                        lines.append(f"   Next: Slot {next_slot} ({next_asset}) @ ${next_bal:.0f} (${to_next:.0f} away)")
                
                # Show position tier info at $100+
                if current_bal >= 100 and position_tier is not None:
                    tier_names = {0: "Tier 1", 1: "Tier 2", 2: "Tier 3 (MAXED)"}
                    tier_name = tier_names.get(position_tier, f"Tier {position_tier+1}")
                    lines.append(f"   Position {tier_name}: {total_position_slots} total slots")
            else:
                # Fallback to old tier system if slot info not available
                tier_info = data.get('tier', {})
                if tier_info and tier_info.get('description'):
                    lines.append(f"🎯 Current Tier: {tier_info['description']}")
                    active_tfs = tier_info.get('active_timeframes', [])
                    if active_tfs:
                        lines.append(f"   Active TFs: {', '.join(active_tfs)}")
                    current_bal = balance.get('current', 0) if balance else 0
                    max_bal = tier_info.get('max_balance', float('inf'))
                    if max_bal != float('inf'):
                        to_next = max_bal - current_bal
                        if to_next > 0:
                            lines.append(f"   Next Tier: ${to_next:.0f} away")
            lines.append("")
            
            # Historical statistics
            stats = data.get('statistics', {})
            if stats:
                today = stats.get('today', {})
                all_time = stats.get('all_time', {})
                
                # Today's stats
                today_trades = today.get('trades', 0)
                today_pnl = today.get('pnl', 0.0)
                today_uptime = today.get('uptime_hours', 0.0)
                lines.append(f"Today: {today_trades} trades | {format_currency(today_pnl)} | {today_uptime:.1f}h uptime")
                
                # All-time stats
                total_trades = all_time.get('total_trades', 0)
                total_pnl = all_time.get('total_pnl', 0.0)
                total_uptime = all_time.get('total_uptime_hours', 0.0)
                avg_daily_uptime = all_time.get('avg_daily_uptime_hours', 0.0)
                trading_days = all_time.get('trading_days', 0)
                
                lines.append(f"All-Time: {total_trades} trades | {format_currency(total_pnl)}")
                lines.append(f"Total Uptime: {total_uptime:.1f}h ({trading_days} days)")
                if avg_daily_uptime > 0:
                    lines.append(f"Avg Daily: {avg_daily_uptime:.1f}h/day")
            else:
                # Fallback to old format
                total_trades_today = data.get('trades_today', 0)
                win_rate_today = data.get('win_rate_today', 0.0)
                lines.append(f"Today: {total_trades_today} trades | {win_rate_today:.0f}% WR")
            
            # Last trade
            if last_trade:
                outcome = last_trade.get('outcome', 'UNKNOWN')
                tf = last_trade.get('timeframe', '?')
                pnl = last_trade.get('pnl', 0)
                duration = last_trade.get('duration_min', 0)
                closed_at = last_trade.get('closed_at', datetime.now())
                time_ago = format_time_ago(closed_at) if isinstance(closed_at, datetime) else 'unknown'
                lines.append(f"Last: {format_trade_outcome(outcome)} {tf} {format_currency(pnl)} ({duration}m, {time_ago})")
            else:
                lines.append(f"Last Trade: None yet")
            
            content = "\n".join(lines)
            
            return Panel(
                content,
                title=self.title,
                border_style="blue",
                padding=(1, 2)
            )
        
        except Exception as e:
            return Panel(
                f"Error rendering bot status: {e}",
                title=self.title,
                border_style="red",
                padding=(1, 2)
            )


class PerformancePanel:
    """Display real-time strategy performance"""
    
    def __init__(self):
        self.title = "📊 PERFORMANCE"
    
    def render(self, data: Dict) -> Panel:
        """Render performance panel"""
        try:
            # Extract performance data
            wins = data.get('wins', 0)
            losses = data.get('losses', 0)
            total_trades = wins + losses
            pnl = data.get('pnl', 0.0)
            max_dd = data.get('max_drawdown', 0.0)
            timeframe_stats = data.get('by_timeframe', {})
            mode = data.get('mode', 'UNKNOWN')
            
            # Build content
            lines = []
            
            # Mode-specific header
            if mode == 'BACKTEST':
                lines.append("═══ BACKTEST RESULTS ═══")
            else:
                lines.append("═══ LIVE TRADING STATS ═══")
            
            # Overall stats
            lines.append(f"Win Rate: {format_win_rate(wins, losses)}")
            lines.append(f"Total Trades: {total_trades}")
            lines.append(f"P&L: {format_currency(pnl)}")
            lines.append(f"Max Drawdown: {format_percentage(max_dd)}")
            lines.append("")
            
            # Per-timeframe stats with seeds and performance
            if mode == 'BACKTEST':
                lines.append("By Timeframe (Historical):")
            else:
                lines.append("By Timeframe (Session):")
            for tf in ['1m', '5m', '15m', '1h', '4h']:
                if tf in timeframe_stats:
                    stats = timeframe_stats[tf]
                    tf_wins = stats.get('wins', 0)
                    tf_losses = stats.get('losses', 0)
                    tf_trades = stats.get('trades', tf_wins + tf_losses)  # Use 'trades' key if available
                    tf_pnl = stats.get('pnl', 0.0)
                    tf_seed = stats.get('seed', None)
                    
                    # Calculate win rate
                    if tf_trades > 0:
                        tf_wr = (tf_wins / tf_trades * 100) if (tf_wins + tf_losses) > 0 else 0
                    else:
                        tf_wr = 0
                    
                    # Format seed info
                    seed_str = f"(Seed {format_seed(tf_seed)})" if tf_seed else ""
                    
                    # Build line with seed, WR, trades, P&L
                    if tf_trades > 0:
                        lines.append(f"  {tf}: {tf_wr:.0f}% WR ({tf_trades}) {format_currency(tf_pnl)} {seed_str}")
                    else:
                        lines.append(f"  {tf}: No data {seed_str}")
                else:
                    lines.append(f"  {tf}: No data")
            
            content = "\n".join(lines)
            
            return Panel(
                content,
                title=self.title,
                border_style="yellow",
                padding=(1, 2)
            )
        
        except Exception as e:
            return Panel(
                f"Error rendering performance: {e}",
                title=self.title,
                border_style="red",
                padding=(1, 2)
            )


class SystemHealthPanel:
    """Monitor system resources and warnings"""
    
    def __init__(self):
        self.title = "🏥 SYSTEM HEALTH"
    
    def render(self, data: Dict) -> Panel:
        """Render system health panel"""
        try:
            # Extract system data
            data_status = data.get('data_status', {})
            connections = data.get('connections', 'unknown')
            warnings = data.get('warnings', [])
            
            # Get system memory
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            mem_used = mem_info.rss
            mem_total = psutil.virtual_memory().total
            
            # Build content
            lines = []
            
            # Data status
            data_fresh = data_status.get('fresh', False)
            data_updated = data_status.get('updated_ago', 'unknown')
            data_icon = format_status_icon('success') if data_fresh else format_status_icon('warning')
            lines.append(f"Data: {data_icon} {'Fresh' if data_fresh else 'Stale'} (Updated {data_updated})")
            
            # Connections
            conn_icon = format_status_icon('success') if connections == 'operational' else format_status_icon('error')
            conn_text = "All systems operational" if connections == 'operational' else connections
            lines.append(f"Connections: {conn_icon} {conn_text}")
            
            # Memory
            lines.append(f"Memory: {format_memory(mem_used)} / {format_memory(mem_total)}")
            lines.append("")
            
            # Warnings
            if warnings:
                lines.append(f"Warnings: {len(warnings)}")
                for warning in warnings[:2]:  # Show max 2 warnings
                    lines.append(f"  ⚠️  {warning}")
            else:
                lines.append("Warnings: None")
            
            lines.append(f"Last Check: {format_timestamp()}")
            
            content = "\n".join(lines)
            
            return Panel(
                content,
                title=self.title,
                border_style="cyan",
                padding=(1, 2)
            )
        
        except Exception as e:
            return Panel(
                f"Error rendering system health: {e}",
                title=self.title,
                border_style="red",
                padding=(1, 2)
            )


class WalletPanel:
    """Display wallet and position sizing info"""
    
    def __init__(self):
        self.title = "💰 WALLET & LIMITS"
    
    def render(self, data: Dict) -> Panel:
        """Render wallet panel"""
        try:
            # Extract wallet data
            metamask = data.get('metamask', {})
            btc_wallet = data.get('btc_wallet', {})
            position_limits = data.get('position_limits', {})
            capital = data.get('capital', 0.0)
            profit = data.get('profit', 0.0)
            
            # Build content
            lines = []
            
            # === WALLET CONNECTION ===
            lines.append("═══ WALLET CONNECTION ═══")
            
            # MetaMask status with action hint
            mm_connected = metamask.get('connected', False)
            mm_icon = format_status_icon('success') if mm_connected else format_status_icon('error')
            if mm_connected:
                mm_addr = metamask.get('address', 'N/A')
                mm_chain = metamask.get('chain_id', '0x1')
                chain_name = {'0x1': 'Ethereum', '0x89': 'Polygon', '0xaa36a7': 'Sepolia'}.get(mm_chain, 'Unknown')
                lines.append(f"MetaMask: {mm_icon} Connected")
                lines.append(f"  Address: {mm_addr[:8]}...{mm_addr[-6:] if len(mm_addr) > 14 else ''}")
                lines.append(f"  Network: {chain_name}")
                
                # Show balance if available
                mm_balance = metamask.get('balance_eth', 0.0)
                mm_balance_usd = metamask.get('balance_usd', 0.0)
                if mm_balance > 0:
                    lines.append(f"  Balance: {mm_balance:.4f} ETH (${mm_balance_usd:.2f})")
                
                lines.append("  → Press 'W' to disconnect")
            else:
                lines.append(f"MetaMask: {mm_icon} Not connected")
                lines.append("  → Press 'W' to connect")
            lines.append("")
            
            # BTC Wallet status with more info
            btc_connected = btc_wallet.get('exists', False)
            btc_icon = format_status_icon('success') if btc_connected else format_status_icon('neutral')
            if btc_connected:
                btc_addr = btc_wallet.get('address', 'N/A')
                btc_balance = btc_wallet.get('balance', 0.0)
                lines.append(f"BTC Wallet: {btc_icon} Created")
                lines.append(f"  Address: {btc_addr[:8]}...{btc_addr[-6:] if len(btc_addr) > 14 else ''}")
                if btc_balance > 0:
                    lines.append(f"  Balance: {btc_balance:.8f} BTC")
            else:
                lines.append(f"BTC Wallet: {btc_icon} Not created")
                lines.append("  → Auto-created on first profit")
            lines.append("")
            
            # === PROFIT TRACKING ===
            lines.append("═══ PROFIT TRACKING ═══")
            profit_threshold = position_limits.get('profit_threshold', 100.0)
            funding_amount = position_limits.get('funding_amount', 50.0)
            
            # Check mode - in backtest, show zero and explain
            mode = data.get('mode', 'UNKNOWN')
            if mode == 'BACKTEST':
                lines.append(f"Current Profit: $0.00 (backtest mode)")
                lines.append(f"")
                lines.append(f"💡 Live Trading Profit Split:")
                lines.append(f"  • At ${profit_threshold:.0f} profit → Fund BTC wallet")
                lines.append(f"  • Amount: ${funding_amount:.0f} (50% of threshold)")
                lines.append(f"  • Keeps trading capital safe")
                lines.append(f"  • BTC for long-term storage")
            else:
                # Live mode - show actual progress
                progress_pct = (profit / profit_threshold * 100) if profit_threshold > 0 else 0
                progress_bar = self._create_progress_bar(progress_pct)
                
                lines.append(f"Profit: {format_currency(profit)} / {format_currency(profit_threshold)}")
                lines.append(f"{progress_bar} {progress_pct:.0f}%")
                
                if progress_pct >= 100:
                    lines.append(f"  ✅ Ready to fund ${funding_amount:.0f} to BTC!")
                    lines.append(f"  → 50% profit secured in BTC wallet")
                else:
                    remaining = profit_threshold - profit
                    lines.append(f"  ${remaining:.2f} more to auto-fund")
                    lines.append(f"  → Then ${funding_amount:.0f} moves to BTC")
            lines.append("")
            
            # === POSITION LIMITS ===
            lines.append("═══ POSITION LIMITS ═══")
            max_position = position_limits.get('max_position_size', 100.0)
            is_small_account = capital < 5000.0
            
            # Show tier info if available
            tier_description = data.get('tier', {}).get('description', None)
            if tier_description:
                lines.append(f"🎯 Tier: {tier_description}")
            
            lines.append(f"Capital: {format_currency(capital, 0)}")
            lines.append(f"Max Per Trade: {format_currency(max_position, 0)}")
            lines.append(f"")
            
            # Explain the position sizing strategy
            if is_small_account:
                lines.append(f"💡 Small Account Strategy:")
                if capital < 1000:
                    lines.append(f"  • Fixed ${max_position:.0f} positions")
                    lines.append(f"  • Protects from over-trading")
                    lines.append(f"  • Grows safely to $100+")
                else:
                    lines.append(f"  • 2% risk per trade")
                    lines.append(f"  • Max ${max_position:.0f} position size")
                    lines.append(f"  • Scales with account growth")
            else:
                lines.append(f"💡 Large Account Strategy:")
                lines.append(f"  • 2% risk per trade")
                lines.append(f"  • Max ${max_position:.0f} per position")
                lines.append(f"  • Full risk management")
            
            # Show utilization if positions exist
            total_position_value = data.get('total_position_value', 0.0)
            if total_position_value > 0:
                utilization_pct = (total_position_value / capital * 100) if capital > 0 else 0
                lines.append(f"")
                lines.append(f"Current Use: {utilization_pct:.1f}% of capital")
            
            content = "\n".join(lines)
            
            return Panel(
                content,
                title=self.title,
                border_style="magenta",
                padding=(1, 2)
            )
        
        except Exception as e:
            return Panel(
                f"Error rendering wallet: {e}",
                title=self.title,
                border_style="red",
                padding=(1, 2)
            )
    
    def _create_progress_bar(self, progress_pct: float, width: int = 20) -> str:
        """Create a text-based progress bar"""
        filled = int(width * progress_pct / 100)
        filled = min(filled, width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"
