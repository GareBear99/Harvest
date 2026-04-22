"""
Seed Catalog - Comprehensive Database for Every Backtest Run

Stores EVERYTHING for troubleshooting:
- Complete configuration
- All trades executed
- Market conditions
- Errors/warnings
- Performance metrics
- Timestamps
- Data files used

Categorized by:
- Timeframe
- Performance tier (excellent/good/poor)
- Date ranges
- Asset
- Version
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict


class SeedCatalog:
    """
    Complete catalog of every backtest run for troubleshooting
    """
    
    def __init__(self, catalog_file: str = "ml/seed_catalog.json"):
        self.catalog_file = catalog_file
        self.entries = []  # List of all backtest entries
        self.index = {
            'by_seed': {},
            'by_timeframe': defaultdict(list),
            'by_performance': defaultdict(list),
            'by_date': defaultdict(list),
            'by_asset': defaultdict(list),
            'by_version': defaultdict(list),
            'by_input_seed': {}
        }
        self.load()
    
    def load(self):
        """Load catalog from file"""
        if os.path.exists(self.catalog_file):
            with open(self.catalog_file, 'r') as f:
                data = json.load(f)
                self.entries = data.get('entries', [])
                self._rebuild_index()
            print(f"📚 Loaded seed catalog: {len(self.entries)} backtest runs")
        else:
            print(f"📚 Creating new seed catalog")
            self.entries = []
    
    def save(self):
        """Save catalog to file"""
        data = {
            'entries': self.entries,
            'last_updated': datetime.now().isoformat(),
            'total_runs': len(self.entries),
            'statistics': self._generate_statistics()
        }
        
        os.makedirs(os.path.dirname(self.catalog_file), exist_ok=True)
        with open(self.catalog_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _rebuild_index(self):
        """Rebuild search indexes"""
        self.index = {
            'by_seed': {},
            'by_timeframe': defaultdict(list),
            'by_performance': defaultdict(list),
            'by_date': defaultdict(list),
            'by_asset': defaultdict(list),
            'by_version': defaultdict(list),
            'by_input_seed': {}
        }
        
        for entry_id, entry in enumerate(self.entries):
            seed = entry['seed']
            self.index['by_seed'][seed] = entry_id
            self.index['by_timeframe'][entry['timeframe']].append(entry_id)
            self.index['by_performance'][self._categorize_performance(entry)].append(entry_id)
            self.index['by_date'][entry['run_date'][:10]].append(entry_id)
            self.index['by_asset'][entry.get('asset', 'unknown')].append(entry_id)
            self.index['by_version'][entry.get('version', 'v1')].append(entry_id)
            
            if entry.get('input_seed'):
                self.index['by_input_seed'][entry['input_seed']] = entry_id
    
    def _categorize_performance(self, entry: Dict) -> str:
        """Categorize performance for indexing"""
        wr = entry.get('win_rate', 0)
        if wr >= 0.75:
            return 'excellent'
        elif wr >= 0.65:
            return 'good'
        elif wr >= 0.50:
            return 'acceptable'
        else:
            return 'poor'
    
    def _generate_statistics(self) -> Dict:
        """Generate catalog statistics"""
        stats = {
            'total_runs': len(self.entries),
            'by_timeframe': {},
            'by_performance': {},
            'by_asset': {},
            'avg_win_rate': 0,
            'total_trades': 0
        }
        
        if not self.entries:
            return stats
        
        # Count by categories
        for entry in self.entries:
            tf = entry['timeframe']
            stats['by_timeframe'][tf] = stats['by_timeframe'].get(tf, 0) + 1
            
            perf = self._categorize_performance(entry)
            stats['by_performance'][perf] = stats['by_performance'].get(perf, 0) + 1
            
            asset = entry.get('asset', 'unknown')
            stats['by_asset'][asset] = stats['by_asset'].get(asset, 0) + 1
            
            stats['total_trades'] += entry.get('total_trades', 0)
        
        # Calculate average win rate
        total_wr = sum(e.get('win_rate', 0) for e in self.entries)
        stats['avg_win_rate'] = total_wr / len(self.entries)
        
        return stats
    
    def add_run(
        self,
        seed: int,
        timeframe: str,
        parameters: Dict,
        backtest_results: Dict,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Add a complete backtest run to catalog
        
        Args:
            seed: Strategy seed
            timeframe: '15m', '1h', '4h'
            parameters: Complete parameter set
            backtest_results: Full backtest results including:
                - win_rate
                - total_trades
                - wins, losses
                - total_pnl
                - trades: list of all trades
                - daily_stats: performance by day
            metadata: Optional metadata:
                - input_seed
                - version
                - asset
                - data_file
                - backtest_seed
                - errors
                - warnings
                
        Returns:
            Entry ID
        """
        metadata = metadata or {}
        
        entry = {
            'entry_id': len(self.entries),
            'run_date': datetime.now().isoformat(),
            
            # Seed info
            'seed': seed,
            'input_seed': metadata.get('input_seed'),
            'version': metadata.get('version', 'v1'),
            'timeframe': timeframe,
            
            # Configuration
            'parameters': parameters.copy(),
            'config_hash': self._hash_config(parameters),
            
            # Results
            'win_rate': backtest_results.get('win_rate', 0),
            'total_trades': backtest_results.get('total_trades', 0),
            'wins': backtest_results.get('wins', 0),
            'losses': backtest_results.get('losses', 0),
            'total_pnl': backtest_results.get('total_pnl', 0),
            
            # Detailed data
            'trades': backtest_results.get('trades', []),
            'daily_stats': backtest_results.get('daily_stats', {}),
            
            # Context
            'asset': metadata.get('asset', 'unknown'),
            'data_file': metadata.get('data_file', 'unknown'),
            'backtest_seed': metadata.get('backtest_seed'),
            'duration_days': metadata.get('duration_days', 0),
            
            # Issues
            'errors': metadata.get('errors', []),
            'warnings': metadata.get('warnings', []),
            'notes': metadata.get('notes', ''),
            
            # Performance metrics
            'max_drawdown': backtest_results.get('max_drawdown', 0),
            'sharpe_ratio': backtest_results.get('sharpe_ratio'),
            'profit_factor': backtest_results.get('profit_factor'),
            'avg_trade_duration': backtest_results.get('avg_trade_duration'),
            
            # Categorization
            'performance_tier': self._categorize_performance({'win_rate': backtest_results.get('win_rate', 0)})
        }
        
        self.entries.append(entry)
        
        # Update indexes
        entry_id = len(self.entries) - 1
        self.index['by_seed'][seed] = entry_id
        self.index['by_timeframe'][timeframe].append(entry_id)
        self.index['by_performance'][entry['performance_tier']].append(entry_id)
        self.index['by_date'][entry['run_date'][:10]].append(entry_id)
        self.index['by_asset'][entry['asset']].append(entry_id)
        self.index['by_version'][entry['version']].append(entry_id)
        
        if entry.get('input_seed'):
            self.index['by_input_seed'][entry['input_seed']] = entry_id
        
        self.save()
        
        return str(entry_id)
    
    def _hash_config(self, config: Dict) -> str:
        """Generate hash of configuration"""
        import hashlib
        sorted_config = dict(sorted(config.items()))
        config_str = json.dumps(sorted_config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def get_run(self, seed: int) -> Optional[Dict]:
        """Get run by seed"""
        entry_id = self.index['by_seed'].get(seed)
        if entry_id is not None:
            return self.entries[entry_id]
        return None
    
    def get_runs_by_timeframe(self, timeframe: str) -> List[Dict]:
        """Get all runs for a timeframe"""
        entry_ids = self.index['by_timeframe'].get(timeframe, [])
        return [self.entries[i] for i in entry_ids]
    
    def get_runs_by_performance(self, tier: str) -> List[Dict]:
        """Get runs by performance tier (excellent/good/acceptable/poor)"""
        entry_ids = self.index['by_performance'].get(tier, [])
        return [self.entries[i] for i in entry_ids]
    
    def get_runs_by_date(self, date: str) -> List[Dict]:
        """Get runs from a specific date (YYYY-MM-DD)"""
        entry_ids = self.index['by_date'].get(date, [])
        return [self.entries[i] for i in entry_ids]
    
    def get_runs_by_asset(self, asset: str) -> List[Dict]:
        """Get all runs for an asset (ETH, BTC, etc.)"""
        entry_ids = self.index['by_asset'].get(asset, [])
        return [self.entries[i] for i in entry_ids]
    
    def search(self, **filters) -> List[Dict]:
        """
        Search catalog with multiple filters
        
        Examples:
            search(timeframe='15m', performance_tier='excellent')
            search(asset='ETH', win_rate_min=0.70)
            search(total_trades_min=20)
        """
        results = self.entries.copy()
        
        # Apply filters
        if 'timeframe' in filters:
            results = [e for e in results if e['timeframe'] == filters['timeframe']]
        
        if 'performance_tier' in filters:
            results = [e for e in results if e['performance_tier'] == filters['performance_tier']]
        
        if 'asset' in filters:
            results = [e for e in results if e.get('asset') == filters['asset']]
        
        if 'version' in filters:
            results = [e for e in results if e.get('version') == filters['version']]
        
        if 'win_rate_min' in filters:
            results = [e for e in results if e.get('win_rate', 0) >= filters['win_rate_min']]
        
        if 'win_rate_max' in filters:
            results = [e for e in results if e.get('win_rate', 0) <= filters['win_rate_max']]
        
        if 'total_trades_min' in filters:
            results = [e for e in results if e.get('total_trades', 0) >= filters['total_trades_min']]
        
        if 'pnl_min' in filters:
            results = [e for e in results if e.get('total_pnl', 0) >= filters['pnl_min']]
        
        return results
    
    def compare_runs(self, seed1: int, seed2: int) -> Dict:
        """Compare two runs side by side"""
        run1 = self.get_run(seed1)
        run2 = self.get_run(seed2)
        
        if not run1 or not run2:
            return {'error': 'One or both runs not found'}
        
        comparison = {
            'seed1': seed1,
            'seed2': seed2,
            'metrics': {
                'win_rate': {
                    'seed1': run1['win_rate'],
                    'seed2': run2['win_rate'],
                    'diff': run2['win_rate'] - run1['win_rate']
                },
                'total_trades': {
                    'seed1': run1['total_trades'],
                    'seed2': run2['total_trades'],
                    'diff': run2['total_trades'] - run1['total_trades']
                },
                'total_pnl': {
                    'seed1': run1['total_pnl'],
                    'seed2': run2['total_pnl'],
                    'diff': run2['total_pnl'] - run1['total_pnl']
                }
            },
            'parameter_differences': self._compare_params(
                run1['parameters'],
                run2['parameters']
            )
        }
        
        return comparison
    
    def _compare_params(self, params1: Dict, params2: Dict) -> Dict:
        """Find parameter differences"""
        differences = {}
        all_keys = set(params1.keys()) | set(params2.keys())
        
        for key in all_keys:
            val1 = params1.get(key)
            val2 = params2.get(key)
            
            if val1 != val2:
                differences[key] = {
                    'seed1': val1,
                    'seed2': val2
                }
        
        return differences
    
    def print_summary(self):
        """Print catalog summary"""
        print("\n" + "="*80)
        print("SEED CATALOG SUMMARY")
        print("="*80)
        
        stats = self._generate_statistics()
        
        print(f"\nTotal Backtest Runs: {stats['total_runs']}")
        print(f"Total Trades Executed: {stats['total_trades']}")
        print(f"Average Win Rate: {stats['avg_win_rate']:.1%}")
        
        print(f"\n📊 By Timeframe:")
        for tf, count in sorted(stats['by_timeframe'].items()):
            print(f"  {tf}: {count} runs")
        
        print(f"\n🎯 By Performance:")
        for tier in ['excellent', 'good', 'acceptable', 'poor']:
            count = stats['by_performance'].get(tier, 0)
            print(f"  {tier.capitalize()}: {count} runs")
        
        print(f"\n💰 By Asset:")
        for asset, count in sorted(stats['by_asset'].items()):
            print(f"  {asset}: {count} runs")
    
    def export_troubleshooting_report(self, output_file: str = "troubleshooting_report.json"):
        """Export detailed report for troubleshooting"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self._generate_statistics(),
            'all_runs': self.entries,
            'indexes': {
                'by_seed': list(self.index['by_seed'].keys()),
                'by_timeframe': {k: len(v) for k, v in self.index['by_timeframe'].items()},
                'by_performance': {k: len(v) for k, v in self.index['by_performance'].items()},
            },
            'issues': self._collect_issues()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Exported troubleshooting report to {output_file}")
    
    def _collect_issues(self) -> Dict:
        """Collect all errors and warnings"""
        issues = {
            'runs_with_errors': [],
            'runs_with_warnings': [],
            'poor_performers': []
        }
        
        for entry in self.entries:
            if entry.get('errors'):
                issues['runs_with_errors'].append({
                    'seed': entry['seed'],
                    'errors': entry['errors']
                })
            
            if entry.get('warnings'):
                issues['runs_with_warnings'].append({
                    'seed': entry['seed'],
                    'warnings': entry['warnings']
                })
            
            if entry['performance_tier'] == 'poor':
                issues['poor_performers'].append({
                    'seed': entry['seed'],
                    'win_rate': entry['win_rate'],
                    'trades': entry['total_trades']
                })
        
        return issues


if __name__ == "__main__":
    print("="*80)
    print("SEED CATALOG - Comprehensive Troubleshooting Database")
    print("="*80)
    
    # Demo
    catalog = SeedCatalog("ml/seed_catalog_demo.json")
    
    # Add sample runs
    print("\n1. Adding sample backtest runs...")
    print("-"*80)
    
    # Good run
    catalog.add_run(
        seed=15913535,
        timeframe='15m',
        parameters={'min_confidence': 0.73, 'min_volume': 1.22},
        backtest_results={
            'win_rate': 0.82,
            'total_trades': 18,
            'wins': 15,
            'losses': 3,
            'total_pnl': 18.30,
            'trades': [{'pnl': 1.2}, {'pnl': 0.8}],  # Simplified
            'max_drawdown': 0.05
        },
        metadata={
            'input_seed': 777,
            'version': 'v1',
            'asset': 'ETH',
            'data_file': 'eth_90days.json',
            'backtest_seed': 42,
            'duration_days': 90
        }
    )
    print(f"✓ Added excellent run: seed=15913535")
    
    # Poor run
    catalog.add_run(
        seed=60507652,
        timeframe='1h',
        parameters={'min_confidence': 0.72, 'min_volume': 1.20},
        backtest_results={
            'win_rate': 0.45,
            'total_trades': 15,
            'wins': 7,
            'losses': 8,
            'total_pnl': -3.20,
            'trades': [],
            'max_drawdown': 0.15
        },
        metadata={
            'input_seed': 100,
            'version': 'v1',
            'asset': 'BTC',
            'data_file': 'btc_90days.json',
            'warnings': ['Low win rate', 'High drawdown']
        }
    )
    print(f"✓ Added poor run: seed=60507652")
    
    # Print summary
    catalog.print_summary()
    
    # Demo search
    print("\n" + "="*80)
    print("SEARCH EXAMPLES")
    print("="*80)
    
    excellent_runs = catalog.search(performance_tier='excellent')
    print(f"\n✓ Found {len(excellent_runs)} excellent runs")
    
    eth_runs = catalog.search(asset='ETH', win_rate_min=0.70)
    print(f"✓ Found {len(eth_runs)} ETH runs with 70%+ WR")
    
    # Export report
    print("\n" + "="*80)
    print("EXPORT")
    print("="*80 + "\n")
    catalog.export_troubleshooting_report("troubleshooting_demo.json")
    
    print("\n" + "="*80)
    print("USAGE")
    print("="*80)
    print("""
Integration:

1. After backtest:
   catalog = SeedCatalog()
   catalog.add_run(
       seed=strategy_seed,
       timeframe='15m',
       parameters=params,
       backtest_results={...},
       metadata={...}
   )

2. Search for troubleshooting:
   poor_runs = catalog.search(performance_tier='poor', asset='ETH')
   
3. Compare runs:
   comparison = catalog.compare_runs(seed1, seed2)
   
4. Export report:
   catalog.export_troubleshooting_report()
""")
