#!/usr/bin/env python3
"""
Slot Allocation Strategy
Implements stair-climbing balance allocation where every $10 earned unlocks ONE slot,
alternating ETH→BTC, with progressive timeframe unlocks.

Logic:
- $10: Slot 1 (ETH), 1m only
- $20: Slot 2 (BTC), 1m only
- $30: Slot 3 (ETH), 1m+5m unlocked
- $40: Slot 4 (BTC), 1m+5m active
- $50: Slot 5 (ETH), 1m+5m+15m unlocked
- $60: Slot 6 (BTC), 1m+5m+15m active
- $70: Slot 7 (ETH), 1m+5m+15m+1h unlocked
- $80: Slot 8 (BTC), 1m+5m+15m+1h active
- $90: Slot 9 (ETH), all 5 TFs unlocked
- $100: Slot 10 (BTC), FULL BASE SYSTEM

At $100+: Position tier system takes over (10→20→30 slots via founder fees)
"""

from typing import List, Dict, Set
from enum import Enum


class Asset(Enum):
    """Supported trading assets"""
    ETH = "ETHUSDT"
    BTC = "BTCUSDT"


class SlotAllocationStrategy:
    """
    Manages slot allocation with ETH→BTC alternation and progressive timeframe unlocks.
    
    Key Concepts:
    - Slot: One trading position capacity that costs ~$10 to use effectively
    - Stair-Climbing: Each $10 earned unlocks 1 slot, alternating ETH→BTC
    - Timeframe Unlocks: More slots = more timeframes available
    - Position Tiers: At $100+, founder fee system unlocks additional position capacity
    """
    
    # Slot allocation: odd slots = ETH, even slots = BTC
    SLOT_ASSET_MAP = {
        1: Asset.ETH,
        2: Asset.BTC,
        3: Asset.ETH,
        4: Asset.BTC,
        5: Asset.ETH,
        6: Asset.BTC,
        7: Asset.ETH,
        8: Asset.BTC,
        9: Asset.ETH,
        10: Asset.BTC
    }
    
    # Timeframe unlocks based on slot count
    TIMEFRAME_UNLOCK_MAP = {
        1: ['1m'],                          # Slots 1-2: 1m only
        2: ['1m'],
        3: ['1m', '5m'],                    # Slots 3-4: 1m+5m
        4: ['1m', '5m'],
        5: ['1m', '5m', '15m'],             # Slots 5-6: 1m+5m+15m
        6: ['1m', '5m', '15m'],
        7: ['1m', '5m', '15m', '1h'],       # Slots 7-8: 1m+5m+15m+1h
        8: ['1m', '5m', '15m', '1h'],
        9: ['1m', '5m', '15m', '1h', '4h'], # Slots 9-10: ALL timeframes
        10: ['1m', '5m', '15m', '1h', '4h']
    }
    
    # Capital per slot (each slot needs ~$10 to trade)
    CAPITAL_PER_SLOT = 10.0
    
    # Minimum balance to start trading
    MIN_BALANCE = 10.0
    
    # Full base system activation threshold
    FULL_BASE_THRESHOLD = 100.0
    
    def __init__(self):
        """Initialize slot allocation strategy"""
        pass
    
    def get_active_slots(self, balance: float) -> int:
        """
        Calculate number of active slots based on balance.
        
        Args:
            balance: Current account balance in USD
            
        Returns:
            Number of active slots (0-10)
        """
        if balance < self.MIN_BALANCE:
            return 0
        
        # Calculate slots: 1 slot per $10
        slots = int(balance // self.CAPITAL_PER_SLOT)
        
        # Cap at 10 slots (full base system at $100)
        return min(slots, 10)
    
    def get_slot_asset(self, slot_number: int) -> Asset:
        """
        Get the asset assigned to a specific slot.
        
        Args:
            slot_number: Slot number (1-10)
            
        Returns:
            Asset enum (ETH or BTC)
        """
        if slot_number < 1 or slot_number > 10:
            raise ValueError(f"Invalid slot number: {slot_number}. Must be 1-10.")
        
        return self.SLOT_ASSET_MAP[slot_number]
    
    def get_active_timeframes(self, balance: float) -> List[str]:
        """
        Get list of active timeframes based on balance.
        
        Args:
            balance: Current account balance
            
        Returns:
            List of active timeframe strings (e.g., ['1m', '5m'])
        """
        slots = self.get_active_slots(balance)
        
        if slots == 0:
            return []
        
        return self.TIMEFRAME_UNLOCK_MAP[slots]
    
    def get_active_assets(self, balance: float) -> List[Asset]:
        """
        Get list of active assets based on balance.
        
        Args:
            balance: Current account balance
            
        Returns:
            List of active Asset enums
        """
        slots = self.get_active_slots(balance)
        
        if slots == 0:
            return []
        
        # Get unique assets from active slots
        active_assets = set()
        for slot_num in range(1, slots + 1):
            active_assets.add(self.SLOT_ASSET_MAP[slot_num])
        
        return list(active_assets)
    
    def is_asset_active(self, balance: float, asset: Asset) -> bool:
        """
        Check if a specific asset is active at current balance.
        
        Args:
            balance: Current account balance
            asset: Asset to check
            
        Returns:
            True if asset has at least one active slot
        """
        return asset in self.get_active_assets(balance)
    
    def get_active_slots_for_asset(self, balance: float, asset: Asset) -> List[int]:
        """
        Get list of active slot numbers for a specific asset.
        
        Args:
            balance: Current account balance
            asset: Asset to get slots for
            
        Returns:
            List of slot numbers assigned to this asset (e.g., [1, 3, 5] for ETH at $50)
        """
        total_slots = self.get_active_slots(balance)
        
        if total_slots == 0:
            return []
        
        # Get slots assigned to this asset
        asset_slots = []
        for slot_num in range(1, total_slots + 1):
            if self.SLOT_ASSET_MAP[slot_num] == asset:
                asset_slots.append(slot_num)
        
        return asset_slots
    
    def get_slot_summary(self, balance: float) -> Dict:
        """
        Get comprehensive summary of slot allocation at current balance.
        
        Args:
            balance: Current account balance
            
        Returns:
            Dict with slot allocation details
        """
        slots = self.get_active_slots(balance)
        
        if slots == 0:
            return {
                'balance': balance,
                'active_slots': 0,
                'active_assets': [],
                'active_timeframes': [],
                'eth_slots': [],
                'btc_slots': [],
                'status': 'INSUFFICIENT_BALANCE',
                'message': f'Need ${self.MIN_BALANCE:.2f} minimum to start trading'
            }
        
        eth_slots = self.get_active_slots_for_asset(balance, Asset.ETH)
        btc_slots = self.get_active_slots_for_asset(balance, Asset.BTC)
        timeframes = self.get_active_timeframes(balance)
        
        # Determine status
        if slots < 10:
            next_slot = slots + 1
            next_balance = next_slot * self.CAPITAL_PER_SLOT
            next_asset = self.SLOT_ASSET_MAP[next_slot]
            status_msg = f'Next: ${next_balance:.0f} unlocks slot {next_slot} ({next_asset.name})'
        else:
            status_msg = 'FULL BASE SYSTEM - All 10 slots active'
        
        return {
            'balance': balance,
            'active_slots': slots,
            'active_assets': [a.name for a in self.get_active_assets(balance)],
            'active_timeframes': timeframes,
            'eth_slots': eth_slots,
            'btc_slots': btc_slots,
            'status': 'ACTIVE',
            'message': status_msg
        }
    
    def format_slot_summary(self, balance: float) -> str:
        """Get human-readable summary of slot allocation"""
        summary = self.get_slot_summary(balance)
        
        if summary['status'] == 'INSUFFICIENT_BALANCE':
            return summary['message']
        
        lines = [
            f"Balance: ${balance:.2f}",
            f"Active Slots: {summary['active_slots']}/10",
            f"ETH Slots: {summary['eth_slots']}",
            f"BTC Slots: {summary['btc_slots']}",
            f"Timeframes: {', '.join(summary['active_timeframes'])}",
            f"Status: {summary['message']}"
        ]
        
        return '\n'.join(lines)


# Singleton instance
_slot_strategy_instance = None


def get_slot_allocation_strategy() -> SlotAllocationStrategy:
    """Get or create slot allocation strategy singleton"""
    global _slot_strategy_instance
    if _slot_strategy_instance is None:
        _slot_strategy_instance = SlotAllocationStrategy()
    return _slot_strategy_instance


# Testing
if __name__ == '__main__':
    strategy = SlotAllocationStrategy()
    
    print("=" * 70)
    print("SLOT ALLOCATION STRATEGY - STAIR-CLIMBING DEMONSTRATION")
    print("=" * 70)
    
    # Test every $10 increment from $10 to $100
    test_balances = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 150, 210]
    
    for balance in test_balances:
        print(f"\n{'='*70}")
        print(f"Balance: ${balance:.2f}")
        print(f"{'='*70}")
        
        summary = strategy.get_slot_summary(balance)
        
        if summary['status'] == 'INSUFFICIENT_BALANCE':
            print(summary['message'])
            continue
        
        print(f"Active Slots: {summary['active_slots']}/10")
        print(f"ETH Slots: {summary['eth_slots']}")
        print(f"BTC Slots: {summary['btc_slots']}")
        print(f"Active Assets: {', '.join(summary['active_assets'])}")
        print(f"Active Timeframes: {', '.join(summary['active_timeframes'])}")
        print(f"Status: {summary['message']}")
        
        # Show slot-by-slot breakdown
        print(f"\nSlot Breakdown:")
        for slot_num in range(1, summary['active_slots'] + 1):
            asset = strategy.get_slot_asset(slot_num)
            print(f"  Slot {slot_num}: {asset.name}")
    
    print(f"\n{'='*70}")
    print("KEY PRINCIPLES")
    print(f"{'='*70}")
    print("• Each $10 earned unlocks 1 slot")
    print("• Slots alternate: ETH→BTC→ETH→BTC...")
    print("• Timeframes unlock progressively:")
    print("  - Slots 1-2: 1m only")
    print("  - Slots 3-4: 1m+5m")
    print("  - Slots 5-6: 1m+5m+15m")
    print("  - Slots 7-8: 1m+5m+15m+1h")
    print("  - Slots 9-10: All 5 timeframes (FULL BASE)")
    print("• At $100+: Position tier system (10→20→30 via founder fees)")
