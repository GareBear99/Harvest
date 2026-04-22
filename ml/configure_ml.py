#!/usr/bin/env python3
"""
ML Configuration CLI Tool
Easy command-line interface for managing ML settings per asset
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.ml_config import get_ml_config


def print_help():
    """Print usage help"""
    print("""
ML Configuration CLI Tool
=========================

Usage: python ml/configure_ml.py [command] [args]

Commands:
  status                    - Show current configuration
  status ETH|BTC            - Show configuration for specific asset
  
  enable ETH|BTC            - Enable ML for asset
  disable ETH|BTC           - Disable ML for asset
  
  enable-all                - Enable ML for all assets
  disable-all               - Disable ML for all assets
  
  feature ETH|BTC [feature] on|off    - Enable/disable specific feature
  timeframe ETH|BTC [tf] on|off       - Enable/disable ML for timeframe
  
  reset                     - Reset all to defaults (ML disabled)
  reset ETH|BTC             - Reset specific asset to defaults

Features:
  adaptive_thresholds       - Adjust thresholds based on performance
  strategy_switching        - Switch between proven strategies
  intelligent_learning      - Learn from failed predictions
  strategy_pool             - Save and manage multiple strategies

Timeframes: 15m, 1h, 4h

Examples:
  python ml/configure_ml.py status
  python ml/configure_ml.py enable ETH
  python ml/configure_ml.py feature ETH adaptive_thresholds on
  python ml/configure_ml.py timeframe BTC 15m on
  python ml/configure_ml.py disable-all
""")


def main():
    if len(sys.argv) < 2:
        get_ml_config().print_status()
        print("\nRun 'python ml/configure_ml.py help' for usage information.")
        return
    
    command = sys.argv[1].lower()
    config = get_ml_config()
    
    if command == 'help':
        print_help()
    
    elif command == 'status':
        if len(sys.argv) == 3:
            # Show specific asset
            config.print_status(sys.argv[2].upper())
        else:
            # Show all
            config.print_status()
    
    elif command == 'enable':
        if len(sys.argv) < 3:
            print("❌ Missing asset name. Usage: enable ETH|BTC")
            return
        asset = sys.argv[2].upper()
        config.enable_ml(asset, True)
        print(f"\n✅ {asset} ML enabled. Use 'feature' command to enable specific features.")
    
    elif command == 'disable':
        if len(sys.argv) < 3:
            print("❌ Missing asset name. Usage: disable ETH|BTC")
            return
        asset = sys.argv[2].upper()
        config.enable_ml(asset, False)
        print(f"\n✅ {asset} ML disabled. Using BASE_STRATEGY only.")
    
    elif command == 'enable-all':
        config.enable_all_ml(True)
        print("\n✅ ML enabled for all assets.")
    
    elif command == 'disable-all':
        config.enable_all_ml(False)
        print("\n✅ ML disabled for all assets. Using BASE_STRATEGY only.")
    
    elif command == 'feature':
        if len(sys.argv) < 5:
            print("❌ Usage: feature ETH|BTC [feature_name] on|off")
            print("Available features: adaptive_thresholds, strategy_switching, intelligent_learning, strategy_pool")
            return
        
        asset = sys.argv[2].upper()
        feature = sys.argv[3].lower()
        enable = sys.argv[4].lower() == 'on'
        
        config.enable_feature(asset, feature, enable)
        print(f"\n✅ {asset} {feature}: {'ENABLED' if enable else 'DISABLED'}")
    
    elif command == 'timeframe':
        if len(sys.argv) < 5:
            print("❌ Usage: timeframe ETH|BTC [15m|1h|4h] on|off")
            return
        
        asset = sys.argv[2].upper()
        tf = sys.argv[3].lower()
        enable = sys.argv[4].lower() == 'on'
        
        config.enable_timeframe_ml(asset, tf, enable)
        print(f"\n✅ {asset} {tf} ML: {'ENABLED' if enable else 'DISABLED'}")
    
    elif command == 'reset':
        if len(sys.argv) == 3:
            # Reset specific asset
            asset = sys.argv[2].upper()
            config.reset_to_defaults(asset)
        else:
            # Reset all
            config.reset_to_defaults()
        print("\n✅ Reset complete. All ML features disabled.")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python ml/configure_ml.py help' for usage information.")


if __name__ == "__main__":
    main()
