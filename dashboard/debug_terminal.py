"""
Debug Terminal Modal
Shows live action logs, validations, and system diagnostics
"""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group
from typing import Dict, Any

from core.debug_daemon import get_daemon


def render_debug_terminal(view: str = 'live', page: int = 0, selected_session: str = None) -> Panel:
    """
    Render debug terminal modal
    
    Args:
        view: 'live', 'summary', or 'errors'
        page: Current page number (for pagination)
        selected_session: Session ID to view (None = current)
    """
    daemon = get_daemon()
    
    if view == 'live':
        return _render_live_log(daemon, page, selected_session)
    elif view == 'summary':
        return _render_summary(daemon, selected_session)
    elif view == 'errors':
        return _render_errors(daemon, selected_session)
    else:
        return _render_live_log(daemon, page, selected_session)


def _render_live_log(daemon, page: int = 0, selected_session: str = None) -> Panel:
    """Render live action log with pagination and session support"""
    
    ITEMS_PER_PAGE = 15
    
    # Get available sessions for header
    available_sessions = daemon.get_recent_sessions()
    current_session_id = daemon.session_id
    
    # Get session data (use snapshots for thread safety)
    if selected_session:
        session_data = daemon.load_session_data(selected_session)
        actions = session_data['actions'] if session_data else []
        validations = session_data['validations'] if session_data else []
        # Find session index for display
        session_idx = next((i for i, s in enumerate(available_sessions) if s['session_id'] == selected_session), -1)
        session_label = f" [Historical Session {session_idx + 1}/{len(available_sessions)}]"
    else:
        # Use thread-safe snapshots instead of direct references
        actions = daemon.get_actions_snapshot()
        validations = daemon.get_validations_snapshot()
        session_label = f" [Current Session - Live]"
    
    content = Text()
    
    if not actions:
        content.append("No debug activity yet.\n\n", style="dim")
        content.append("Debug logging will appear here as dashboard actions occur.\n", style="dim")
        content.append("Try: Press R to refresh, S to open seeds, H for help.\n\n", style="yellow")
        
        # Show session info even when empty
        if len(available_sessions) > 1:
            content.append(f"Available sessions: {len(available_sessions)}\n", style="dim")
            content.append("Press Tab to cycle through historical sessions.\n", style="cyan dim")
    else:
        # Calculate pagination
        total_actions = len(actions)
        total_pages = (total_actions + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        page = max(0, min(page, total_pages - 1))  # Clamp page
        
        start_idx = page * ITEMS_PER_PAGE
        end_idx = min(start_idx + ITEMS_PER_PAGE, total_actions)
        page_actions = actions[start_idx:end_idx]
        
        # Header with session and page info
        content.append(f"Actions {start_idx + 1}-{end_idx} of {total_actions}", style="bold cyan")
        content.append(session_label, style="dim")
        content.append(f" (Page {page + 1}/{total_pages})\n\n", style="dim")
        
        # Show actions
        for action in page_actions:
            timestamp = action['timestamp'].split('T')[1][:12] if 'T' in action['timestamp'] else action['timestamp'][:12]
            action_id = action['action_id']
            action_name = action['action_name']
            status = action.get('status', 'pending')
            
            # Status icon
            if status == 'SUCCESS':
                icon = "✅"
                style = "green"
            elif status == 'FAILED':
                icon = "❌"
                style = "red"
            else:
                icon = "⏳"
                style = "yellow"
            
            content.append(f"[{timestamp}] {icon} {action_id}: ", style=style)
            content.append(f"{action_name}", style=style)
            
            # Show validation if complete
            validation_id = action.get('validation_id')
            if validation_id:
                validation = next((v for v in validations if v['validation_id'] == validation_id), None)
                if validation:
                    checks_passed = sum(1 for c in validation['checks'] if c['passed'])
                    checks_total = len(validation['checks'])
                    content.append(f" ({checks_passed}/{checks_total})", style="dim")
            
            content.append("\n")
            
            # Show failure details
            if status == 'FAILED' and validation_id:
                validation = next((v for v in validations if v['validation_id'] == validation_id), None)
                if validation:
                    failed_checks = [c for c in validation['checks'] if not c['passed']]
                    for check in failed_checks[:2]:  # Show max 2 failures per action
                        content.append(f"   ❌ {check['check_name']}: {check.get('error', 'failed')}\n", style="red dim")
    
    # Footer with controls and session info
    footer = Text("\n" + "─" * 70 + "\n", style="dim")
    
    # Navigation controls
    if actions and len(actions) > ITEMS_PER_PAGE:
        footer.append("[↑/↓]", style="bold cyan")
        footer.append(" Page  ", style="dim")
    else:
        footer.append("[↑/↓]", style="dim")
        footer.append(" Page  ", style="dim")
    
    # Session switching
    if len(available_sessions) > 1:
        footer.append("[Tab]", style="bold yellow")
        footer.append(f" Session({len(available_sessions)})  ", style="dim")
    else:
        footer.append("[Tab]", style="dim")
        footer.append(" Session  ", style="dim")
    
    footer.append("[1/2/3]", style="bold green")
    footer.append(" View  ", style="dim")
    footer.append("[ESC/Q]", style="bold white")
    footer.append(" Close", style="dim")
    
    full_content = Group(content, footer)
    
    return Panel(
        full_content,
        title="🐛 Debug Terminal - Live Action Tracking",
        border_style="cyan",
        padding=(1, 2)
    )


def _render_summary(daemon) -> Panel:
    """Render session summary with statistics"""
    
    summary = daemon.get_session_summary()
    
    content = Text()
    content.append("═══ SESSION SUMMARY ═══\n\n", style="bold cyan")
    
    # Session info
    content.append(f"Session ID: ", style="dim")
    content.append(f"{summary['session_id']}\n", style="cyan")
    content.append(f"Duration: ", style="dim")
    content.append(f"{summary['duration_seconds']:.1f}s\n\n", style="cyan")
    
    # Statistics
    stats = summary['stats']
    content.append("═══ STATISTICS ═══\n", style="bold yellow")
    content.append(f"Actions Logged: ", style="dim")
    content.append(f"{stats['actions_logged']}\n", style="green")
    content.append(f"Validations: ", style="dim")
    content.append(f"{stats['validations_performed']}\n", style="green")
    content.append(f"Meta-Validations: ", style="dim")
    content.append(f"{stats['meta_validations_performed']}\n", style="green")
    content.append(f"Errors: ", style="dim")
    error_style = "red" if stats['errors_logged'] > 0 else "green"
    content.append(f"{stats['errors_logged']}\n", style=error_style)
    content.append(f"Anomalies: ", style="dim")
    anomaly_style = "yellow" if stats['anomalies_logged'] > 0 else "green"
    content.append(f"{stats['anomalies_logged']}\n\n", style=anomaly_style)
    
    # Success rates
    rates = summary['success_rates']
    content.append("═══ SUCCESS RATES ═══\n", style="bold green")
    content.append(f"Validations: ", style="dim")
    content.append(f"{rates['validation_success_rate']}\n", style="green")
    content.append(f"Meta-Validations: ", style="dim")
    content.append(f"{rates['meta_validation_success_rate']}\n\n", style="green")
    
    # Health
    health = summary['health']
    content.append("═══ SYSTEM HEALTH ═══\n", style="bold")
    content.append(f"Status: ", style="dim")
    health_style = "green" if health['overall_status'] == 'healthy' else "red"
    content.append(f"{health['overall_status'].upper()}\n", style=health_style)
    content.append(f"Critical Errors: ", style="dim")
    content.append(f"{health['critical_errors']}\n", style="red" if health['critical_errors'] > 0 else "green")
    content.append(f"Warnings: ", style="dim")
    content.append(f"{health['warnings']}\n", style="yellow" if health['warnings'] > 0 else "green")
    
    # Add footer
    footer = Text("\n" + "─" * 70 + "\n", style="dim")
    footer.append("[1]", style="bold cyan")
    footer.append(" Live Log  ", style="dim")
    footer.append("[2]", style="bold yellow")
    footer.append(" Summary  ", style="dim")
    footer.append("[3]", style="bold red")
    footer.append(" Errors  ", style="dim")
    footer.append("[ESC/Q]", style="bold white")
    footer.append(" Close", style="dim")
    
    full_content = Group(content, footer)
    
    return Panel(
        full_content,
        title="🐛 Debug Terminal - Summary",
        border_style="yellow",
        padding=(1, 2)
    )


def _render_errors(daemon) -> Panel:
    """Render errors and anomalies"""
    
    # Use thread-safe snapshots
    errors = daemon.get_errors_snapshot()[-10:]  # Last 10 errors
    anomalies = daemon.get_anomalies_snapshot()[-10:]  # Last 10 anomalies
    
    content = Text()
    
    # Errors section
    content.append("═══ ERRORS ═══\n", style="bold red")
    if errors:
        for i, error in enumerate(errors, 1):
            timestamp = error['timestamp'].split('T')[1][:8]  # Extract time
            content.append(f"{i}. ", style="dim")
            content.append(f"[{timestamp}] ", style="dim")
            content.append(f"{error['message']}\n", style="red")
            if error.get('context'):
                content.append(f"   Context: {error['context']}\n", style="dim")
    else:
        content.append("No errors logged ✅\n", style="green")
    
    content.append("\n")
    
    # Anomalies section
    content.append("═══ ANOMALIES ═══\n", style="bold yellow")
    if anomalies:
        for i, anomaly in enumerate(anomalies, 1):
            timestamp = anomaly['timestamp'].split('T')[1][:8]
            content.append(f"{i}. ", style="dim")
            content.append(f"[{timestamp}] ", style="dim")
            content.append(f"{anomaly['message']}\n", style="yellow")
            if anomaly.get('context'):
                content.append(f"   Context: {anomaly['context']}\n", style="dim")
    else:
        content.append("No anomalies detected ✅\n", style="green")
    
    # Add footer
    footer = Text("\n" + "─" * 70 + "\n", style="dim")
    footer.append("[1]", style="bold cyan")
    footer.append(" Live Log  ", style="dim")
    footer.append("[2]", style="bold yellow")
    footer.append(" Summary  ", style="dim")
    footer.append("[3]", style="bold red")
    footer.append(" Errors  ", style="dim")
    footer.append("[ESC/Q]", style="bold white")
    footer.append(" Close", style="dim")
    
    full_content = Group(content, footer)
    
    return Panel(
        full_content,
        title="🐛 Debug Terminal - Errors & Anomalies",
        border_style="red",
        padding=(1, 2)
    )


def handle_debug_key(key: str, current_view: str, current_page: int, current_session_idx: int, available_sessions: list) -> tuple[bool, str, str, int, int]:
    """
    Handle keyboard input in debug terminal
    
    Returns:
        (should_close, message, new_view, new_page, new_session_idx)
    """
    if key.lower() in ['q', 'escape'] or key == '\x1b':
        return True, "Debug terminal closed", current_view, current_page, current_session_idx
    
    elif key == '1':
        return False, "Switched to live log", 'live', 0, current_session_idx
    
    elif key == '2':
        return False, "Switched to summary view", 'summary', current_page, current_session_idx
    
    elif key == '3':
        return False, "Switched to errors view", 'errors', current_page, current_session_idx
    
    # Pagination controls
    elif key in ['↓', 'j', 'J']:  # Down/Next page
        return False, f"Next page", current_view, current_page + 1, current_session_idx
    
    elif key in ['↑', 'k', 'K']:  # Up/Previous page
        return False, f"Previous page", current_view, max(0, current_page - 1), current_session_idx
    
    # Session switching
    elif key == '\t':  # Tab - cycle sessions
        if available_sessions:
            new_idx = (current_session_idx + 1) % len(available_sessions)
            session_name = "current" if available_sessions[new_idx].get('is_current') else available_sessions[new_idx]['session_id'][:8]
            return False, f"Switched to {session_name} session", current_view, 0, new_idx
        return False, "No other sessions available", current_view, current_page, current_session_idx
    
    else:
        return False, f"Unknown key: {key}", current_view, current_page, current_session_idx
