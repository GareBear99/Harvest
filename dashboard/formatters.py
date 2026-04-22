#!/usr/bin/env python3
"""
Data Formatting Utilities
Format data for dashboard display
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional


def format_currency(value: float, decimals: int = 2) -> str:
    """Format currency value with $ sign"""
    if value >= 0:
        return f"${value:,.{decimals}f}"
    else:
        return f"-${abs(value):,.{decimals}f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format percentage value"""
    return f"{value:.{decimals}f}%"


def format_percentage_change(value: float, decimals: int = 1) -> str:
    """Format percentage change with +/- prefix"""
    if value >= 0:
        return f"+{value:.{decimals}f}%"
    else:
        return f"{value:.{decimals}f}%"


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format timestamp as HH:MM:SS"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%H:%M:%S")


def format_time_ago(dt: datetime) -> str:
    """Format time difference as '5m ago' or '2h ago'"""
    now = datetime.now()
    diff = now - dt
    
    if diff < timedelta(seconds=60):
        return f"{int(diff.total_seconds())}s ago"
    elif diff < timedelta(hours=1):
        return f"{int(diff.total_seconds() / 60)}m ago"
    elif diff < timedelta(days=1):
        return f"{int(diff.total_seconds() / 3600)}h ago"
    else:
        return f"{int(diff.total_seconds() / 86400)}d ago"


def format_memory(bytes_value: int) -> str:
    """Format memory size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.0f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.0f} PB"


def format_seed(seed: int) -> str:
    """Format seed number with commas"""
    return f"{seed:,}"


def format_win_rate(wins: int, losses: int) -> str:
    """Format win rate as percentage with W/L count"""
    total = wins + losses
    if total == 0:
        return "N/A (0W 0L)"
    
    win_rate = (wins / total) * 100
    return f"{win_rate:.1f}% ({wins}W {losses}L)"


def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to max length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_status_icon(status: str) -> str:
    """Get status emoji icon"""
    icons = {
        'running': '🟢',
        'stopped': '🔴',
        'paused': '🟡',
        'error': '❌',
        'success': '✅',
        'warning': '⚠️',
        'info': 'ℹ️',
        'whitelist': '✅',
        'blacklist': '⛔',
        'neutral': '⚪'
    }
    return icons.get(status.lower(), '⚫')


def format_trade_outcome(outcome: str) -> str:
    """Format trade outcome with icon"""
    if outcome in ['TP', 'WIN', 'PROFIT']:
        return f"✅ {outcome}"
    elif outcome in ['SL', 'LOSS']:
        return f"❌ {outcome}"
    else:
        return f"⚪ {outcome}"


def format_position_side(side: str) -> str:
    """Format position side (LONG/SHORT) with color indicators"""
    if side.upper() == 'LONG':
        return "🟢 LONG"
    elif side.upper() == 'SHORT':
        return "🔴 SHORT"
    else:
        return side
