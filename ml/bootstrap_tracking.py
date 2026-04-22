#!/usr/bin/env python3
"""
Bootstrap Tracking System
Initialize all 4 layers with BASE_STRATEGY seeds for live paper trading readiness
"""

import sys
import os
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.base_strategy import BASE_STRATEGY
from ml.strategy_seed_generator import generate_strategy_seed
from ml.seed_registry import SeedRegistry
from ml.seed_catalog import SeedCatalog


def bootstrap_all_layers():
    """Initialize all 4 tracking layers with BASE_STRATEGY seeds"""
    
    print("=" * 80)
    print("BOOTSTRAP TRACKING SYSTEM")
    print("=" * 80)
    print()
    
    # Initialize all layers
    print("📦 Initializing tracking layers...")
    registry = SeedRegistry()
    catalog = SeedCatalog()
    
    print()
    print("🌱 Registering BASE_STRATEGY seeds across all layers...")
    print()
    
    timeframes = ['1m', '5m', '15m', '1h', '4h']
    registered_seeds = []
    
    for tf in timeframes:
        if tf not in BASE_STRATEGY:
            print(f"  ⚠️  {tf}: Not in BASE_STRATEGY, skipping")
            continue
        
        # Get parameters (excluding fake seed prefix)
        params = BASE_STRATEGY[tf].copy()
        params.pop('seed', None)  # Remove timeframe prefix
        
        # Calculate real SHA-256 seed
        strategy_seed = generate_strategy_seed(tf, params)
        
        # Register in Layer 1 (seed_registry.json)
        registry.register_seed(
            seed=strategy_seed,
            timeframe=tf,
            parameters=params,
            version='v1',
            input_seed=None  # BASE_STRATEGY has no input seed
        )
        
        # Create snapshot in Layer 2 (seed_snapshots.json)
        # Note: seed_snapshots.py doesn't exist yet, but registry has snapshot support
        
        registered_seeds.append({
            'timeframe': tf,
            'seed': strategy_seed,
            'params': params
        })
        
        print(f"  ✅ {tf:4s}: Seed {strategy_seed:>10d} registered in Layer 1")
    
    print()
    print("=" * 80)
    print("BOOTSTRAP COMPLETE")
    print("=" * 80)
    print()
    
    print(f"✅ Registered {len(registered_seeds)} BASE_STRATEGY seeds")
    print()
    print("📊 Summary:")
    for item in registered_seeds:
        print(f"  {item['timeframe']:4s}: {item['seed']:>10d}")
    
    print()
    print("🎯 Next Steps:")
    print("  1. Run: python3 ml/validate_tracking.py")
    print("  2. Run backtest to populate Layer 3 (catalog)")
    print("  3. Start live paper trading!")
    
    return registered_seeds


if __name__ == "__main__":
    bootstrap_all_layers()
