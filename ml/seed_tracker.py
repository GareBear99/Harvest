"""
Seed Performance Tracker - Never Use Bad Seeds Again

Maintains separate lists:
- All seeds tested (complete history)
- Good seeds (70%+ WR, suitable for reuse)
- Bad seeds (blacklist - never use again)
- Per-timeframe performance

Auto-filters seeds based on performance thresholds.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class SeedTracker:
    """
    Track all seeds and their performance
    
    Automatically categorizes:
    - Good seeds: 70%+ WR, 15+ trades
    - Bad seeds: <55% WR or <0 PnL (blacklisted)
    - Untested/insufficient data
    """
    
    def __init__(self, tracker_file: str = "ml/seed_performance_tracker.json"):
        self.tracker_file = tracker_file
        self.seeds = {}  # {seed: performance_data}
        self.blacklist = set()  # Seeds to never use
        self.whitelist = set()  # Proven good seeds
        self.load()
    
    def load(self):
        """Load tracker from file"""
        if os.path.exists(self.tracker_file):
            with open(self.tracker_file, 'r') as f:
                data = json.load(f)
                self.seeds = {int(k): v for k, v in data.get('seeds', {}).items()}
                self.blacklist = set(data.get('blacklist', []))
                self.whitelist = set(data.get('whitelist', []))
            
            print(f"📋 Loaded seed tracker:")
            print(f"   Total seeds: {len(self.seeds)}")
            print(f"   Whitelist (good): {len(self.whitelist)}")
            print(f"   Blacklist (bad): {len(self.blacklist)}")
        else:
            print(f"📋 Creating new seed tracker")
            self.seeds = {}
            self.blacklist = set()
            self.whitelist = set()
    
    def save(self):
        """Save tracker to file"""
        data = {
            'seeds': {str(k): v for k, v in self.seeds.items()},
            'blacklist': list(self.blacklist),
            'whitelist': list(self.whitelist),
            'last_updated': datetime.now().isoformat(),
            'statistics': self._generate_statistics()
        }
        
        os.makedirs(os.path.dirname(self.tracker_file), exist_ok=True)
        with open(self.tracker_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_performance(
        self,
        seed: int,
        timeframe: str,
        win_rate: float,
        total_trades: int,
        total_pnl: float,
        **kwargs
    ):
        """
        Record seed performance
        
        Args:
            seed: Strategy seed
            timeframe: '15m', '1h', '4h'
            win_rate: Win rate (0.0 to 1.0)
            total_trades: Number of trades
            total_pnl: Total profit/loss
            **kwargs: Additional metrics (wins, losses, max_drawdown, etc.)
        """
        if seed not in self.seeds:
            self.seeds[seed] = {
                'seed': seed,
                'first_tested': datetime.now().isoformat(),
                'timeframe': timeframe,
                'test_count': 0,
                'performance_history': []
            }
        
        seed_data = self.seeds[seed]
        
        # Record this test
        test_record = {
            'test_date': datetime.now().isoformat(),
            'win_rate': win_rate,
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'wins': kwargs.get('wins', 0),
            'losses': kwargs.get('losses', 0),
            'max_drawdown': kwargs.get('max_drawdown', 0)
        }
        
        seed_data['performance_history'].append(test_record)
        seed_data['test_count'] += 1
        
        # Update aggregate stats
        seed_data['latest_win_rate'] = win_rate
        seed_data['latest_trades'] = total_trades
        seed_data['latest_pnl'] = total_pnl
        seed_data['total_trades_all_tests'] = sum(
            t['total_trades'] for t in seed_data['performance_history']
        )
        seed_data['avg_win_rate'] = sum(
            t['win_rate'] for t in seed_data['performance_history']
        ) / len(seed_data['performance_history'])
        seed_data['total_pnl_all_tests'] = sum(
            t['total_pnl'] for t in seed_data['performance_history']
        )
        
        # Auto-categorize
        self._categorize_seed(seed)
        
        self.save()
    
    def _categorize_seed(self, seed: int):
        """Automatically categorize seed as good or bad"""
        seed_data = self.seeds[seed]
        
        # Need minimum data to categorize
        if seed_data['total_trades_all_tests'] < 15:
            return  # Insufficient data
        
        avg_wr = seed_data['avg_win_rate']
        total_pnl = seed_data['total_pnl_all_tests']
        
        # Blacklist criteria (BAD seeds - never use)
        if avg_wr < 0.55 or total_pnl < 0:
            if seed not in self.blacklist:
                self.blacklist.add(seed)
                print(f"  ⛔ BLACKLISTED seed {seed}: WR={avg_wr:.1%}, PnL=${total_pnl:.2f}")
            
            # Remove from whitelist if it was there
            if seed in self.whitelist:
                self.whitelist.discard(seed)
        
        # Whitelist criteria (GOOD seeds - safe to reuse)
        elif avg_wr >= 0.70 and total_pnl > 0:
            if seed not in self.whitelist:
                self.whitelist.add(seed)
                print(f"  ✅ WHITELISTED seed {seed}: WR={avg_wr:.1%}, PnL=${total_pnl:.2f}")
    
    def is_blacklisted(self, seed: int) -> bool:
        """Check if seed is blacklisted"""
        return seed in self.blacklist
    
    def is_whitelisted(self, seed: int) -> bool:
        """Check if seed is whitelisted"""
        return seed in self.whitelist
    
    def get_seed_status(self, seed: int) -> str:
        """Get seed status: 'blacklist', 'whitelist', 'neutral', or 'unknown'"""
        if seed in self.blacklist:
            return 'blacklist'
        elif seed in self.whitelist:
            return 'whitelist'
        elif seed in self.seeds:
            return 'neutral'
        else:
            return 'unknown'
    
    def get_good_seeds(self, timeframe: Optional[str] = None, min_trades: int = 15) -> List[int]:
        """
        Get all good seeds (whitelisted)
        
        Args:
            timeframe: Optional filter by timeframe
            min_trades: Minimum trades required
            
        Returns:
            List of seed IDs
        """
        good_seeds = []
        
        for seed in self.whitelist:
            seed_data = self.seeds[seed]
            
            # Apply filters
            if timeframe and seed_data.get('timeframe') != timeframe:
                continue
            
            if seed_data.get('total_trades_all_tests', 0) < min_trades:
                continue
            
            good_seeds.append(seed)
        
        return good_seeds
    
    def get_bad_seeds(self) -> List[int]:
        """Get all bad seeds (blacklisted)"""
        return list(self.blacklist)
    
    def get_seed_performance(self, seed: int) -> Optional[Dict]:
        """Get complete performance data for a seed"""
        return self.seeds.get(seed)
    
    def get_seeds_by_timeframe(self, timeframe: str) -> Dict[str, List[int]]:
        """
        Get seeds categorized by performance for a timeframe
        
        Returns:
            {
                'whitelist': [...],
                'blacklist': [...],
                'neutral': [...]
            }
        """
        result = {
            'whitelist': [],
            'blacklist': [],
            'neutral': []
        }
        
        for seed, data in self.seeds.items():
            if data.get('timeframe') != timeframe:
                continue
            
            status = self.get_seed_status(seed)
            if status in result:
                result[status].append(seed)
        
        return result
    
    def _generate_statistics(self) -> Dict:
        """Generate statistics"""
        stats = {
            'total_seeds': len(self.seeds),
            'whitelisted': len(self.whitelist),
            'blacklisted': len(self.blacklist),
            'neutral': len(self.seeds) - len(self.whitelist) - len(self.blacklist),
            'by_timeframe': {}
        }
        
        # Count by timeframe
        for seed_data in self.seeds.values():
            tf = seed_data.get('timeframe', 'unknown')
            if tf not in stats['by_timeframe']:
                stats['by_timeframe'][tf] = {
                    'total': 0,
                    'whitelist': 0,
                    'blacklist': 0
                }
            
            stats['by_timeframe'][tf]['total'] += 1
            
            seed = seed_data['seed']
            if seed in self.whitelist:
                stats['by_timeframe'][tf]['whitelist'] += 1
            elif seed in self.blacklist:
                stats['by_timeframe'][tf]['blacklist'] += 1
        
        return stats
    
    def print_summary(self):
        """Print tracker summary"""
        print("\n" + "="*80)
        print("SEED PERFORMANCE TRACKER")
        print("="*80)
        
        stats = self._generate_statistics()
        
        print(f"\nTotal Seeds Tracked: {stats['total_seeds']}")
        print(f"✅ Whitelist (Good): {stats['whitelisted']} seeds")
        print(f"⛔ Blacklist (Bad): {stats['blacklisted']} seeds")
        print(f"⚪ Neutral: {stats['neutral']} seeds")
        
        print(f"\n📊 By Timeframe:")
        for tf, data in sorted(stats['by_timeframe'].items()):
            print(f"  {tf}:")
            print(f"    Total: {data['total']}")
            print(f"    ✅ Good: {data['whitelist']}")
            print(f"    ⛔ Bad: {data['blacklist']}")
    
    def print_whitelist(self, timeframe: Optional[str] = None):
        """Print whitelisted seeds"""
        print("\n" + "="*80)
        print("WHITELISTED SEEDS (Safe to Reuse)")
        print("="*80)
        
        seeds = self.get_good_seeds(timeframe)
        
        if not seeds:
            print("\nNo whitelisted seeds yet")
            return
        
        print(f"\nFound {len(seeds)} good seeds")
        if timeframe:
            print(f"Filtered by: {timeframe}")
        
        for seed in sorted(seeds):
            data = self.seeds[seed]
            print(f"\n  Seed: {seed}")
            print(f"    Timeframe: {data['timeframe']}")
            print(f"    Avg WR: {data['avg_win_rate']:.1%}")
            print(f"    Total Trades: {data['total_trades_all_tests']}")
            print(f"    Total PnL: ${data['total_pnl_all_tests']:+.2f}")
            print(f"    Tests: {data['test_count']}")
    
    def print_blacklist(self):
        """Print blacklisted seeds"""
        print("\n" + "="*80)
        print("BLACKLISTED SEEDS (Never Use)")
        print("="*80)
        
        if not self.blacklist:
            print("\nNo blacklisted seeds")
            return
        
        print(f"\nBlacklisted: {len(self.blacklist)} seeds")
        
        for seed in sorted(self.blacklist):
            data = self.seeds[seed]
            print(f"\n  ⛔ Seed: {seed}")
            print(f"    Timeframe: {data['timeframe']}")
            print(f"    Avg WR: {data['avg_win_rate']:.1%}")
            print(f"    Total PnL: ${data['total_pnl_all_tests']:+.2f}")
            print(f"    Reason: {'Low WR' if data['avg_win_rate'] < 0.55 else 'Negative PnL'}")
    
    def export_seed_lists(self, output_dir: str = "ml"):
        """Export whitelist and blacklist to separate files"""
        # Whitelist
        whitelist_data = {
            'generated_at': datetime.now().isoformat(),
            'count': len(self.whitelist),
            'seeds': [
                {
                    'seed': seed,
                    'timeframe': self.seeds[seed]['timeframe'],
                    'avg_win_rate': self.seeds[seed]['avg_win_rate'],
                    'total_trades': self.seeds[seed]['total_trades_all_tests'],
                    'total_pnl': self.seeds[seed]['total_pnl_all_tests']
                }
                for seed in sorted(self.whitelist)
            ]
        }
        
        whitelist_file = os.path.join(output_dir, 'seed_whitelist.json')
        with open(whitelist_file, 'w') as f:
            json.dump(whitelist_data, f, indent=2)
        
        # Blacklist
        blacklist_data = {
            'generated_at': datetime.now().isoformat(),
            'count': len(self.blacklist),
            'seeds': [
                {
                    'seed': seed,
                    'timeframe': self.seeds[seed]['timeframe'],
                    'avg_win_rate': self.seeds[seed]['avg_win_rate'],
                    'total_pnl': self.seeds[seed]['total_pnl_all_tests'],
                    'reason': 'Low WR' if self.seeds[seed]['avg_win_rate'] < 0.55 else 'Negative PnL'
                }
                for seed in sorted(self.blacklist)
            ]
        }
        
        blacklist_file = os.path.join(output_dir, 'seed_blacklist.json')
        with open(blacklist_file, 'w') as f:
            json.dump(blacklist_data, f, indent=2)
        
        print(f"✅ Exported whitelist to {whitelist_file}")
        print(f"✅ Exported blacklist to {blacklist_file}")


if __name__ == "__main__":
    print("="*80)
    print("SEED PERFORMANCE TRACKER - Never Use Bad Seeds")
    print("="*80)
    
    # Demo
    tracker = SeedTracker("ml/seed_performance_tracker_demo.json")
    
    # Record some performances
    print("\n1. Recording seed performances...")
    print("-"*80)
    
    # Good seed
    tracker.record_performance(
        seed=15913535,
        timeframe='15m',
        win_rate=0.82,
        total_trades=18,
        total_pnl=18.30,
        wins=15,
        losses=3
    )
    
    # Another test of same good seed
    tracker.record_performance(
        seed=15913535,
        timeframe='15m',
        win_rate=0.78,
        total_trades=20,
        total_pnl=15.50,
        wins=16,
        losses=4
    )
    
    # Bad seed
    tracker.record_performance(
        seed=60507652,
        timeframe='1h',
        win_rate=0.45,
        total_trades=15,
        total_pnl=-3.20,
        wins=7,
        losses=8
    )
    
    # Another bad seed
    tracker.record_performance(
        seed=24012345,
        timeframe='4h',
        win_rate=0.52,
        total_trades=18,
        total_pnl=-5.40,
        wins=9,
        losses=9
    )
    
    # Summary
    tracker.print_summary()
    
    # Show lists
    tracker.print_whitelist()
    tracker.print_blacklist()
    
    # Export
    print("\n" + "="*80)
    print("EXPORT")
    print("="*80 + "\n")
    tracker.export_seed_lists()
    
    # Demo usage
    print("\n" + "="*80)
    print("USAGE EXAMPLE")
    print("="*80)
    print("""
Before testing a seed:

    tracker = SeedTracker()
    
    # Check if seed is blacklisted
    if tracker.is_blacklisted(seed):
        print(f"⛔ Seed {seed} is blacklisted - skipping")
        continue
    
    # Or get status
    status = tracker.get_seed_status(seed)
    if status == 'blacklist':
        print(f"⛔ Never use seed {seed}")
    elif status == 'whitelist':
        print(f"✅ Seed {seed} is proven good")
    
    # Get all good seeds for a timeframe
    good_15m_seeds = tracker.get_good_seeds(timeframe='15m')
    print(f"Safe to use: {good_15m_seeds}")
""")
