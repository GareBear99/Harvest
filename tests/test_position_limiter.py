#!/usr/bin/env python3
"""
Quick test to verify position size limiter is working correctly
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.position_size_limiter import get_position_limiter

def test_position_limiter():
    """Test position size limiter with different capital amounts"""
    limiter = get_position_limiter()
    
    print("=" * 70)
    print("POSITION SIZE LIMITER TEST")
    print("=" * 70)
    print()
    
    # Test scenarios
    scenarios = [
        ("Small account", 10.0, 150.0),
        ("Growing account", 100.0, 200.0),
        ("Medium account", 1000.0, 500.0),
        ("Large account", 5000.0, 300.0),
        ("Very large account", 10000.0, 500.0),
    ]
    
    for name, capital, requested_size in scenarios:
        print(f"Test: {name}")
        print(f"  Capital: ${capital:.2f}")
        print(f"  Requested position: ${requested_size:.2f}")
        
        limited, was_limited, info = limiter.limit_position_size(
            requested_size, capital, "1h"
        )
        
        print(f"  Allowed position: ${limited:.2f}")
        print(f"  Was limited: {was_limited}")
        if was_limited:
            print(f"  Reason: {info['message']}")
        print()
    
    # Show stats
    print("=" * 70)
    print("LIMITER STATISTICS")
    print("=" * 70)
    stats = limiter.get_stats()
    print(f"Total checks: {stats['total_checks']}")
    print(f"Limited: {stats['limits_applied']}")
    print(f"Limited %: {stats['limit_rate_pct']:.1f}%")
    print(f"Small account threshold: ${stats['small_account_threshold']:,.0f}")
    print(f"Max position (small): ${stats['max_position_small']}")
    print(f"Max position % (large): {stats['max_position_pct_large']}%")
    print()
    
    # Show info for dashboard
    print("=" * 70)
    print("DASHBOARD INFO")
    print("=" * 70)
    for capital in [10.0, 100.0, 1000.0, 5000.0, 10000.0]:
        info = limiter.get_position_info_for_display(capital)
        print(f"Capital ${capital:.0f}:")
        print(f"  Max position: ${info['max_position_size']:.2f}")
        print(f"  Rule: {info['rule']}")
        print(f"  Status: {info['status']}")
        print()

if __name__ == "__main__":
    test_position_limiter()
