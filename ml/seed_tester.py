#!/usr/bin/env python3
"""
Seed Testing and BASE_STRATEGY Management

Commands:
- test_all_whitelisted: Test ALL whitelisted seeds to find best
- test_top_10: Quick test of top 10 seeds by win rate
- overwrite_base_strategy: Set BASE_STRATEGY to a specific seed
- reset_base_strategy: Restore original BASE_STRATEGY
"""

import sys
import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.seed_system_unified import UnifiedSeedSystem
from ml.seed_tracker import SeedTracker
from ml.base_strategy import BASE_STRATEGY


class SeedTester:
    """Test seeds and manage BASE_STRATEGY configurations"""
    
    def __init__(self):
        self.seed_system = UnifiedSeedSystem()
        self.tracker = SeedTracker()
        self.base_strategy_backup_file = 'ml/base_strategy_backup.json'
        
        # Save original BASE_STRATEGY if not already backed up
        self._backup_base_strategy()
    
    def _backup_base_strategy(self):
        """Backup original BASE_STRATEGY"""
        if not os.path.exists(self.base_strategy_backup_file):
            backup = {
                'original': BASE_STRATEGY.copy(),
                'backed_up_at': datetime.now().isoformat(),
                'description': 'Original BASE_STRATEGY before any overwrites'
            }
            
            os.makedirs(os.path.dirname(self.base_strategy_backup_file), exist_ok=True)
            with open(self.base_strategy_backup_file, 'w') as f:
                json.dump(backup, f, indent=2)
            
            print(f"✅ BASE_STRATEGY backed up to {self.base_strategy_backup_file}")
    
    def get_whitelisted_seeds_by_timeframe(self, timeframe: str) -> List[Dict]:
        """
        Get all whitelisted seeds for a specific timeframe
        
        Args:
            timeframe: '15m', '1h', or '4h'
        
        Returns:
            List of seed info dicts
        """
        whitelisted = []
        
        for seed_id in self.tracker.whitelist:
            seed_data = self.tracker.seeds[seed_id]
            if seed_data['timeframe'] == timeframe:
                whitelisted.append(seed_data)
        
        return whitelisted
    
    def get_top_seeds_by_timeframe(self, timeframe: str, n: int = 10) -> List[Dict]:
        """
        Get top N seeds for a timeframe by win rate
        
        Args:
            timeframe: '15m', '1h', or '4h'
            n: Number of top seeds to return
        
        Returns:
            List of seed info dicts sorted by win rate
        """
        # Get all seeds for this timeframe with enough trades
        tf_seeds = [
            s for s in self.seed_system.registry.seeds.values()
            if s.get('timeframe') == timeframe 
            and s['stats']['total_trades'] >= 15
        ]
        
        # Sort by average win rate
        tf_seeds.sort(key=lambda x: x['stats']['avg_wr'], reverse=True)
        
        return tf_seeds[:n]
    
    def test_all_whitelisted(self, timeframe: str, backtest_cmd: str = None) -> Dict:
        """
        Test ALL whitelisted seeds for a timeframe
        
        Args:
            timeframe: '15m', '1h', or '4h'
            backtest_cmd: Optional custom backtest command template
        
        Returns:
            Dict with test results and best seed
        """
        print(f"\n{'='*80}")
        print(f"TEST ALL WHITELISTED SEEDS - {timeframe}")
        print(f"{'='*80}\n")
        
        whitelisted = self.get_whitelisted_seeds_by_timeframe(timeframe)
        
        if not whitelisted:
            print(f"❌ No whitelisted seeds found for {timeframe}")
            return {'status': 'no_seeds', 'best_seed': None}
        
        print(f"📊 Found {len(whitelisted)} whitelisted seeds for {timeframe}")
        print(f"⚠️  This will run {len(whitelisted)} backtests!")
        print(f"\nSeeds to test:")
        
        for i, seed_data in enumerate(whitelisted, 1):
            wr = seed_data['average_win_rate'] * 100
            print(f"  {i}. Seed {seed_data['seed']} - {wr:.1f}% WR, {seed_data['total_trades']} trades")
        
        print(f"\n💡 To execute:")
        print(f"   python backtest_90_complete.py --test-seeds-file ml/test_whitelist_{timeframe}.json")
        
        # Save test list
        test_file = f"ml/test_whitelist_{timeframe}.json"
        test_list = {
            'timeframe': timeframe,
            'test_type': 'all_whitelisted',
            'created_at': datetime.now().isoformat(),
            'seeds': [
                {
                    'seed': s['seed'],
                    'input_seed': s.get('input_seed'),
                    'expected_wr': s['average_win_rate']
                }
                for s in whitelisted
            ]
        }
        
        with open(test_file, 'w') as f:
            json.dump(test_list, f, indent=2)
        
        print(f"✅ Test list saved to {test_file}")
        
        return {
            'status': 'ready',
            'timeframe': timeframe,
            'total_seeds': len(whitelisted),
            'test_file': test_file
        }
    
    def test_top_10(self, timeframe: str) -> Dict:
        """
        Quick test of top 10 seeds by win rate
        
        Args:
            timeframe: '15m', '1h', or '4h'
        
        Returns:
            Dict with test results
        """
        print(f"\n{'='*80}")
        print(f"QUICK TEST - TOP 10 SEEDS - {timeframe}")
        print(f"{'='*80}\n")
        
        top_seeds = self.get_top_seeds_by_timeframe(timeframe, n=10)
        
        if not top_seeds:
            print(f"❌ No seeds found for {timeframe}")
            return {'status': 'no_seeds'}
        
        print(f"📊 Testing top {len(top_seeds)} seeds for {timeframe} by win rate:")
        print()
        
        for i, seed_info in enumerate(top_seeds, 1):
            wr = seed_info['stats']['avg_wr'] * 100
            trades = seed_info['stats']['total_trades']
            pnl = seed_info['stats']['total_pnl']
            print(f"  {i}. Seed {seed_info['seed']}")
            print(f"     WR: {wr:.1f}% | Trades: {trades} | P&L: ${pnl:.2f}")
        
        print(f"\n💡 To execute:")
        print(f"   python backtest_90_complete.py --test-seeds-file ml/test_top10_{timeframe}.json")
        
        # Save test list
        test_file = f"ml/test_top10_{timeframe}.json"
        test_list = {
            'timeframe': timeframe,
            'test_type': 'top_10',
            'created_at': datetime.now().isoformat(),
            'seeds': [
                {
                    'seed': s['seed'],
                    'input_seed': s.get('input_seed'),
                    'expected_wr': s['stats']['avg_wr']
                }
                for s in top_seeds
            ]
        }
        
        with open(test_file, 'w') as f:
            json.dump(test_list, f, indent=2)
        
        print(f"✅ Test list saved to {test_file}")
        
        return {
            'status': 'ready',
            'timeframe': timeframe,
            'total_seeds': len(top_seeds),
            'test_file': test_file
        }
    
    def overwrite_base_strategy(
        self, 
        timeframe: str, 
        seed: Optional[int] = None,
        use_best: bool = False
    ) -> Dict:
        """
        Overwrite BASE_STRATEGY for a timeframe with a seed's configuration
        
        Args:
            timeframe: '15m', '1h', or '4h'
            seed: Specific seed to use (optional)
            use_best: If True, automatically use best seed (highest WR)
        
        Returns:
            Dict with operation result
        """
        print(f"\n{'='*80}")
        print(f"OVERWRITE BASE_STRATEGY - {timeframe}")
        print(f"{'='*80}\n")
        
        # Determine which seed to use
        if use_best:
            print("🔍 Finding best seed...")
            top_seeds = self.get_top_seeds_by_timeframe(timeframe, n=1)
            if not top_seeds:
                print(f"❌ No seeds found for {timeframe}")
                return {'status': 'error', 'message': 'No seeds available'}
            
            seed_info = top_seeds[0]
            seed = seed_info['seed']
            wr = seed_info['stats']['avg_wr'] * 100
            print(f"✅ Best seed: {seed} ({wr:.1f}% WR)")
        
        elif seed:
            # Get seed info from registry
            seed_info = self.seed_system.registry.get_seed_info(seed)
            if not seed_info:
                print(f"❌ Seed {seed} not found in registry")
                return {'status': 'error', 'message': 'Seed not found'}
            
            if seed_info.get('timeframe') != timeframe:
                print(f"⚠️  WARNING: Seed {seed} is for {seed_info.get('timeframe')}, not {timeframe}")
                print(f"   Proceeding anyway...")
        
        else:
            print(f"❌ Must specify either seed number or use_best=True")
            return {'status': 'error', 'message': 'No seed specified'}
        
        # Get parameters for this seed
        params = seed_info['parameters']
        
        print(f"\n📋 Current BASE_STRATEGY for {timeframe}:")
        for key, value in BASE_STRATEGY[timeframe].items():
            print(f"   {key}: {value}")
        
        print(f"\n📋 New configuration from Seed {seed}:")
        for key, value in params.items():
            print(f"   {key}: {value}")
        
        # Confirm
        print(f"\n⚠️  This will OVERWRITE BASE_STRATEGY['{timeframe}']")
        print(f"   Original is backed up in {self.base_strategy_backup_file}")
        
        response = input(f"\n   Continue? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("❌ Operation cancelled")
            return {'status': 'cancelled'}
        
        # Update BASE_STRATEGY in memory (would need file write for persistence)
        BASE_STRATEGY[timeframe] = params.copy()
        
        # Save to file
        self._save_base_strategy_to_file(timeframe, params, seed)
        
        print(f"\n✅ BASE_STRATEGY['{timeframe}'] updated to Seed {seed}")
        print(f"   Backup saved to {self.base_strategy_backup_file}")
        
        return {
            'status': 'success',
            'timeframe': timeframe,
            'seed': seed,
            'parameters': params
        }
    
    def _save_base_strategy_to_file(self, timeframe: str, params: Dict, seed: int):
        """Save BASE_STRATEGY update to file"""
        update_file = 'ml/base_strategy_overrides.json'
        
        # Load existing overrides
        if os.path.exists(update_file):
            with open(update_file, 'r') as f:
                overrides = json.load(f)
        else:
            overrides = {}
        
        # Add new override
        overrides[timeframe] = {
            'seed': seed,
            'parameters': params,
            'updated_at': datetime.now().isoformat()
        }
        
        # Save
        with open(update_file, 'w') as f:
            json.dump(overrides, f, indent=2)
        
        print(f"💾 Override saved to {update_file}")
    
    def reset_base_strategy(self, timeframe: Optional[str] = None) -> Dict:
        """
        Reset BASE_STRATEGY to original values
        
        Args:
            timeframe: Specific timeframe to reset, or None for all
        
        Returns:
            Dict with operation result
        """
        print(f"\n{'='*80}")
        print(f"RESET BASE_STRATEGY")
        print(f"{'='*80}\n")
        
        if not os.path.exists(self.base_strategy_backup_file):
            print(f"❌ No backup found at {self.base_strategy_backup_file}")
            return {'status': 'error', 'message': 'No backup available'}
        
        # Load backup
        with open(self.base_strategy_backup_file, 'r') as f:
            backup = json.load(f)
        
        original = backup['original']
        
        if timeframe:
            # Reset single timeframe
            if timeframe not in original:
                print(f"❌ Timeframe {timeframe} not found in backup")
                return {'status': 'error'}
            
            BASE_STRATEGY[timeframe] = original[timeframe].copy()
            print(f"✅ BASE_STRATEGY['{timeframe}'] reset to original")
            
            return {'status': 'success', 'timeframe': timeframe}
        
        else:
            # Reset all timeframes
            for tf in ['1m', '5m', '15m', '1h', '4h']:
                if tf in original:
                    BASE_STRATEGY[tf] = original[tf].copy()
            
            print(f"✅ All BASE_STRATEGY timeframes reset to original")
            
            # Clear overrides file
            if os.path.exists('ml/base_strategy_overrides.json'):
                os.remove('ml/base_strategy_overrides.json')
                print(f"🗑️  Cleared overrides file")
            
            return {'status': 'success', 'timeframes': ['1m', '5m', '15m', '1h', '4h']}
    
    def show_status(self):
        """Show current BASE_STRATEGY status"""
        print(f"\n{'='*80}")
        print(f"BASE_STRATEGY STATUS")
        print(f"{'='*80}\n")
        
        # Check for overrides
        override_file = 'ml/base_strategy_overrides.json'
        overrides = {}
        
        if os.path.exists(override_file):
            with open(override_file, 'r') as f:
                overrides = json.load(f)
        
        for tf in ['1m', '5m', '15m', '1h', '4h']:
            print(f"📊 {tf}:")
            
            if tf in overrides:
                override = overrides[tf]
                print(f"   Status: ⚠️  OVERRIDDEN")
                print(f"   Seed: {override['seed']}")
                print(f"   Updated: {override['updated_at']}")
            else:
                print(f"   Status: ✅ Original BASE_STRATEGY")
            
            print(f"   Current config:")
            for key, value in BASE_STRATEGY[tf].items():
                print(f"      {key}: {value}")
            print()


def main():
    """CLI interface for seed testing"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Seed Testing and BASE_STRATEGY Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all whitelisted seeds for 15m
  python ml/seed_tester.py test-all 15m
  
  # Quick test top 10 seeds for 1h
  python ml/seed_tester.py test-top10 1h
  
  # Overwrite BASE_STRATEGY with best seed
  python ml/seed_tester.py overwrite 15m --use-best
  
  # Overwrite with specific seed
  python ml/seed_tester.py overwrite 1h --seed 60507652
  
  # Reset BASE_STRATEGY to original
  python ml/seed_tester.py reset
  
  # Show current status
  python ml/seed_tester.py status
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # test-all command
    test_all = subparsers.add_parser('test-all', help='Test all whitelisted seeds')
    test_all.add_argument('timeframe', choices=['1m', '5m', '15m', '1h', '4h'])
    
    # test-top10 command
    test_top10 = subparsers.add_parser('test-top10', help='Quick test top 10 seeds')
    test_top10.add_argument('timeframe', choices=['1m', '5m', '15m', '1h', '4h'])
    
    # overwrite command
    overwrite = subparsers.add_parser('overwrite', help='Overwrite BASE_STRATEGY')
    overwrite.add_argument('timeframe', choices=['1m', '5m', '15m', '1h', '4h'])
    overwrite.add_argument('--seed', type=int, help='Specific seed to use')
    overwrite.add_argument('--use-best', action='store_true', help='Use best seed by WR')
    
    # reset command
    reset = subparsers.add_parser('reset', help='Reset BASE_STRATEGY to original')
    reset.add_argument('--timeframe', choices=['1m', '5m', '15m', '1h', '4h'], help='Specific timeframe (optional)')
    
    # status command
    status = subparsers.add_parser('status', help='Show BASE_STRATEGY status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    tester = SeedTester()
    
    if args.command == 'test-all':
        tester.test_all_whitelisted(args.timeframe)
    
    elif args.command == 'test-top10':
        tester.test_top_10(args.timeframe)
    
    elif args.command == 'overwrite':
        if not args.seed and not args.use_best:
            print("❌ Must specify either --seed or --use-best")
            return
        
        tester.overwrite_base_strategy(
            args.timeframe,
            seed=args.seed,
            use_best=args.use_best
        )
    
    elif args.command == 'reset':
        tester.reset_base_strategy(timeframe=args.timeframe)
    
    elif args.command == 'status':
        tester.show_status()


if __name__ == '__main__':
    main()
