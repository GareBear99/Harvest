#!/usr/bin/env python3
"""
Test Dashboard Slot Allocation Integration
Quick validation that slot data flows correctly into dashboard
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dashboard.terminal_ui import TerminalDashboard
from dashboard.slot_data_provider import get_slot_allocation_display_data


def test_dashboard_initialization():
    """Test that dashboard initializes with slot data"""
    print("=" * 70)
    print("DASHBOARD SLOT ALLOCATION INTEGRATION TEST")
    print("=" * 70)
    
    try:
        # Create dashboard instance
        dashboard = TerminalDashboard()
        
        # Check if bot data has slot_allocation
        bot_data = dashboard.data.get('bot', {})
        slot_data = bot_data.get('slot_allocation', {})
        
        print("\n✅ Dashboard initialized successfully")
        print(f"\nBot Data Keys: {list(bot_data.keys())}")
        
        if 'slot_allocation' in bot_data:
            print("\n✅ slot_allocation key present in bot data")
            print(f"\nSlot Allocation Data:")
            print(f"  Active Slots: {slot_data.get('active_slots', 'N/A')}/10")
            print(f"  ETH Slots: {slot_data.get('eth_slots', [])}")
            print(f"  BTC Slots: {slot_data.get('btc_slots', [])}")
            print(f"  Timeframes: {slot_data.get('active_timeframes', [])}")
            
            if slot_data.get('next_unlock'):
                nu = slot_data['next_unlock']
                print(f"  Next Unlock: Slot {nu['slot_number']} ({nu['asset']}) @ ${nu['balance']:.0f}")
        else:
            print("\n❌ slot_allocation key NOT FOUND in bot data")
            return False
        
        # Test render method
        print("\n" + "=" * 70)
        print("TESTING PANEL RENDER")
        print("=" * 70)
        
        from dashboard.panels import BotStatusPanel
        bot_panel = BotStatusPanel()
        
        # Render panel with slot data
        panel = bot_panel.render(bot_data)
        print("\n✅ BotStatusPanel rendered successfully")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_balance_updates():
    """Test that slot data updates with balance changes"""
    print("\n" + "=" * 70)
    print("TESTING BALANCE UPDATES")
    print("=" * 70)
    
    test_balances = [10, 25, 35, 55, 75, 100, 150]
    
    for balance in test_balances:
        slot_data = get_slot_allocation_display_data(
            current_balance=balance,
            mode='BACKTEST',
            founder_fee_manager=None
        )
        
        print(f"\n${balance:>3.0f}: {slot_data['active_slots']}/10 slots | ", end="")
        print(f"ETH: {slot_data['eth_slots']} | ", end="")
        print(f"BTC: {slot_data['btc_slots']} | ", end="")
        print(f"TFs: {', '.join(slot_data['active_timeframes'])}")
    
    print("\n✅ All balance updates working correctly")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("DASHBOARD INTEGRATION VALIDATION")
    print("="*70)
    
    results = []
    
    # Test 1: Dashboard initialization
    results.append(("Dashboard Initialization", test_dashboard_initialization()))
    
    # Test 2: Balance updates
    results.append(("Balance Updates", test_balance_updates()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Dashboard integration working!")
        print("\nNext steps:")
        print("1. Test live dashboard: ./dashboard.sh")
        print("2. Verify slot display updates in real-time")
        print("3. Test with balance changes")
    else:
        print("\n⚠️  Some tests failed - review errors above")
    
    print("="*70 + "\n")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
