"""
Seed Registry - Database of all tested seeds with performance stats

Tracks:
- Every seed tested
- Win rate, trade count, P&L
- Parameters used
- Test dates
- Best/worst performers

Like a Minecraft seed database - you can look up any seed's performance
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict


class SeedRegistry:
    """
    Registry tracking all tested strategy seeds and their performance
    """
    
    def __init__(self, registry_file: str = "ml/seed_registry.json"):
        self.registry_file = registry_file
        self.seeds = {}  # {seed: {stats, params, history}}
        self.load()
    
    def load(self):
        """Load registry from file"""
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                data = json.load(f)
                self.seeds = data.get('seeds', {})
            print(f"📊 Loaded seed registry: {len(self.seeds)} seeds tracked")
        else:
            print(f"📝 Creating new seed registry at {self.registry_file}")
            self.seeds = {}
    
    def save(self):
        """Save registry to file"""
        data = {
            'seeds': self.seeds,
            'last_updated': datetime.now().isoformat(),
            'total_seeds': len(self.seeds)
        }
        
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        with open(self.registry_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_seed(
        self,
        seed: int,
        timeframe: str,
        parameters: Dict,
        version: str = 'v1',
        input_seed: Optional[int] = None
    ):
        """
        Register a new seed (before testing)
        
        Args:
            seed: Strategy seed
            timeframe: '15m', '1h', '4h'
            parameters: Strategy parameters
            version: Parameter version
            input_seed: Optional input seed used to generate params
        """
        seed_key = str(seed)
        
        if seed_key not in self.seeds:
            self.seeds[seed_key] = {
                'seed': seed,
                'timeframe': timeframe,
                'parameters': parameters,
                'version': version,
                'input_seed': input_seed,
                'registered_at': datetime.now().isoformat(),
                'test_history': [],
                'stats': {
                    'total_tests': 0,
                    'total_trades': 0,
                    'total_wins': 0,
                    'total_losses': 0,
                    'total_pnl': 0.0,
                    'best_wr': 0.0,
                    'worst_wr': 1.0,
                    'avg_wr': 0.0
                }
            }
            self.save()
    
    def record_test_result(
        self,
        seed: int,
        test_results: Dict
    ):
        """
        Record backtest results for a seed
        
        Args:
            seed: Strategy seed
            test_results: Dict with:
                - win_rate: Float (0.0 to 1.0)
                - trades: Int
                - wins: Int
                - losses: Int
                - pnl: Float
                - test_date: ISO date string
                - dataset: str (e.g., 'ETH_90days')
        """
        seed_key = str(seed)
        
        if seed_key not in self.seeds:
            print(f"⚠️  Seed {seed} not registered, registering now...")
            # Register with minimal info
            self.seeds[seed_key] = {
                'seed': seed,
                'registered_at': datetime.now().isoformat(),
                'test_history': [],
                'stats': {
                    'total_tests': 0,
                    'total_trades': 0,
                    'total_wins': 0,
                    'total_losses': 0,
                    'total_pnl': 0.0,
                    'best_wr': 0.0,
                    'worst_wr': 1.0,
                    'avg_wr': 0.0
                }
            }
        
        # Add test result to history
        test_record = {
            'test_date': test_results.get('test_date', datetime.now().isoformat()),
            'dataset': test_results.get('dataset', 'unknown'),
            'win_rate': test_results['win_rate'],
            'trades': test_results['trades'],
            'wins': test_results['wins'],
            'losses': test_results['losses'],
            'pnl': test_results['pnl']
        }
        
        self.seeds[seed_key]['test_history'].append(test_record)
        
        # Update aggregate stats
        stats = self.seeds[seed_key]['stats']
        stats['total_tests'] += 1
        stats['total_trades'] += test_results['trades']
        stats['total_wins'] += test_results['wins']
        stats['total_losses'] += test_results['losses']
        stats['total_pnl'] += test_results['pnl']
        
        # Update best/worst WR
        wr = test_results['win_rate']
        if wr > stats['best_wr']:
            stats['best_wr'] = wr
        if wr < stats['worst_wr']:
            stats['worst_wr'] = wr
        
        # Calculate average WR across all tests
        if stats['total_trades'] > 0:
            stats['avg_wr'] = stats['total_wins'] / stats['total_trades']
        
        self.save()
    
    def get_seed_info(self, seed: int) -> Optional[Dict]:
        """Get full info for a seed"""
        return self.seeds.get(str(seed))
    
    def get_top_performers(self, n: int = 10, min_trades: int = 10) -> List[Dict]:
        """
        Get top performing seeds
        
        Args:
            n: Number of top seeds to return
            min_trades: Minimum trade count to be considered
            
        Returns:
            List of seed info dicts, sorted by win rate
        """
        valid_seeds = []
        
        for seed_key, info in self.seeds.items():
            stats = info['stats']
            if stats['total_trades'] >= min_trades:
                valid_seeds.append(info)
        
        # Sort by average win rate
        valid_seeds.sort(key=lambda x: x['stats']['avg_wr'], reverse=True)
        
        return valid_seeds[:n]
    
    def get_worst_performers(self, n: int = 10, min_trades: int = 10) -> List[Dict]:
        """Get worst performing seeds"""
        valid_seeds = []
        
        for seed_key, info in self.seeds.items():
            stats = info['stats']
            if stats['total_trades'] >= min_trades:
                valid_seeds.append(info)
        
        # Sort by average win rate (ascending)
        valid_seeds.sort(key=lambda x: x['stats']['avg_wr'])
        
        return valid_seeds[:n]
    
    def get_by_timeframe(self, timeframe: str) -> List[Dict]:
        """Get all seeds for a specific timeframe"""
        return [
            info for info in self.seeds.values()
            if info.get('timeframe') == timeframe
        ]
    
    def print_summary(self):
        """Print registry summary"""
        print("\n" + "="*80)
        print("SEED REGISTRY SUMMARY")
        print("="*80 + "\n")
        
        total_seeds = len(self.seeds)
        total_tests = sum(s['stats']['total_tests'] for s in self.seeds.values())
        total_trades = sum(s['stats']['total_trades'] for s in self.seeds.values())
        
        print(f"Total Seeds Tracked: {total_seeds}")
        print(f"Total Tests Run: {total_tests}")
        print(f"Total Trades: {total_trades}")
        
        # By timeframe
        by_timeframe = defaultdict(int)
        for info in self.seeds.values():
            tf = info.get('timeframe', 'unknown')
            by_timeframe[tf] += 1
        
        print(f"\nSeeds by Timeframe:")
        for tf, count in sorted(by_timeframe.items()):
            print(f"  {tf}: {count} seeds")
        
        # Top performers
        print(f"\n🏆 Top 5 Performers (min 10 trades):")
        top = self.get_top_performers(n=5, min_trades=10)
        if top:
            for i, info in enumerate(top, 1):
                stats = info['stats']
                seed = info['seed']
                tf = info.get('timeframe', '?')
                print(f"  {i}. Seed {seed} ({tf}): {stats['avg_wr']:.1%} WR, "
                      f"{stats['total_trades']} trades, ${stats['total_pnl']:+.2f} PnL")
        else:
            print("  (No seeds with 10+ trades yet)")
        
        # Worst performers
        print(f"\n📉 Worst 3 Performers (min 10 trades):")
        worst = self.get_worst_performers(n=3, min_trades=10)
        if worst:
            for i, info in enumerate(worst, 1):
                stats = info['stats']
                seed = info['seed']
                tf = info.get('timeframe', '?')
                print(f"  {i}. Seed {seed} ({tf}): {stats['avg_wr']:.1%} WR, "
                      f"{stats['total_trades']} trades, ${stats['total_pnl']:+.2f} PnL")
        else:
            print("  (No seeds with 10+ trades yet)")
    
    def export_to_csv(self, filename: str = "seed_registry.csv"):
        """Export registry to CSV for analysis"""
        import csv
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'seed', 'timeframe', 'version', 'input_seed',
                'total_tests', 'total_trades', 'avg_wr', 'best_wr', 'worst_wr',
                'total_pnl', 'registered_at'
            ])
            
            # Data
            for seed_key, info in self.seeds.items():
                stats = info['stats']
                writer.writerow([
                    info['seed'],
                    info.get('timeframe', ''),
                    info.get('version', ''),
                    info.get('input_seed', ''),
                    stats['total_tests'],
                    stats['total_trades'],
                    f"{stats['avg_wr']:.4f}",
                    f"{stats['best_wr']:.4f}",
                    f"{stats['worst_wr']:.4f}",
                    f"{stats['total_pnl']:.2f}",
                    info.get('registered_at', '')
                ])
        
        print(f"✅ Exported {len(self.seeds)} seeds to {filename}")


if __name__ == "__main__":
    # Demo usage
    print("="*80)
    print("SEED REGISTRY - Performance Database")
    print("="*80)
    
    # Create registry
    registry = SeedRegistry("ml/seed_registry_demo.json")
    
    # Register some test seeds
    print("\n1. Registering test seeds...")
    print("-"*80)
    
    test_seeds = [
        (15542880, '15m', {'min_confidence': 0.78, 'min_volume': 1.30}, 42),
        (15913535, '15m', {'min_confidence': 0.73, 'min_volume': 1.22}, 777),
        (60507652, '1h', {'min_confidence': 0.72, 'min_volume': 1.20}, 100),
    ]
    
    for seed, tf, params, input_seed in test_seeds:
        registry.register_seed(seed, tf, params, version='v1', input_seed=input_seed)
        print(f"  ✓ Registered seed {seed} ({tf})")
    
    # Record test results
    print("\n2. Recording test results...")
    print("-"*80)
    
    # Seed 42 performs well
    registry.record_test_result(15542880, {
        'win_rate': 0.75,
        'trades': 20,
        'wins': 15,
        'losses': 5,
        'pnl': 12.50,
        'dataset': 'ETH_90days'
    })
    print(f"  ✓ Recorded test for seed 15542880: 75% WR")
    
    # Seed 777 performs excellent
    registry.record_test_result(15913535, {
        'win_rate': 0.82,
        'trades': 18,
        'wins': 15,
        'losses': 3,
        'pnl': 18.30,
        'dataset': 'ETH_90days'
    })
    print(f"  ✓ Recorded test for seed 15913535: 82% WR")
    
    # Seed 100 performs poorly
    registry.record_test_result(60507652, {
        'win_rate': 0.45,
        'trades': 15,
        'wins': 7,
        'losses': 8,
        'pnl': -3.20,
        'dataset': 'ETH_90days'
    })
    print(f"  ✓ Recorded test for seed 60507652: 45% WR")
    
    # Print summary
    registry.print_summary()
    
    # Export to CSV
    print("\n" + "="*80)
    print("EXPORT")
    print("="*80 + "\n")
    registry.export_to_csv("seed_registry_demo.csv")
    
    print("\n" + "="*80)
    print("USAGE")
    print("="*80)
    print("""
To integrate with backtests:

1. At backtest start:
   registry = SeedRegistry()
   registry.register_seed(seed, timeframe, params, version='v1')

2. After backtest completes:
   registry.record_test_result(seed, {
       'win_rate': 0.75,
       'trades': 20,
       'wins': 15,
       'losses': 5,
       'pnl': 12.50,
       'dataset': 'ETH_90days'
   })

3. View performance anytime:
   registry.print_summary()
   best_seeds = registry.get_top_performers()
""")
