#!/usr/bin/env python3
"""
Slot Allocation Data Provider for Dashboard
Provides formatted slot allocation information for display
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Optional
from core.slot_allocation_strategy import get_slot_allocation_strategy, Asset
from core.founder_fee_manager import FounderFeeManager


def get_slot_allocation_display_data(
    current_balance: float,
    mode: str = 'LIVE',
    founder_fee_manager: Optional[FounderFeeManager] = None
) -> Dict:
    """
    Get formatted slot allocation data for dashboard display.
    
    Args:
        current_balance: Current account balance
        mode: Trading mode ('LIVE', 'PAPER', 'BACKTEST')
        founder_fee_manager: Optional FounderFeeManager instance for position tier info
        
    Returns:
        Dict with slot allocation display data
    """
    strategy = get_slot_allocation_strategy()
    
    # Get slot allocation summary
    summary = strategy.get_slot_summary(current_balance)
    
    # Build display data
    display_data = {
        'active_slots': summary['active_slots'],
        'total_slots': 10,  # Base system has 10 slots ($10-$100)
        'eth_slots': strategy.get_active_slots_for_asset(current_balance, Asset.ETH),
        'btc_slots': strategy.get_active_slots_for_asset(current_balance, Asset.BTC),
        'active_timeframes': summary['active_timeframes'],
        'active_assets': summary['active_assets'],
        'status': summary['status'],
        'message': summary['message']
    }
    
    # Add next unlock information
    if summary['active_slots'] < 10:
        next_slot = summary['active_slots'] + 1
        next_balance = next_slot * 10
        next_asset = strategy.get_slot_asset(next_slot)
        
        display_data['next_unlock'] = {
            'slot_number': next_slot,
            'balance': next_balance,
            'asset': next_asset.name,
            'amount_needed': next_balance - current_balance
        }
    else:
        display_data['next_unlock'] = None
    
    # Add position tier information (for $100+ balances)
    if current_balance >= 100.0 and founder_fee_manager:
        position_tier = founder_fee_manager.config.get('position_tier', 0)
        positions_per_tf_per_asset = founder_fee_manager.get_position_limit()
        total_position_slots = founder_fee_manager.get_total_position_limit()
        
        display_data['position_tier'] = position_tier
        display_data['positions_per_tf_per_asset'] = positions_per_tf_per_asset
        display_data['total_position_slots'] = total_position_slots
        
        # Next position tier unlock info
        if position_tier < 2:  # Not maxed yet
            next_tier_thresholds = {0: 110.0, 1: 210.0}
            if position_tier in next_tier_thresholds:
                next_tier_balance = next_tier_thresholds[position_tier]
                display_data['next_position_tier'] = {
                    'balance': next_tier_balance,
                    'tier': position_tier + 1,
                    'amount_needed': max(0, next_tier_balance - current_balance),
                    'fee_required': 10.0,
                    'new_total_slots': (position_tier + 2) * 10  # Tier 0→10, 1→20, 2→30
                }
    
    return display_data


def format_slot_allocation_for_console(balance: float, mode: str = 'LIVE') -> str:
    """
    Format slot allocation as console-friendly text.
    
    Args:
        balance: Current balance
        mode: Trading mode
        
    Returns:
        Formatted string for console output
    """
    data = get_slot_allocation_display_data(balance, mode)
    
    lines = []
    lines.append(f"Slot Allocation: {data['active_slots']}/{data['total_slots']} active")
    
    if data['eth_slots']:
        lines.append(f"  ETH Slots: {data['eth_slots']}")
    if data['btc_slots']:
        lines.append(f"  BTC Slots: {data['btc_slots']}")
    
    if data['active_timeframes']:
        lines.append(f"  Timeframes: {', '.join(data['active_timeframes'])}")
    
    if data.get('next_unlock'):
        next_unlock = data['next_unlock']
        lines.append(f"  Next: Slot {next_unlock['slot_number']} ({next_unlock['asset']}) @ ${next_unlock['balance']:.0f}")
    
    if data.get('position_tier') is not None:
        tier = data['position_tier']
        total = data['total_position_slots']
        tier_names = {0: "Tier 1", 1: "Tier 2", 2: "Tier 3 (MAXED)"}
        lines.append(f"  Position {tier_names.get(tier, f'Tier {tier+1}')}: {total} total slots")
    
    return '\n'.join(lines)


# Testing
if __name__ == '__main__':
    print("=" * 70)
    print("SLOT ALLOCATION DATA PROVIDER - TEST")
    print("=" * 70)
    
    test_balances = [10, 25, 35, 55, 75, 100, 150, 250]
    
    for balance in test_balances:
        print(f"\n--- Balance: ${balance:.0f} ---")
        
        # Get display data
        data = get_slot_allocation_display_data(balance, mode='LIVE')
        
        print(f"Active Slots: {data['active_slots']}/10")
        print(f"ETH Slots: {data['eth_slots']}")
        print(f"BTC Slots: {data['btc_slots']}")
        print(f"Timeframes: {', '.join(data['active_timeframes'])}")
        
        if data.get('next_unlock'):
            nu = data['next_unlock']
            print(f"Next Unlock: Slot {nu['slot_number']} ({nu['asset']}) @ ${nu['balance']:.0f}")
        
        if data.get('position_tier') is not None:
            print(f"Position Tier: {data['position_tier']} ({data['total_position_slots']} total slots)")
        
        print(f"\nFormatted Output:")
        print(format_slot_allocation_for_console(balance))
