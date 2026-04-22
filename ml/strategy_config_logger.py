#!/usr/bin/env python3
"""
Strategy Configuration Logger
Provides transparent logging of which strategy configuration is active for each timeframe.

Shows REAL SHA-256 deterministic seeds with bidirectional traceability through the 4-layer tracking system:
- Layer 1: seed_registry.json (performance database)
- Layer 2: seed_snapshots.json (SHA-256 verification)
- Layer 3: seed_catalog.json (trade-by-trade records)
- Layer 4: seed_performance_tracker.json (whitelist/blacklist)

This module does NOT change strategy behavior - it only logs what's being used.
"""

import json
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class StrategyConfigLogger:
    """
    Logs strategy configuration sources and parameters with REAL seed system.
    Shows SHA-256 deterministic seeds with bidirectional traceability.
    """
    
    def __init__(self):
        self.config_sources = {}
        self.active_configs = {}
        
    def extract_strategy_params(self, config: Dict) -> Dict:
        """Extract parameters for seed generation (matches strategy_seed_generator.py)"""
        param_keys = [
            'min_confidence',
            'min_volume', 
            'min_trend',
            'min_adx',
            'min_roc',
            'atr_min',
            'atr_max'
        ]
        
        params = {}
        for key in param_keys:
            if key in config:
                params[key] = config[key]
        
        return params
    
    def calculate_config_hash(self, params: Dict) -> str:
        """Calculate SHA-256 hash of configuration (matches seed_catalog.py)"""
        # Create canonical JSON representation
        canonical = json.dumps(params, sort_keys=True)
        
        # Calculate SHA-256 hash
        hash_obj = hashlib.sha256(canonical.encode())
        return hash_obj.hexdigest()[:12]  # First 12 chars for display
    
    def lookup_input_seed(self, strategy_seed: int) -> Optional[int]:
        """Look up input seed from seed_registry.json if available"""
        registry_path = Path('ml/seed_registry.json')
        if not registry_path.exists():
            return None
        
        try:
            with open(registry_path, 'r') as f:
                data = json.load(f)
            
            seed_info = data.get('seeds', {}).get(str(strategy_seed))
            if seed_info:
                return seed_info.get('input_seed')
        except:
            pass
        
        return None
    
    def check_tracking_layers(self, strategy_seed: int) -> Dict[str, bool]:
        """Check if seed exists in all 4 tracking layers"""
        layers = {
            'registry': False,
            'snapshots': False,
            'catalog': False,
            'tracker': False
        }
        
        seed_str = str(strategy_seed)
        
        # Layer 1: seed_registry.json
        registry_path = Path('ml/seed_registry.json')
        if registry_path.exists():
            try:
                with open(registry_path, 'r') as f:
                    data = json.load(f)
                if seed_str in data.get('seeds', {}):
                    layers['registry'] = True
            except:
                pass
        
        # Layer 2: seed_snapshots.json
        snapshots_path = Path('ml/seed_snapshots.json')
        if snapshots_path.exists():
            try:
                with open(snapshots_path, 'r') as f:
                    data = json.load(f)
                if seed_str in data.get('snapshots', {}):
                    layers['snapshots'] = True
            except:
                pass
        
        # Layer 3: seed_catalog.json (check entries list)
        catalog_path = Path('ml/seed_catalog.json')
        if catalog_path.exists():
            try:
                with open(catalog_path, 'r') as f:
                    data = json.load(f)
                for entry in data.get('entries', []):
                    if entry.get('seed') == strategy_seed:
                        layers['catalog'] = True
                        break
            except:
                pass
        
        # Layer 4: seed_performance_tracker.json
        tracker_path = Path('ml/seed_performance_tracker.json')
        if tracker_path.exists():
            try:
                with open(tracker_path, 'r') as f:
                    data = json.load(f)
                if seed_str in data.get('seeds', {}):
                    layers['tracker'] = True
            except:
                pass
        
        return layers
    
    def get_tracking_stats(self, strategy_seed: int) -> Optional[Dict]:
        """Get performance stats from seed_registry.json if available"""
        registry_path = Path('ml/seed_registry.json')
        if not registry_path.exists():
            return None
        
        try:
            with open(registry_path, 'r') as f:
                data = json.load(f)
            
            seed_info = data.get('seeds', {}).get(str(strategy_seed))
            if seed_info:
                return seed_info.get('stats', {})
        except:
            pass
        
        return None
        
    def determine_config_source(self, timeframe: str, symbol: str = 'ETH') -> Dict:
        """
        Determine which strategy configuration is being used for a timeframe.
        
        Precedence order:
        1. User override (via CLI --seed)
        2. Fallback strategies (from grid search)
        3. ML learned strategies (if enabled)
        4. BASE_STRATEGY (always available)
        
        Args:
            timeframe: '1m', '5m', '15m', '1h', '4h'
            symbol: Asset symbol (ETH, BTC)
            
        Returns:
            Dict with 'source', 'file', 'config' keys
        """
        result = {
            'timeframe': timeframe,
            'symbol': symbol,
            'source': None,
            'source_file': None,
            'config': None,
            'seed': None,
            'notes': []
        }
        
        # Check for user override (this would be set by CLI args, not checked here)
        # User overrides are handled at runtime, not detectable from files
        
        # Check for fallback strategies
        fallback_path = Path('ml/fallback_strategies.json')
        if fallback_path.exists():
            try:
                with open(fallback_path, 'r') as f:
                    fallback_data = json.load(f)
                
                key = f"{symbol}USDT_{timeframe}"
                if key in fallback_data:
                    strategies = fallback_data[key].get('strategies', [])
                    if strategies:
                        # Use first strategy (best one from grid search)
                        best_strategy = strategies[0]
                        result['source'] = 'fallback'
                        result['source_file'] = 'ml/fallback_strategies.json'
                        result['config'] = best_strategy.get('config', {})
                        result['seed'] = best_strategy.get('seed')
                        result['notes'].append(f"Optimized from grid search ({len(strategies)} total)")
                        result['notes'].append(f"Updated: {fallback_data[key].get('updated_at', 'unknown')}")
                        return result
            except Exception as e:
                result['notes'].append(f"Error reading fallback strategies: {e}")
        
        # Check for ML learned strategies
        ml_config_path = Path('ml/ml_config.json')
        learned_path = Path('ml/learned_strategies.json')
        
        if ml_config_path.exists() and learned_path.exists():
            try:
                # Check if ML is enabled for this symbol
                with open(ml_config_path, 'r') as f:
                    ml_config = json.load(f)
                
                if ml_config.get('assets', {}).get(symbol, {}).get('ml_enabled', False):
                    with open(learned_path, 'r') as f:
                        learned_data = json.load(f)
                    
                    if timeframe in learned_data:
                        result['source'] = 'ml_learned'
                        result['source_file'] = 'ml/learned_strategies.json'
                        result['config'] = learned_data[timeframe].get('config', {})
                        result['seed'] = learned_data[timeframe].get('seed')
                        result['notes'].append('Adaptive ML learning enabled')
                        result['notes'].append(f"Performance: {learned_data[timeframe].get('win_rate', 0):.1%} WR")
                        return result
            except Exception as e:
                result['notes'].append(f"Error reading ML config: {e}")
        
        # Fall back to BASE_STRATEGY
        try:
            from ml.base_strategy import BASE_STRATEGY
            
            if timeframe in BASE_STRATEGY:
                result['source'] = 'base'
                result['source_file'] = 'ml/base_strategy.py'
                result['config'] = BASE_STRATEGY[timeframe].copy()
                result['seed'] = BASE_STRATEGY[timeframe].get('seed')
                result['notes'].append('Immutable fallback (always available)')
                
                # Check if this is because nothing else exists
                if not fallback_path.exists():
                    result['notes'].append('⚠️  No fallback strategies - run grid search!')
                    
        except Exception as e:
            result['notes'].append(f"Error reading BASE_STRATEGY: {e}")
            
        return result
    
    def log_all_active_configs(self, active_timeframes: list, symbol: str = 'ETH', 
                                seed_override: Optional[int] = None) -> None:
        """
        Log configuration for all active timeframes.
        
        Args:
            active_timeframes: List of timeframes to check
            symbol: Asset symbol
            seed_override: If provided, user specified a seed override
        """
        print("\n" + "="*80)
        print("📋 ACTIVE STRATEGY CONFIGURATION")
        print("="*80)
        
        if seed_override:
            print(f"⚡ USER OVERRIDE: Seed {seed_override} specified via CLI")
            print(f"   All strategies will use this seed for deterministic testing")
            print()
        
        print(f"Symbol: {symbol}")
        print(f"Active Timeframes: {', '.join(active_timeframes)}")
        print()
        
        print("Strategy Source Priority Order:")
        print("  1. User Override (--seed flag)")
        print("  2. Fallback Strategies (grid search optimized)")
        print("  3. ML Learned Strategies (adaptive)")
        print("  4. BASE_STRATEGY (fallback)")
        print()
        
        for tf in active_timeframes:
            config_info = self.determine_config_source(tf, symbol)
            self.active_configs[tf] = config_info
            
            print(f"{'─'*80}")
            print(f"⏱️  {tf.upper()} Timeframe")
            print(f"{'─'*80}")
            
            source_icons = {
                'base': '📋',
                'fallback': '🎯',
                'ml_learned': '🤖',
                'user_override': '⚡'
            }
            
            icon = source_icons.get(config_info['source'], '❓')
            source_name = {
                'base': 'BASE_STRATEGY',
                'fallback': 'Fallback Strategy (Grid Search)',
                'ml_learned': 'ML Learned Strategy',
                'user_override': 'User Override'
            }.get(config_info['source'], 'Unknown')
            
            print(f"Source: {icon} {source_name}")
            if config_info['source_file']:
                print(f"File:   {config_info['source_file']}")
            
            # Calculate REAL SHA-256 deterministic seed
            config = config_info.get('config', {})
            if config:
                # Extract params and generate strategy seed
                params = self.extract_strategy_params(config)
                
                if params:
                    # Generate deterministic seed from parameters (SHA-256 hash)
                    try:
                        from ml.strategy_seed_generator import generate_strategy_seed
                        strategy_seed = generate_strategy_seed(tf, params)
                    except Exception as e:
                        strategy_seed = None
                        print(f"\n⚠️  Could not generate strategy seed: {e}")
                    
                    if strategy_seed:
                        # Calculate config hash for verification
                        config_hash = self.calculate_config_hash(params)
                        
                        # Look up input seed (for reproduction)
                        input_seed = self.lookup_input_seed(strategy_seed)
                        
                        # Check tracking layers
                        tracking = self.check_tracking_layers(strategy_seed)
                        
                        # Get performance stats if available
                        stats = self.get_tracking_stats(strategy_seed)
                        
                        print(f"\n🔑 Seed Information:")
                        print(f"  Strategy Seed:  {strategy_seed} (SHA-256 deterministic hash)")
                        if input_seed:
                            print(f"  Input Seed:     {input_seed} (use to reproduce these params)")
                        print(f"  Config Hash:    {config_hash} (SHA-256 verification)")
                        
                        # Show tracking status
                        print(f"\n📊 Tracking Status:")
                        registry_status = "✅" if tracking['registry'] else "❌"
                        snapshots_status = "✅" if tracking['snapshots'] else "❌"
                        catalog_status = "✅" if tracking['catalog'] else "❌"
                        tracker_status = "✅" if tracking['tracker'] else "❌"
                        
                        print(f"  {registry_status} Layer 1: seed_registry.json", end="")
                        if stats and tracking['registry']:
                            total_trades = stats.get('total_trades', 0)
                            avg_wr = stats.get('avg_wr', 0)
                            print(f" ({total_trades} trades, {avg_wr:.1%} WR)")
                        else:
                            print(" (not yet tracked)")
                        
                        print(f"  {snapshots_status} Layer 2: seed_snapshots.json", end="")
                        print(" (verified)" if tracking['snapshots'] else " (not yet verified)")
                        
                        print(f"  {catalog_status} Layer 3: seed_catalog.json", end="")
                        print(" (all trades logged)" if tracking['catalog'] else " (no trades logged)")
                        
                        print(f"  {tracker_status} Layer 4: seed_performance_tracker.json", end="")
                        if tracking['tracker']:
                            print(" (tracked)")
                        else:
                            print(" (not yet tracked)")
                
                print(f"\nKey Parameters:")
                print(f"  Min Confidence: {config.get('min_confidence', 'N/A')}")
                print(f"  Min Volume:     {config.get('min_volume', 'N/A')}×")
                print(f"  Min Trend:      {config.get('min_trend', 'N/A')}")
                print(f"  Min ADX:        {config.get('min_adx', 'N/A')}")
                print(f"  Min ROC:        {config.get('min_roc', 'N/A')}")
                print(f"  ATR Range:      {config.get('atr_min', 'N/A')} - {config.get('atr_max', 'N/A')}")
            
            # Print notes
            print(f"\nNotes:")
            if params and strategy_seed:
                print(f"  • Seed is bidirectionally traceable through 4-layer system")
                if input_seed:
                    print(f"  • To reproduce: python3 -c \"from ml.seed_to_strategy import seed_to_strategy; print(seed_to_strategy('{tf}', {input_seed}))\"")
                else:
                    print(f"  • To verify: Check config_hash {config_hash} in seed_snapshots.json")
            
            if config_info['notes']:
                for note in config_info['notes']:
                    print(f"  • {note}")
            
            print()
        
        print("="*80)
        print()
    
    def log_strategy_comparison(self, timeframe: str, symbol: str = 'ETH') -> None:
        """
        Show comparison of all available strategies for a timeframe.
        Useful for understanding what would change if you switched sources.
        
        Args:
            timeframe: Timeframe to compare
            symbol: Asset symbol
        """
        print(f"\n{'='*80}")
        print(f"📊 STRATEGY COMPARISON: {symbol} {timeframe}")
        print(f"{'='*80}\n")
        
        # Get BASE_STRATEGY
        try:
            from ml.base_strategy import BASE_STRATEGY
            base_config = BASE_STRATEGY.get(timeframe, {})
            print(f"📋 BASE_STRATEGY:")
            print(f"   Confidence: {base_config.get('min_confidence', 'N/A')}")
            print(f"   Volume:     {base_config.get('min_volume', 'N/A')}×")
            print(f"   ADX:        {base_config.get('min_adx', 'N/A')}")
            print()
        except:
            print(f"❌ BASE_STRATEGY not available\n")
        
        # Get Fallback strategy
        fallback_path = Path('ml/fallback_strategies.json')
        if fallback_path.exists():
            try:
                with open(fallback_path, 'r') as f:
                    fallback_data = json.load(f)
                key = f"{symbol}USDT_{timeframe}"
                if key in fallback_data and fallback_data[key].get('strategies'):
                    fb_config = fallback_data[key]['strategies'][0]['config']
                    print(f"🎯 Fallback Strategy (Grid Search):")
                    print(f"   Confidence: {fb_config.get('min_confidence', 'N/A')}")
                    print(f"   Volume:     {fb_config.get('min_volume', 'N/A')}×")
                    print(f"   ADX:        {fb_config.get('min_adx', 'N/A')}")
                    print(f"   Updated:    {fallback_data[key].get('updated_at', 'unknown')[:10]}")
                    print()
            except:
                pass
        else:
            print(f"❌ No fallback strategies (run: python3 auto_strategy_updater.py --force)\n")
        
        # Get ML learned
        learned_path = Path('ml/learned_strategies.json')
        if learned_path.exists():
            try:
                with open(learned_path, 'r') as f:
                    learned_data = json.load(f)
                if timeframe in learned_data:
                    ml_config = learned_data[timeframe].get('config', {})
                    print(f"🤖 ML Learned Strategy:")
                    print(f"   Confidence: {ml_config.get('min_confidence', 'N/A')}")
                    print(f"   Volume:     {ml_config.get('min_volume', 'N/A')}×")
                    print(f"   ADX:        {ml_config.get('min_adx', 'N/A')}")
                    print(f"   Win Rate:   {learned_data[timeframe].get('win_rate', 0):.1%}")
                    print()
            except:
                pass
        
        print(f"{'='*80}\n")
    
    def export_config_snapshot(self, output_file: str = 'ml/strategy_snapshot.json') -> None:
        """
        Export current configuration snapshot to file.
        Useful for tracking what was used in a backtest.
        
        Args:
            output_file: Path to save snapshot
        """
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'active_configs': self.active_configs,
            'note': 'Snapshot of strategy configurations at backtest start'
        }
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        print(f"📸 Strategy snapshot saved to: {output_file}")


# Convenience function
def log_strategy_config(active_timeframes: list, symbol: str = 'ETH', 
                        seed_override: Optional[int] = None) -> StrategyConfigLogger:
    """
    Quick function to log strategy configuration.
    
    Args:
        active_timeframes: List of active timeframes
        symbol: Asset symbol
        seed_override: User-specified seed if any
        
    Returns:
        StrategyConfigLogger instance
    """
    logger = StrategyConfigLogger()
    logger.log_all_active_configs(active_timeframes, symbol, seed_override)
    return logger


if __name__ == "__main__":
    # Test the logger
    print("Testing Strategy Configuration Logger")
    print()
    
    logger = StrategyConfigLogger()
    
    # Test single timeframe
    print("Testing single timeframe determination:")
    config = logger.determine_config_source('15m', 'ETH')
    print(f"15m config source: {config['source']}")
    print(f"Config: {config['config']}")
    print()
    
    # Test all timeframes
    logger.log_all_active_configs(['1m', '5m', '15m', '1h', '4h'], 'ETH')
    
    # Test comparison
    logger.log_strategy_comparison('15m', 'ETH')
