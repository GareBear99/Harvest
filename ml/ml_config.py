#!/usr/bin/env python3
"""
Machine Learning Configuration
Controls ML features per asset - treats each asset as a separate bot
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional


class MLConfig:
    """
    Configuration for machine learning features
    Each asset (ETH, BTC) is treated as a completely separate bot
    
    When ML is disabled for an asset:
    - Uses BASE_STRATEGY thresholds only
    - No adaptive adjustments
    - No strategy switching
    - No learning from errors
    
    When ML is enabled for an asset:
    - Adaptive threshold adjustments
    - Strategy pool and switching
    - Intelligent error learning
    - Per-timeframe strategies
    """
    
    def __init__(self, config_file: str = "ml/ml_config.json"):
        self.config_file = config_file
        
        # Default configuration - each asset separate
        self.config = {
            'assets': {
                'ETH': {
                    'ml_enabled': False,  # Master switch for ETH bot
                    'features': {
                        'adaptive_thresholds': False,
                        'strategy_switching': False,
                        'intelligent_learning': False,
                        'strategy_pool': False,
                    },
                    'timeframes': {
                        '15m': {'enabled': True, 'use_ml': False},
                        '1h': {'enabled': True, 'use_ml': False},
                        '4h': {'enabled': True, 'use_ml': False}
                    }
                },
                'BTC': {
                    'ml_enabled': False,  # Master switch for BTC bot
                    'features': {
                        'adaptive_thresholds': False,
                        'strategy_switching': False,
                        'intelligent_learning': False,
                        'strategy_pool': False,
                    },
                    'timeframes': {
                        '15m': {'enabled': True, 'use_ml': False},
                        '1h': {'enabled': True, 'use_ml': False},
                        '4h': {'enabled': True, 'use_ml': False}
                    }
                }
            },
            'global_settings': {
                'max_strategies_per_timeframe': 3,
                'min_trades_for_proven': 20,
                'min_win_rate_for_proven': 0.72,
                'switch_threshold_wr': 0.58,
                'switch_threshold_losses': 5,
                'failsafe_unprofitable_threshold': 3  # Reset to BASE after 3 unprofitable trades
            },
            'base_strategy_restore_point': self._get_base_strategy_snapshot()
        }
        
        # Ensure base strategy snapshot always present
        if 'base_strategy_restore_point' not in self.config:
            self.config['base_strategy_restore_point'] = self._get_base_strategy_snapshot()
            self.save_config()
    
    def is_ml_enabled(self, asset: str) -> bool:
        """Check if ML is enabled for specific asset"""
        asset = asset.upper()
        if asset not in self.config['assets']:
            return False
        return self.config['assets'][asset]['ml_enabled']
    
    def is_feature_enabled(self, asset: str, feature: str) -> bool:
        """
        Check if specific ML feature is enabled for asset
        
        Args:
            asset: 'ETH' or 'BTC'
            feature: One of 'adaptive_thresholds', 'strategy_switching', 
                    'intelligent_learning', 'strategy_pool'
        """
        asset = asset.upper()
        if not self.is_ml_enabled(asset):
            return False
        
        if asset not in self.config['assets']:
            return False
        
        return self.config['assets'][asset]['features'].get(feature, False)
    
    def is_timeframe_ml_enabled(self, asset: str, timeframe: str) -> bool:
        """Check if ML is enabled for specific asset + timeframe"""
        asset = asset.upper()
        if not self.is_ml_enabled(asset):
            return False
        
        if asset not in self.config['assets']:
            return False
        
        tf_config = self.config['assets'][asset]['timeframes'].get(timeframe, {})
        return tf_config.get('use_ml', False)
    
    def is_timeframe_enabled(self, asset: str, timeframe: str) -> bool:
        """Check if timeframe is enabled for trading on asset"""
        asset = asset.upper()
        if asset not in self.config['assets']:
            return True
        
        tf_config = self.config['assets'][asset]['timeframes'].get(timeframe, {})
        return tf_config.get('enabled', True)
    
    def enable_ml(self, asset: str, enable: bool = True):
        """Enable or disable all ML features for specific asset"""
        asset = asset.upper()
        if asset not in self.config['assets']:
            print(f"⚠️  Unknown asset: {asset}")
            return
        
        self.config['assets'][asset]['ml_enabled'] = enable
        self.save_config()
        
        status = "ENABLED" if enable else "DISABLED"
        print(f"🤖 {asset} Machine Learning: {status}")
        
        if not enable:
            print(f"   → {asset} using BASE_STRATEGY only (no adaptive learning)")
    
    def enable_all_ml(self, enable: bool = True):
        """Enable or disable ML for all assets"""
        for asset in self.config['assets'].keys():
            self.enable_ml(asset, enable)
    
    def enable_feature(self, asset: str, feature: str, enable: bool = True):
        """Enable or disable specific ML feature for asset"""
        asset = asset.upper()
        if asset not in self.config['assets']:
            print(f"⚠️  Unknown asset: {asset}")
            return
        
        if feature not in self.config['assets'][asset]['features']:
            print(f"⚠️  Unknown feature: {feature}")
            return
        
        self.config['assets'][asset]['features'][feature] = enable
        self.save_config()
        
        status = "ENABLED" if enable else "DISABLED"
        print(f"   {asset} {feature}: {status}")
    
    def enable_timeframe_ml(self, asset: str, timeframe: str, enable: bool = True):
        """Enable or disable ML for specific asset + timeframe"""
        asset = asset.upper()
        if asset not in self.config['assets']:
            print(f"⚠️  Unknown asset: {asset}")
            return
        
        if timeframe not in self.config['assets'][asset]['timeframes']:
            self.config['assets'][asset]['timeframes'][timeframe] = {}
        
        self.config['assets'][asset]['timeframes'][timeframe]['use_ml'] = enable
        self.save_config()
        
        status = "ENABLED" if enable else "DISABLED"
        print(f"   {asset} {timeframe} ML: {status}")
    
    def enable_timeframe(self, asset: str, timeframe: str, enable: bool = True):
        """Enable or disable timeframe for trading on asset"""
        asset = asset.upper()
        if asset not in self.config['assets']:
            print(f"⚠️  Unknown asset: {asset}")
            return
        
        if timeframe not in self.config['assets'][asset]['timeframes']:
            self.config['assets'][asset]['timeframes'][timeframe] = {}
        
        self.config['assets'][asset]['timeframes'][timeframe]['enabled'] = enable
        self.save_config()
        
        status = "ENABLED" if enable else "DISABLED"
        print(f"   {asset} {timeframe} trading: {status}")
    
    def get_mode_description(self, asset: str) -> str:
        """Get human-readable description of current mode for asset"""
        asset = asset.upper()
        if asset not in self.config['assets']:
            return "UNKNOWN ASSET"
        
        if not self.config['assets'][asset]['ml_enabled']:
            return "BASE MODE (No ML)"
        
        enabled_features = [
            f for f, enabled in self.config['assets'][asset]['features'].items() 
            if enabled
        ]
        
        if not enabled_features:
            return "ML ENABLED (No features)"
        
        return f"ML ACTIVE ({len(enabled_features)} features)"
    
    def print_status(self, asset: Optional[str] = None):
        """Print configuration status for specific asset or all assets"""
        print(f"\n{'='*80}")
        print("🤖 MACHINE LEARNING CONFIGURATION")
        print(f"{'='*80}\n")
        
        if asset:
            # Show single asset
            self._print_asset_status(asset.upper())
        else:
            # Show all assets
            for asset_name in ['ETH', 'BTC']:
                self._print_asset_status(asset_name)
                print()
    
    def _print_asset_status(self, asset: str):
        """Print status for single asset"""
        if asset not in self.config['assets']:
            print(f"❌ {asset}: UNKNOWN ASSET")
            return
        
        asset_config = self.config['assets'][asset]
        mode = self.get_mode_description(asset)
        ml_status = '✅ ON' if asset_config['ml_enabled'] else '❌ OFF'
        
        print(f"🔹 {asset} Bot")
        print(f"   Mode: {mode}")
        print(f"   ML Switch: {ml_status}")
        
        if asset_config['ml_enabled']:
            print(f"   ML Features:")
            for feature, enabled in asset_config['features'].items():
                status = '✅' if enabled else '❌'
                print(f"     {status} {feature}")
        
        print(f"   Timeframes:")
        for tf in ['15m', '1h', '4h']:
            tf_config = asset_config['timeframes'].get(tf, {})
            trading = '✅' if tf_config.get('enabled', True) else '❌'
            ml = '✅' if (asset_config['ml_enabled'] and tf_config.get('use_ml', False)) else '❌'
            print(f"     {tf}: Trading {trading} | ML {ml}")
    
    def save_config(self):
        """Save configuration to disk"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving ML config: {e}")
    
    def load_config(self):
        """Load configuration from disk"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                
                # Merge with defaults
                self._merge_config(saved_config)
                
                print(f"📂 Loaded ML config from {self.config_file}")
            else:
                print(f"📝 No ML config found - using defaults (ML disabled for all assets)")
                self.save_config()
        except Exception as e:
            print(f"⚠️  Error loading ML config: {e}")
            print(f"📝 Using default config (ML disabled for all assets)")
    
    def _try_load_config(self) -> Optional[dict]:
        """Try to load existing config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading ML config: {e}")
        return None
    
    def _get_base_strategy_snapshot(self) -> dict:
        """Get immutable snapshot of BASE_STRATEGY for restore point"""
        try:
            from ml.base_strategy import BASE_STRATEGY
            return {
                'timestamp': datetime.now().isoformat() if hasattr(datetime, 'now') else None,
                'strategies': BASE_STRATEGY.copy(),
                'description': 'Immutable BASE_STRATEGY restore point'
            }
        except ImportError:
            # If base_strategy not available yet, return empty
            return {
                'timestamp': None,
                'strategies': {
                    '15m': {'min_confidence': 0.70, 'min_volume': 1.15, 'min_trend': 0.55, 'min_adx': 25, 'min_roc': -1.0, 'atr_min': 0.4, 'atr_max': 3.5},
                    '1h': {'min_confidence': 0.66, 'min_volume': 1.10, 'min_trend': 0.50, 'min_adx': 25, 'min_roc': -1.0, 'atr_min': 0.4, 'atr_max': 3.5},
                    '4h': {'min_confidence': 0.63, 'min_volume': 1.05, 'min_trend': 0.46, 'min_adx': 25, 'min_roc': -1.0, 'atr_min': 0.4, 'atr_max': 3.5}
                },
                'description': 'Immutable BASE_STRATEGY restore point'
            }
    
    def get_base_strategy_snapshot(self) -> dict:
        """Get the saved BASE_STRATEGY snapshot"""
        return self.config.get('base_strategy_restore_point', {}).get('strategies', {})
    
    def _merge_config(self, saved_config: dict):
        """Merge saved config with defaults"""
        # Update assets
        if 'assets' in saved_config:
            for asset, asset_config in saved_config['assets'].items():
                if asset not in self.config['assets']:
                    # New asset in saved config
                    self.config['assets'][asset] = asset_config
                else:
                    # Merge existing asset
                    if 'ml_enabled' in asset_config:
                        self.config['assets'][asset]['ml_enabled'] = asset_config['ml_enabled']
                    
                    if 'features' in asset_config:
                        self.config['assets'][asset]['features'].update(asset_config['features'])
                    
                    if 'timeframes' in asset_config:
                        for tf, tf_config in asset_config['timeframes'].items():
                            if tf not in self.config['assets'][asset]['timeframes']:
                                self.config['assets'][asset]['timeframes'][tf] = {}
                            self.config['assets'][asset]['timeframes'][tf].update(tf_config)
        
        # Update global settings
        if 'global_settings' in saved_config:
            self.config['global_settings'].update(saved_config['global_settings'])
        
        # Ensure base strategy snapshot
        if 'base_strategy_restore_point' in saved_config:
            self.config['base_strategy_restore_point'] = saved_config['base_strategy_restore_point']
    
    def reset_to_defaults(self, asset: Optional[str] = None):
        """Reset to default configuration (ML disabled)"""
        if asset:
            # Reset single asset
            asset = asset.upper()
            if asset in self.config['assets']:
                self.config['assets'][asset]['ml_enabled'] = False
                for feature in self.config['assets'][asset]['features']:
                    self.config['assets'][asset]['features'][feature] = False
                for tf in self.config['assets'][asset]['timeframes']:
                    self.config['assets'][asset]['timeframes'][tf]['use_ml'] = False
                print(f"🔄 {asset} reset to defaults: ML DISABLED, using BASE_STRATEGY only")
        else:
            # Reset all assets
            for asset in self.config['assets']:
                self.config['assets'][asset]['ml_enabled'] = False
                for feature in self.config['assets'][asset]['features']:
                    self.config['assets'][asset]['features'][feature] = False
                for tf in self.config['assets'][asset]['timeframes']:
                    self.config['assets'][asset]['timeframes'][tf]['use_ml'] = False
            print(f"🔄 All assets reset to defaults: ML DISABLED, using BASE_STRATEGY only")
        
        self.save_config()


# Singleton instance
_ml_config_instance: Optional[MLConfig] = None


def get_ml_config() -> MLConfig:
    """Get global ML configuration instance"""
    global _ml_config_instance
    if _ml_config_instance is None:
        _ml_config_instance = MLConfig()
    return _ml_config_instance


if __name__ == "__main__":
    # Test the config system
    config = MLConfig()
    
    print("="*80)
    print("TEST: Default Configuration (ML disabled for both assets)")
    print("="*80)
    config.print_status()
    
    print("\n" + "="*80)
    print("TEST: Enable ML for ETH only (full features)")
    print("="*80)
    config.enable_ml('ETH', True)
    config.enable_feature('ETH', 'adaptive_thresholds', True)
    config.enable_feature('ETH', 'strategy_switching', True)
    config.enable_feature('ETH', 'intelligent_learning', True)
    config.enable_feature('ETH', 'strategy_pool', True)
    config.enable_timeframe_ml('ETH', '15m', True)
    config.enable_timeframe_ml('ETH', '1h', True)
    config.print_status()
    
    print("\n" + "="*80)
    print("TEST: Enable ML for BTC (partial features)")
    print("="*80)
    config.enable_ml('BTC', True)
    config.enable_feature('BTC', 'adaptive_thresholds', True)
    config.enable_feature('BTC', 'strategy_pool', True)
    config.enable_timeframe_ml('BTC', '15m', True)
    config.print_status()
    
    print("\n" + "="*80)
    print("TEST: Disable ETH ML, keep BTC ML")
    print("="*80)
    config.enable_ml('ETH', False)
    config.print_status()
    
    print("\n" + "="*80)
    print("TEST: Show individual asset status")
    print("="*80)
    config.print_status('ETH')
