#!/usr/bin/env python3
"""
Paper Trading Tracker
Tracks 48 hours of paper trading performance before allowing live trading
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PaperTradingTracker:
    """Track paper trading performance and validate requirements"""
    
    def __init__(self, tracker_file: str = 'data/paper_trading_tracker.json'):
        self.tracker_file = tracker_file
        self.data = self._load_tracker()
        self.REQUIRED_HOURS = 48
        self.MIN_TRADES_REQUIRED = 1
        self.DEFAULT_BALANCE = 300.0  # Maximize earning potential with $300
        self.BTC_FEE_PERCENT = 0.02  # 2% BTC transaction fee for stair climbing
        self.ETH_TO_BTC_FEE_PERCENT = 0.01  # 1% fee for ETH->BTC conversion
        self.GAS_FEE_PER_TX = 0.50  # ~$0.50 average gas fee per transaction
    
    def _load_tracker(self) -> Dict:
        """Load paper trading tracker data"""
        try:
            if os.path.exists(self.tracker_file):
                with open(self.tracker_file, 'r') as f:
                    return json.load(f)
            return self._get_default_tracker()
        except Exception as e:
            print(f"Error loading paper trading tracker: {e}")
            return self._get_default_tracker()
    
    def _get_default_tracker(self) -> Dict:
        """Get default tracker structure"""
        return {
            'status': 'not_started',  # not_started, running, completed, failed
            'started_at': None,
            'ended_at': None,
            'duration_hours': 0,
            'starting_balance': self.DEFAULT_BALANCE,
            'current_balance': self.DEFAULT_BALANCE,
            'total_pnl': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'wallet_connected': False,  # NEW: Track wallet connection
            'wallet_address': None,  # NEW: Store connected wallet address
            'trades': [],
            'btc_fees_paid': 0.0,  # Track BTC stair climbing fees
            'gas_fees_paid': 0.0,  # Track ETH gas fees
            'conversion_fees_paid': 0.0,  # Track ETH->BTC conversion fees
            'pending_btc_transfer': 0.0,  # Accumulated profits waiting for batch transfer
            'btc_transfers_count': 0,  # Number of batch transfers to BTC
            'active_slots': 10,  # $100 = full base system
            'requirements': {
                'min_duration_hours': 48,
                'min_trades': 1,
                'min_pnl': 0.0,
                'all_met': False
            },
            'validation': {
                'duration_met': False,
                'trades_met': False,
                'pnl_met': False,
                'last_check': None
            }
        }
    
    def _save_tracker(self):
        """Save tracker data to file (atomic write)"""
        try:
            from core.file_lock import atomic_write
            os.makedirs(os.path.dirname(self.tracker_file), exist_ok=True)
            
            # Atomic write using temp file + rename
            with atomic_write(self.tracker_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving paper trading tracker: {e}")
    
    def start_paper_trading(self, starting_balance: float = None) -> Dict:
        """Start paper trading session with $100 default (full base system)"""
        if self.data['status'] == 'running':
            return {
                'success': False,
                'message': 'Paper trading already in progress'
            }
        
        # Use default balance if not specified
        if starting_balance is None:
            starting_balance = self.DEFAULT_BALANCE
        
        # Calculate active slots based on balance
        from core.slot_allocation_strategy import get_slot_allocation_strategy
        strategy = get_slot_allocation_strategy()
        active_slots = strategy.get_active_slots(starting_balance)
        
        self.data = self._get_default_tracker()
        self.data['status'] = 'running'
        self.data['started_at'] = datetime.now().isoformat()
        self.data['starting_balance'] = starting_balance
        self.data['active_slots'] = active_slots
        
        # Calculate BTC funding requirement
        # Slots alternate ETH/BTC: 1=ETH, 2=BTC, 3=ETH, 4=BTC...
        # BTC slots are even numbers: 2, 4, 6, 8, 10
        btc_slots = active_slots // 2  # Integer division
        total_btc_funding = btc_slots * 10.0  # Each slot needs $10
        
        # Calculate fees for ETH→BTC conversion to fund BTC slots
        if total_btc_funding > 0:
            conversion_fee = total_btc_funding * self.ETH_TO_BTC_FEE_PERCENT  # 1%
            btc_fee = total_btc_funding * self.BTC_FEE_PERCENT  # 2%
            gas_fee = self.GAS_FEE_PER_TX  # $0.50 for the transfer
            setup_fees = conversion_fee + btc_fee + gas_fee
            
            self.data['btc_fees_paid'] = btc_fee
            self.data['conversion_fees_paid'] = conversion_fee
            self.data['gas_fees_paid'] = gas_fee
            self.data['total_pnl'] = -setup_fees
            self.data['current_balance'] = starting_balance - setup_fees
            self.data['btc_funding'] = total_btc_funding
            self.data['setup_fees'] = setup_fees
        else:
            # Only ETH slot 1, no BTC funding needed
            self.data['btc_fees_paid'] = 0.0
            self.data['conversion_fees_paid'] = 0.0
            self.data['gas_fees_paid'] = 0.0
            self.data['total_pnl'] = 0.0
            self.data['current_balance'] = starting_balance
            self.data['btc_funding'] = 0.0
            self.data['setup_fees'] = 0.0
        
        self._save_tracker()
        
        setup_msg = f'Paper trading started with ${starting_balance:.2f} ({active_slots} slots active)'
        if total_btc_funding > 0:
            setup_msg += f'\nBTC funding: ${total_btc_funding:.2f} (fees: ${setup_fees:.2f})'
            setup_msg += f'\nStarting P&L: -${setup_fees:.2f} (must overcome to be profitable)'
        
        return {
            'success': True,
            'message': setup_msg,
            'started_at': self.data['started_at'],
            'active_slots': active_slots,
            'btc_funding': total_btc_funding if total_btc_funding > 0 else 0,
            'setup_fees': setup_fees if total_btc_funding > 0 else 0
        }
    
    def record_trade(self, trade: Dict) -> Dict:
        """
        Record a paper trade with realistic fee structure:
        - Gas fee on every trade (~$0.50)
        
        Args:
            trade: Dict with keys: timeframe, asset, entry_price, exit_price, position_size, pnl, outcome
        """
        if self.data['status'] != 'running':
            return {
                'success': False,
                'message': 'Paper trading not active'
            }
        
        # Add timestamp
        trade['timestamp'] = datetime.now().isoformat()
        
        # Gas fee on every trade
        gas_fee = self.GAS_FEE_PER_TX
        trade['gas_fee'] = gas_fee
        self.data['gas_fees_paid'] = self.data.get('gas_fees_paid', 0) + gas_fee
        
        # Calculate net P&L (gross profit - gas fee)
        net_pnl = trade.get('pnl', 0) - gas_fee
        trade['total_fees'] = gas_fee
        trade['net_pnl'] = net_pnl
        
        # Update stats
        self.data['trades'].append(trade)
        self.data['total_trades'] += 1
        self.data['total_pnl'] += net_pnl
        self.data['current_balance'] = self.data['starting_balance'] + self.data['total_pnl']
        
        if trade.get('outcome') == 'win':
            self.data['winning_trades'] += 1
        elif trade.get('outcome') == 'loss':
            self.data['losing_trades'] += 1
        
        if self.data['total_trades'] > 0:
            self.data['win_rate'] = self.data['winning_trades'] / self.data['total_trades']
        
        self._save_tracker()
        
        return {
            'success': True,
            'message': f'Trade recorded: {trade.get("outcome")} ${net_pnl:+.2f} (gross: ${trade.get("pnl", 0):.2f} - gas: ${gas_fee:.2f})',
            'total_trades': self.data['total_trades'],
            'total_pnl': self.data['total_pnl'],
            'total_fees': gas_fee
        }
    
    def get_elapsed_hours(self) -> float:
        """Get elapsed hours since paper trading started"""
        if not self.data.get('started_at'):
            return 0.0
        
        started = datetime.fromisoformat(self.data['started_at'])
        elapsed = datetime.now() - started
        return elapsed.total_seconds() / 3600
    
    def link_wallet_connection(self, wallet_address: str) -> Dict:
        """Link wallet connection to paper trading session and start if needed"""
        self.data['wallet_connected'] = True
        self.data['wallet_address'] = wallet_address
        
        # If paper trading not started yet, start it now
        if self.data['status'] == 'not_started':
            result = self.start_paper_trading()
            self._save_tracker()
            return {
                'success': True,
                'message': f'Wallet connected and paper trading started: {result["message"]}',
                'paper_trading_started': True
            }
        elif self.data['status'] == 'running':
            self._save_tracker()
            return {
                'success': True,
                'message': 'Wallet linked to existing paper trading session',
                'paper_trading_started': False
            }
        else:
            self._save_tracker()
            return {
                'success': True,
                'message': f'Wallet connected (paper trading status: {self.data["status"]})',
                'paper_trading_started': False
            }
    
    def unlink_wallet_connection(self) -> Dict:
        """Unlink wallet connection - stops paper trading if running"""
        was_connected = self.data.get('wallet_connected', False)
        self.data['wallet_connected'] = False
        old_address = self.data.get('wallet_address')
        self.data['wallet_address'] = None
        
        # If paper trading is running, stop it
        if self.data['status'] == 'running' and was_connected:
            self.data['status'] = 'stopped'
            self.data['ended_at'] = datetime.now().isoformat()
            self._save_tracker()
            return {
                'success': True,
                'message': f'Wallet disconnected and paper trading stopped (was: {old_address})',
                'paper_trading_stopped': True
            }
        
        self._save_tracker()
        return {
            'success': True,
            'message': 'Wallet disconnected',
            'paper_trading_stopped': False
        }
    
    def check_requirements(self) -> Dict:
        """Check if all requirements are met"""
        if self.data['status'] != 'running':
            return {
                'all_met': False,
                'reason': f'Paper trading status: {self.data["status"]}'
            }
        
        # Check wallet connection first
        if not self.data.get('wallet_connected', False):
            return {
                'all_met': False,
                'reason': 'Wallet not connected (required for paper trading)'
            }
        
        elapsed_hours = self.get_elapsed_hours()
        self.data['duration_hours'] = elapsed_hours
        
        # Check each requirement
        duration_met = elapsed_hours >= self.REQUIRED_HOURS
        trades_met = self.data['total_trades'] >= self.MIN_TRADES_REQUIRED
        pnl_met = self.data['total_pnl'] > 0
        
        # Update validation status
        self.data['validation'] = {
            'duration_met': duration_met,
            'trades_met': trades_met,
            'pnl_met': pnl_met,
            'last_check': datetime.now().isoformat()
        }
        
        all_met = duration_met and trades_met and pnl_met
        self.data['requirements']['all_met'] = all_met
        
        self._save_tracker()
        
        return {
            'all_met': all_met,
            'duration': {
                'met': duration_met,
                'required': self.REQUIRED_HOURS,
                'current': elapsed_hours,
                'remaining': max(0, self.REQUIRED_HOURS - elapsed_hours)
            },
            'trades': {
                'met': trades_met,
                'required': self.MIN_TRADES_REQUIRED,
                'current': self.data['total_trades']
            },
            'pnl': {
                'met': pnl_met,
                'required': 0.0,
                'current': self.data['total_pnl']
            }
        }
    
    def complete_paper_trading(self) -> Dict:
        """Complete paper trading session"""
        if self.data['status'] != 'running':
            return {
                'success': False,
                'message': 'Paper trading not active'
            }
        
        requirements = self.check_requirements()
        
        if requirements['all_met']:
            self.data['status'] = 'completed'
            self.data['ended_at'] = datetime.now().isoformat()
            self._save_tracker()
            
            return {
                'success': True,
                'message': 'Paper trading completed successfully',
                'approved_for_live': True,
                'stats': {
                    'duration_hours': self.data['duration_hours'],
                    'total_trades': self.data['total_trades'],
                    'win_rate': self.data['win_rate'],
                    'total_pnl': self.data['total_pnl'],
                    'final_balance': self.data['current_balance']
                }
            }
        else:
            return {
                'success': False,
                'message': 'Requirements not met',
                'approved_for_live': False,
                'requirements': requirements
            }
    
    def stop_paper_trading(self) -> Dict:
        """Stop paper trading (without completing)"""
        if self.data['status'] != 'running':
            return {
                'success': False,
                'message': 'Paper trading not active'
            }
        
        self.data['status'] = 'stopped'
        self.data['ended_at'] = datetime.now().isoformat()
        self._save_tracker()
        
        return {
            'success': True,
            'message': 'Paper trading stopped'
        }
    
    def get_status(self) -> Dict:
        """Get current paper trading status"""
        if self.data['status'] == 'running':
            elapsed_hours = self.get_elapsed_hours()
            self.data['duration_hours'] = elapsed_hours
        
        return {
            'status': self.data['status'],
            'started_at': self.data.get('started_at'),
            'ended_at': self.data.get('ended_at'),
            'duration_hours': self.data.get('duration_hours', 0),
            'starting_balance': self.data['starting_balance'],
            'current_balance': self.data['current_balance'],
            'total_pnl': self.data['total_pnl'],
            'total_trades': self.data['total_trades'],
            'winning_trades': self.data['winning_trades'],
            'losing_trades': self.data['losing_trades'],
            'win_rate': self.data['win_rate'],
            'btc_fees_paid': self.data.get('btc_fees_paid', 0.0),
            'gas_fees_paid': self.data.get('gas_fees_paid', 0.0),
            'conversion_fees_paid': self.data.get('conversion_fees_paid', 0.0),
            'total_fees_paid': self.data.get('btc_fees_paid', 0.0) + self.data.get('gas_fees_paid', 0.0) + self.data.get('conversion_fees_paid', 0.0),
            'pending_btc_transfer': self.data.get('pending_btc_transfer', 0.0),
            'btc_transfers_count': self.data.get('btc_transfers_count', 0),
            'active_slots': self.data.get('active_slots', 10),
            'requirements': self.data.get('requirements', {}),
            'validation': self.data.get('validation', {})
        }
    
    def is_approved_for_live(self) -> Tuple[bool, str]:
        """Check if approved for live trading"""
        if self.data['status'] != 'completed':
            return False, f"Paper trading not completed (status: {self.data['status']})"
        
        requirements = self.check_requirements()
        
        if not requirements['all_met']:
            reasons = []
            if not requirements['duration']['met']:
                reasons.append(f"Duration: {requirements['duration']['current']:.1f}h / {requirements['duration']['required']}h")
            if not requirements['trades']['met']:
                reasons.append(f"Trades: {requirements['trades']['current']} / {requirements['trades']['required']}")
            if not requirements['pnl']['met']:
                reasons.append(f"PnL: ${requirements['pnl']['current']:.2f} (must be positive)")
            
            return False, "Requirements not met: " + ", ".join(reasons)
        
        return True, "Approved for live trading"
    
    def get_recent_trades(self, n: int = 10) -> List[Dict]:
        """Get recent trades"""
        return self.data['trades'][-n:] if self.data['trades'] else []
    
    def reset(self) -> Dict:
        """Reset paper trading data"""
        self.data = self._get_default_tracker()
        self._save_tracker()
        
        return {
            'success': True,
            'message': 'Paper trading data reset'
        }


def get_paper_trading_tracker(tracker_file: str = 'data/paper_trading_tracker.json') -> PaperTradingTracker:
    """Get paper trading tracker instance"""
    return PaperTradingTracker(tracker_file)


if __name__ == "__main__":
    # Test the paper trading tracker
    tracker = get_paper_trading_tracker()
    
    print("=" * 70)
    print("PAPER TRADING TRACKER TEST")
    print("=" * 70)
    print()
    
    # Reset any existing session
    tracker.reset()
    print("Reset existing session\n")
    
    # Start paper trading with default $100 balance
    result = tracker.start_paper_trading()
    print(f"Start: {result['message']}")
    if 'active_slots' in result:
        print(f"Active Slots: {result['active_slots']}")
    print()
    
    # Simulate trades across multiple timeframes and assets
    trades = [
        {'timeframe': '1m', 'asset': 'ETH', 'entry_price': 100, 'exit_price': 102, 'position_size': 1.0, 'pnl': 0.50, 'outcome': 'win'},
        {'timeframe': '5m', 'asset': 'BTC', 'entry_price': 102, 'exit_price': 103, 'position_size': 1.0, 'pnl': 0.80, 'outcome': 'win'},
        {'timeframe': '15m', 'asset': 'ETH', 'entry_price': 103, 'exit_price': 102, 'position_size': 1.0, 'pnl': -0.20, 'outcome': 'loss'},
    ]
    
    for trade in trades:
        result = tracker.record_trade(trade)
        print(f"Trade: {result['message']}")
    
    print()
    
    # Check requirements
    requirements = tracker.check_requirements()
    print("Requirements Check:")
    print(f"  Duration: {requirements['duration']['current']:.1f}h / {requirements['duration']['required']}h - {'✅' if requirements['duration']['met'] else '❌'}")
    print(f"  Trades: {requirements['trades']['current']} / {requirements['trades']['required']} - {'✅' if requirements['trades']['met'] else '❌'}")
    print(f"  PnL: ${requirements['pnl']['current']:.2f} - {'✅' if requirements['pnl']['met'] else '❌'}")
    print(f"  All Met: {'✅' if requirements['all_met'] else '❌'}")
    print()
    
    # Check approval status
    approved, reason = tracker.is_approved_for_live()
    print(f"Live Trading Approval: {'✅ ' + reason if approved else '❌ ' + reason}")
